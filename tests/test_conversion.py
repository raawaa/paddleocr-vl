from __future__ import annotations

import json
from pathlib import Path

import pytest

from paddleocr_vl.conversion import Conversion, Input, JobProgress
from paddleocr_vl.errors import JobFailedError, JobTimeoutError, RateLimitError
from paddleocr_vl.media import materialize_media  # noqa: F401  (used in test indirectly)

from fake_api import FakeJobApi


def _build_jsonl() -> str:
    """Three-page JSONL with markdown text and a couple of image refs."""
    return "\n".join([
        json.dumps({
            "result": {
                "layoutParsingResults": [
                    {"markdown": {"text": "Hello, world.", "images": {}}}
                ]
            }
        }),
        json.dumps({
            "result": {
                "layoutParsingResults": [
                    {
                        "markdown": {
                            "text": "Second page.",
                            "images": {
                                "img1.jpg": "https://fake/img1.jpg",
                            },
                        },
                        "outputImages": {},
                    }
                ]
            }
        }),
        json.dumps({
            "result": {
                "layoutParsingResults": [
                    {
                        "markdown": {
                            "text": "Third page.",
                            "images": {},
                        },
                        "outputImages": {
                            "chart": "https://fake/chart.png",
                        },
                    }
                ]
            }
        }),
    ])


class _FakeResponse:
    def __init__(self, content: bytes = b"FAKE"):
        self.status_code = 200
        self.content = content


def _fake_get(url, timeout=60):
    return _FakeResponse(b"FAKE")


def test_run_pdf_happy_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    pdf_path = tmp_path / "input.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%fake")
    media_dir = tmp_path / "media"

    fake = FakeJobApi(
        job_id="job-abc",
        poll_responses=[{"state": "done", "resultUrl": {"jsonUrl": "https://fake/jsonl"}}],
        jsonl_text=_build_jsonl(),
    )
    monkeypatch.setattr("paddleocr_vl.media.requests.get", _fake_get)

    result = Conversion(api=fake).run(
        Input(source=pdf_path, media_dir=media_dir, options={})
    )

    assert result.job_id == "job-abc"
    assert result.media_dir == media_dir
    assert "Hello, world." in result.markdown
    assert "Second page." in result.markdown
    assert "Third page." in result.markdown
    assert result.elapsed_s >= 0

    assert (media_dir / "img1.jpg").exists()
    assert (media_dir / "img1.jpg").read_bytes() == b"FAKE"
    assert (media_dir / "chart_2.jpg").exists()
    assert (media_dir / "chart_2.jpg").read_bytes() == b"FAKE"

    assert fake.submit_calls == [(pdf_path, "", {})]
    assert fake.poll_calls == ["job-abc"]
    assert fake.download_calls == ["https://fake/jsonl"]


def test_run_url_happy_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Conversion.run accepts a URL string as source and routes it through
    the same submit/poll/download path as a file source."""
    media_dir = tmp_path / "media"
    url = "https://example.com/file.pdf"

    fake = FakeJobApi(
        job_id="job-url-1",
        poll_responses=[{"state": "done", "resultUrl": {"jsonUrl": "https://fake/jsonl"}}],
        jsonl_text=_build_jsonl(),
    )
    monkeypatch.setattr("paddleocr_vl.media.requests.get", _fake_get)

    result = Conversion(api=fake).run(
        Input(source=url, media_dir=media_dir, options={})
    )

    assert result.job_id == "job-url-1"
    assert result.media_dir == media_dir
    assert "Hello, world." in result.markdown
    assert "Second page." in result.markdown
    assert result.elapsed_s >= 0

    assert fake.submit_calls == [(url, "", {})]
    assert fake.poll_calls == ["job-url-1"]
    assert fake.download_calls == ["https://fake/jsonl"]


# ----- batch policy tests --------------------------------------------------

def _make_pdf(tmp_path: Path, name: str) -> Path:
    p = tmp_path / name
    p.write_bytes(b"%PDF-1.4\n%fake")
    return p


def test_run_batch_halts_on_rate_limit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When one PDF in a directory run hits RateLimitError, the batch loop
    stops iterating and returns the accumulated ok/fail counts (counting
    the remaining PDFs as failed)."""
    from paddleocr_vl.cli import _run_batch

    pdf1 = _make_pdf(tmp_path, "a.pdf")
    pdf2 = _make_pdf(tmp_path, "b.pdf")
    pdf3 = _make_pdf(tmp_path, "c.pdf")
    output_dir = tmp_path / "out"

    fake = FakeJobApi(
        job_id="job-halt",
        poll_responses=[
            {"state": "done", "resultUrl": {"jsonUrl": "https://fake/jsonl"}},
            RateLimitError("quota exhausted"),
            {"state": "done", "resultUrl": {"jsonUrl": "https://fake/jsonl"}},
        ],
        jsonl_text=_build_jsonl(),
    )
    monkeypatch.setattr("paddleocr_vl.media.requests.get", _fake_get)

    ok, fail = _run_batch(
        [pdf1, pdf2, pdf3],
        fake,
        output_dir=output_dir,
        options={},
    )

    assert ok == 1
    assert fail == 2
    assert (output_dir / "a.md").exists()
    assert not (output_dir / "b.md").exists()
    assert not (output_dir / "c.md").exists()
    assert len(fake.submit_calls) == 2
    assert len(fake.poll_calls) == 2


def test_run_batch_continues_on_other_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When one PDF hits a non-rate-limit PaddleOCRError (e.g. JobFailedError),
    the batch loop continues with the remaining PDFs."""
    from paddleocr_vl.cli import _run_batch

    pdf1 = _make_pdf(tmp_path, "a.pdf")
    pdf2 = _make_pdf(tmp_path, "b.pdf")
    pdf3 = _make_pdf(tmp_path, "c.pdf")
    output_dir = tmp_path / "out"

    fake = FakeJobApi(
        job_id="job-cont",
        poll_responses=[
            {"state": "done", "resultUrl": {"jsonUrl": "https://fake/jsonl"}},
            JobFailedError("ocr engine crashed"),
            {"state": "done", "resultUrl": {"jsonUrl": "https://fake/jsonl"}},
        ],
        jsonl_text=_build_jsonl(),
    )
    monkeypatch.setattr("paddleocr_vl.media.requests.get", _fake_get)

    ok, fail = _run_batch(
        [pdf1, pdf2, pdf3],
        fake,
        output_dir=output_dir,
        options={},
    )

    assert ok == 2
    assert fail == 1
    assert (output_dir / "a.md").exists()
    assert not (output_dir / "b.md").exists()
    assert (output_dir / "c.md").exists()
    assert len(fake.submit_calls) == 3
    assert len(fake.poll_calls) == 3


# ----- error-path tests --------------------------------------------------

def test_run_raises_job_failed_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`Conversion.run` raises `JobFailedError` when the API reports
    `state == "failed"`, surfacing the server's `errorMsg` in the message."""
    pdf_path = _make_pdf(tmp_path, "input.pdf")
    media_dir = tmp_path / "media"

    fake = FakeJobApi(
        job_id="job-failed",
        poll_responses=[
            {"state": "failed", "errorMsg": "ocr engine exploded"},
        ],
        jsonl_text=_build_jsonl(),
    )
    monkeypatch.setattr("paddleocr_vl.media.requests.get", _fake_get)

    with pytest.raises(JobFailedError, match="ocr engine exploded"):
        Conversion(api=fake).run(
            Input(source=pdf_path, media_dir=media_dir, options={})
        )


def test_run_raises_job_timeout_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`Conversion.run` raises `JobTimeoutError` when polling exceeds the
    configured timeout. The `FakeJobApi` records the call and signals
    timeout by raising the exception directly."""
    pdf_path = _make_pdf(tmp_path, "input.pdf")
    media_dir = tmp_path / "media"

    fake = FakeJobApi(
        job_id="job-tmo",
        poll_responses=[
            JobTimeoutError("作业超时 (1800s), job_id: job-tmo"),
        ],
        jsonl_text=_build_jsonl(),
    )
    monkeypatch.setattr("paddleocr_vl.media.requests.get", _fake_get)

    with pytest.raises(JobTimeoutError, match="作业超时"):
        Conversion(api=fake).run(
            Input(source=pdf_path, media_dir=media_dir, options={})
        )

    assert fake.poll_calls == ["job-tmo"]


def test_run_raises_rate_limit_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`Conversion.run` raises `RateLimitError` when `submit` raises it
    (e.g. the server returns HTTP 429)."""
    from paddleocr_vl.errors import RateLimitError as _RateLimitError
    pdf_path = _make_pdf(tmp_path, "input.pdf")
    media_dir = tmp_path / "media"

    fake = FakeJobApi(
        job_id="job-rl",
        submit_error=_RateLimitError("quota exhausted"),
        jsonl_text=_build_jsonl(),
    )
    monkeypatch.setattr("paddleocr_vl.media.requests.get", _fake_get)

    with pytest.raises(_RateLimitError, match="quota exhausted"):
        Conversion(api=fake).run(
            Input(source=pdf_path, media_dir=media_dir, options={})
        )

    assert len(fake.submit_calls) == 1
    assert fake.poll_calls == []


# ----- progress-callback test --------------------------------------------

def test_run_calls_progress_callback_with_typed_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The `on_progress` callback is invoked with `JobProgress` instances;
    `elapsed_s` and `extracted` increase monotonically, and `total`
    matches the fixture value across all events."""
    pdf_path = _make_pdf(tmp_path, "input.pdf")
    media_dir = tmp_path / "media"

    fake = FakeJobApi(
        job_id="job-prog",
        poll_responses=[
            {"extractProgress": {"totalPages": 10, "extractedPages": 3}},
            {"extractProgress": {"totalPages": 10, "extractedPages": 7}},
            {"state": "done", "resultUrl": {"jsonUrl": "https://fake/jsonl"}},
        ],
        jsonl_text=_build_jsonl(),
    )
    monkeypatch.setattr("paddleocr_vl.media.requests.get", _fake_get)

    progress_events: list[JobProgress] = []
    Conversion(api=fake).run(
        Input(source=pdf_path, media_dir=media_dir, options={}),
        on_progress=progress_events.append,
    )

    assert len(progress_events) == 2
    assert all(isinstance(e, JobProgress) for e in progress_events)
    assert progress_events[0].elapsed_s < progress_events[1].elapsed_s
    assert progress_events[0].extracted < progress_events[1].extracted
    assert progress_events[0].total == 10
    assert progress_events[1].total == 10


def test_spinner_does_not_know_api_field_names() -> None:
    """The spinner (UI) is decoupled from the API's field names. It must
    not contain `totalPages` or `extractedPages` — those are the API's
    vocabulary, surfaced through `JobProgress.total` / `.extracted`."""
    import inspect

    from paddleocr_vl import cli

    source = inspect.getsource(cli._Spinner)
    assert "totalPages" not in source
    assert "extractedPages" not in source

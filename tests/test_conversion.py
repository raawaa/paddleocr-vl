from __future__ import annotations

import json
from pathlib import Path

import pytest

from paddleocr_vl.conversion import Conversion, Input
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

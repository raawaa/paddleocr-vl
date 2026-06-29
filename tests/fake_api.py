from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from paddleocr_vl.conversion import JobProgress


class FakeJobApi:
    """In-memory JobApi for tests.

    Configure per-test via the constructor: a job_id to return from
    `submit`, a list of `poll` responses (or a `done` state), and
    JSONL text to return from `download`.

    `poll_responses` is consumed one entry per `poll()` call. Each entry
    can be either a dict (a normal poll body) or an `Exception` instance
    to raise. When the list is exhausted, `poll()` defaults to a `done`
    response. This lets a single FakeJobApi drive multi-step batch tests
    where each PDF gets its own `submit`/`poll` pair.
    """

    def __init__(
        self,
        *,
        job_id: str = "fake-job-1",
        poll_responses: list | None = None,
        jsonl_text: str = "",
    ):
        self._job_id = job_id
        self._poll_responses = list(poll_responses or [])
        self._jsonl_text = jsonl_text
        self.submit_calls: list[tuple] = []
        self.poll_calls: list[str] = []
        self.download_calls: list[str] = []
        self._poll_iter = iter(self._poll_responses)

    def submit(
        self,
        source,
        *,
        model: str = "",
        options: dict | None = None,
    ) -> str:
        self.submit_calls.append((source, model, dict(options or {})))
        return self._job_id

    def poll(
        self,
        job_id: str,
        *,
        on_progress: Callable[[JobProgress], None] | None = None,
        poll_interval: float = 5.0,
        timeout: float = 1800.0,
    ) -> dict:
        self.poll_calls.append(job_id)
        try:
            response = next(self._poll_iter)
        except StopIteration:
            response = {
                "state": "done",
                "resultUrl": {"jsonUrl": "https://fake/jsonl"},
            }

        if isinstance(response, Exception):
            raise response

        state = response.get("state", "")
        if state in ("done", "failed"):
            if on_progress:
                on_progress(JobProgress(elapsed_s=1, extracted=0, total=0))
            return response

        if on_progress:
            progress = response.get("extractProgress") or {}
            on_progress(JobProgress(
                elapsed_s=1,
                extracted=progress.get("extractedPages", 0),
                total=progress.get("totalPages", 0),
            ))
        return response

    def download(self, jsonl_url: str) -> str:
        self.download_calls.append(jsonl_url)
        return self._jsonl_text

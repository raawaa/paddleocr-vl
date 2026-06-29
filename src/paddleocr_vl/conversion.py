from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Protocol, runtime_checkable

from .errors import PaddleOCRError
from .media import materialize_media
from .parser import parse_jsonl


@dataclass(frozen=True)
class Input:
    source: Path | str
    media_dir: Path
    options: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ConversionResult:
    markdown: str
    media_dir: Path
    job_id: str
    elapsed_s: float


@dataclass(frozen=True)
class JobProgress:
    elapsed_s: int
    extracted: int
    total: int


ProgressCallback = Callable[[JobProgress], None]


@runtime_checkable
class JobApi(Protocol):
    def submit(
        self,
        source: Path | str,
        *,
        model: str,
        options: dict,
    ) -> str: ...

    def poll(
        self,
        job_id: str,
        *,
        on_progress: ProgressCallback | None = None,
    ) -> dict: ...

    def download(self, jsonl_url: str) -> str: ...


class Conversion:
    def __init__(self, api: JobApi):
        self._api = api

    def run(
        self,
        input: Input,
        *,
        on_progress: ProgressCallback | None = None,
    ) -> ConversionResult:
        t0 = time.time()
        job_id = self._api.submit(
            input.source, model="", options=input.options
        )
        result_data = self._api.poll(job_id, on_progress=on_progress)
        jsonl_url = result_data.get("resultUrl", {}).get("jsonUrl", "")
        if not jsonl_url:
            raise PaddleOCRError("无法获取 jsonl 结果 URL")
        jsonl_text = self._api.download(jsonl_url)
        parsed = parse_jsonl(jsonl_text)
        materialize_media(parsed, input.media_dir)
        markdown = "\n\n".join(p.text for p in parsed.pages if p.text)
        elapsed = time.time() - t0
        return ConversionResult(
            markdown=markdown,
            media_dir=input.media_dir,
            job_id=job_id,
            elapsed_s=elapsed,
        )

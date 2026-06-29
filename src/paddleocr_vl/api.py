from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Callable

import requests

from .conversion import JobProgress
from . import config as _config
from .errors import JobFailedError, JobTimeoutError, RateLimitError

API_BASE_URL = "https://paddleocr.aistudio-app.com/api/v2/ocr/jobs"
API_MODEL = "PaddleOCR-VL-1.6"
DEFAULT_OPTIONAL_PAYLOAD = {
    "useDocOrientationClassify": False,
    "useDocUnwarping": False,
    "useChartRecognition": False,
}
POLL_INTERVAL = 5
JOB_TIMEOUT = 1800
MAX_RETRIES = 3
RETRY_DELAY = 5


def read_api_token() -> str:
    token = os.environ.get("PADDLEOCR_API_TOKEN")
    if token:
        return token
    token = _config.read_token()
    if token:
        return token
    print(
        "错误: 未找到 API token\n"
        "  请通过以下任一方式配置:\n"
        f"    1. 运行: paddleocr-vl config set-token <token>\n"
        "    2. 设置环境变量: export PADDLEOCR_API_TOKEN='...'\n"
        f"    3. 编辑配置文件: {_config.get_config_path()}",
        file=sys.stderr,
    )
    sys.exit(1)


class RequestsJobApi:
    def __init__(
        self,
        api_token: str,
        *,
        api_base_url: str = API_BASE_URL,
        max_retries: int = MAX_RETRIES,
        retry_delay: float = RETRY_DELAY,
    ):
        self._token = api_token
        self._api_base_url = api_base_url
        self._max_retries = max_retries
        self._retry_delay = retry_delay

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"bearer {self._token}"}

    def submit(
        self,
        source: Path | str,
        *,
        model: str = API_MODEL,
        options: dict | None = None,
    ) -> str:
        payload = DEFAULT_OPTIONAL_PAYLOAD if options is None else options
        if isinstance(source, Path):
            return self._submit_file(source, model=model, payload=payload)
        return self._submit_url(str(source), model=model, payload=payload)

    def _submit_file(self, pdf_path: Path, *, model: str, payload: dict) -> str:
        last_error = ""
        for attempt in range(1, self._max_retries + 2):
            try:
                with open(pdf_path, "rb") as f:
                    files = {"file": (pdf_path.name, f, "application/pdf")}
                    data = {
                        "model": model,
                        "optionalPayload": json.dumps(payload),
                    }
                    resp = requests.post(
                        self._api_base_url,
                        headers=self._auth_headers(),
                        data=data,
                        files=files,
                        timeout=300,
                    )

                if resp.status_code == 429:
                    raise RateLimitError(resp.text[:200])

                if resp.status_code >= 500 and attempt <= self._max_retries:
                    delay = self._retry_delay * (2 ** (attempt - 1))
                    print(
                        f"  服务器错误 ({resp.status_code}), "
                        f"重试 {attempt}/{self._max_retries} ({delay}s)...",
                        file=sys.stderr,
                    )
                    time.sleep(delay)
                    last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                    continue

                resp.raise_for_status()
                return resp.json()["data"]["jobId"]

            except requests.RequestException as e:
                if attempt <= self._max_retries:
                    delay = self._retry_delay * (2 ** (attempt - 1))
                    print(
                        f"  请求失败: {e}, "
                        f"重试 {attempt}/{self._max_retries} ({delay}s)...",
                        file=sys.stderr,
                    )
                    time.sleep(delay)
                    last_error = str(e)
                    continue
                raise

        raise RuntimeError(
            f"提交失败 (重试 {self._max_retries} 次后): {last_error}"
        )

    def _submit_url(self, file_url: str, *, model: str, payload: dict) -> str:
        last_error = ""
        for attempt in range(1, self._max_retries + 2):
            try:
                body = {
                    "fileUrl": file_url,
                    "model": model,
                    "optionalPayload": payload,
                }
                resp = requests.post(
                    self._api_base_url,
                    json=body,
                    headers={
                        **self._auth_headers(),
                        "Content-Type": "application/json",
                    },
                    timeout=60,
                )

                if resp.status_code == 429:
                    raise RateLimitError(resp.text[:200])

                if resp.status_code >= 500 and attempt <= self._max_retries:
                    delay = self._retry_delay * (2 ** (attempt - 1))
                    print(
                        f"  服务器错误 ({resp.status_code}), "
                        f"重试 {attempt}/{self._max_retries} ({delay}s)...",
                        file=sys.stderr,
                    )
                    time.sleep(delay)
                    last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                    continue

                resp.raise_for_status()
                return resp.json()["data"]["jobId"]

            except requests.RequestException as e:
                if attempt <= self._max_retries:
                    delay = self._retry_delay * (2 ** (attempt - 1))
                    print(
                        f"  请求失败: {e}, "
                        f"重试 {attempt}/{self._max_retries} ({delay}s)...",
                        file=sys.stderr,
                    )
                    time.sleep(delay)
                    last_error = str(e)
                    continue
                raise

        raise RuntimeError(
            f"提交失败 (重试 {self._max_retries} 次后): {last_error}"
        )

    def poll(
        self,
        job_id: str,
        *,
        on_progress: Callable[[JobProgress], None] | None = None,
        poll_interval: float = POLL_INTERVAL,
        timeout: float = JOB_TIMEOUT,
    ) -> dict:
        poll_endpoint = f"{self._api_base_url}/{job_id}"
        start = time.time()

        while True:
            elapsed = time.time() - start
            if elapsed > timeout:
                raise JobTimeoutError(
                    f"作业超时 ({timeout}s), job_id: {job_id}"
                )

            try:
                resp = requests.get(
                    poll_endpoint, headers=self._auth_headers(), timeout=30
                )
                resp.raise_for_status()
            except requests.RequestException:
                if on_progress:
                    on_progress(JobProgress(int(elapsed), 0, 0))
                time.sleep(poll_interval)
                continue

            body = resp.json()
            data = body.get("data", {})
            state = data.get("state", "")

            if state == "done":
                return data
            elif state == "failed":
                err_msg = data.get("errorMsg") or "未知错误"
                raise JobFailedError(
                    f"作业失败: {err_msg} (job_id: {job_id})"
                )

            if on_progress:
                progress = data.get("extractProgress") or {}
                on_progress(JobProgress(
                    elapsed_s=int(elapsed),
                    extracted=progress.get("extractedPages", 0),
                    total=progress.get("totalPages", 0),
                ))

            time.sleep(poll_interval)

    def download(self, jsonl_url: str) -> str:
        resp = requests.get(jsonl_url, timeout=300)
        resp.raise_for_status()
        return resp.text


def submit_job(
    pdf_path: Path,
    api_token: str,
    *,
    api_base_url: str = API_BASE_URL,
    model: str = API_MODEL,
    optional_payload: dict | None = None,
    max_retries: int = MAX_RETRIES,
    retry_delay: float = RETRY_DELAY,
) -> str:
    """Thin shim — calls RequestsJobApi. Deprecated; will be removed in #4."""
    api = RequestsJobApi(
        api_token,
        api_base_url=api_base_url,
        max_retries=max_retries,
        retry_delay=retry_delay,
    )
    return api.submit(pdf_path, model=model, options=optional_payload)


def submit_job_url(
    file_url: str,
    api_token: str,
    *,
    api_base_url: str = API_BASE_URL,
    model: str = API_MODEL,
    optional_payload: dict | None = None,
    max_retries: int = MAX_RETRIES,
    retry_delay: float = RETRY_DELAY,
) -> str:
    """Thin shim — calls RequestsJobApi. Deprecated; will be removed in #4."""
    api = RequestsJobApi(
        api_token,
        api_base_url=api_base_url,
        max_retries=max_retries,
        retry_delay=retry_delay,
    )
    return api.submit(file_url, model=model, options=optional_payload)


def poll_job(
    api_token: str,
    job_id: str,
    *,
    api_base_url: str = API_BASE_URL,
    poll_interval: float = POLL_INTERVAL,
    timeout: float = JOB_TIMEOUT,
    progress_callback=None,
) -> dict:
    """Thin shim — calls RequestsJobApi. Deprecated; will be removed in #4."""
    api = RequestsJobApi(api_token, api_base_url=api_base_url)

    def _adapter(progress: JobProgress) -> None:
        if progress_callback is None:
            return
        progress_callback(int(progress.elapsed_s), {
            "totalPages": progress.total,
            "extractedPages": progress.extracted,
        })

    return api.poll(
        job_id,
        on_progress=_adapter,
        poll_interval=poll_interval,
        timeout=timeout,
    )


def download_result(json_url: str) -> str:
    """Thin shim — wraps requests.get. Deprecated; will be removed in #4."""
    resp = requests.get(json_url, timeout=300)
    resp.raise_for_status()
    return resp.text

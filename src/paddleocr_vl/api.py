import json
import os
import sys
import time
from pathlib import Path

import requests

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
    """提交 PDF 到 PaddleOCR API，返回 job_id。"""
    headers = {"Authorization": f"bearer {api_token}"}
    payload = DEFAULT_OPTIONAL_PAYLOAD if optional_payload is None else optional_payload
    last_error = ""

    for attempt in range(1, max_retries + 2):
        try:
            with open(pdf_path, "rb") as f:
                files = {"file": (pdf_path.name, f, "application/pdf")}
                data = {
                    "model": model,
                    "optionalPayload": json.dumps(payload),
                }
                resp = requests.post(
                    api_base_url,
                    headers=headers,
                    data=data,
                    files=files,
                    timeout=300,
                )

            if resp.status_code == 429:
                raise RateLimitError(resp.text[:200])

            if resp.status_code >= 500 and attempt <= max_retries:
                delay = retry_delay * (2 ** (attempt - 1))
                print(
                    f"  服务器错误 ({resp.status_code}), "
                    f"重试 {attempt}/{max_retries} ({delay}s)...",
                    file=sys.stderr,
                )
                time.sleep(delay)
                last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                continue

            resp.raise_for_status()
            return resp.json()["data"]["jobId"]

        except requests.RequestException as e:
            if attempt <= max_retries:
                delay = retry_delay * (2 ** (attempt - 1))
                print(
                    f"  请求失败: {e}, "
                    f"重试 {attempt}/{max_retries} ({delay}s)...",
                    file=sys.stderr,
                )
                time.sleep(delay)
                last_error = str(e)
                continue
            raise

    raise RuntimeError(f"提交失败 (重试 {max_retries} 次后): {last_error}")


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
    """通过远程 URL 提交 PDF 到 PaddleOCR API，返回 job_id。"""
    headers = {
        "Authorization": f"bearer {api_token}",
        "Content-Type": "application/json",
    }
    payload = DEFAULT_OPTIONAL_PAYLOAD if optional_payload is None else optional_payload
    last_error = ""

    for attempt in range(1, max_retries + 2):
        try:
            body = {
                "fileUrl": file_url,
                "model": model,
                "optionalPayload": payload,
            }
            resp = requests.post(
                api_base_url, json=body, headers=headers, timeout=60
            )

            if resp.status_code == 429:
                raise RateLimitError(resp.text[:200])

            if resp.status_code >= 500 and attempt <= max_retries:
                delay = retry_delay * (2 ** (attempt - 1))
                print(
                    f"  服务器错误 ({resp.status_code}), "
                    f"重试 {attempt}/{max_retries} ({delay}s)...",
                    file=sys.stderr,
                )
                time.sleep(delay)
                last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"
                continue

            resp.raise_for_status()
            return resp.json()["data"]["jobId"]

        except requests.RequestException as e:
            if attempt <= max_retries:
                delay = retry_delay * (2 ** (attempt - 1))
                print(
                    f"  请求失败: {e}, "
                    f"重试 {attempt}/{max_retries} ({delay}s)...",
                    file=sys.stderr,
                )
                time.sleep(delay)
                last_error = str(e)
                continue
            raise

    raise RuntimeError(f"提交失败 (重试 {max_retries} 次后): {last_error}")


def poll_job(
    api_token: str,
    job_id: str,
    *,
    api_base_url: str = API_BASE_URL,
    poll_interval: float = POLL_INTERVAL,
    timeout: float = JOB_TIMEOUT,
    progress_callback=None,
) -> dict:
    """轮询直至 job 完成或失败。返回 result data dict。

    progress_callback 签名: callback(elapsed_s, progress_dict | None)
    progress_dict 包含 extractProgress: {totalPages, extractedPages, ...}
    """
    poll_endpoint = f"{api_base_url}/{job_id}"
    headers = {"Authorization": f"bearer {api_token}"}
    start = time.time()

    while True:
        elapsed = time.time() - start
        if elapsed > timeout:
            raise JobTimeoutError(
                f"作业超时 ({timeout}s), job_id: {job_id}"
            )

        try:
            resp = requests.get(poll_endpoint, headers=headers, timeout=30)
            resp.raise_for_status()
        except requests.RequestException:
            if progress_callback:
                progress_callback(int(time.time() - start), None)
            time.sleep(poll_interval)
            continue

        body = resp.json()
        data = body.get("data", {})
        state = data.get("state", "")

        if state == "done":
            return data
        elif state == "failed":
            err_msg = data.get("errorMsg") or "未知错误"
            raise JobFailedError(f"作业失败: {err_msg} (job_id: {job_id})")

        if progress_callback:
            progress = data.get("extractProgress")
            progress_callback(int(time.time() - start), progress)

        time.sleep(poll_interval)


def download_result(json_url: str) -> str:
    """下载 JSONL 结果文件。"""
    resp = requests.get(json_url, timeout=300)
    resp.raise_for_status()
    return resp.text

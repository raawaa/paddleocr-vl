import json
from pathlib import Path

import requests


def parse_jsonl_to_markdown(
    jsonl_text: str,
    media_dir: Path,
    pdf_stem: str,
) -> str:
    """解析 JSONL 结果，提取 markdown 文本并下载图片。

    返回完整的 markdown 字符串（不写文件）。
    图片下载到 media_dir 中。
    """
    all_parts = []

    for line_num, line in enumerate(jsonl_text.strip().splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        result = obj.get("result", obj)
        for parsing_result in result.get("layoutParsingResults", []):
            md = parsing_result.get("markdown", {})
            text = md.get("text", "")
            if text:
                all_parts.append(text)

            for img_local_path, img_url in md.get("images", {}).items():
                img_full_path = media_dir / img_local_path
                img_full_path.parent.mkdir(parents=True, exist_ok=True)
                try:
                    img_resp = requests.get(img_url, timeout=60)
                    if img_resp.status_code == 200:
                        img_full_path.write_bytes(img_resp.content)
                except requests.RequestException:
                    pass

    return "\n\n".join(all_parts)

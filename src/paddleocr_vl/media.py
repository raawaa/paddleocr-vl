from __future__ import annotations

from pathlib import Path

import requests

from .parser import ParsedJsonl


def materialize_media(parsed: ParsedJsonl, media_dir: Path) -> None:
    """Download all images referenced by the parsed result into media_dir.

    markdown_images keep their local path from the JSONL response.
    outputImages get a `{name}_{page_num}.jpg` suffix per page.
    Network failures on individual images are silently skipped (matching
    the pre-refactor behavior).
    """
    for page_num, page in enumerate(parsed.pages):
        for img_local_path, img_url in page.markdown_images.items():
            img_full_path = media_dir / img_local_path
            img_full_path.parent.mkdir(parents=True, exist_ok=True)
            _download_to(img_url, img_full_path)

        for img_name, img_url in page.output_images.items():
            img_full_path = media_dir / f"{img_name}_{page_num}.jpg"
            img_full_path.parent.mkdir(parents=True, exist_ok=True)
            _download_to(img_url, img_full_path)


def _download_to(url: str, dest: Path) -> None:
    try:
        resp = requests.get(url, timeout=60)
        if resp.status_code == 200:
            dest.write_bytes(resp.content)
    except requests.RequestException:
        pass

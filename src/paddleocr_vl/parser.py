from __future__ import annotations

import json
from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedPage:
    text: str
    markdown_images: dict[str, str]
    output_images: dict[str, str]


@dataclass(frozen=True)
class ParsedJsonl:
    pages: list[ParsedPage]


def parse_jsonl(jsonl_text: str) -> ParsedJsonl:
    """Parse the JSONL result text into a structured form.

    Pure: no filesystem writes, no network IO. The image URL maps are
    preserved so a separate materialize step can download them.
    """
    pages: list[ParsedPage] = []
    for line in jsonl_text.strip().splitlines():
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
            pages.append(
                ParsedPage(
                    text=text,
                    markdown_images=dict(md.get("images", {})),
                    output_images=dict(
                        parsing_result.get("outputImages", {})
                    ),
                )
            )
    return ParsedJsonl(pages=pages)

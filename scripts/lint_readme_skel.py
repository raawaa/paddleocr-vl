#!/usr/bin/env python3
"""Lint 双语 README 的结构骨架一致性。

只校验 markdown 标记与结构元数据，不校验自然语言文字。
抓取规则集见本仓库 grill 决策（README 评估者导向 / 双语结构镜像承诺），
落点为 `scripts/lint_readme_skel.py`。

捕获的不一致（任何一个不一致都让脚本 exit 1）：
    1. `#` 标题层级序列（H1/H2/H3 出现的顺序）
    2. 代码块 fence 成对数（奇数 fence 报告未闭合）
    3. 每个代码块的 lang 标签序列（按 opening fence 顺序）
    4. 每张表格的 (行数, 列数) 序列
    5. 顶层 markdown 列表的项数

不抓取：标题文字、段落文字、表格单元格内容、链接 URL、行内代码。

用法：
    python scripts/lint_readme_skel.py README.md README.zh.md
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


HEADING_RE = re.compile(r"^(#+)\s")
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")
LIST_RE = re.compile(r"^(\s*)([-*+]|\d+\.)\s")


def skeleton(lines: list[str]) -> dict:
    headings: list[int] = []
    fence_langs: list[str] = []
    fence_open_close: list[str] = []
    in_code = False
    table_rows: int | None = None
    table_cols: int | None = None
    tables: list[tuple[int, int]] = []
    top_list_items = 0

    for line in lines:
        m = FENCE_RE.match(line)
        if m:
            if not in_code:
                meta = m.group(2).strip()
                lang = meta.split()[0] if meta else ""
                fence_langs.append(lang)
                fence_open_close.append("open")
                in_code = True
            else:
                fence_open_close.append("close")
                in_code = False
            continue

        if in_code:
            continue

        m = HEADING_RE.match(line)
        if m:
            headings.append(len(m.group(1)))
            continue

        if TABLE_ROW_RE.match(line):
            cols = line.count("|") - 1
            if table_rows is None:
                table_rows = 1
                table_cols = cols
            else:
                table_rows += 1
        else:
            if table_rows is not None:
                tables.append((table_rows, table_cols))
                table_rows = None
                table_cols = None

        m = LIST_RE.match(line)
        if m and len(m.group(1)) == 0:
            top_list_items += 1

    if table_rows is not None:
        tables.append((table_rows, table_cols))

    fence_count = len(fence_open_close)
    return {
        "heading_levels": headings,
        "fence_count": fence_count,
        "fence_paired": fence_count % 2 == 0,
        "fence_langs": fence_langs,
        "tables": tables,
        "top_list_items": top_list_items,
    }


def diff_skel(a: dict, b: dict, label_a: str, label_b: str) -> list[str]:
    msgs: list[str] = []

    if not a["fence_paired"]:
        msgs.append(f"{label_a}: fence_count={a['fence_count']} (odd — code block not closed)")
    if not b["fence_paired"]:
        msgs.append(f"{label_b}: fence_count={b['fence_count']} (odd — code block not closed)")

    def cmp(key: str, show_as: str = "repr") -> str | None:
        if a[key] == b[key]:
            return None
        if show_as == "repr":
            return f"  {key!r}:\n    {label_a}={a[key]!r}\n    {label_b}={b[key]!r}"
        return f"  {key}: {label_a}={a[key]} {label_b}={b[key]}"

    for key in ("heading_levels", "fence_langs", "tables", "top_list_items"):
        m = cmp(key)
        if m:
            msgs.append(m)
    return msgs


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(f"usage: {argv[0]} <skel-a> <skel-b> [<skel-c> ...]", file=sys.stderr)
        return 2

    paths = [Path(p) for p in argv[1:]]
    for p in paths:
        if not p.exists():
            print(f"error: file not found: {p}", file=sys.stderr)
            return 2

    skels = [skeleton(p.read_text(encoding="utf-8").splitlines()) for p in paths]
    base_skel = skels[0]
    base_path = paths[0]

    rc = 0
    for path, skel in zip(paths[1:], skels[1:]):
        msgs = diff_skel(base_skel, skel, str(base_path), str(path))
        if msgs:
            print(f"\n!!! Structural skeleton mismatch: {base_path} ↔ {path}", file=sys.stderr)
            for m in msgs:
                print(m, file=sys.stderr)
            rc = 1
        else:
            print(f"OK: {base_path} ↔ {path}  (skeleton matches)")

    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv))

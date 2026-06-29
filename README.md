# paddleocr-vl

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)

[English](README.md) | [中文](README.zh.md)

A CLI tool that converts PDFs (file, remote URL, or whole directory) to
Markdown using the [PaddleOCR-VL-1.6](https://github.com/PaddlePaddle/PaddleOCR)
Baidu API.

**Limits to know before you start:** the API is roughly free for the first
~20K pages per day, returns HTTP 429 once that runs out, and silently drops
pages beyond ~100 in a single PDF. See `docs/troubleshooting.md` for the
detailed behavior.

## Quick start

```bash
# 1. Install
uv tool install git+https://github.com/raawaa/paddleocr-vl.git

# 2. Save your token once
paddleocr-vl config set-token "your_token_here"

# 3. Convert
paddleocr-vl convert report.pdf
```

A conversion usually takes 5s to 2 minutes — a spinner runs on stderr and
prints the job time + character count when done. The Markdown file lands at
`report.md` next to your input.

> **Requirements:** Python 3.10+ and a PaddleOCR API token from
> [aistudio.baidu.com/paddleocr](https://aistudio.baidu.com/paddleocr).

## Examples

```bash
# Single PDF — input.pdf → input.md
paddleocr-vl convert report.pdf

# Remote URL — no local download needed
paddleocr-vl convert https://example.com/spec.pdf

# Batch — a directory of PDFs, each gets its own .md + media folder
paddleocr-vl convert ~/pdfs/ -o ~/out/

# Pipe to your editor
paddleocr-vl convert report.pdf --stdout | glow
```

## How it works

1. **Submit** — upload a PDF (or pass a remote URL) and receive a `jobId`
2. **Poll** — query the job state every 5 seconds
3. **Download** — fetch the JSONL with Markdown text and image URLs
4. **Parse** — assemble the Markdown and download images into a `_media` folder

## Documentation

- [Reference](docs/reference.md) — every CLI flag
- [Features & options](docs/features.md) — boolean toggles, numeric / string options, priority
- [Install](docs/install.md) — pip, local clone, `uv` upgrade
- [Troubleshooting](docs/troubleshooting.md) — errors, silent failures

## License

GNU General Public License v3.0 — see [LICENSE](LICENSE).

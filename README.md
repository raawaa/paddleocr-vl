# paddleocr-vl

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)

[English](README.md) | [中文](README.zh.md)

A CLI tool that converts PDFs to Markdown using the [PaddleOCR-VL-1.5](https://github.com/PaddlePaddle/PaddleOCR) Baidu API.

## Quick start

```bash
# 1. Install
uv tool install git+https://github.com/raawaa/paddleocr-vl.git

# 2. Set your API token (one-time)
paddleocr-vl config set-token "your_token_here"

# 3. Convert a PDF
paddleocr-vl convert report.pdf
```

Done. Your Markdown file is at `report.md`.

> **Requirements:** Python 3.10+ and a [PaddleOCR API token](https://aistudio.baidu.com/paddleocr).

### Alternative installation methods

```bash
# Via pip
pip install git+https://github.com/raawaa/paddleocr-vl.git

# Or run locally without installing
git clone https://github.com/raawaa/paddleocr-vl.git
cd paddleocr-vl
uv sync
uv run -m paddleocr_vl convert input.pdf
```

## Examples

```bash
# Convert a single PDF (output: input.pdf → input.md)
paddleocr-vl convert input.pdf

# Specify output path
paddleocr-vl convert input.pdf -o output/report.md

# Print Markdown to stdout (pipe to other tools like glow)
paddleocr-vl convert input.pdf --stdout | glow

# Process all PDFs in a directory
paddleocr-vl convert ~/pdfs/ -o ~/output/

# Enable optional features
paddleocr-vl convert input.pdf --chart-recognition
paddleocr-vl convert input.pdf --enable-all-features --no-doc-unwarping
```

## Configuration

### API token

The token is resolved in this order (first wins):

1. `--token` CLI argument
2. `PADDLEOCR_API_TOKEN` environment variable
3. Config file (`~/.config/paddleocr-vl/config.json` on Linux/macOS, `%APPDATA%\paddleocr-vl\config.json` on Windows)

```bash
# Option 1: CLI argument (per-invocation override)
paddleocr-vl convert input.pdf --token "your_token_here"

# Option 2: Environment variable
export PADDLEOCR_API_TOKEN="your_token_here"
paddleocr-vl convert input.pdf

# Option 3: Config file (set once, forget it)
paddleocr-vl config set-token "your_token_here"
paddleocr-vl convert input.pdf
```

### Optional features

The PaddleOCR-VL-1.5 API offers three optional processing features, all **disabled by default**:

| Feature | Flag | Description |
|---------|------|-------------|
| Document orientation classification | `--orientation-classify` | Auto-detect and correct page orientation |
| Document unwarping (deskew) | `--doc-unwarping` | Straighten curved or skewed document photos |
| Chart recognition | `--chart-recognition` | Extract and structure chart content |

Use individual flags to enable specific features, or `--enable-all-features` for all at once.

To persist preferences (so they apply automatically to every conversion):

```bash
paddleocr-vl config set-feature orientation-classify true
paddleocr-vl config remove-feature orientation-classify
```

When sources conflict, the effective setting follows this order (last wins):

1. Default — all disabled
2. Configuration file — persistent preferences
3. `--enable-all-features` — quick enable all
4. Individual flag — explicit override

### Config management commands

```bash
paddleocr-vl config set-token "your_token_here"   # save token
paddleocr-vl config remove-token                    # delete saved token
paddleocr-vl config set-feature <name> true|false   # save feature preference
paddleocr-vl config remove-feature <name>           # delete feature preference
paddleocr-vl config show                            # view current config
```

## Reference

```
paddleocr-vl convert <input> [options]

Positional arguments:
  input                 PDF file path or directory containing PDFs

Options:
  -o, --output PATH             Output path (file or directory)
  --stdout                      Write Markdown to stdout
  --media-dir PATH              Directory for extracted images
  --token TEXT                  API token
                                (default: config file or $PADDLEOCR_API_TOKEN)
  --api-base-url URL            API endpoint URL
                                (default: https://paddleocr.aistudio-app.com/api/v2/ocr/jobs)
  --model TEXT                  Model name (default: PaddleOCR-VL-1.5)
  --timeout SECONDS             Job timeout in seconds (default: 1800)
  --poll-interval SEC           Poll interval in seconds (default: 5)
  --enable-all-features         Enable all optional API features
  --orientation-classify /      Enable/disable document orientation classification
  --no-orientation-classify
  --doc-unwarping /             Enable/disable document unwarping (deskew)
  --no-doc-unwarping
  --chart-recognition /         Enable/disable chart recognition
  --no-chart-recognition
  --verbose, -v                 Verbose output
  --version, -V                 Show version
```

## How it works

The PaddleOCR API uses an **asynchronous job** model:

1. **submit** — upload the PDF file to the API endpoint, receive a `jobId`
2. **poll** — query the job status every 5 seconds until processing is done
3. **download** — fetch the JSONL result containing Markdown text and image URLs
4. **parse** — extract Markdown content and download embedded images locally

## License

This project is licensed under the GNU General Public License v3.0 — see the [LICENSE](LICENSE) file for details.

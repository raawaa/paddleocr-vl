# paddleocr-vl

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)

A CLI tool that converts PDFs to Markdown using the [PaddleOCR-VL-1.5](https://github.com/PaddlePaddle/PaddleOCR) Baidu API.

## Features

- **Single PDF conversion** — convert one PDF to Markdown with a single command
- **Batch conversion** — process entire directories of PDFs
- **stdout piping** — output Markdown to stdout for use with other tools (e.g., `glow`)
- **Asynchronous job processing** — submits PDFs to the API and polls for results with a live spinner
- **Automatic retry** — exponential backoff on server errors
- **Rate limit handling** — clean error on HTTP 429 (daily quota exhausted)
- **Image extraction** — downloads embedded images from the API result
- **Minimal dependencies** — only requires `requests`

## Requirements

- Python 3.10+
- A [PaddleOCR API](https://paddleocr.aistudio-app.com) token

## Installation

```bash
# Set your API token (required)
export PADDLEOCR_API_TOKEN="your_token_here"
```

### Via uv (recommended)

```bash
uv tool install git+https://github.com/raawaa/paddleocr-vl.git
```

### Via pip

```bash
pip install git+https://github.com/raawaa/paddleocr-vl.git
```

### Or run locally without installing

```bash
git clone https://github.com/raawaa/paddleocr-vl.git
cd paddleocr-vl
uv sync
uv run python -m paddleocr_vl convert input.pdf
```

## Usage

### Single file

```bash
# Output next to the PDF (input.pdf → input.md)
paddleocr-vl convert report.pdf

# Specify output path
paddleocr-vl convert report.pdf -o output/report.md

# Output to stdout (pipe to other tools)
paddleocr-vl convert report.pdf --stdout | glow
```

### Batch conversion

```bash
# Process all PDFs in a directory
paddleocr-vl convert ~/pdfs/ -o ~/output/
```

### Options

```
paddleocr-vl convert <input> [options]

Positional arguments:
  input                 PDF file path or directory containing PDFs

Options:
  -o, --output PATH     Output path (file or directory)
  --stdout              Write Markdown to stdout
  --media-dir PATH      Directory for extracted images
  --token TEXT          API token (default: $PADDLEOCR_API_TOKEN)
  --api-base-url URL    API endpoint URL
  --model TEXT          Model name (default: PaddleOCR-VL-1.5)
  --timeout SECONDS     Job timeout in seconds (default: 1800)
  --poll-interval SEC   Poll interval in seconds (default: 5)
  --enable-all-features Enable all optional API features
  --verbose, -v         Verbose output
  --version, -V         Show version
```

## How it works

The PaddleOCR API uses an **asynchronous job** model:

1. `submit` — upload the PDF file to the API endpoint, receive a `jobId`
2. `poll` — query the job status every 5 seconds until processing is done
3. `download` — fetch the JSONL result containing Markdown text and image URLs
4. `parse` — extract Markdown content and download embedded images locally

## Configuration

### Environment variables

| Variable | Description |
|----------|-------------|
| `PADDLEOCR_API_TOKEN` | PaddleOCR API token **(required)** |

### API optional features

By default, the following features are **disabled** to reduce processing time and cost:

- Document orientation classification
- Document unwarping (deskew)
- Chart recognition

Use `--enable-all-features` to enable all of them.

## License

This project is licensed under the GNU General Public License v3.0 — see the [LICENSE](LICENSE) file for details.

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
- A [PaddleOCR API](https://aistudio.baidu.com/paddleocr) token

## Installation

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

## Quick setup

Set your API token once — then just run `paddleocr-vl convert`:

```bash
paddleocr-vl config set-token "your_token_here"
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
  --token TEXT          API token (default: config file or $PADDLEOCR_API_TOKEN)
  --api-base-url URL    API endpoint URL
  --model TEXT          Model name (default: PaddleOCR-VL-1.5)
  --timeout SECONDS     Job timeout in seconds (default: 1800)
  --poll-interval SEC   Poll interval in seconds (default: 5)
  --enable-all-features
                        Enable all optional API features
  --orientation-classify / --no-orientation-classify
                        Enable/disable document orientation classification
  --doc-unwarping / --no-doc-unwarping
                        Enable/disable document unwarping (deskew)
  --chart-recognition / --no-chart-recognition
                        Enable/disable chart recognition
  --verbose, -v               Verbose output
  --version, -V               Show version
```

## How it works

The PaddleOCR API uses an **asynchronous job** model:

1. `submit` — upload the PDF file to the API endpoint, receive a `jobId`
2. `poll` — query the job status every 5 seconds until processing is done
3. `download` — fetch the JSONL result containing Markdown text and image URLs
4. `parse` — extract Markdown content and download embedded images locally

## Configuration

### API token

The token is resolved in this order (first wins):

1. `--token` CLI argument
2. `PADDLEOCR_API_TOKEN` environment variable
3. Config file at `~/.config/paddleocr-vl/config.json`

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

Manage your config:

```bash
paddleocr-vl config set-token "your_token_here"   # save token
paddleocr-vl config show                            # view current config
paddleocr-vl config remove-token                    # delete saved token
```

## Optional Features

The PaddleOCR-VL-1.5 API offers three optional processing features. All are **disabled by default** to reduce processing time and cost:

| Feature | CLI flag | Description |
|---------|----------|-------------|
| Document orientation classification | `--orientation-classify` | Auto-detect and correct page orientation |
| Document unwarping (deskew) | `--doc-unwarping` | Straighten curved or skewed document photos |
| Chart recognition | `--chart-recognition` | Extract and structure chart content |

### Via CLI flags

Use individual flags to enable specific features, or `--enable-all-features` for all at once:

```bash
# Enable only chart recognition
paddleocr-vl convert input.pdf --chart-recognition

# Enable all except document unwarping
paddleocr-vl convert input.pdf --enable-all-features --no-doc-unwarping
```

### Via configuration file (persistent)

Save preferences to the config file so they apply to every conversion automatically:

```bash
# Enable orientation classification permanently
paddleocr-vl config set-feature orientation-classify true

# Remove a saved feature setting
paddleocr-vl config remove-feature orientation-classify

# View current config including features
paddleocr-vl config show
```

### Priority

When multiple sources conflict, the effective setting follows this order (last wins):

1. Default — all disabled
2. Configuration file — persistent preferences
3. `--enable-all-features` — quick enable all
4. Individual flag (`--orientation-classify` / `--no-orientation-classify`, etc.) — explicit override

This means CLI flags always override config file settings for a single invocation.

## License

This project is licensed under the GNU General Public License v3.0 — see the [LICENSE](LICENSE) file for details.

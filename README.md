# paddleocr-vl

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)

[English](README.md) | [中文](README.zh.md)

A CLI tool that converts PDFs to Markdown using the [PaddleOCR-VL-1.6](https://github.com/PaddlePaddle/PaddleOCR) Baidu API.

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

# Convert from a remote PDF URL
paddleocr-vl convert https://example.com/document.pdf

# Enable optional features
paddleocr-vl convert input.pdf --chart-recognition
paddleocr-vl convert input.pdf --enable-all-features --no-doc-unwarping

# Tune model inference parameters
paddleocr-vl convert input.pdf --temperature 0.3 --top-p 0.9

# Cross-page table merging + heading restructuring
paddleocr-vl convert input.pdf --restructure-pages

# Disable layout detection, OCR only
paddleocr-vl convert input.pdf --no-layout-detection

# Fine-tune layout detection
paddleocr-vl convert input.pdf --layout-threshold 0.3 --layout-nms
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

The PaddleOCR-VL-1.6 API provides various optional parameters in three categories:

#### Boolean toggles

All **disabled by default** to save processing time and cost:

| Feature | Flag | Description |
|---------|------|-------------|
| Document orientation classification | `--orientation-classify` | Auto-detect and correct page orientation |
| Document unwarping (deskew) | `--doc-unwarping` | Straighten curved or skewed document photos |
| Chart recognition | `--chart-recognition` | Extract and structure chart content |
| Layout detection | `--layout-detection` | Detect and sort different regions in a document |
| Layout NMS | `--layout-nms` | Remove duplicate or overlapping bounding boxes |
| Prettify Markdown | `--prettify-markdown` | Output formatted Markdown text |
| Show formula numbers | `--show-formula-number` | Display formula numbers in output |
| Visualize | `--visualize` | Return intermediate visualization images |
| Restructure pages | `--restructure-pages` | Cross-page table merging + heading level recognition |
| Merge tables | `--merge-tables` | Detect and merge cross-page tables |
| Relevel titles | `--relevel-titles` | Recognize paragraph heading levels |

Use individual flags to enable specific features, or `--enable-all-features` for all boolean toggles at once.

To persist preferences (so they apply automatically to every conversion):

```bash
paddleocr-vl config enable-feature layout-detection
paddleocr-vl config disable-feature chart-recognition
```

#### Numeric parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `--temperature` | float | Sampling temperature (lower if unstable) |
| `--top-p` | float | Top-p sampling (lower if divergent) |
| `--repetition-penalty` | float | Repetition penalty (raise if repeating) |
| `--layout-threshold` | float | Layout score threshold (0-1, default 0.5) |
| `--layout-unclip-ratio` | float | Box expansion coefficient (default 1.0) |
| `--min-pixels` | int | Minimum input pixels |
| `--max-pixels` | int | Maximum input pixels |

#### String parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `--layout-merge-bboxes-mode` | `large`, `small`, `union` | Box merge mode |
| `--layout-shape-mode` | `rect`, `quad`, `poly`, `auto` | Geometry shape |
| `--prompt-label` | `ocr`, `formula`, `table`, `chart` | Prompt label (effective when layout detection is off) |

#### Priority

When sources conflict, the effective setting follows this order (last wins):

1. Default — original 3 features default to false
2. Config file — persistent boolean preferences
3. `--enable-all-features` — enable all boolean features
4. Individual CLI flag — explicit override

### Config management commands

```bash
paddleocr-vl config set-token "your_token_here"   # save token
paddleocr-vl config remove-token                    # delete saved token
paddleocr-vl config enable-feature <name>    # save feature preference (enabled)
paddleocr-vl config disable-feature <name>   # save feature preference (disabled)
paddleocr-vl config show                            # view current config
```

## Reference

```
usage: paddleocr-vl convert [-h] [-o OUTPUT] [--stdout] [--media-dir MEDIA_DIR]
                            [--token TOKEN] [--api-base-url API_BASE_URL]
                            [--model MODEL] [--timeout TIMEOUT]
                            [--poll-interval POLL_INTERVAL]
                            [--enable-all-features]
                            [--orientation-classify | --no-orientation-classify]
                            [--doc-unwarping | --no-doc-unwarping]
                            [--chart-recognition | --no-chart-recognition]
                            [--layout-detection | --no-layout-detection]
                            [--layout-nms | --no-layout-nms]
                            [--prettify-markdown | --no-prettify-markdown]
                            [--show-formula-number | --no-show-formula-number]
                            [--visualize | --no-visualize]
                            [--restructure-pages | --no-restructure-pages]
                            [--merge-tables | --no-merge-tables]
                            [--relevel-titles | --no-relevel-titles]
                            [--temperature TEMPERATURE] [--top-p TOP_P]
                            [--repetition-penalty REPETITION_PENALTY]
                            [--layout-threshold LAYOUT_THRESHOLD]
                            [--layout-unclip-ratio LAYOUT_UNCLIP_RATIO]
                            [--min-pixels MIN_PIXELS]
                            [--max-pixels MAX_PIXELS]
                            [--layout-merge-bboxes-mode {large,small,union}]
                            [--layout-shape-mode {rect,quad,poly,auto}]
                            [--prompt-label {ocr,formula,table,chart}]
                            [--verbose] input

positional arguments:
  input                  PDF file path, URL, or directory

options:
  -h, --help             show this help message and exit
  -o, --output OUTPUT    Output path (file or directory)
  --stdout               Write Markdown to stdout
  --media-dir MEDIA_DIR  Directory for extracted images
  --token TOKEN          API token (default: config file or $PADDLEOCR_API_TOKEN)
  --api-base-url URL     API endpoint (default: https://paddleocr.aistudio-app.com/api/v2/ocr/jobs)
  --model MODEL          Model name (default: PaddleOCR-VL-1.6)
  --timeout TIMEOUT      Job timeout in seconds (default: 1800)
  --poll-interval SEC    Poll interval in seconds (default: 5)
  --enable-all-features  Enable all optional features
  --orientation-classify, --no-orientation-classify   Document orientation classification
  --doc-unwarping, --no-doc-unwarping                 Document unwarping (deskew)
  --chart-recognition, --no-chart-recognition         Chart recognition
  --layout-detection, --no-layout-detection           Layout detection
  --layout-nms, --no-layout-nms                       Remove overlapping bounding boxes
  --prettify-markdown, --no-prettify-markdown         Prettify Markdown output
  --show-formula-number, --no-show-formula-number     Show formula numbers
  --visualize, --no-visualize                         Return visualization images
  --restructure-pages, --no-restructure-pages         Restructure multi-page PDFs
  --merge-tables, --no-merge-tables                   Merge cross-page tables
  --relevel-titles, --no-relevel-titles               Recognize heading levels
  --temperature TEMPERATURE                           Sampling temperature
  --top-p TOP_P                                       Top-p sampling
  --repetition-penalty REPETITION_PENALTY             Repetition penalty
  --layout-threshold LAYOUT_THRESHOLD                 Layout score threshold
  --layout-unclip-ratio LAYOUT_UNCLIP_RATIO           Box expansion coefficient
  --min-pixels MIN_PIXELS                             Minimum input pixels
  --max-pixels MAX_PIXELS                             Maximum input pixels
  --layout-merge-bboxes-mode {large,small,union}      Box merge mode
  --layout-shape-mode {rect,quad,poly,auto}           Geometry shape
  --prompt-label {ocr,formula,table,chart}            Prompt label
  --verbose, -v                                       Verbose output
```

## How it works

The PaddleOCR API uses an **asynchronous job** model:

1. **submit** — upload a PDF file (or pass a remote PDF URL) to the API, receive a `jobId`
2. **poll** — query the job status every 5 seconds until processing is done
3. **download** — fetch the JSONL result containing Markdown text and image URLs
4. **parse** — extract Markdown content and download embedded images locally

## License

This project is licensed under the GNU General Public License v3.0 — see the [LICENSE](LICENSE) file for details.

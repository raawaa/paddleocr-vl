# CLI reference

The full `paddleocr-vl convert` interface, plus the `config` subcommands. This
file is curated from `src/paddleocr_vl/cli.py` — if the source changes,
update this list. (Run `paddleocr-vl convert --help` for the version pinned
to your installed build.)

## `convert` — global options

These flags configure I/O behavior, not the OCR model itself.

- `-o, --output OUTPUT` — Output path (file for single input, directory for batch)
- `--stdout` — Write Markdown to stdout (single-file mode only; conflicts with `-o`)
- `--media-dir MEDIA_DIR` — Directory for extracted images (default: alongside the output)
- `--token TOKEN` — API token (default: config file or `$PADDLEOCR_API_TOKEN` env var)
- `--api-base-url URL` — API endpoint (default: `https://paddleocr.aistudio-app.com/api/v2/ocr/jobs`)
- `--model MODEL` — Model name (default: `PaddleOCR-VL-1.6`)
- `--timeout TIMEOUT` — Job timeout in seconds (default: `1800`)
- `--poll-interval SEC` — Poll interval in seconds (default: `5`)
- `--verbose, -v` — Verbose output

### Positional argument

- `input` — PDF file path, remote URL, or directory of PDFs

## `convert` — boolean feature flags

The 11 feature flags mapped to the PaddleOCR API. Group A carries a
tool-side default of `false`; Group B's default is whatever the API decides
(see [features.md](features.md)).

**Group A — tool-side `false`:**

- `--orientation-classify` / `--no-orientation-classify` — Auto-detect and correct page orientation
- `--doc-unwarping` / `--no-doc-unwarping` — Straighten curved or skewed document photos
- `--chart-recognition` / `--no-chart-recognition` — Extract and structure chart content

**Group B — API-side default:**

- `--layout-detection` / `--no-layout-detection` — Detect and sort regions
- `--layout-nms` / `--no-layout-nms` — Remove overlapping bounding boxes
- `--prettify-markdown` / `--no-prettify-markdown` — Output formatted Markdown text
- `--show-formula-number` / `--no-show-formula-number` — Display formula numbers
- `--visualize` / `--no-visualize` — Return intermediate visualization images
- `--restructure-pages` / `--no-restructure-pages` — Cross-page table merge + heading recognition
- `--merge-tables` / `--no-merge-tables` — Merge cross-page tables
- `--relevel-titles` / `--no-relevel-titles` — Recognize paragraph heading levels

Plus:

- `--enable-all-features` — Set every one of the 11 boolean feature flags to `true`

## `convert` — numeric options

Per-invocation; never persisted (ADR-0003).

- `--temperature FLOAT` — Sampling temperature (lower for unstable output)
- `--top-p FLOAT` — Top-p sampling (lower for diverging output)
- `--repetition-penalty FLOAT` — Repetition penalty (raise if repeating)
- `--layout-threshold FLOAT` — Layout score threshold, 0–1 (default `0.5`)
- `--layout-unclip-ratio FLOAT` — Box expansion coefficient (default `1.0`)
- `--min-pixels INT` — Minimum input pixels
- `--max-pixels INT` — Maximum input pixels

## `convert` — string options

Per-invocation; never persisted (ADR-0003).

- `--layout-merge-bboxes-mode {large,small,union}` — Box merge mode
- `--layout-shape-mode {rect,quad,poly,auto}` — Geometry shape
- `--prompt-label {ocr,formula,table,chart}` — Prompt label (effective when `--no-layout-detection`)

## `config` — subcommands

For managing the persisted config file (Windows path: `%APPDATA%\paddleocr-vl\config.json`;
Linux/macOS: `~/.config/paddleocr-vl/config.json`).

- `paddleocr-vl config set-token <token>` — Save the API token
- `paddleocr-vl config remove-token` — Delete the saved token
- `paddleocr-vl config enable-feature <name>` — Persist a feature flag as enabled
- `paddleocr-vl config disable-feature <name>` — Persist a feature flag as disabled
- `paddleocr-vl config show` — Print the current config (token is masked)

`<name>` is the kebab-case CLI flag without `--`, for example
`chart-recognition` or `layout-nms`.

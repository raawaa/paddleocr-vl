# paddleocr-vl

A CLI tool that converts PDFs to Markdown using the PaddleOCR-VL-1.6 Baidu API.

## Pipeline

**Conversion**:
The end-to-end flow from a PDF input to a Markdown output. A single conversion wraps exactly one job. Implemented as the `Conversion` module in `src/paddleocr_vl/conversion.py`.
_Avoid_: "task", "run"

**Input**:
The typed value a `Conversion` accepts: a `source` (PDF path or URL), a `media_dir` for image downloads, and an `options` dict. The CLI resolves media-dir and merges options before constructing an `Input`.
_Avoid_: "args", "request", "parameters"

**ConversionResult**:
The typed value a `Conversion` returns: the final markdown text, the media directory, the server's `job_id`, and elapsed seconds. The caller is responsible for writing the markdown to disk.
_Avoid_: "output", "response"

**Job**:
The API-side async task identified by a `jobId`. The unit of work the server manages.
_Avoid_: "conversion" (that's the whole pipeline), "task"

**Extraction**:
The API's own verb for the OCR work it performs on each page — visible in `extractProgress` and `extractedPages` in poll responses. The CLI does not use this term.
_Avoid_: Don't introduce as a term in our code or docs.

## Settings

**Option**:
A setting passed in the API's `optionalPayload`. Three subtypes: feature flag, numeric option, string option.
_Avoid_: "parameter", "setting", "config"

**Feature flag**:
A boolean option. Toggled by `--<flag>` / `--no-<flag>` on the CLI, or `config enable-feature` / `disable-feature` to persist. Persisted entries live in `Config.features` (see ADR-0003).
_Avoid_: "toggle", "boolean option", "flag" (the project uses "flag" only for CLI argument names, not for the concept)

**Numeric option**:
A floating-point or integer option (e.g. `--temperature`, `--layout-threshold`). Per-invocation only; never persisted (ADR-0003).
_Avoid_: "parameter", "numeric feature"

**String option**:
An enum-valued option (e.g. `--layout-merge-bboxes-mode`, `--prompt-label`). Per-invocation only; never persisted (ADR-0003).
_Avoid_: "choice", "string feature"

## Auth

**Token**:
The API auth credential. Resolved in priority order: CLI `--token`, `PADDLEOCR_API_TOKEN` env var, config file. First found wins.
_Avoid_: "API key", "credential", "auth"

**Config**:
The JSON file at `~/.config/paddleocr-vl/config.json` (or platform equivalent) that holds the token and persisted feature flags.
_Avoid_: "settings file", "preferences"

## I/O

**Media directory**:
The directory where images from the OCR result are saved — markdown-embedded images always, plus visualization images when `--visualize` is on.
_Avoid_: "image directory" (too narrow — visualization images are stored there too), "output directory" (too generic)

**Input mode**:
The kind of input the `convert` command accepts: a PDF file, a remote URL, or a directory of PDFs.
_Avoid_: "input type"

**Job state**:
The status the API reports during polling: `done` or `failed` are the only two states the CLI distinguishes. Intermediate progress is reported via `extractProgress` but is not modeled as a named state.
_Avoid_: "status" (too generic), "phase" (we don't use this)

## Limits

**Free tier**:
The PaddleOCR API allows ~20K parsed pages per day. Exceeding it returns HTTP 429, which the CLI surfaces as `RateLimitError` (`src/paddleocr_vl/errors.py:5`).
_Avoid_: "free quota", "credit", "free allowance"

**Rate limit**:
The API's per-day page budget, exhausted above 20K pages/day. CLI behavior on hitting it: batch mode halts immediately (`cli.py:266-271`); single-file mode exits non-zero.
_Avoid_: "throttle", "429" (the HTTP status is an implementation detail, not a domain term)

**Page cap**:
The PaddleOCR API silently drops pages beyond ~100 in a single PDF input — no error is raised; the result just ends earlier than the source. The CLI does **not** detect or warn about this; it is a documented upstream behavior surfaced only in `README`/docs.
_Avoid_: "page limit", "max pages", "truncation limit"

## Documentation

**README**:
The repo-root `README.md` and `README.zh.md`. Their audience is the **evaluator** — first 30 seconds decide install/no-install. Content must be structurally identical across languages; only the natural-language strings may differ. Both files are guarded by a structural skeleton lint in CI.
_Avoid_: Treating README as a Reference manual (that's `docs/reference.md`)

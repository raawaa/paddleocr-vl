# Features & options

CLI flags fall into two categories: **feature flags** (boolean toggles, persisted
into the config file) and **options** (numeric / string values, per-invocation
only). Boolean feature flags live under `paddleocr-vl config enable-feature /
disable-feature`; numeric and string options never persist (see [ADR-0003](adr/0003-config-persistence-boolean-only.md)).

## Feature flags (boolean toggles)

These are the boolean switches passed to the API. There are 11 in total —
3 with a tool-side default of `false`, and 8 whose effective default is
whatever the PaddleOCR API decides (we do not pin those upstream defaults
here; check aistudio docs for current behavior).

### Tool-side default: `false`

The tool always sends `false` for these unless you override them.

| Flag | What it does |
|---|---|
| `--orientation-classify` | Auto-detect and correct page orientation |
| `--doc-unwarping` | Straighten curved or skewed document photos |
| `--chart-recognition` | Extract and structure chart content |

### API-side default

When you don't set one of these, the CLI omits the key entirely and lets
the API decide. Current upstream defaults aren't mirrored into this tool.

| Flag | What it does |
|---|---|
| `--layout-detection` | Detect and sort different regions in a document |
| `--layout-nms` | Remove duplicate or overlapping bounding boxes |
| `--prettify-markdown` | Output formatted Markdown text |
| `--show-formula-number` | Display formula numbers in output |
| `--visualize` | Return intermediate visualization images |
| `--restructure-pages` | Cross-page table merging + heading level recognition |
| `--merge-tables` | Detect and merge cross-page tables |
| `--relevel-titles` | Recognize paragraph heading levels |

### A note on API key naming

The flag names above are stable, but the underlying API key names aren't
uniform:

- A handful of keys start with `use*` (e.g. `useDocOrientationClassify`) —
  enable-semantics.
- Most keys have no prefix and read as verbs (e.g. `restructurePages`,
  `mergeTables`).
- One is a single word: `visualize`.

This mix is the upstream PaddleOCR API's choice; this tool does not
normalize it.

### Persistence

Only boolean feature flags persist into the config file. Numeric and string
options never do. If you want a flag set on every invocation, run:

```bash
paddleocr-vl config enable-feature chart-recognition
paddleocr-vl config disable-feature layout-nms
```

### Priority (last wins)

When the same flag can come from several sources, the effective value flows
through this order — later layers overwrite earlier ones:

1. **Default** — 3 tool-side `false` values plus 8 keys the CLI omits
2. **Config file** — persisted flags from `paddleocr-vl config enable-feature / disable-feature`
3. **`--enable-all-features`** — sets every boolean feature flag to `true`
4. **Individual CLI flag** — e.g. `--chart-recognition` or `--no-layout-nms`

Combining `--enable-all-features` with a `--no-<flag>` produces "all minus
one" — handy for probing everything while excluding one costly feature.

### Override doesn't persist

A single CLI flag override (e.g. `--no-chart-recognition`) only affects
**the current invocation**. The config file is not updated. To make the
override permanent, run `paddleocr-vl config disable-feature
chart-recognition`.

## Numeric options

Pass per-invocation. Never persisted.

| Flag | Type | Description |
|---|---|---|
| `--temperature` | float | Sampling temperature (lower if output is unstable) |
| `--top-p` | float | Top-p sampling (lower if output diverges) |
| `--repetition-penalty` | float | Repetition penalty (raise if repeating) |
| `--layout-threshold` | float | Layout score threshold, 0–1, default `0.5` |
| `--layout-unclip-ratio` | float | Box expansion coefficient, default `1.0` |
| `--min-pixels` | int | Minimum input pixels |
| `--max-pixels` | int | Maximum input pixels |

## String options

Pass per-invocation. Never persisted.

| Flag | Values | Description |
|---|---|---|
| `--layout-merge-bboxes-mode` | `large`, `small`, `union` | Box merge mode |
| `--layout-shape-mode` | `rect`, `quad`, `poly`, `auto` | Geometry shape |
| `--prompt-label` | `ocr`, `formula`, `table`, `chart` | Prompt label (effective when layout detection is off) |

## Config management commands

```bash
paddleocr-vl config set-token "your_token_here"     # save token
paddleocr-vl config remove-token                    # delete saved token
paddleocr-vl config enable-feature <name>           # enable a feature flag
paddleocr-vl config disable-feature <name>          # disable a feature flag
paddleocr-vl config show                            # view current config
```

`<name>` is the kebab-case CLI flag without `--`, e.g. `chart-recognition`,
`layout-nms`.

# Troubleshooting

Three error types are surfaced explicitly. Below each, what it means and how
to recover.

## Rate limit hit (HTTP 429)

You exceeded the daily page quota (~20K pages/day free tier). Surfaced as
`RateLimitError` in `src/paddleocr_vl/errors.py`.

- **Single-file mode:** the conversion exits non-zero with the API's
  truncation of the 429 response.
- **Batch mode:** the entire batch halts at the failing PDF (see
  [ADR-0002](adr/0002-batch-policy-in-cli.md)). The CLI prints a
  `=== 批量处理中断: 已完成 X/Y ===` line and counts every remaining PDF
  as failed.

Recovery:

- Wait until the next day's quota resets.
- Or split the remaining files into a separate run after the reset.

## Job failed (`JobFailedError`)

The PaddleOCR API reported `state == "failed"` for a job.

Common causes:

- The PDF is corrupted, password-protected, or non-standard.
- The first 5 bytes aren't `%PDF-` — `cli.is_real_pdf` rejects it before
  submission.
- The API rejected the file for some other reason.

Recovery:

- Try opening the PDF locally. If it's corrupted, fix the source.
- In batch mode, per-file `JobFailedError` (and any non-rate-limit
  `PaddleOCRError`) is caught and the loop continues with the next PDF,
  marked `✗`.

## Polling timeout (`JobTimeoutError`)

Default `--timeout` is `1800` (30 minutes). Some large or complex PDFs
genuinely take longer.

Recovery:

- Bump `--timeout 3600` (or higher) on the next attempt.
- Split the PDF (the API caps each input at ~100 pages; see Silent
  failures below).

## Silent failures

These don't raise errors, but can leave the output incomplete. Check the
result by hand when they matter.

### Image download failure

If a Markdown image references a URL that returns 4xx, 5xx, or times out,
the download is silently skipped (`media._download_to` catches
`requests.RequestException` and discards the failure). The Markdown file
is still written — the `<img>` link just stays broken.

Check after a conversion:

```bash
grep -oE '!\[[^]]*\]\([^)]+\)' output.md | wc -l   # references in markdown
ls your_output_media/ | wc -l                       # downloaded files
```

If the two counts differ, re-run after fixing the network, or fetch the
missing images by hand.

### Page cap (100 pages per PDF)

The PaddleOCR API silently drops pages beyond ~100 in a single input — no
error is raised, the result just ends earlier than the source. This tool
does not warn about it.

For multi-hundred-page inputs, split the PDF beforehand (e.g. with
`pdftk` or `qpdf`).

## See also

- [`features.md`](features.md) — option descriptions and priority rules
- [`reference.md`](reference.md) — full CLI flag list
- [`install.md`](install.md) — installation and upgrade paths
- ADR-0002 — why batch mode halts on `RateLimitError` but continues on
  other errors

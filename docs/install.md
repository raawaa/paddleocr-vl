# Install

## Recommended: `uv tool`

[`uv`](https://github.com/astral-sh/uv) installs the CLI as an isolated tool
so it doesn't pollute your system Python.

```bash
uv tool install git+https://github.com/raawaa/paddleocr-vl.git
```

After install, `paddleocr-vl` is on your `$PATH`.

### Upgrading

`uv tool upgrade` decides whether to reinstall by comparing the published
version string. Since version numbers come from git tags, **a reinstall only
happens after a new tag is pushed**. If you want the latest commit regardless:

```bash
uv tool install git+https://github.com/raawaa/paddleocr-vl.git --reinstall
```

### Uninstall

```bash
uv tool uninstall paddleocr-vl
```

## Alternative: `pip`

```bash
pip install git+https://github.com/raawaa/paddleocr-vl.git
```

This installs into whichever Python environment `pip` is currently bound
to. If you use a venv, activate it first.

## Local clone (development)

```bash
git clone https://github.com/raawaa/paddleocr-vl.git
cd paddleocr-vl
uv sync                  # create .venv with project + dev deps
uv run -m paddleocr_vl convert input.pdf
```

Use this mode when you're editing the source — `uv run` picks up your
local changes immediately. CI uses the same `uv sync` workflow.

## Get an API token

Sign in at [aistudio.baidu.com/paddleocr](https://aistudio.baidu.com/paddleocr)
and create an application token. The first ~20K pages per day are free;
beyond that, the API returns HTTP 429 (see [troubleshooting.md](troubleshooting.md)).

Save the token once so every subsequent invocation picks it up:

```bash
paddleocr-vl config set-token "your_token_here"
```

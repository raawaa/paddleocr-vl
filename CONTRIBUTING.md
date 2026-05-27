# Contributing

Thanks for your interest in contributing to paddleocr-vl!

## How to contribute

1. **Report bugs** — open an [issue](https://github.com/raawaa/paddleocr-vl/issues) with a clear description
2. **Suggest features** — open an issue to discuss before implementing
3. **Submit code** — fork the repo and open a pull request

## Development setup

```bash
git clone https://github.com/raawaa/paddleocr-vl.git
cd paddleocr-vl
uv sync
uv run python -m paddleocr_vl --help
```

## Pull request workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Make your changes
4. Run the smoke test: `uv run python -m paddleocr_vl --help`
5. Push and open a PR

## Commit message format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add support for ...
fix: handle edge case when ...
docs: update README usage examples
chore: bump version to 0.2.0
```

import json
import os
from pathlib import Path


def get_config_dir() -> Path:
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg_config) if xdg_config else Path.home() / ".config"
    return base / "paddleocr-vl"


def get_config_path() -> Path:
    return get_config_dir() / "config.json"


def _read() -> dict:
    p = get_config_path()
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def _write(data: dict) -> None:
    p = get_config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def read_token() -> str | None:
    return _read().get("api_token")


def write_token(token: str) -> None:
    cfg = _read()
    cfg["api_token"] = token
    _write(cfg)


def remove_token() -> None:
    cfg = _read()
    if "api_token" not in cfg:
        return
    cfg.pop("api_token", None)
    _write(cfg)

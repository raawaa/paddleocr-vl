import json
import os
import platform
import sys
from pathlib import Path


FEATURE_MAP = {
    "orientation-classify": "useDocOrientationClassify",
    "doc-unwarping": "useDocUnwarping",
    "chart-recognition": "useChartRecognition",
}


def get_config_dir() -> Path:
    if platform.system() == "Windows":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
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


def get_feature_key(short_name: str) -> str | None:
    """将 CLI 短名（如 orientation-classify）转为 API payload key（如 useDocOrientationClassify）。"""
    return FEATURE_MAP.get(short_name)


def read_features() -> dict:
    """读取配置文件中的 features 段，返回 dict。"""
    return _read().get("features", {})


def set_feature(name: str, value: bool) -> None:
    """设置单个 feature 并保存到配置文件。"""
    api_key = get_feature_key(name)
    if api_key is None:
        valid = ", ".join(FEATURE_MAP)
        print(f"错误: 未知特性 '{name}'，可用: {valid}", file=sys.stderr)
        sys.exit(1)
    cfg = _read()
    if "features" not in cfg:
        cfg["features"] = {}
    cfg["features"][api_key] = value
    _write(cfg)

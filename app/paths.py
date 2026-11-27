"""Пути приложения.

Полная сборка хранит данные рядом с установленным приложением.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "ZapretApp-discord-youtube-telegram"
DATA_NAME = "ZapretTG"
APP_VERSION = "1.0 BETA"

IS_FROZEN = bool(getattr(sys, "frozen", False))
IS_WINDOWS = sys.platform == "win32"


def _resource_root() -> Path:
    if IS_FROZEN:
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent.parent


RESOURCE_DIR = _resource_root() / "resources"
BUNDLED_ZAPRET = RESOURCE_DIR / "zapret"
INSTALLED_LAYOUT = IS_FROZEN and _resource_root() == Path(sys.executable).parent / "_internal"


def _data_root() -> Path:
    override = os.environ.get("ZAPRETTG_DATA")
    if override:
        return Path(override)
    if INSTALLED_LAYOUT:
        return Path(sys.executable).parent
    if IS_WINDOWS:
        base = os.environ.get("ProgramW6432") or os.environ.get("ProgramFiles") or r"C:\Program Files"
        return Path(base) / APP_NAME
    return Path.home() / ".local" / "share" / APP_NAME


DATA_DIR = _data_root()
DEFAULT_DOWNLOADS = DATA_DIR / "downloads"
ZAPRET_DIR = DATA_DIR / "components" / "zapret" / "default"
CONFIG_FILE = DATA_DIR / "settings" / "config.json"
LOG_DIR = DATA_DIR / "logs"
UI_CACHE_DIR = DATA_DIR / "cache" / "ui"
APP_LOG = LOG_DIR / "app.log"
PROXY_LOG = LOG_DIR / "tg-proxy.log"
ZAPRET_LOG = LOG_DIR / "zapret.log"


def exe_path() -> str:
    if IS_FROZEN:
        return sys.executable
    return f'"{sys.executable}" "{Path(sys.argv[0]).resolve()}"'


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

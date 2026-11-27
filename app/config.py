"""Настройки приложения (один JSON для обеих утилит)."""
from __future__ import annotations

import json
import logging
import os
import tempfile
import threading
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict

from .paths import APP_NAME, CONFIG_FILE, DEFAULT_DOWNLOADS, ensure_dirs

log = logging.getLogger("zapret-tg.config")


def _default_tg() -> Dict[str, Any]:
    # Те же значения по умолчанию, что и в оригинальном tg-ws-proxy
    return {
        "host": "127.0.0.1",
        "port": 1443,
        "secret": os.urandom(16).hex(),
        "dc_ip": ["2:149.154.167.220", "4:149.154.167.220"],
        "verbose": False,
        "check_updates": True,
        "log_max_mb": 5,
        "buf_kb": 256,
        "pool_size": 4,
        "cfproxy": True,
        "h2": True,
        "cfproxy_user_domain_enabled": False,
        "cfproxy_user_domain": [],
        "cfproxy_worker_enabled": False,
        "cfproxy_worker_domain": [],
        "force_test_dc": False,
        "no_secure": False,
        "fake_tls_domain": "",
        "proxy_protocol": False,
    }


DEFAULTS: Dict[str, Any] = {
    "app": {
        "autostart": False,          # запуск при входе в Windows (планировщик)
        "start_minimized": True,     # при автозапуске — сразу в трей
        "close_to_tray": True,       # крестик сворачивает в трей
        "theme": "dark",             # dark / light
        "translucent": True,         # полупрозрачное окно с размытием (Windows 10/11)
        "notifications": True,
        "language": "ru",
        "language_chosen": False,
        "auto_download_updates": True,
        "download_folder": "",
        "first_run_done": False,
    },
    "zapret": {
        "enabled_on_start": True,    # включать обход при запуске приложения
        "strategy": "general.bat",
        "engine_version": "default",
        "mode": "app",               # app — процесс внутри приложения, service — служба Windows
        "auto_restart": True,        # перезапускать winws.exe, если упал
        "check_updates": True,
    },
    "dns": {
        "enabled": False,
        "provider": "xbox",          # xbox / comss / cloudflare / google / custom
        "mode": "auto",              # auto / system / local
        "custom_v4": "",
        "custom_v6": "",
        "custom_doh": "",
        "saved": {},                 # исходные DNS адаптеров для отката
        "doh_added": [],
        "applied_mode": "",
    },
    "tg": {
        "enabled_on_start": True,
        "engine_version": "1.11.4",
        "previous_engine_version": "1.11.4",
        **_default_tg(),
    },
}


class Config:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.data: Dict[str, Any] = deepcopy(DEFAULTS)
        self.load()

    def load(self) -> None:
        ensure_dirs()
        if CONFIG_FILE.exists():
            try:
                raw = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                for section, values in DEFAULTS.items():
                    merged = deepcopy(values)
                    merged.update(raw.get(section, {}) or {})
                    self.data[section] = merged
            except Exception as exc:  # повреждённый конфиг — начинаем с умолчаний
                log.warning("Не удалось прочитать конфиг: %r", exc)
        self.save()

    def save(self) -> None:
        with self._lock:
            ensure_dirs()
            tmp = CONFIG_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, CONFIG_FILE)

    def get(self, section: str, key: str, default: Any = None) -> Any:
        with self._lock:
            return self.data.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value: Any, save: bool = True) -> None:
        with self._lock:
            values = self.data.setdefault(section, {})
            had_key = key in values
            previous = values.get(key)
            values[key] = value
            if save:
                try:
                    self.save()
                except OSError:
                    if had_key:
                        values[key] = previous
                    else:
                        del values[key]
                    raise

    @property
    def selected_download_folder(self) -> Path | None:
        saved = self.get("app", "download_folder")
        if isinstance(saved, str) and Path(saved).is_absolute():
            return Path(saved)
        return None

    @property
    def download_folder(self) -> Path:
        return self.selected_download_folder or DEFAULT_DOWNLOADS

    def set_download_folder(self, folder: Path) -> None:
        if folder.is_absolute() and folder == folder.parent:
            folder = folder / APP_NAME
            folder.mkdir(exist_ok=True)
        with tempfile.TemporaryFile(dir=folder):
            pass
        self.set("app", "download_folder", str(folder))

    def section(self, name: str) -> Dict[str, Any]:
        with self._lock:
            return deepcopy(self.data.get(name, {}))

    def update_section(self, name: str, values: Dict[str, Any]) -> None:
        with self._lock:
            previous = self.data.get(name, {})
            self.data[name] = {**previous, **values}
            try:
                self.save()
            except OSError:
                self.data[name] = previous
                raise

    @property
    def previous_tg_selection(self):
        with self._lock:
            tg = self.data["tg"]
            previous = tg.get("undo_engine_version", tg.get("previous_engine_version"))
            return previous if previous != tg["engine_version"] else None

    def select_tg_version(self, version, running_version, *, restore=False):
        from .versions import tg_versions
        with self._lock:
            current = self.get("tg", "engine_version")
            if restore:
                version = self.previous_tg_selection
            if version not in tg_versions():
                raise ValueError("Версия Telegram-прокси не найдена")
            if current != version or restore:
                change = {
                    "engine_version": version,
                    "undo_engine_version": None if restore else current,
                }
                if running_version != version:
                    change["previous_engine_version"] = running_version
                self.update_section("tg", change)
            return version

"""Точка входа ZapretTG."""
from __future__ import annotations

import logging
import logging.handlers
import os
import sys
import threading


def _setup_logging() -> None:
    from .paths import APP_LOG, ensure_dirs
    ensure_dirs()
    h = logging.handlers.RotatingFileHandler(APP_LOG, maxBytes=1024 * 1024, backupCount=1, encoding="utf-8")
    h.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-5s  %(message)s", "%Y-%m-%d %H:%M:%S"))
    h.addFilter(lambda r: r.name.startswith("zapret-tg"))
    root = logging.getLogger()
    root.addHandler(h)
    root.setLevel(logging.INFO)
    lg = logging.getLogger("zapret-tg")
    lg.setLevel(logging.INFO)


def _wine_compat() -> None:
    """Под Wine нет CopyFile2, которым пользуется shutil.copy2 в Python 3.12."""
    try:
        import ctypes
        ctypes.windll.ntdll.wine_get_version  # есть только в Wine
    except Exception:
        return
    try:
        import _winapi
        if hasattr(_winapi, "CopyFile2"):
            delattr(_winapi, "CopyFile2")
    except Exception:
        pass


def _selftest(out_path) -> int:
    """Проверка сборки: все модули импортируются, стратегии разбираются, окно создаётся."""
    import os
    import tempfile
    import traceback
    lines = []
    ok = True
    try:
        os.environ["ZAPRETTG_DATA"] = tempfile.mkdtemp(prefix="zaprettg-selftest-")
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from importlib import reload
        from . import paths
        reload(paths)
        from .config import Config
        from .zapret import ZapretManager
        cfg = Config()
        from .versions import configure_tg_imports
        configure_tg_imports(cfg)
        from .tgproxy import TgProxyManager, TGWS_VERSION
        from .dns import DnsManager
        z = ZapretManager(cfg)
        z.root = paths.ZAPRET_DIR
        z.install_files()
        z.prepare_versions()
        strategies = z.strategies()
        for st in strategies:
            args = z.build_args(st)
            assert "%" not in args and "winws" not in args.lower(), st
        lines.append(f"zapret {z.local_version()}: {len(strategies)} стратегий разобрано")
        from .versions import tg_versions
        assert '1.10.3' in dict(z.installed_versions())
        assert '1.11.4' in tg_versions() and '1.12.0' in tg_versions()
        lines.append('дополнительные версии доступны')
        lines.append(f"tg-ws-proxy {TGWS_VERSION}")
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication([])
        from .ui.main_window import MainWindow
        w = MainWindow(cfg, z, TgProxyManager(cfg), DnsManager(cfg))
        for key in w.pages:
            w.go(key, animate=False)
        lines.append(f"интерфейс: {len(w.pages)} страниц")
        w.timer.stop()
        w.tray.hide()
    except Exception:
        ok = False
        lines.append(traceback.format_exc())
    lines.append("SELFTEST OK" if ok else "SELFTEST FAILED")
    text = "\n".join(lines)
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        print(text)
    return 0 if ok else 1


def _cleanup() -> int:
    """Вызывается деинсталлятором: вернуть систему в исходное состояние."""
    from . import winutils
    from .config import Config
    from .dns import DnsManager
    from .zapret import SERVICE_NAME
    try:
        cfg = Config()
        if cfg.get("dns", "enabled") or cfg.get("dns", "saved"):
            DnsManager(cfg).disable()
    except Exception:
        pass
    # закрыть работающий ZapretTG, но не себя (и не свой загрузчик onefile)
    try:
        import os
        import psutil
        me = psutil.Process(os.getpid())
        mine = {me.pid} | {p.pid for p in me.parents()}
        for p in psutil.process_iter(["name"]):
            if (p.info.get("name") or "").lower() == "zaprettg.exe" and p.pid not in mine:
                try:
                    p.kill()
                except Exception:
                    pass
    except Exception:
        pass
    winutils.kill_image("winws.exe")
    winutils.set_autostart(False)
    for svc in (SERVICE_NAME, "WinDivert", "WinDivert14"):
        if winutils.service_info(svc) is not None:
            winutils.stop_and_delete_service(svc)
    return 0


def _prepare_installation() -> int:
    """Populate the selected folder without starting network services."""
    from . import paths
    from .config import Config
    from .migration import _copy_tree, migrate_on_startup
    from .versions import TG_VERSIONS, ZAPRET_VERSIONS, install_bundled_zapret
    from .zapret import ZapretManager

    if not paths.INSTALLED_LAYOUT:
        return 1
    try:
        new_install = not paths.CONFIG_FILE.is_file()
        migrate_on_startup()
        _setup_logging()
        cfg = Config()
        if new_install:
            cfg.set("app", "download_folder", "")
        manager = ZapretManager(cfg)
        manager.install_files()
        for relative in ("service.bat", "general.bat", "bin/winws.exe", "bin/WinDivert.dll", "bin/WinDivert64.sys"):
            if not (manager.root / relative).is_file():
                raise FileNotFoundError(manager.root / relative)
        install_bundled_zapret()
        if not (ZAPRET_VERSIONS / "1.10.3" / "bin" / "winws.exe").is_file():
            raise FileNotFoundError("Zapret 1.10.3")
        for source in (paths.RESOURCE_DIR / "tgws").iterdir():
            if source.is_dir():
                _copy_tree(source, TG_VERSIONS / source.name)
        for folder in (paths.DEFAULT_DOWNLOADS / "zapret", paths.DEFAULT_DOWNLOADS / "telegram", paths.UI_CACHE_DIR):
            folder.mkdir(parents=True, exist_ok=True)
        return 0
    except Exception:
        if not logging.getLogger().handlers:
            _setup_logging()
        logging.getLogger("zapret-tg").exception("Не удалось подготовить файлы при установке")
        return 1


def main() -> int:
    from .paths import APP_NAME, IS_WINDOWS, APP_VERSION
    if IS_WINDOWS:
        _wine_compat()
    from . import winutils

    args = sys.argv[1:]
    from .restart import restart_component_state, wait_for_previous
    if not wait_for_previous(args):
        return 1
    autostart = "--autostart" in args

    # служебные режимы (для установщика и CI) — без окна
    for a in args:
        if a.startswith("--selftest"):
            return _selftest(a.partition("=")[2] or None)
    if "--prepare-install" in args:
        return _prepare_installation()
    if "--cleanup" in args:
        return _cleanup()
    if "--autostart-on" in args:
        ok, _ = winutils.set_autostart(True)
        return 0 if ok else 1

    if IS_WINDOWS and not winutils.is_admin():
        # zapret (WinDivert) требует прав администратора
        if winutils.relaunch_as_admin(args):
            return 0

    if IS_WINDOWS:
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f"{APP_NAME}.App")
        except Exception:
            pass

    from PySide6.QtCore import Qt
    from PySide6.QtNetwork import QLocalServer, QLocalSocket
    from PySide6.QtWidgets import QApplication, QMessageBox

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)

    # один экземпляр: второй запуск только показывает окно первого.
    # Мьютекс — основная защита (два экземпляра «воевали» за winws.exe и порт
    # прокси), локальный сокет — чтобы попросить первый экземпляр показаться.
    key = "ZapretTG-single-instance"
    first_instance = winutils.acquire_single_instance("ZapretTG-mutex")
    sock = QLocalSocket()
    sock.connectToServer(key)
    if sock.waitForConnected(1500 if not first_instance else 300):
        sock.write(b"show")
        sock.flush()
        sock.waitForBytesWritten(500)
        return 0
    if not first_instance:
        return 0  # первый экземпляр ещё запускается
    QLocalServer.removeServer(key)
    server = QLocalServer()
    server.listen(key)

    try:
        from .migration import migrate_on_startup
        migrate_on_startup()
    except Exception as exc:
        from .ui.language import saved_language, translate_text
        message = f"Не удалось перенести данные в Program Files:\n{exc}\n\nСтарая папка сохранена. Закройте программу и проверьте доступ к новой папке."
        QMessageBox.critical(None, APP_NAME, translate_text(message, saved_language()))
        return 1

    _setup_logging()
    log = logging.getLogger("zapret-tg")
    log.info("===== %s %s запуск (autostart=%s, admin=%s) =====", APP_NAME, APP_VERSION, autostart, winutils.is_admin())

    from .config import Config
    from .ui.first_start import choose_download_drive, choose_first_language
    cfg = Config()
    if not choose_first_language(cfg) or not choose_download_drive(cfg):
        return 0

    from .zapret import ZapretManager
    from .versions import configure_tg_imports, clear_tg_imports
    engine_path = None
    engine_warning = ''
    try:
        engine_path = configure_tg_imports(cfg)
        from .tgproxy import TgProxyManager
    except Exception:
        log.exception('Ошибка загрузки выбранной версии Telegram-прокси; откат')
        clear_tg_imports(engine_path)
        previous = cfg.get('tg', 'previous_engine_version', '1.11.4')
        cfg.set('tg', 'engine_version', previous)
        fallback_path = None
        try:
            fallback_path = configure_tg_imports(cfg)
            from .tgproxy import TgProxyManager
        except Exception:
            log.exception('Откат к предыдущей версии не удался; возврат ко встроенной')
            clear_tg_imports(fallback_path)
            cfg.set('tg', 'engine_version', '1.11.4')
            previous = '1.11.4'
            from .tgproxy import TgProxyManager
        engine_warning = f'Выбранная версия Telegram-прокси не загрузилась. Восстановлена версия {previous}.'
    from .dns import DnsManager
    from .ui.main_window import MainWindow
    zapret = ZapretManager(cfg)
    legacy_service_warning = ''
    if cfg.get('zapret', 'mode') == 'service':
        from pathlib import Path
        from .zapret import SERVICE_NAME
        old_root = str(Path(os.environ.get('ProgramData') or r'C:\ProgramData') / 'ZapretTG')
        service = winutils.service_info(SERVICE_NAME) or {}
        if old_root.casefold() in str(service.get('binpath') or '').casefold():
            legacy_service_warning = ('Служба Zapret использует старую папку. Переустановите службу '
                                      'на вкладке Zapret, чтобы использовать новую папку.')
    try:
        zapret.install_files()
        zapret.prepare_versions()
    except Exception as exc:
        log.exception("Не удалось установить файлы zapret")
        from .ui.language import translate_text
        QMessageBox.critical(None, APP_NAME, translate_text(f"Не удалось подготовить файлы zapret:\n{exc}", cfg.get('app', 'language', 'ru')))
    tg = TgProxyManager(cfg)
    dns = DnsManager(cfg)

    # реальное состояние автозапуска
    try:
        cfg.set("app", "autostart", winutils.autostart_enabled())
        winutils.autostart_refresh()  # exe перенесли — обновить путь в планировщике
    except Exception:
        pass
    if cfg.get("zapret", "mode") == "service" and not zapret.service_installed():
        cfg.set("zapret", "mode", "app")

    win = MainWindow(cfg, zapret, tg, dns)

    def on_new_connection():
        c = server.nextPendingConnection()
        if c:
            c.waitForReadyRead(300)
            c.readAll()
            c.disconnectFromServer()
        win.show_window()

    server.newConnection.connect(on_new_connection)

    first_run = not cfg.get("app", "first_run_done")
    if autostart and cfg.get("app", "start_minimized", True) and not first_run:
        pass  # только трей
    else:
        win.show()

    def start_components():
        warnings = []
        # оригинальный TgWsProxy занимает тот же порт — прокси не смог бы запуститься
        if winutils.process_running("TgWsProxy.exe") or winutils.process_running("TgWsProxy_windows.exe"):
            warnings.append("Запущен оригинальный TgWsProxy — он занимает порт прокси. Закройте его "
                            "(значок в трее → Выход) и уберите из автозагрузки.")
        if cfg.get("dns", "enabled"):
            try:
                ok, msg = dns.enable()
                if not ok:
                    warnings.append("DNS: " + msg)
            except Exception as exc:
                log.exception("dns")
        if restart_component_state(args, 'zapret', bool(cfg.get("zapret", "enabled_on_start", True))):
            if cfg.get("zapret", "mode") == "service":
                if zapret.service_state() != "running":
                    zapret.service_start()
            else:
                ok, msg = zapret.start()
                if not ok:
                    log.warning("zapret: %s", msg)
        if restart_component_state(args, 'tg', bool(cfg.get("tg", "enabled_on_start", True))):
            ok, msg = tg.start()
            if not ok:
                log.warning("tg: %s", msg)
                warnings.append("Telegram прокси: " + msg.split("\n")[0])
        return warnings

    def after_start(warnings):
        win.refresh_now()
        if engine_warning:
            warnings.append(engine_warning)
        if legacy_service_warning:
            warnings.append(legacy_service_warning)
        for w in warnings or []:
            win.toast(w, "warn", 10000)
        if first_run:
            cfg.set("app", "first_run_done", True)
            win.toast("Готово! Обход и Telegram прокси включены. Нажмите «Подключить Telegram», "
                      "чтобы добавить прокси в Telegram Desktop.", "ok", 9000)

    from .ui.widgets import run_bg
    run_bg(start_components, after_start, lambda e: log.error("Ошибка запуска: %r", e))
    win.check_updates_later()

    app.aboutToQuit.connect(win.quit_app)
    return app.exec()

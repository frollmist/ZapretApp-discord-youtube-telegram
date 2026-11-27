import os
import tempfile
import logging
import threading
import time
from unittest.mock import patch
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
with tempfile.TemporaryDirectory() as directory:
    os.environ['ZAPRETTG_DATA'] = directory
    from PySide6.QtWidgets import QApplication, QLabel
    from app.config import Config
    from app.paths import APP_NAME, DATA_NAME
    from app.zapret import ZapretManager
    from app.tgproxy import TgProxyManager
    from app.dns import DnsManager
    from app.ui.main_window import MainWindow
    app = QApplication([])
    cfg = Config()
    zapret = ZapretManager(cfg)
    zapret.install_files()
    zapret.prepare_versions()
    window = MainWindow(cfg, zapret, TgProxyManager(cfg), DnsManager(cfg))
    assert APP_NAME == 'ZapretApp-discord-youtube-telegram'
    assert DATA_NAME == 'ZapretTG'
    assert window.windowTitle() == APP_NAME
    assert any(item.text() == APP_NAME and item.wordWrap() for item in window.findChildren(QLabel))
    assert any(APP_NAME in item.text() for item in window.pages['settings'].findChildren(QLabel))
    window.go('settings', animate=False)
    window.set_language('en')
    assert window.nav_buttons['home'].text() == 'Home'
    assert window.titlebar.title.text() == 'Settings'
    assert any(label.text() == 'Version 1.0 BETA' for label in window.findChildren(QLabel))
    window.set_language('ru')
    assert window.nav_buttons['home'].text() == 'Главная'
    assert window.titlebar.title.text() == 'Настройки'
    assert any(label.text() == 'Версия 1.0 BETA' for label in window.findChildren(QLabel))
    window.go('zapret', animate=False)
    assert window.pages['zapret'].engine_combo.findData('1.10.3') >= 0
    zpage = window.pages['zapret']
    release_check = threading.Event()
    def fake_select(progress):
        progress(1, 2, 'general', 'YouTube')
        assert release_check.wait(5)
        cfg.set('zapret', 'strategy', 'general.bat')
        return True, 'Рабочая стратегия найдена'
    with patch.object(zapret, 'auto_select_strategy', fake_select):
        zpage._auto_select()
        deadline = time.monotonic() + 5
        while 'YouTube' not in zpage.auto_status.text() and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(0.01)
        assert zpage.auto_status.text() == 'Проверка 1/2: general — YouTube'
        assert not zpage.auto_button.isEnabled()
        release_check.set()
        deadline = time.monotonic() + 5
        while not zpage.auto_button.isEnabled() and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(0.01)
        assert zpage.auto_status.text() == 'Завершено: general'
        assert zpage.auto_status.objectName() == 'autoDone'
    with patch.object(zapret, 'auto_select_strategy', lambda progress: (False, 'Ничего не найдено')):
        zpage._auto_select()
        deadline = time.monotonic() + 5
        while not zpage.auto_button.isEnabled() and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(0.01)
        assert zpage.auto_status.objectName() == 'autoError'
        assert zpage.auto_status.text() == 'Не удалось подобрать'
    window.go('tg', animate=False)
    tg_page = window.pages['tg']
    index = tg_page.engine_combo.findData('1.12.0')
    assert index >= 0
    tg_page.engine_combo.setCurrentIndex(index)
    with patch('app.restart.launch_restart') as launcher:
        tg_page._select_engine()
        launcher.assert_not_called()
        assert app.activeModalWidget() is None
    assert cfg.get('tg', 'engine_version') == '1.12.0'
    assert cfg.get('tg', 'previous_engine_version') == '1.11.4'
    assert not tg_page.restart_button.isHidden()
    tg_page.engine_combo.setCurrentIndex(tg_page.engine_combo.findData('1.11.4'))
    tg_page._select_engine()
    assert tg_page.restart_button.isHidden()
    with patch('app.updates.install_components', return_value=[('tg', True, '1.12.0', '', False)]), \
         patch('app.ui.main_window.run_bg', side_effect=lambda work, done, *rest: done(work())), \
         patch('app.restart.launch_restart') as launcher:
        window.download_updates_now(manual=True, kind='tg')
        launcher.assert_not_called()
        assert app.activeModalWidget() is None
    assert not tg_page.restart_button.isHidden()
    quit_calls = []
    with patch('app.restart.launch_restart', side_effect=OSError('test error')), \
         patch.object(window, 'quit_app', lambda: quit_calls.append(True)):
        window.restart_app()
        assert not quit_calls
    with patch('app.restart.launch_restart') as launcher, \
         patch.object(window, 'quit_app', lambda: quit_calls.append(True)):
        tg_page.restart_button.click()
        launcher.assert_called_once()
        assert quit_calls == [True]
    window.timer.stop()
    window.tray.hide()
    logging.shutdown()
    print('FULL_UI_LANGUAGE_OK')

import logging
import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['ZAPRETTG_DATA'] = tempfile.mkdtemp(prefix='english-ui-')

from PySide6.QtWidgets import QApplication, QAbstractButton, QComboBox, QLabel, QLineEdit, QSpinBox, QWidget
from app import diagnostics
from app.config import Config
from app.paths import APP_NAME
from app.dns import DnsManager
from app.tgproxy import TgProxyManager
from app.ui.language import translate_text
from app.ui.first_start import choose_download_drive
from app.ui.main_window import MainWindow
from app.zapret import ZapretManager


class EnglishUITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.cfg = Config()
        cls.zapret = ZapretManager(cls.cfg)
        cls.zapret.install_files()
        cls.zapret.prepare_versions()
        cls.window = MainWindow(cls.cfg, cls.zapret, TgProxyManager(cls.cfg), DnsManager(cls.cfg))

    @classmethod
    def tearDownClass(cls):
        cls.window.timer.stop()
        cls.window.tray.hide()
        logging.shutdown()

    def test_static_interface_and_tooltips_are_english(self):
        w = self.window
        w.set_language('en')
        cyrillic = re.compile(r'[А-Яа-яЁё]')
        for name, page in w.pages.items():
            w.go(name, animate=False)
            text_items = [w.titlebar.title.text(), w.titlebar.sub.text()]
            for obj in page.findChildren(QWidget):
                if isinstance(obj, (QLabel, QAbstractButton)):
                    text_items.append(obj.text())
                if isinstance(obj, QComboBox):
                    text_items.extend(obj.itemText(i) for i in range(obj.count()))
                if isinstance(obj, QLineEdit):
                    text_items.append(obj.placeholderText())
                if isinstance(obj, QSpinBox):
                    text_items.append(obj.suffix())
                text_items.append(obj.toolTip())
            untranslated = [s for s in text_items if s and s != 'Русский' and cyrillic.search(s)]
            self.assertFalse(untranslated, f'{name}: {untranslated}')

    def test_diagnostics_and_language_switch(self):
        w = self.window
        w.set_language('en')
        w.go('diag', animate=False)
        page = w.pages['diag']
        page._show([
            diagnostics.Check(diagnostics.WARN, 'Включён системный прокси: 127.0.0.1:10809',
                              'Убедитесь, что он рабочий, или отключите его, если не используете'),
            diagnostics.Check(diagnostics.WARN, 'Найдены службы VPN: HappService',
                              'Некоторые VPN конфликтуют с zapret — отключите их на время работы обхода'),
            diagnostics.Check(diagnostics.WARN, 'Защищённый DNS (DoH) не настроен',
                              'Настройте безопасный DNS в браузере или в параметрах Windows 11'),
            diagnostics.Check(diagnostics.WARN, 'WinDivert активен, но winws.exe не запущен',
                              'Возможно, WinDivert занят другой программой обхода',
                              action='fix_windivert', action_label='Удалить WinDivert'),
            diagnostics.Check(diagnostics.OK, 'Папка zapret', r'C:\Program Files\Zapret'),
            diagnostics.Check(diagnostics.OK, 'Base Filtering Engine работает'),
            diagnostics.Check(diagnostics.OK, 'TCP timestamps включены'),
        ])
        texts = [obj.text() for cls in (QLabel, QAbstractButton) for obj in page.findChildren(cls)]
        self.assertIn('Complete: 0 errors, 4 warnings', texts)
        self.assertIn('System proxy enabled: 127.0.0.1:10809', texts)
        self.assertIn('VPN services found: HappService', texts)
        self.assertIn('Remove WinDivert', texts)
        self.assertFalse([s for s in texts if re.search(r'[А-Яа-яЁё]', s)], texts)
        w.set_language('ru')
        texts = [obj.text() for obj in page.findChildren(QLabel)]
        self.assertIn('Готово: ошибок — 0, предупреждений — 4', texts)
        self.assertIn('Включён системный прокси: 127.0.0.1:10809', texts)
        w.set_language('en')
        self.assertEqual(page.status.text(), 'Complete: 0 errors, 4 warnings')

    def test_proxy_notice_and_upstream_language(self):
        from ui.i18n import get_language
        w = self.window
        w.set_language('en')
        self.assertEqual(get_language().value, 'en')
        with patch.object(w, 'isVisible', return_value=True), patch.object(w._toast, 'show_msg') as show:
            w.toast('Прокси запущен на 127.0.0.1:1443', 'ok')
            self.assertEqual(show.call_args.args[0], 'Proxy started on 127.0.0.1:1443')
        w.set_language('ru')
        self.assertEqual(get_language().value, 'ru')
        self.assertEqual(translate_text('Прокси запущен на 127.0.0.1:1443', 'ru'), 'Прокси запущен на 127.0.0.1:1443')

    def test_connectivity_card_and_proxy_client_are_independent(self):
        w = self.window
        w.set_language('en')
        page = w.pages['home']
        results = {'Discord': False, 'YouTube': True, 'Telegram Web': None}
        with patch('app.ui.page_home.run_bg', side_effect=lambda fn, done, failed: done(results)):
            page.check_button.click()
        self.assertEqual([state.text() for state in page.site_states.values()], ['Unavailable', 'Available', 'No response'])
        w.set_language('ru')
        self.assertEqual(page.site_states['YouTube'].text(), 'Доступен')
        for active, expected in [(0, 'Ожидание клиента'), (1, 'Клиент подключён')]:
            page.on_status({}, {'running': True, 'stats': {'active': active}})
            self.assertIn(expected, page.proxy_client.text())
        self.assertEqual(page.site_states['Telegram Web'].text(), 'Нет ответа')

    def test_release_notes_open_on_the_app_in_both_languages(self):
        from PySide6.QtWidgets import QTabWidget
        from app.paths import APP_VERSION
        from app.ui.release_notes import ReleaseNotesDialog
        for language, expected in [('en', 'Connectivity check'), ('ru', 'Проверка связи')]:
            self.window.set_language(language)
            for kind in (None, 'zapret', 'tg'):
                with self.subTest(language=language, kind=kind), patch('app.ui.release_notes.run_bg') as fetch:
                    dlg = ReleaseNotesDialog(self.window, kind)
                    tabs = dlg.findChild(QTabWidget)
                    self.assertEqual(tabs.tabText(tabs.currentIndex()), 'ZapretApp')
                    texts = [item.text() for item in tabs.currentWidget().findChildren(QLabel)]
                    self.assertIn('ZapretApp ' + APP_VERSION, texts)
                    self.assertIn(expected, texts)
                    fetch.assert_not_called()
                    dlg.deleteLater()

    def test_dashboard_mark_has_clear_background_and_keyhole(self):
        mark = self.window.rail.findChild(QLabel, 'dashboardLogo').pixmap().toImage()
        self.assertFalse(mark.isNull())
        def alpha(x, y):
            return mark.pixelColor(round(mark.width() * x), round(mark.height() * y)).alpha()
        for point in [(0.15, 0.5), (0.85, 0.5), (0.50, 0.30), (0.50, 0.46)]:
            self.assertEqual(alpha(*point), 0)
        for point in [(0.50, 0.18), (0.34, 0.48), (0.50, 0.82)]:
            self.assertGreater(alpha(*point), 240)

    def test_release_notes_show_each_components_own_release(self):
        from PySide6.QtWidgets import QPlainTextEdit, QTabWidget
        from app.ui.release_notes import ReleaseNotesDialog
        self.window.set_language('en')
        releases = {'zapret': {'tag_name': 'v2', 'body': 'First line\nSecond line'},
                    'tg': {'tag_name': 'v3', 'body': ''}}
        with patch('app.ui.release_notes.latest_release', side_effect=releases.get) as fetch, \
                patch('app.ui.release_notes.run_bg', side_effect=lambda fn, cb, err: cb(fn())):
            dlg = ReleaseNotesDialog(self.window)
            tabs = dlg.findChild(QTabWidget)
            self.assertEqual(tabs.count(), 3)
            for index, (tag, body) in enumerate([('v2', 'First line\nSecond line'), ('v3', 'The author did not provide release notes.')], start=1):
                tabs.setCurrentIndex(index)
                page = tabs.currentWidget()
                self.assertIn(tag, page.findChild(QLabel).text())
                self.assertEqual(page.findChild(QPlainTextEdit).toPlainText(), body)
            tabs.setCurrentIndex(1)
            self.assertEqual(fetch.call_count, 2)
        dlg.deleteLater()

    def test_updates_and_system_tray(self):
        w = self.window
        w.set_language('en')
        with patch('app.updates.check_component_versions', return_value=[
                ('zapret', '1.10.4', '1.10.4', True, ''),
                ('tg', '1.11.4', '1.12.0', False, '')]), \
             patch('app.ui.main_window.run_bg', side_effect=lambda fn, cb, *rest: cb(fn())):
            w.check_component_updates(manual=True)
        self.assertEqual(w.release_info.text(), 'Zapret 1.10.4: up to date\nTG 1.11.4: 1.12.0 available')
        w._build_tray_menu()
        texts = [action.text() for action in w.tray_menu.actions()]
        self.assertIn('Exit', texts)
        self.assertIn('Copy proxy link', texts)

    def test_first_start_drive_dialog_and_saved_choice(self):
        from PySide6.QtCore import QFileInfo, QTimer
        from PySide6.QtWidgets import QInputDialog
        cfg = self.cfg
        self.addCleanup(cfg.set, 'app', 'download_folder', cfg.get('app', 'download_folder'))
        cfg.set('app', 'download_folder', '')
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp) / 'Downloads'
            folder.mkdir()
            seen = []

            def answer(accept):
                dialog = QApplication.activeModalWidget()
                seen.append((dialog.labelText(), dialog.comboBoxItems(), dialog.textValue()))
                if accept:
                    dialog.accept()
                else:
                    dialog.reject()

            with patch('app.ui.first_start.QDir.drives', return_value=[QFileInfo(str(folder))]):
                QTimer.singleShot(0, lambda: answer(False))
                self.assertFalse(choose_download_drive(cfg))
                self.assertIsNone(Config().selected_download_folder)
                QTimer.singleShot(0, lambda: answer(True))
                self.assertTrue(choose_download_drive(cfg))
            self.assertEqual(len(seen), 2)
            self.assertEqual(seen[1][1:], ([str(folder)], str(folder)))
            saved = Config()
            self.assertEqual(saved.download_folder, folder)
            with patch.object(QInputDialog, 'exec', side_effect=AssertionError('unexpected dialog')):
                self.assertTrue(choose_download_drive(saved))

    def test_first_start_retries_unwritable_drive(self):
        from PySide6.QtWidgets import QDialog
        cfg = self.cfg
        self.addCleanup(cfg.set, 'app', 'download_folder', cfg.get('app', 'download_folder'))
        cfg.set('app', 'download_folder', '')
        with tempfile.TemporaryDirectory() as tmp, \
             patch('app.ui.first_start.QInputDialog') as picker, \
             patch('app.ui.first_start.QMessageBox.warning') as warning:
            picker.return_value.exec.return_value = QDialog.Accepted
            picker.return_value.textValue.side_effect = [str(Path(tmp) / 'missing'), tmp]
            self.assertTrue(choose_download_drive(cfg))
            warning.assert_called_once()
            self.assertEqual(Config().download_folder, Path(tmp))

    def test_selecting_drive_creates_named_folder(self):
        w = self.window
        settings = w.pages['settings']
        self.addCleanup(w.cfg.set, 'app', 'download_folder', w.cfg.get('app', 'download_folder'))
        self.addCleanup(settings.download_path.setText, str(w.cfg.download_folder))
        with tempfile.TemporaryDirectory() as tmp:
            drive = Path(tmp)
            destination = drive / APP_NAME

            # Exercise the drive-root branch on a real, disposable directory.
            class TestDrivePath(type(drive)):
                @property
                def parent(self):
                    return self if self == drive else super().parent

            with patch('app.ui.page_misc.Path', TestDrivePath), \
                 patch('app.ui.page_misc.QFileDialog.getExistingDirectory', return_value=str(drive)):
                destination.write_text('existing file')
                with patch.object(w, 'toast') as toast:
                    settings._choose_download_folder()
                    toast.assert_called_once()
                self.assertNotEqual(w.cfg.download_folder, destination)
                self.assertEqual(destination.read_text(), 'existing file')
                destination.unlink()
                settings._choose_download_folder()
                self.assertTrue(destination.is_dir())
                self.assertEqual(settings.download_path.text(), str(destination))
                marker = destination / 'existing.zip'
                marker.touch()
                settings._choose_download_folder()
                self.assertEqual(list(destination.iterdir()), [marker])
                self.assertEqual(Config().download_folder, destination)

    def test_download_folder_persists_and_routes_updates(self):
        w = self.window
        settings = w.pages['settings']
        old = w.cfg.get('app', 'download_folder')
        self.addCleanup(w.cfg.set, 'app', 'download_folder', old)
        self.addCleanup(settings.download_path.setText, str(w.cfg.download_folder))
        w.set_language('en')
        picker = 'app.ui.page_misc.QFileDialog.getExistingDirectory'
        with tempfile.TemporaryDirectory(prefix='downloads ') as folder:
            selected = Path(folder) / 'Папка обновлений'
            selected.mkdir()
            with patch(picker, return_value=str(selected)) as dialog:
                settings._choose_download_folder()
                self.assertEqual(dialog.call_args.args[1], 'Update download folder')
            self.assertEqual(Config().download_folder, selected)
            self.assertEqual(settings.download_path.text(), str(selected))
            with patch(picker, return_value=''):
                settings._choose_download_folder()
            with patch(picker, return_value=str(selected / 'missing')), patch.object(w, 'toast') as toast:
                settings._choose_download_folder()
                toast.assert_called_once()
            self.assertEqual(Config().download_folder, selected)
            with patch('app.ui.page_misc.winutils.open_path') as open_folder:
                settings._open_updates()
                open_folder.assert_called_once_with(str(selected))
            with patch('app.updates.install_components', return_value=[]) as install, \
                 patch('app.ui.main_window.run_bg', side_effect=lambda fn, cb, *rest: cb(fn())):
                for kind, manual in [('tg', True), ('zapret', True), (None, False)]:
                    w.download_updates_now(manual=manual, kind=kind)
                    install.assert_called_with(kind, selected)

    def test_dynamic_status_and_confirmation(self):
        from app.ui.fancy import ConfirmDialog
        w = self.window
        w.set_language('en')
        w.go('home', animate=False)
        with patch.object(w, 'isVisible', return_value=True):
            w.on_status({'running': True, 'app_running': True, 'uptime': 120, 'strategy': 'general.bat'},
                        {'running': True, 'uptime': 61, 'port': 1443,
                         'stats': {'active': 5, 'up': '5KB', 'down': '10KB', 'up_raw': 5, 'down_raw': 10}},
                        {'enabled': False})
        home = w.pages['home']
        self.assertIn('running 2 min', home.m_z.status.text())
        self.assertNotRegex(home.m_t.sub.text(), r'[А-Яа-яЁё]')
        self.assertTrue(home.m_z.switch.isChecked())
        self.assertTrue(home.m_t.property('active'))
        self.assertFalse(home.m_d.switch.isChecked())
        self.assertEqual(home.m_d.status.text(), 'off')
        for section, card in home.modules.items():
            card.details.click()
            self.assertEqual(w._current, section)
        dialog = ConfirmDialog(w.pages['diag'], 'Кэш Discord', 'Закрыть Discord и очистить его кэш?', ok='Очистить')
        texts = [item.text() for cls in (QLabel, QAbstractButton) for item in dialog.findChildren(cls)]
        self.assertIn('Discord cache', texts)
        self.assertIn('Close Discord and clear its cache?', texts)
        self.assertIn('Clear', texts)
        self.assertIn('Cancel', texts)


if __name__ == '__main__':
    unittest.main()

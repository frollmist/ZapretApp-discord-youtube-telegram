import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QComboBox, QVBoxLayout, QDialog, QPushButton
from app.ui.language import apply_language

class LanguageTest(unittest.TestCase):
    def test_upgrade_prompts_until_the_user_chooses(self):
        from app.config import Config
        from app.ui.first_start import choose_first_language

        app = QApplication.instance() or QApplication([])

        def choose_russian(dialog):
            button = next(b for b in dialog.findChildren(QPushButton) if b.text() == 'Русский')
            button.click()
            return dialog.result()

        with TemporaryDirectory() as folder:
            path = Path(folder) / 'config.json'
            path.write_text('{"app":{"language":"en","first_run_done":true}}', encoding='utf-8')
            with patch('app.config.CONFIG_FILE', path), patch('app.config.ensure_dirs'):
                with patch.object(QDialog, 'exec', return_value=QDialog.Rejected):
                    self.assertFalse(choose_first_language(Config()))
                self.assertEqual(Config().get('app', 'language'), 'en')
                with patch.object(QDialog, 'exec', choose_russian):
                    self.assertTrue(choose_first_language(Config()))
                saved = Config()
                self.assertEqual(saved.get('app', 'language'), 'ru')
                self.assertTrue(saved.get('app', 'language_chosen'))
                with patch.object(QDialog, 'exec', side_effect=AssertionError('Repeated prompt')):
                    self.assertTrue(choose_first_language(saved))

    def test_switch_and_dynamic_text(self):
        app = QApplication.instance() or QApplication([])
        window = QWidget()
        layout = QVBoxLayout(window)
        state = QLabel('ОТКЛЮЧЕНО')
        combo = QComboBox()
        combo.addItem('Стратегия')
        layout.addWidget(state)
        layout.addWidget(combo)
        apply_language(window, 'en')
        self.assertEqual(state.text(), 'OFF')
        self.assertEqual(combo.itemText(0), 'Strategy')
        state.setText('ВКЛЮЧЕНО')
        apply_language(window, 'en')
        self.assertEqual(state.text(), 'ON')
        apply_language(window, 'ru')
        self.assertEqual(state.text(), 'ВКЛЮЧЕНО')
        self.assertEqual(combo.itemText(0), 'Стратегия')

if __name__ == '__main__': unittest.main()

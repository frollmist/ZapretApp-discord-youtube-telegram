"""First-launch choices before the main window opens."""
from pathlib import Path

from PySide6.QtCore import QDir
from PySide6.QtWidgets import QDialog, QHBoxLayout, QInputDialog, QLabel, QMessageBox, QPushButton, QVBoxLayout

from ..config import Config
from ..paths import APP_NAME, INSTALLED_LAYOUT
from .icons import app_icon
from .language import translate_text
from .theme import PALETTES, qss


def choose_first_language(cfg: Config) -> bool:
    if cfg.get("app", "language_chosen"):
        return True

    dialog = QDialog()
    dialog.setWindowTitle("ZapretApp")
    dialog.setWindowIcon(app_icon())
    palette = PALETTES.get(cfg.get("app", "theme"), PALETTES["dark"])
    dialog.setStyleSheet(qss(palette) + f"QDialog {{ background: {palette['surface_solid']}; }}")
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(24, 22, 24, 22)
    layout.setSpacing(16)
    heading = QLabel("Выберите язык / Choose your language")
    heading.setObjectName("sectionTitle")
    layout.addWidget(heading)
    row = QHBoxLayout()
    layout.addLayout(row)

    def select(language: str) -> None:
        try:
            cfg.update_section("app", {"language": language, "language_chosen": True})
        except OSError as exc:
            message = "Could not save your choice." if language == "en" else "Не удалось сохранить выбор."
            QMessageBox.warning(dialog, "ZapretApp", f"{message}\n{exc}")
            return
        dialog.accept()

    for code, name in (("ru", "Русский"), ("en", "English")):
        button = QPushButton(name)
        button.clicked.connect(lambda checked=False, language=code: select(language))
        row.addWidget(button, 1)

    return dialog.exec() == QDialog.Accepted


def choose_download_drive(cfg: Config) -> bool:
    if INSTALLED_LAYOUT or cfg.selected_download_folder is not None:
        return True

    language = cfg.get("app", "language", "ru")
    dialog = QInputDialog()
    dialog.setWindowTitle(APP_NAME)
    dialog.setLabelText(translate_text("На какой диск скачивать обновления?", language))
    dialog.setOkButtonText(translate_text("Продолжить", language))
    dialog.setCancelButtonText(translate_text("Выход", language))
    drives = [str(Path(drive.absoluteFilePath())) for drive in QDir.drives()]
    if not drives:
        QMessageBox.warning(None, APP_NAME, translate_text("Не удалось найти доступные диски.", language))
        return False
    dialog.setComboBoxItems(drives)
    dialog.setComboBoxEditable(False)
    if cfg.download_folder.anchor in drives:
        dialog.setTextValue(cfg.download_folder.anchor)

    while dialog.exec() == QDialog.Accepted:
        try:
            cfg.set_download_folder(Path(dialog.textValue()))
            return True
        except OSError as exc:
            QMessageBox.warning(dialog, APP_NAME, translate_text(f"Не удалось выбрать папку: {exc}", language))
    return False

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QLabel, QPlainTextEdit, QTabWidget, QVBoxLayout, QWidget
from shiboken6 import isValid

from .. import winutils
from ..paths import APP_VERSION
from ..updates import RELEASES, latest_release
from .language import translate_text
from .theme import PALETTES, qss
from .widgets import button, label, row, run_bg


APP_CHANGES = (
    ("Проверка связи", "На главной можно проверить Discord, YouTube и Telegram Web и увидеть, подключён ли клиент к Telegram-прокси."),
    ("Отмена последнего изменения", "Кнопка «Вернуть как было» возвращает предыдущую стратегию или версию Zapret. На вкладке Telegram она возвращает предыдущую версию прокси."),
    ("Оформление главной", "У замка между кнопками Telegram и Zapret теперь прозрачный фон."),
)


class ReleaseNotesDialog(QDialog):
    def __init__(self, parent, kind=None):
        super().__init__(parent)
        language = parent.cfg.get("app", "language", "ru")
        self.tr_text = lambda text: translate_text(text, language)
        self.setWindowTitle(self.tr_text("Что нового"))
        self.resize(600, 420)
        palette = PALETTES.get(parent.cfg.get("app", "theme"), PALETTES["dark"])
        self.setStyleSheet(qss(palette) + f"""
            QDialog, QTabWidget::pane, QWidget#releasePage {{ background: {palette['surface_solid']}; }}
        """)
        tabs = QTabWidget()
        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        app_page = QWidget()
        app_page.setObjectName("releasePage")
        notes = QVBoxLayout(app_page)
        notes.setContentsMargins(16, 16, 16, 16)
        notes.setSpacing(6)
        notes.addWidget(label(f"ZapretApp {APP_VERSION}", "titleText"))
        for heading, detail in APP_CHANGES:
            notes.addSpacing(8)
            notes.addWidget(label(self.tr_text(heading), "sectionTitle"))
            notes.addWidget(label(self.tr_text(detail), wrap=True, selectable=True))
        notes.addStretch()
        tabs.addTab(app_page, "ZapretApp")
        pending = {}
        for key, repo, _ in RELEASES:
            if kind is None or key == kind:
                page = QWidget()
                page.setObjectName("releasePage")
                column = QVBoxLayout(page)
                status = QLabel(self.tr_text("Загрузка описания…"))
                body = QPlainTextEdit()
                body.setReadOnly(True)
                url = f"https://github.com/{repo}/releases/latest"
                column.addWidget(status)
                column.addWidget(body)
                column.addLayout(row(button(self.tr_text("Открыть на GitHub"), "", "link",
                                            lambda checked=False, link=url: winutils.open_url(link)), None))
                index = tabs.addTab(page, "Zapret" if key == "zapret" else "TG WS Proxy")
                pending[index] = (key, status, body)

        def load_selected(index):
            if index in pending:
                self._load(*pending.pop(index))

        tabs.currentChanged.connect(load_selected)

    def _load(self, kind, status, body):
        def done(release):
            if not isValid(status):
                return
            tag = str(release.get("tag_name") or "").strip()
            status.setTextFormat(Qt.PlainText)
            status.setText(f"{self.tr_text('Последний релиз')} · {tag}")
            body.setPlainText(str(release.get("body") or "").strip() or self.tr_text("Автор не добавил описание."))

        def failed(error):
            if not isValid(status):
                return
            status.setText(self.tr_text("Не удалось загрузить описание."))
            body.setPlainText(str(error))

        run_bg(lambda: latest_release(kind), done, failed)

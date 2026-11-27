"""Главное окно (полупрозрачное, со своей рамкой), трей и связка UI с менеджерами."""
from __future__ import annotations

import logging
import time
from typing import Dict, Optional

from PySide6.QtCore import QEasingCurve, QPoint, QPointF, QPropertyAnimation, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QColor, QCursor, QPainter, QPainterPath, QRadialGradient
from PySide6.QtWidgets import (QApplication, QButtonGroup, QFrame, QGraphicsOpacityEffect, QHBoxLayout, QLabel,
                               QMainWindow, QMenu, QPushButton, QStackedWidget, QSystemTrayIcon, QToolButton,
                               QVBoxLayout, QWidget)

from .. import winutils
from ..paths import APP_NAME, APP_VERSION, DATA_DIR, UI_CACHE_DIR
from . import icons, window_fx
from .fancy import C, style_popup
from .page_dns import DnsPage
from .page_home import HomePage
from .page_misc import DiagnosticsPage, LogsPage, SettingsPage
from .page_tg import TelegramPage
from .page_zapret import ZapretPage
from .theme import PALETTES, qss
from .language import apply_language, translate_text
from .widgets import Palette, Toast, label, run_bg

log = logging.getLogger("zapret-tg.ui")

NAV = [
    ("home", "Главная", "home"),
    ("zapret", "Zapret", "shield"),
    ("tg", "Telegram", "send"),
    ("dns", "DNS", "sparkle"),
    ("diag", "Проверка", "pulse"),
    ("settings", "Настройки", "gear"),
    ("logs", "Логи", "doc"),
]

EDGE = 6


class Shell(QWidget):
    """Фон окна: полупрозрачная тонировка + мягкие цветные «пятна» света."""

    def __init__(self, win: "MainWindow"):
        super().__init__()
        self.win = win
        self.setObjectName("root")
        self.setMouseTracking(True)
        self.blur = False

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect())
        radius = 0.0 if (self.win.isMaximized() or window_fx.round_corners_native()) else 14.0
        path = QPainterPath()
        path.addRoundedRect(r, radius, radius)
        rgb = Palette.p.get("window", (18, 20, 36))
        translucent = self.win.cfg.get("app", "translucent", True)
        alpha = 0.80 if (self.blur and translucent) else 0.985
        p.fillPath(path, QColor(rgb[0], rgb[1], rgb[2], int(255 * alpha)))
        p.setClipPath(path)
        # световые пятна как на референсе (пурпур справа сверху, фиолет слева снизу)
        for (fx, fy, key, a) in ((0.92, 0.0, "accent", 0.16), (0.0, 1.0, "accent2", 0.13), (0.55, 0.62, "accent3", 0.04)):
            g = QRadialGradient(QPointF(r.width() * fx, r.height() * fy), max(r.width(), r.height()) * 0.55)
            c = C(key)
            c.setAlphaF(a)
            g.setColorAt(0, c)
            c2 = C(key)
            c2.setAlphaF(0)
            g.setColorAt(1, c2)
            p.fillRect(r, g)
        if radius:
            p.setClipping(False)
            p.setPen(QColor(255, 255, 255, 22))
            p.drawRoundedRect(r.adjusted(0.5, 0.5, -0.5, -0.5), radius, radius)
        p.end()

    # ------- изменение размера за края (системными средствами Qt)
    def _edges(self, pos: QPoint):
        if self.win.isMaximized():
            return Qt.Edges()
        w, h = self.width(), self.height()
        e = Qt.Edges()
        if pos.x() <= EDGE:
            e |= Qt.LeftEdge
        if pos.x() >= w - EDGE:
            e |= Qt.RightEdge
        if pos.y() <= EDGE:
            e |= Qt.TopEdge
        if pos.y() >= h - EDGE:
            e |= Qt.BottomEdge
        return e

    def mouseMoveEvent(self, e):
        ed = self._edges(e.position().toPoint())
        cur = Qt.ArrowCursor
        if ed in (Qt.LeftEdge | Qt.TopEdge, Qt.RightEdge | Qt.BottomEdge):
            cur = Qt.SizeFDiagCursor
        elif ed in (Qt.RightEdge | Qt.TopEdge, Qt.LeftEdge | Qt.BottomEdge):
            cur = Qt.SizeBDiagCursor
        elif ed & (Qt.LeftEdge | Qt.RightEdge):
            cur = Qt.SizeHorCursor
        elif ed & (Qt.TopEdge | Qt.BottomEdge):
            cur = Qt.SizeVerCursor
        self.setCursor(cur)
        super().mouseMoveEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            ed = self._edges(e.position().toPoint())
            if ed and self.win.windowHandle():
                self.win.windowHandle().startSystemResize(ed)
                return
        super().mousePressEvent(e)


class TitleBar(QWidget):
    def __init__(self, win: "MainWindow"):
        super().__init__()
        self.win = win
        self.setObjectName("titleBar")
        self.setFixedHeight(64)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(26, 14, 10, 0)
        lay.setSpacing(6)
        col = QVBoxLayout()
        col.setSpacing(0)
        self.title = label("", "titleText")
        self.sub = label("", "titleSub")
        col.addWidget(self.title)
        col.addWidget(self.sub)
        lay.addLayout(col, 1)
        self.chips = QLabel()
        self.chips.setObjectName("hint")
        lay.addWidget(self.chips, 0, Qt.AlignTop)
        lay.addSpacing(14)
        self.b_min = self._wbtn("min", win.showMinimized, "Свернуть")
        self.b_max = self._wbtn("max", self._toggle_max, "Развернуть")
        self.b_close = self._wbtn("close", win.close, "Закрыть", close=True)
        for b in (self.b_min, self.b_max, self.b_close):
            lay.addWidget(b, 0, Qt.AlignTop)

    def _wbtn(self, ic: str, fn, tip: str, close: bool = False) -> QPushButton:
        b = QPushButton()
        b.setObjectName("winClose" if close else "winBtn")
        b.setFixedSize(40, 32)
        b.setToolTip(tip)
        b.setCursor(Qt.PointingHandCursor)
        b.clicked.connect(fn)
        b._ic = ic
        return b

    def repaint_icons(self) -> None:
        col = Palette.p["muted"]
        self.b_min.setIcon(icons.icon("min", col, 16))
        self.b_max.setIcon(icons.icon("restore" if self.win.isMaximized() else "max", col, 16))
        self.b_close.setIcon(icons.icon("close", col, 16))
        for b in (self.b_min, self.b_max, self.b_close):
            b.setIconSize(QSize(16, 16))

    def _toggle_max(self) -> None:
        if self.win.isMaximized():
            self.win.showNormal()
        else:
            self.win.showMaximized()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and self.win.windowHandle():
            self.win.windowHandle().startSystemMove()
            return
        super().mousePressEvent(e)

    def mouseDoubleClickEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._toggle_max()


class Rail(QFrame):
    """Узкая боковая панель с иконками и подсветкой активного пункта."""

    def __init__(self):
        super().__init__()
        self.setObjectName("rail")
        self.setFixedWidth(165)
        self.active: Optional[QToolButton] = None

    def paintEvent(self, e):
        super().paintEvent(e)
        if self.active is None:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        g = self.active.geometry()
        from PySide6.QtGui import QLinearGradient
        lg = QLinearGradient(0, g.top(), 0, g.bottom())
        lg.setColorAt(0, C("accent"))
        lg.setColorAt(1, C("accent2"))
        p.setPen(Qt.NoPen)
        p.setBrush(lg)
        p.drawRoundedRect(QRectF(2, g.top() + 12, 4, g.height() - 24), 2, 2)
        p.end()


class MainWindow(QMainWindow):
    def __init__(self, cfg, zapret, tg, dns):
        super().__init__()
        self.cfg, self.zapret, self.tg, self.dns = cfg, zapret, tg, dns
        from ..tgproxy import set_language as set_proxy_language
        set_proxy_language(cfg.get('app', 'language', 'ru'))
        self.window = self
        self._quitting = False
        self._polling = False
        self._last_z: Dict = {}
        self._last_t: Dict = {}
        self._last_d: Dict = {}
        self._tray_hint_shown = False
        self._ticks = 0
        self._prev_bytes = None
        self._updates_busy = False
        self._checks_busy = False

        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(icons.app_icon("on"))
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowMinMaxButtonsHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.resize(1200, 860)
        self.setMinimumSize(1000, 660)
        self.apply_theme(cfg.get("app", "theme", "dark"))

        self.shell = Shell(self)
        outer = QHBoxLayout(self.shell)
        outer.setContentsMargins(EDGE - 2, EDGE - 2, EDGE - 2, EDGE - 2)
        outer.setSpacing(0)

        # ---- rail
        self.rail = Rail()
        rv = QVBoxLayout(self.rail)
        rv.setContentsMargins(10, 18, 10, 14)
        rv.setSpacing(6)
        logo = QLabel()
        px = icons.app_pixmap(84, "on")
        px.setDevicePixelRatio(2)
        logo.setPixmap(px)
        logo.setAlignment(Qt.AlignHCenter)
        logo.setToolTip(f"{APP_NAME} {APP_VERSION}")
        rv.addWidget(logo, 0, Qt.AlignHCenter)
        brand = label(APP_NAME, "tiny", wrap=True)
        brand.setMaximumWidth(145)
        brand.setAlignment(Qt.AlignHCenter)
        rv.addWidget(brand)
        rv.addSpacing(20)
        self.nav_group = QButtonGroup(self)
        self.nav_buttons: Dict[str, QToolButton] = {}
        for key, text, ic in NAV:
            b = QToolButton()
            b.setObjectName("railBtn")
            b.setText(text)
            b.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            b.setIconSize(QSize(22, 22))
            b.setFixedSize(145, 44)
            b.clicked.connect(lambda _=False, k=key: self.go(k))
            self.nav_group.addButton(b)
            self.nav_buttons[key] = b
            rv.addWidget(b, 0, Qt.AlignHCenter)
        rv.addStretch(1)
        self.rail_dots = label("", "tiny")
        self.rail_dots.setAlignment(Qt.AlignHCenter)
        rv.addWidget(self.rail_dots)
        version_label = label("Версия 1.0 BETA", "tiny")
        version_label.setAlignment(Qt.AlignHCenter)
        rv.addWidget(version_label)
        self.release_info = label("Обновления: проверка…", "tiny", wrap=True)
        self.release_info.setAlignment(Qt.AlignHCenter)
        rv.addWidget(self.release_info)
        outer.addWidget(self.rail)

        # ---- content
        content = QWidget()
        content.setObjectName("content")
        cv = QVBoxLayout(content)
        cv.setContentsMargins(0, 0, 0, 0)
        cv.setSpacing(0)
        self.titlebar = TitleBar(self)
        cv.addWidget(self.titlebar)
        self.stack = QStackedWidget()
        self.pages = {
            "home": HomePage(self),
            "zapret": ZapretPage(self),
            "tg": TelegramPage(self),
            "dns": DnsPage(self),
            "diag": DiagnosticsPage(self),
            "settings": SettingsPage(self),
            "logs": LogsPage(self),
        }
        for p in self.pages.values():
            self.stack.addWidget(p)
        cv.addWidget(self.stack, 1)
        outer.addWidget(content, 1)
        self.setCentralWidget(self.shell)
        self._toast = Toast(self.shell)
        self._current = "home"
        self._paint_icons()
        self.go("home", animate=False)

        # ---- трей
        self.tray = QSystemTrayIcon(icons.app_icon("off"), self)
        self.tray.setToolTip(APP_NAME)
        self.tray_menu = QMenu()
        style_popup(self.tray_menu)
        self.tray_menu.aboutToShow.connect(self._build_tray_menu)
        self.tray.setContextMenu(self.tray_menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.messageClicked.connect(self.show_window)
        self.tray.show()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_now)
        self.timer.start(2000)
        QTimer.singleShot(50, self.refresh_now)

    # ------------------------------------------------------------- тема
    def apply_theme(self, name: str) -> None:
        pal = PALETTES.get(name, PALETTES["dark"])
        Palette.p = pal
        arrow = check = ""
        try:
            d = UI_CACHE_DIR
            d.mkdir(parents=True, exist_ok=True)
            fa, fc = d / f"arrow_{name}.png", d / "check.png"
            icons.pixmap("chevron", pal["muted"], 12, 2.2).save(str(fa))
            icons.pixmap("check", "#ffffff", 14, 2.6).save(str(fc))
            arrow, check = str(fa).replace("\\", "/"), str(fc).replace("\\", "/")
        except Exception:
            pass
        QApplication.instance().setStyleSheet(qss(pal, arrow, check))

    def apply_backdrop(self) -> None:
        dark = self.cfg.get("app", "theme", "dark") == "dark"
        try:
            hwnd = int(self.winId())
        except Exception:
            hwnd = 0
        self.shell.blur = window_fx.apply_backdrop(hwnd, dark, bool(self.cfg.get("app", "translucent", True)))
        self.shell.update()

    def set_theme(self, name: str) -> None:
        self.cfg.set("app", "theme", name)
        self.apply_theme(name)
        self.apply_backdrop()
        self._paint_icons()
        for p in self.pages.values():
            p.update()
        self.shell.update()
        self.on_status(self._last_z, self._last_t, self._last_d)

    def set_translucent(self, on: bool) -> None:
        self.cfg.set("app", "translucent", on)
        self.apply_backdrop()

    def _paint_icons(self) -> None:
        p = Palette.p
        for key, _t, ic in NAV:
            self.nav_buttons[key].setIcon(icons.icon(ic, p["text"] if key == self._current else p["faint"], 22))
        self.titlebar.repaint_icons()

    def showEvent(self, e):
        super().showEvent(e)
        QTimer.singleShot(0, self.apply_backdrop)
        if not getattr(self, "_fitted", False):
            self._fitted = True
            QTimer.singleShot(0, self._fit_to_screen)

    def _content_min_width(self) -> int:
        need = 0
        for p in self.pages.values():
            inner = getattr(p, "inner", None)
            if inner is not None:
                need = max(need, inner.minimumSizeHint().width())
        sb = 12  # вертикальная полоса прокрутки
        return self.rail.width() + need + sb + 2 * EDGE

    def _fit_to_screen(self) -> None:
        """Окно не меньше содержимого и не больше экрана (учитывая масштаб Windows)."""
        min_w = max(1000, self._content_min_width())
        scr = self.screen().availableGeometry() if self.screen() else None
        if scr is not None:
            min_w = min(min_w, scr.width())
            min_h = min(660, scr.height())
            self.setMinimumSize(min_w, min_h)
            w = max(min_w, min(self.width(), int(scr.width() * 0.94)))
            h = max(min_h, min(self.height(), int(scr.height() * 0.94)))
            if not self.isMaximized():
                self.resize(w, h)
                self.move(scr.x() + (scr.width() - w) // 2, scr.y() + (scr.height() - h) // 2)
        else:
            self.setMinimumWidth(min_w)

    def changeEvent(self, e):
        super().changeEvent(e)
        if e.type() == e.Type.WindowStateChange:
            self.titlebar.repaint_icons()
            m = 0 if self.isMaximized() else EDGE - 2
            self.shell.layout().setContentsMargins(m, m, m, m)
            self.shell.update()

    # --------------------------------------------------------- навигация
    def go(self, key: str, animate: bool = True) -> None:
        old = self.pages.get(self._current)
        if old and key != self._current:
            old.on_hide()
        self._current = key
        b = self.nav_buttons[key]
        b.setChecked(True)
        self.rail.active = b
        self.rail.update()
        page = self.pages[key]
        self.titlebar.title.setText(page.title)
        self.titlebar.sub.setText(page.subtitle)
        self.stack.setCurrentWidget(page)
        self._paint_icons()
        page.on_show()
        if self._last_z or self._last_t:
            page.on_status(self._last_z, self._last_t, self._last_d)
        language = self.cfg.get("app", "language", "ru")
        if language == "en":
            for section in (self.rail, self.titlebar, page):
                apply_language(section, language)
        if animate:
            eff = QGraphicsOpacityEffect(page)
            page.setGraphicsEffect(eff)
            a = QPropertyAnimation(eff, b"opacity", page)
            a.setDuration(200)
            a.setStartValue(0.0)
            a.setEndValue(1.0)
            a.setEasingCurve(QEasingCurve.OutCubic)
            a.finished.connect(lambda: page.setGraphicsEffect(None))  # не держим эффект — экономим ресурсы
            a.start()
            self._page_anim = a

    def toast(self, msg: str, level: str = "info", ms: int = 4500) -> None:
        msg = translate_text(msg, self.cfg.get('app', 'language', 'ru'))
        if self.isVisible() and not self.isMinimized():
            self._toast.show_msg(msg, level, ms)
        elif level in ("err", "warn") and self.cfg.get("app", "notifications", True):
            self.tray.showMessage(APP_NAME, msg, QSystemTrayIcon.Warning if level == "warn" else QSystemTrayIcon.Critical, 5000)
        log.info("[%s] %s", level, msg)

    def set_language(self, language: str) -> None:
        if language not in ("ru", "en"):
            return
        self.cfg.set("app", "language", language)
        from ..tgproxy import set_language as set_proxy_language
        set_proxy_language(language)
        apply_language(self, language)
        if self._last_z or self._last_t:
            self.on_status(self._last_z, self._last_t, self._last_d)

    # ----------------------------------------------------------- статус
    def refresh_now(self) -> None:
        if self._polling:
            return
        self._polling = True
        self._ticks += 1
        ensure_dns = self._ticks % 30 == 0  # ~раз в минуту (или реже, когда окно скрыто)

        def collect():
            if ensure_dns:
                try:
                    self.dns.ensure()
                except Exception:
                    log.exception("dns.ensure")
            zs = self.zapret.status()
            st = self.tg.stats()
            ts = {
                "running": self.tg.is_running(),
                "active": self.tg.is_active(),
                "error": self.tg.last_error,
                "host": self.cfg.get("tg", "host"),
                "port": self.cfg.get("tg", "port"),
                "stats": st,
                "uptime": self.tg.uptime(),
                "t": time.time(),
            }
            ds = self.dns.status()
            return zs, ts, ds

        def done(res):
            self._polling = False
            zs, ts, ds = res
            # скорость трафика прокси
            st = ts.get("stats") or {}
            now_b = (st.get("up_raw", 0), st.get("down_raw", 0), ts["t"])
            if self._prev_bytes and now_b[2] > self._prev_bytes[2]:
                dt = now_b[2] - self._prev_bytes[2]
                ts["speed_up"] = max(0, now_b[0] - self._prev_bytes[0]) / dt
                ts["speed_down"] = max(0, now_b[1] - self._prev_bytes[1]) / dt
            self._prev_bytes = now_b
            self.on_status(zs, ts, ds)

        run_bg(collect, done, lambda e: setattr(self, "_polling", False))
        want = 2000 if (self.isVisible() and not self.isMinimized()) else 8000
        if self.timer.interval() != want:
            self.timer.setInterval(want)

    def on_status(self, zs: Dict, ts: Dict, ds: Optional[Dict] = None) -> None:
        if not zs and not ts:
            return
        ds = ds or {}
        prev_z, prev_t = self._last_z, self._last_t
        self._last_z, self._last_t, self._last_d = zs, ts, ds
        z_on, t_on, d_on = bool(zs.get("running")), bool(ts.get("running")), bool(ds.get("enabled"))
        state = "on" if z_on and t_on else ("partial" if z_on or t_on else "off")
        self.tray.setIcon(icons.app_icon(state))
        en = self.cfg.get('app', 'language', 'ru') == 'en'
        on_text, off_text = ('on', 'off') if en else ('вкл', 'выкл')
        self.tray.setToolTip(f"{APP_NAME}\nZapret: {on_text if z_on else off_text}\n"
                             f"{'Telegram proxy' if en else 'Telegram прокси'}: {on_text if t_on else off_text}\n"
                             f"DNS: {on_text if d_on else off_text}")
        dot = lambda on: f"<span style='color:{Palette.p['on'] if on else Palette.p['faint']}'>●</span>"
        self.rail_dots.setText(f"{dot(z_on)} {dot(t_on)} {dot(d_on)}")
        self.rail_dots.setToolTip("Zapret · Telegram · DNS")
        if self.isVisible():
            self.pages[self._current].on_status(zs, ts, ds)
            if self.cfg.get("app", "language", "ru") == "en":
                apply_language(self.pages[self._current], "en")
            if self._current != "home":
                self.pages["home"].feed_speed(ts)
        else:
            self.pages["home"].feed_speed(ts)
        if not self.isVisible() and self.cfg.get("app", "notifications", True):
            if prev_z.get("running") and not z_on and zs.get("error"):
                error = translate_text(str(zs["error"]).split("\n")[0], 'en' if en else 'ru')
                self.tray.showMessage(APP_NAME, "Zapret: " + error, QSystemTrayIcon.Warning, 5000)
            if prev_t.get("running") and not t_on and ts.get("error"):
                error = translate_text(str(ts["error"]).split("\n")[0], 'en' if en else 'ru')
                self.tray.showMessage(APP_NAME, ("Telegram proxy: " if en else "Telegram прокси: ") + error,
                                      QSystemTrayIcon.Warning, 5000)

    # ------------------------------------------------- действия (контекст)
    def set_zapret(self, on: bool) -> None:
        home = self.pages["home"]
        home.set_busy("zapret", True)
        use_service = self.cfg.get("zapret", "mode") == "service" and self.zapret.service_installed()

        def work():
            if use_service:
                return self.zapret.service_start() if on else self.zapret.service_stop()
            return self.zapret.start() if on else self.zapret.stop()

        def done(res):
            home.set_busy("zapret", False)
            ok, msg = res
            if use_service and ok:
                msg = "Служба zapret запущена" if on else "Служба zapret остановлена"
            self.toast(msg or ("Готово" if ok else "Ошибка"), "ok" if ok else "err", 3000 if ok else 8000)
            self.refresh_now()

        run_bg(work, done, lambda e: (home.set_busy("zapret", False), self.toast(str(e), "err")))

    def set_tg(self, on: bool) -> None:
        home = self.pages["home"]
        home.set_busy("tg", True)

        def done(res):
            home.set_busy("tg", False)
            ok, msg = res
            self.toast(msg, "ok" if ok else "err", 3000 if ok else 8000)
            self.refresh_now()

        run_bg(self.tg.start if on else self.tg.stop, done,
               lambda e: (home.set_busy("tg", False), self.toast(str(e), "err")))

    def set_dns(self, on: bool, provider: Optional[str] = None) -> None:
        home = self.pages["home"]
        home.set_busy("dns", True)
        self.toast("Включаю DNS…" if on else "Возвращаю прежний DNS…", "info", 2500)

        def done(res):
            home.set_busy("dns", False)
            ok, msg = res
            self.toast(msg, "ok" if ok else "err", 4000 if ok else 9000)
            self.refresh_now()
            self.pages["dns"].on_show()

        run_bg(lambda: self.dns.enable(provider) if on else self.dns.disable(), done,
               lambda e: (home.set_busy("dns", False), self.toast(str(e), "err")))

    def set_all(self, on: bool) -> None:
        z_on = bool(self._last_z.get("running"))
        t_on = bool(self._last_t.get("running"))
        d_on = bool(self._last_d.get("enabled"))
        if z_on != on:
            self.set_zapret(on)
        if t_on != on:
            self.set_tg(on)
        if d_on != on:
            self.set_dns(on)

    def apply_strategy(self, strategy: str) -> None:
        def done(result):
            ok, message = result
            self.reload_strategies()
            page = self.pages["zapret"]
            page.combo.setCurrentIndex(page.combo.findData(self.cfg.get("zapret", "strategy")))
            page.undo_button.setEnabled(bool(self.cfg.get("zapret", "undo_selection")))
            page._note()
            self.toast(message, "ok" if ok else "err")
            self.refresh_now()
        run_bg(lambda: self.zapret.select_strategy(strategy), done, lambda error: done((False, str(error))))

    def restart_zapret_if_running(self, msg: Optional[str]) -> None:
        if self.zapret.is_running_app():
            run_bg(self.zapret.start, lambda r: (self.toast((msg + ". " if msg else "") + ("Обход перезапущен" if r[0] else r[1]),
                                                            "ok" if r[0] else "err"), self.refresh_now()))
        elif self.cfg.get("zapret", "mode") == "service" and self.zapret.service_state() == "running":
            self.toast((msg + ". " if msg else "") + "Для службы: переустановите её, чтобы применить изменения", "warn", 6000)
        elif msg:
            self.toast(msg, "ok")

    def reload_strategies(self) -> None:
        self.pages["home"].reload_strategies()

    def open_telegram(self) -> None:
        url = self.tg.link()
        if not self.tg.is_running():
            self.toast("Сначала включите Telegram прокси", "warn")
            return
        if not winutils.open_url(url):
            QApplication.clipboard().setText(url)
            self.toast("Не удалось открыть Telegram. Ссылка скопирована — отправьте её в Telegram и нажмите на неё.", "warn", 8000)
        else:
            self.toast("Telegram предложит добавить прокси — нажмите «Включить»", "ok")

    def copy_link(self) -> None:
        QApplication.clipboard().setText(self.tg.link())
        self.toast("Ссылка скопирована. Отправьте её себе в Telegram и нажмите на неё.", "ok")

    def set_autostart(self, on: bool) -> None:
        def done(res):
            ok, out = res
            real = winutils.autostart_enabled()
            self.cfg.set("app", "autostart", real)
            for k in ("home", "settings"):
                self.pages[k].on_show()
            if ok:
                self.toast("Автозапуск включён" if on else "Автозапуск выключен", "ok")
            else:
                self.toast("Не удалось изменить автозапуск: " + out.strip()[:200], "err")
        run_bg(lambda: winutils.set_autostart(on), done)

    # ------------------------------------------------------------ трей
    def _build_tray_menu(self) -> None:
        m = self.tray_menu
        m.clear()
        zs, ts, ds = self._last_z, self._last_t, self._last_d
        a = m.addAction("Открыть " + APP_NAME)
        a.triggered.connect(self.show_window)
        f = a.font()
        f.setBold(True)
        a.setFont(f)
        m.addSeparator()
        za = m.addAction("Zapret")
        za.setCheckable(True)
        za.setChecked(bool(zs.get("running")))
        za.triggered.connect(lambda on: self.set_zapret(on))
        sub = m.addMenu("Стратегия")
        style_popup(sub)
        grp = QActionGroup(sub)
        cur = self.cfg.get("zapret", "strategy")
        svc = zs.get("service") == "running"
        for s in self.zapret.strategies():
            act = sub.addAction(self.zapret.strategy_title(s))
            act.setCheckable(True)
            act.setChecked(s == cur)
            act.setEnabled(not svc)
            act.triggered.connect(lambda _=False, st=s: self.apply_strategy(st))
            grp.addAction(act)
        ta = m.addAction("Telegram прокси")
        ta.setCheckable(True)
        ta.setChecked(bool(ts.get("running")))
        ta.triggered.connect(lambda on: self.set_tg(on))
        da = m.addAction("DNS для нейросетей")
        da.setCheckable(True)
        da.setChecked(bool(ds.get("enabled")))
        da.triggered.connect(lambda on: self.set_dns(on))
        m.addSeparator()
        m.addAction("Подключить Telegram").triggered.connect(self.open_telegram)
        m.addAction("Копировать ссылку прокси").triggered.connect(self.copy_link)
        m.addSeparator()
        m.addAction("Выход").triggered.connect(self.quit_app)
        apply_language(m, self.cfg.get('app', 'language', 'ru'))

    def _tray_activated(self, reason) -> None:
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            if self.isVisible() and not self.isMinimized():
                self.hide()
            else:
                self.show_window()

    def show_window(self) -> None:
        if self.isMinimized():
            self.showNormal()
        self.show()
        self.raise_()
        self.activateWindow()
        self.pages[self._current].on_show()
        self.refresh_now()

    def hideEvent(self, e):
        self.pages[self._current].on_hide()
        super().hideEvent(e)

    def closeEvent(self, e):
        if self._quitting or not self.cfg.get("app", "close_to_tray", True):
            e.accept()
            self.quit_app()
            return
        e.ignore()
        self.hide()
        if not self._tray_hint_shown:
            self._tray_hint_shown = True
            msg = "Приложение продолжает работать в трее. Выход — правой кнопкой по значку."
            self.tray.showMessage(APP_NAME, translate_text(msg, self.cfg.get('app', 'language', 'ru')),
                                  QSystemTrayIcon.Information, 4000)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self._toast.isVisible():
            self._toast.reposition()

    def quit_app(self) -> None:
        if self._quitting:
            return
        self._quitting = True
        self.timer.stop()
        self.tray.hide()
        self.hide()
        for fn in (self.tg.stop, self.zapret.stop, self.dns.shutdown):
            try:
                fn()
            except Exception:
                log.exception("Ошибка при остановке")
        QApplication.instance().quit()

    def restart_app(self) -> None:
        if self._quitting:
            return
        try:
            from ..restart import launch_restart
            if self.cfg.get('zapret', 'mode') == 'service':
                zapret_active = self.zapret.service_state() == 'running'
            else:
                zapret_active = self.zapret.is_running_app() or bool(self.zapret._want_running)
            launch_restart(zapret_active, self.tg.is_active())
        except Exception as exc:
            log.exception('Не удалось перезапустить приложение')
            self.toast(f'Не удалось перезапустить приложение: {exc}', 'err', 9000)
            return
        self.quit_app()

    # ----------------------------------------------- проверка обновлений
    def show_release_notes(self, kind=None):
        from .release_notes import ReleaseNotesDialog
        dialog = ReleaseNotesDialog(self, kind)
        dialog.exec()
        dialog.deleteLater()

    def download_updates_now(self, manual: bool = False, kind: str = None) -> None:
        if self._updates_busy:
            if manual:
                self.toast("Проверка обновлений уже выполняется", "info")
            return
        from ..updates import install_components
        download_folder = self.cfg.download_folder
        self._updates_busy = True
        if manual:
            self.toast("Проверяю и скачиваю обновления…", "info")
        def work():
            results = install_components(kind, download_folder)
            if not manual:
                return results
            out = []
            for component, ok, version, detail, fresh in results:
                if ok and component == 'zapret':
                    selected, message = self.zapret.select_version(version)
                    if not selected:
                        out.append((component, False, version, 'Версия скачана, но не включена: ' + message, fresh))
                        continue
                elif ok and component == 'tg':
                    from ..tgproxy import TGWS_VERSION
                    try:
                        self.cfg.select_tg_version(version, TGWS_VERSION)
                    except (OSError, ValueError) as exc:
                        out.append((component, False, version, 'Версия скачана, но не включена: ' + str(exc), fresh))
                        continue
                out.append((component, ok, version, detail, fresh))
            return out
        def done(results):
            self._updates_busy = False
            names = {"zapret": "Zapret", "tg": "TG WS Proxy"}
            for component, ok, version, detail, fresh in results:
                if ok and (manual or fresh):
                    message = f"{names[component]} {version}: версия добавлена"
                    if manual and component == 'tg':
                        from ..tgproxy import TGWS_VERSION
                        if version != TGWS_VERSION:
                            message += '. Для применения нажмите «Перезапустить приложение» на вкладке Telegram.'
                        else:
                            message = f"{names[component]} {version}: актуальная версия уже работает."
                    elif manual and component == 'zapret':
                        message += ' и выбрана.'
                    self.toast(message, "ok", 9000)
                elif not ok:
                    log.warning("Не удалось скачать обновление %s: %s", component, detail)
                    if manual:
                        self.toast(f"{names[component]}: {detail}", "err", 9000)
            if manual:
                self.pages['zapret'].reload()
                self.pages['tg'].reload_versions()
                self.reload_strategies()
                self.refresh_now()
        def failed(error):
            self._updates_busy = False
            log.warning("Ошибка проверки обновлений: %s", error)
            if manual:
                self.toast(f"Ошибка обновления: {error}", "err", 9000)
        run_bg(work, done, failed)

    def check_component_updates(self, manual: bool = False) -> None:
        if self._checks_busy:
            if manual:
                self.toast('Проверка обновлений уже выполняется', 'info')
            return
        from ..updates import check_component_versions
        from ..tgproxy import TGWS_VERSION
        self._checks_busy = True
        self.release_info.setText('Обновления: проверка…')
        apply_language(self.rail, self.cfg.get('app', 'language', 'ru'))
        zversion = self.zapret.local_version()
        def done(results):
            self._checks_busy = False
            lines = []
            for component, current, latest, current_ok, error in results:
                name = 'Zapret' if component == 'zapret' else 'TG'
                if current_ok is None:
                    lines.append(f'{name}: проверка выключена' if error == 'отключена в настройках' else f'{name}: ошибка проверки')
                    log.warning('Обновления %s: %s', name, error)
                elif current_ok:
                    lines.append(f'{name} {current}: актуально')
                else:
                    lines.append(f'{name} {current}: доступна {latest}')
            message = '\n'.join(lines)
            self.release_info.setText(message)
            apply_language(self.rail, self.cfg.get('app', 'language', 'ru'))
            if self.isVisible() or manual:
                self.toast(message, 'info', 9000)
        def failed(error):
            self._checks_busy = False
            self.release_info.setText('Обновления: ошибка проверки')
            apply_language(self.rail, self.cfg.get('app', 'language', 'ru'))
            if manual:
                self.toast(f'Ошибка проверки: {error}', 'err')
        enabled = tuple(component for component, section in (('zapret', 'zapret'), ('tg', 'tg'))
                        if manual or self.cfg.get(section, 'check_updates', True))
        run_bg(lambda: check_component_versions(zversion, TGWS_VERSION, enabled), done, failed)

    def check_updates_later(self) -> None:
        QTimer.singleShot(6000, self.check_component_updates)
        self._download_timer = QTimer(self)
        self._download_timer.setInterval(6 * 60 * 60 * 1000)
        self._download_timer.timeout.connect(lambda: self.download_updates_now() if self.cfg.get("app", "auto_download_updates", True) else None)
        self._download_timer.start()
        QTimer.singleShot(12000, lambda: self.download_updates_now() if self.cfg.get("app", "auto_download_updates", True) else None)

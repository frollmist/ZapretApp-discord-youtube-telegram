"""Главная: «стопка» модулей, кольца состояния, список модулей и график трафика."""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from .base import Page, fmt_uptime, human_speed, ru_bytes
from .fancy import Combo, GradientBar, Ring, Sparkline, StackEmblem
from .widgets import Card, ElidedLabel, IconBadge, Palette, Pill, ToggleSwitch, button, label, row, run_bg, setting_row
from .language import apply_language, translate_text
from ..connectivity import SITES, check_sites
from ..paths import RESOURCE_DIR
from . import icons


class ModuleRow(QFrame):
    def __init__(self, icon: str, title: str, sub: str):
        super().__init__()
        self.setObjectName("moduleRow")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 10, 14, 10)
        lay.setSpacing(12)
        self.badge = IconBadge(icon, 40)
        lay.addWidget(self.badge)
        col = QVBoxLayout()
        col.setSpacing(1)
        self.title = ElidedLabel(title, "cardTitle")
        self.sub = ElidedLabel(sub, "hint")
        self.sub.setMinimumWidth(130)
        col.addWidget(self.title)
        col.addWidget(self.sub)
        lay.addLayout(col, 1)
        self.extra = QHBoxLayout()
        self.extra.setSpacing(8)
        lay.addLayout(self.extra)
        self.state = self  # статус показывается в подстроке (set_state), без отдельной колонки
        self._state = ""
        self._sub = sub
        self.pill = Pill("", "accent")
        lay.addWidget(self.pill)
        self.switch = ToggleSwitch(big=True)
        lay.addWidget(self.switch)

    def setText(self, state: str) -> None:  # совместимость: m.state.setText(...)
        self._state = state
        self._render()

    def set_sub(self, sub: str) -> None:
        self._sub = sub
        self._render()

    def _render(self) -> None:
        txt = f"{self._state} · {self._sub}" if self._state and self._sub else (self._state or self._sub)
        self.sub.setText(txt)


class HomePage(Page):
    title = "Главная"
    subtitle = "Обход блокировок, Telegram прокси и DNS для нейросетей"

    def __init__(self, ctx):
        super().__init__(ctx)
        self._busy = {"zapret": False, "tg": False, "dns": False}

        # Главная панель в стиле референса: два самостоятельных управления.
        dashboard = Card(padding=24, spacing=10)
        powers = QHBoxLayout()
        powers.setContentsMargins(24, 24, 24, 16)
        powers.setSpacing(30)
        self.tg_state = label("ОТКЛЮЧЕНО", "hint")
        self.z_state = label("ОТКЛЮЧЕНО", "hint")
        self.tg_uptime = label("00:00:00", "tiny")
        self.z_uptime = label("00:00:00", "tiny")
        self.tg_power = self._power_control("TELEGRAM", self.tg_state, self.tg_uptime,
                                            lambda: self._toggle("tg"), powers)
        logo_col = QVBoxLayout()
        logo_col.addStretch()
        center_logo = QLabel()
        center_logo.setObjectName("dashboardLogo")
        center_logo.setAlignment(Qt.AlignCenter)
        mark = QIcon(str(RESOURCE_DIR / "dashboard-lock.svg"))
        center_logo.setPixmap(mark.pixmap(QSize(100, 100), center_logo.devicePixelRatioF()))
        logo_col.addWidget(center_logo)
        logo_col.addStretch()
        powers.addLayout(logo_col, 1)
        self.z_power = self._power_control("ZAPRET", self.z_state, self.z_uptime,
                                           lambda: self._toggle("zapret"), powers)
        dashboard.lay.addLayout(powers)
        dashboard.lay.addLayout(row(None,
                                    button("Подключить Telegram", "ghost", "link", ctx.open_telegram),
                                    button("Подобрать стратегию", "ghost", "flask", lambda: ctx.go("zapret")),
                                    None))
        self.body.addWidget(dashboard)

        self.connectivity = Card(padding=16, spacing=8)
        self.check_button = button("Проверить связь", "", "pulse", self._check_sites)
        self.connectivity.lay.addLayout(row(label("Доступность сайтов", "sectionTitle"), None, self.check_button))
        self.site_states = {}
        sites = QHBoxLayout()
        for name in SITES:
            state = Pill("Ещё не проверялось", "off")
            sites.addWidget(label(name))
            sites.addWidget(state)
            sites.addStretch(1)
            self.site_states[name] = state
        self.connectivity.lay.addLayout(sites)
        self.proxy_client = label("", "hint")
        self.connectivity.lay.addWidget(self.proxy_client)
        self.body.addWidget(self.connectivity)

        # ================= верх: стопка + состояние
        hero = Card(padding=22, spacing=10)
        hl = QHBoxLayout()
        hl.setSpacing(18)
        self.emblem = StackEmblem()
        hl.addWidget(self.emblem, 11)
        right = QVBoxLayout()
        right.setSpacing(10)
        self.hero_title = label("Состояние защиты", "heroTitle")
        self.hero_sub = label("", "muted", wrap=True)
        right.addWidget(self.hero_title)
        right.addWidget(self.hero_sub)
        right.addSpacing(4)
        self.bar_conn = GradientBar("Соединения TG", "accent3", "accent2")
        self.bar_up = GradientBar("Отправлено", "accent2", "accent")
        self.bar_down = GradientBar("Получено", "accent", "accent2")
        for b in (self.bar_conn, self.bar_up, self.bar_down):
            right.addWidget(b)
        right.addSpacing(6)
        rings = QHBoxLayout()
        rings.setSpacing(6)
        self.r_z = Ring("Zapret", "accent")
        self.r_t = Ring("Telegram", "accent3")
        self.r_d = Ring("DNS", "accent2")
        self.r_z.clicked.connect(lambda: self._toggle("zapret"))
        self.r_t.clicked.connect(lambda: self._toggle("tg"))
        self.r_d.clicked.connect(lambda: self._toggle("dns"))
        for r in (self.r_z, self.r_t, self.r_d):
            r.setToolTip("Нажмите, чтобы включить или выключить")
            rings.addWidget(r)
        rings.addStretch(1)
        right.addLayout(rings)
        right.addStretch(1)
        self.all_btn = button("Включить всё", "primary", "power", self._toggle_all)
        right.addLayout(row(self.all_btn, button("Подключить Telegram", "ghost", "link", ctx.open_telegram), None))
        hl.addLayout(right, 10)
        hero.lay.addLayout(hl)
        self.body.addWidget(hero)
        hero.hide()

        # ================= низ: модули + график
        grid = QGridLayout()
        grid.setHorizontalSpacing(14)
        mods = Card(padding=18, spacing=10)
        mods.lay.addLayout(row(label("Модули", "sectionTitle"), None,
                               label("нажмите на кольцо или переключатель", "tiny")))
        self.m_z = ModuleRow("shield", "Zapret", "YouTube, Discord и др.")
        self.m_t = ModuleRow("send", "Telegram прокси", "WebSocket-мост для Telegram Desktop")
        self.m_d = ModuleRow("sparkle", "DNS для нейросетей", "ChatGPT, Claude, Gemini, Copilot…")
        self.combo = Combo(min_chars=11)
        self.combo.setToolTip("Стратегия zapret")
        self.combo.activated.connect(self._strategy)
        self.m_z.extra.addWidget(self.combo)
        self.m_z.pill.hide()
        self.m_z.switch.clicked.connect(lambda on: self._set("zapret", on))
        self.m_t.switch.clicked.connect(lambda on: self._set("tg", on))
        self.m_d.switch.clicked.connect(lambda on: self._set("dns", on))
        self.m_d.pill.setCursor(Qt.PointingHandCursor)
        for m in (self.m_z, self.m_t, self.m_d):
            mods.lay.addWidget(m)
        self.auto_switch = ToggleSwitch()
        self.auto_switch.clicked.connect(lambda on: ctx.window.set_autostart(on))
        mods.lay.addWidget(setting_row("Запускать вместе с Windows", "свёрнуто в трей, всё включится само",
                                       self.auto_switch))
        grid.addWidget(mods, 0, 0)

        chart = Card(padding=18, spacing=6)
        chart.lay.addLayout(row(label("Трафик Telegram", "sectionTitle"), None,
                                label("за последние 2 минуты", "tiny")))
        sp = QHBoxLayout()
        self.speed_down = label("0 Б/с", "statValue")
        self.speed_up = label("0 Б/с", "statValue")
        sp.addLayout(self._stat(self.speed_down, "▼ загрузка"))
        sp.addSpacing(18)
        sp.addLayout(self._stat(self.speed_up, "▲ отправка"))
        sp.addStretch(1)
        chart.lay.addLayout(sp)
        self.spark = Sparkline(60)
        self.spark.unit = lambda v: human_speed(v).replace(" ", " ")
        chart.lay.addWidget(self.spark, 1)
        chart.setParent(self)
        chart.hide()
        grid.setColumnStretch(0, 11)
        self.body.addLayout(grid)
        self.finish()
        self.reload_strategies()

    @staticmethod
    def _power_control(title, state, uptime, callback, layout):
        col = QVBoxLayout()
        col.setSpacing(7)
        heading = label(title, "sectionTitle")
        for item in (heading, state, uptime):
            item.setAlignment(Qt.AlignCenter)
        power = QPushButton()
        power.setObjectName("heroPower")
        power.setFixedSize(102, 102)
        power.setIcon(icons.icon("power", "#e6ebff", 36, 1.8))
        power.setIconSize(QSize(36, 36))
        power.setCursor(Qt.PointingHandCursor)
        power.setToolTip(f"Включить или выключить {title}")
        power.clicked.connect(callback)
        col.addWidget(heading)
        col.addWidget(state)
        col.addSpacing(8)
        col.addWidget(power, 0, Qt.AlignHCenter)
        col.addSpacing(8)
        col.addWidget(uptime)
        layout.addLayout(col, 2)
        return power

    @staticmethod
    def _stat(value_label, caption):
        col = QVBoxLayout()
        col.setSpacing(0)
        col.addWidget(value_label)
        col.addWidget(label(caption, "statLabel"))
        return col

    # -------------------------------------------------------- действия
    def _check_sites(self):
        self.check_button.setEnabled(False)
        for state in self.site_states.values():
            state.set("Проверяем…", "accent")
        apply_language(self.connectivity, self.ctx.cfg.get("app", "language"))

        def done(results):
            self.check_button.setEnabled(True)
            for name, state in self.site_states.items():
                text, color = {True: ("Доступен", "on"), False: ("Недоступен", "err"),
                               None: ("Нет ответа", "warn")}[results.get(name)]
                # Keep the Russian source so a later language switch works.
                state.set(text, color)
            apply_language(self.connectivity, self.ctx.cfg.get("app", "language"))

        run_bg(check_sites, done, lambda error: done({}))

    def _set(self, mod: str, on: bool) -> None:
        if self._busy.get(mod):
            return
        if mod == "zapret":
            self.ctx.set_zapret(on)
        elif mod == "tg":
            self.ctx.set_tg(on)
        else:
            self.ctx.set_dns(on)

    def _toggle(self, mod: str) -> None:
        cur = {"zapret": self.m_z, "tg": self.m_t, "dns": self.m_d}[mod].switch.isChecked()
        self._set(mod, not cur)

    def _toggle_all(self) -> None:
        z, t, d = self.m_z.switch.isChecked(), self.m_t.switch.isChecked(), self.m_d.switch.isChecked()
        self.ctx.set_all(not (z and t and d))

    def set_busy(self, mod: str, on: bool) -> None:
        self._busy[mod] = on
        m = {"zapret": self.m_z, "tg": self.m_t, "dns": self.m_d}[mod]
        m.switch.setEnabled(not on)
        if on:
            ring = {"zapret": self.r_z, "tg": self.r_t, "dns": self.r_d}[mod]
            ring.set(ring._target, "…")

    def reload_strategies(self) -> None:
        z = self.ctx.zapret
        cur = self.ctx.cfg.get("zapret", "strategy")
        self.combo.blockSignals(True)
        self.combo.clear()
        for s in z.strategies():
            self.combo.addItem(z.strategy_title(s), s)
        self.combo.setCurrentIndex(max(self.combo.findData(cur), 0))
        self.combo.blockSignals(False)

    def _strategy(self, _i) -> None:
        self.ctx.apply_strategy(self.combo.currentData())

    def on_show(self) -> None:
        self.auto_switch.setChecked(bool(self.ctx.cfg.get("app", "autostart")))

    def feed_speed(self, ts: dict) -> None:
        if "speed_down" in ts:
            self.spark.push(ts["speed_down"] + ts.get("speed_up", 0))
            self.speed_down.setText(human_speed(ts["speed_down"]))
            self.speed_up.setText(human_speed(ts.get("speed_up", 0)))

    # ---------------------------------------------------------- статус
    def on_status(self, zs: dict, ts: dict, ds: dict = None) -> None:
        ds = ds or {}
        lang = self.ctx.cfg.get('app', 'language', 'ru')
        tr = lambda text: translate_text(text, lang)
        for bar, title in ((self.bar_conn, 'Соединения TG'), (self.bar_up, 'Отправлено'), (self.bar_down, 'Получено')):
            bar.title = tr(title)
        p = Palette.p
        z_on, t_on, d_on = bool(zs.get("running")), bool(ts.get("running")), bool(ds.get("enabled"))
        self.z_state.setText("ВКЛЮЧЕНО" if z_on else "ОТКЛЮЧЕНО")
        self.tg_state.setText("ВКЛЮЧЕНО" if t_on else "ОТКЛЮЧЕНО")
        self.z_uptime.setText(fmt_uptime(zs.get("uptime")) or "00:00:00")
        self.tg_uptime.setText(fmt_uptime(ts.get("uptime")) or "00:00:00")
        self.z_power.setEnabled(not self._busy["zapret"])
        self.tg_power.setEnabled(not self._busy["tg"])
        self.feed_speed(ts)

        for mod, m, on in (("zapret", self.m_z, z_on), ("tg", self.m_t, t_on), ("dns", self.m_d, d_on)):
            if not self._busy[mod]:
                m.switch.setChecked(on)
            key = {"zapret": "accent", "tg": "accent3", "dns": "accent2"}[mod]
            m.badge.set_color(p[key] if on else p["faint"], p["accent_soft"] if on else p["surface2"])

        # ---- zapret
        if zs.get("service") == "running":
            z_state, z_sub = "служба Windows", f"стратегия {zs.get('service_strategy') or '?'}"
        elif zs.get("app_running"):
            up = fmt_uptime(zs.get("uptime"))
            z_state, z_sub = (f"работает {up}" if up else "работает"), ""
        elif zs.get("restarting"):
            z_state, z_sub = "перезапуск…", "winws.exe восстанавливается"
        elif zs.get("foreign_winws"):
            z_state, z_sub = "запущен извне", "winws.exe запущен не приложением"
        elif zs.get("error"):
            z_state, z_sub = "ошибка", str(zs.get("error")).split("\n")[0]
        else:
            z_state, z_sub = "выключен", "YouTube, Discord и др."
        self.m_z.state.setText(z_state)
        self.m_z.set_sub(z_sub)
        self.m_z.sub.setToolTip(str(zs.get("error") or ""))
        self.combo.setEnabled(zs.get("service") != "running")

        # ---- telegram
        st = ts.get("stats") or {}
        client = ("Клиент подключён" if st.get("active") else "Ожидание клиента") if t_on else "Прокси выключен"
        self.proxy_client.setText("Telegram · " + client)
        if t_on:
            up = fmt_uptime(ts.get("uptime"))
            t_state = f"работает {up}" if up else "работает"
            t_sub = f"{st.get('active', 0)} соед. · ▲ {ru_bytes(st.get('up'))} ▼ {ru_bytes(st.get('down'))}"
        elif ts.get("active"):
            t_state, t_sub = "перезапуск…", str(ts.get("error") or "")[:70]
        elif ts.get("error"):
            t_state, t_sub = "ошибка", str(ts.get("error")).split("\n")[0][:70]
        else:
            t_state, t_sub = "выключен", "мост для Telegram Desktop"
        self.m_t.state.setText(t_state)
        self.m_t.set_sub(t_sub)
        self.m_t.pill.setText(f":{ts.get('port')}")

        # ---- dns
        self.m_d.pill.setText(ds.get("provider_name", "DNS"))
        if d_on:
            mode = "через приложение" if ds.get("mode") == "local" else "системный"
            self.m_d.state.setText("включён")
            self.m_d.set_sub(f"{mode} · нейросети доступны")
        else:
            self.m_d.state.setText("выключен")
            self.m_d.set_sub("ChatGPT, Claude, Gemini, Copilot…")

        # ---- кольца, полосы, стопка
        for ring, on, mod in ((self.r_z, z_on, "zapret"), (self.r_t, t_on, "tg"), (self.r_d, d_on, "dns")):
            if not self._busy[mod]:
                ring.set(1.0 if on else 0.0, tr("ВКЛ" if on else "ВЫКЛ"))
        active = int(st.get("active", 0) or 0)
        upb, downb = int(st.get("up_raw", 0) or 0), int(st.get("down_raw", 0) or 0)
        tot = max(1, upb + downb)
        self.bar_conn.set(min(1.0, active / 24) if t_on else 0, str(active) if t_on else "—")
        self.bar_up.set(upb / tot if upb else 0, tr(ru_bytes(st.get("up"))))
        self.bar_down.set(downb / tot if downb else 0, tr(ru_bytes(st.get("down"))))
        self.emblem.set_layer(0, t_on, f"127.0.0.1:{ts.get('port')}" if t_on else tr("выключен"))
        self.emblem.set_layer(1, z_on, self.ctx.zapret.strategy_title(zs.get("strategy") or "") if z_on else tr("выключен"))
        self.emblem.set_layer(2, d_on, ds.get("provider_name", "") if d_on else tr("выключен"))

        n = sum((z_on, t_on, d_on))
        if n == 3:
            self.hero_sub.setText("Все модули работают: сайты, Telegram и нейросети доступны.")
        elif n:
            off = [name for name, on in (("zapret", z_on), ("Telegram прокси", t_on), ("DNS", d_on)) if not on]
            self.hero_sub.setText("Выключено: " + ", ".join(off) + ".")
        else:
            self.hero_sub.setText("Всё выключено. Нажмите «Включить всё» или на кольцо модуля.")
        self.all_btn.setText("Выключить всё" if n == 3 else "Включить всё")

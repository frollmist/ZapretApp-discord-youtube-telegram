"""Home dashboard for the three connection modules."""
from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QWidget, QVBoxLayout

from .base import Page, fmt_uptime, ru_bytes
from .fancy import Combo
from .language import apply_language
from .widgets import Card, ElidedLabel, IconBadge, Palette, Pill, ToggleSwitch, button, hline, label, row, run_bg
from ..connectivity import SITES, check_sites


class ModuleCard(Card):
    def __init__(self, name, icon, description, toggle, open_page):
        super().__init__(padding=16, spacing=8)
        self.setObjectName("moduleCard")
        self.badge = IconBadge(icon, 34)
        self.switch = ToggleSwitch()
        self.switch.setAccessibleName(name)
        self.switch.clicked.connect(toggle)
        self.lay.addLayout(row(self.badge, None, self.switch))
        self.lay.addSpacing(4)
        self.lay.addWidget(label(name, "moduleTitle"))
        self.sub = ElidedLabel(description, "hint")
        self.lay.addWidget(self.sub)
        self.lay.addSpacing(4)
        self.lay.addWidget(hline())
        self.status = ElidedLabel("выключен", "moduleStatus")
        self.details = button("›", "moduleLink", on_click=open_page, tip=name)
        self.details.setAccessibleName(name)
        self.details.setFixedSize(32, 28)
        self.lay.addLayout(row(self.status, self.details, stretch_at=0))
        self.update_state(False, "выключен", description)

    def update_state(self, active, status, description):
        if self.switch.isEnabled():
            self.switch.setChecked(active)
        if self.property("active") != active:
            self.setProperty("active", active)
            self.style().unpolish(self)
            self.style().polish(self)
            self.status.style().unpolish(self.status)
            self.status.style().polish(self.status)
        self.badge.set_color(Palette.p["accent"], Palette.p["input"])
        self.status.setText(status)
        self.sub.setText(description)


class HomePage(Page):
    title = "Центр связи"
    subtitle = ""

    def __init__(self, ctx):
        super().__init__(ctx)
        self.m_t = ModuleCard("Telegram", "send", "Локальный прокси", ctx.set_tg, lambda: ctx.go("tg"))
        self.m_z = ModuleCard("Zapret", "shield", "Discord и YouTube", ctx.set_zapret, lambda: ctx.go("zapret"))
        self.m_d = ModuleCard("DNS", "sparkle", "DNS для нейросетей", ctx.set_dns, lambda: ctx.go("dns"))
        self.modules = {"tg": self.m_t, "zapret": self.m_z, "dns": self.m_d}
        cards = QHBoxLayout()
        cards.setSpacing(12)
        for module in self.modules.values():
            cards.addWidget(module, 1)
        self.body.addLayout(cards)

        self.connectivity = Card(padding=18, spacing=8)
        self.check_button = button("Проверить связь", "", "pulse", self._check_sites)
        self.connectivity.lay.addLayout(row(label("Доступность сайтов", "sectionTitle"), None, self.check_button))
        self.site_states = {}
        for name in SITES:
            self.connectivity.lay.addWidget(hline())
            state = Pill("Ещё не проверялось", "off")
            self.connectivity.lay.addLayout(row(label(name), None, state))
            self.site_states[name] = state
        self.body.addWidget(self.connectivity)
        self.proxy_client = label("Telegram · Прокси выключен", "hint")
        self.body.addLayout(row(self.proxy_client, None, button("Настроить Telegram", "ghost", "gear", lambda: ctx.go("tg"))))

        # Keep the home shortcuts accessible without duplicating the module controls.
        self.quick = QWidget()
        actions = QVBoxLayout(self.quick)
        actions.setContentsMargins(0, 4, 0, 0)
        self.combo = Combo(min_chars=11)
        self.combo.setToolTip("Стратегия zapret")
        self.combo.activated.connect(self._strategy)
        self.auto_switch = ToggleSwitch()
        self.auto_switch.clicked.connect(ctx.set_autostart)
        actions.addLayout(row(label("Стратегия"), self.combo, None,
                              button("Подключить Telegram", "ghost", "link", ctx.open_telegram)))
        actions.addLayout(row(label("Запускать вместе с Windows"), None, self.auto_switch))
        self.quick.hide()
        shortcuts = button("Быстрые действия", "link")
        shortcuts.setCheckable(True)
        shortcuts.toggled.connect(self.quick.setVisible)
        self.body.addLayout(row(shortcuts, None))
        self.body.addWidget(self.quick)
        self.finish()
        self.reload_strategies()

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

    def set_busy(self, mod: str, on: bool) -> None:
        self.modules[mod].switch.setEnabled(not on)

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

    def on_status(self, zs: dict, ts: dict, ds: dict = None) -> None:
        ds = ds or {}
        z_on, t_on, d_on = bool(zs.get("running")), bool(ts.get("running")), bool(ds.get("enabled"))
        status = "включён" if z_on else "выключен"
        strategy = zs.get("service_strategy") or zs.get("strategy")
        description = self.ctx.zapret.strategy_title(strategy) if strategy and z_on else "Discord и YouTube"
        if zs.get("service") == "running":
            status = "служба Windows"
        elif zs.get("restarting"):
            status = "перезапуск…"
        elif zs.get("foreign_winws"):
            status = "запущен извне"
        elif zs.get("error") and not z_on:
            status, description = "ошибка", str(zs["error"]).splitlines()[0]
        elif z_on and zs.get("uptime"):
            status = "работает " + fmt_uptime(zs["uptime"])
        self.m_z.update_state(z_on, status, description)
        self.combo.setEnabled(zs.get("service") != "running")
        stats = ts.get("stats") or {}
        client = ("Клиент подключён" if stats.get("active") else "Ожидание клиента") if t_on else "Прокси выключен"
        self.proxy_client.setText("Telegram · " + client)
        status = "выключен"
        description = "Локальный прокси"
        if t_on:
            status = "включён"
            if ts.get("port"):
                description = f"127.0.0.1:{ts['port']}"
        elif ts.get("active"):
            status = "перезапуск…"
        elif ts.get("error"):
            status, description = "ошибка", str(ts["error"]).splitlines()[0]
        self.m_t.update_state(t_on, status, description)
        self.m_t.status.setToolTip(f"▲ {ru_bytes(stats.get('up'))} ▼ {ru_bytes(stats.get('down'))}" if t_on else "")
        self.m_d.update_state(d_on, "включён" if d_on else "выключен", ds.get("provider_name") or "DNS для нейросетей")

"""Shared colour palettes and Qt styles for the desktop interface."""
from __future__ import annotations

PALETTES = {
    "dark": {
        "window": (23, 19, 41),
        "rail": "#1d182f",
        "surface": "#29233d",
        "surface_solid": "#29233d",
        "surface2": "#272137",
        "surface3": "#352d46",
        "border": "#4b405f",
        "border_strong": "#6b5d83",
        "text": "#f6f1ff",
        "muted": "#c3b8d1",
        "faint": "#a89bb8",
        "accent": "#c5a9ff",
        "accent2": "#a78cde",
        "accent3": "#94c8dc",
        "accent_hover": "#dbcaff",
        "accent_soft": "#3d304f",
        "accent_ink": "#211330",
        "glow_left": "#534174",
        "glow_right": "#395365",
        "on": "#9aecd2",
        "on_soft": "#2a413d",
        "warn": "#ffcc82",
        "warn_soft": "#453626",
        "err": "#ff9cb0",
        "err_soft": "#492e40",
        "input": "#211c32",
        "knob": "#fffaff",
        "track_off": "#61566f",
        "disc_off_top": "#3e344e",
        "disc_off_side": "#292232",
        "menu": "#29233d",
    },
    "light": {
        "window": (241, 238, 248),
        "rail": "#f8f5fc",
        "surface": "#fffaff",
        "surface_solid": "#fffaff",
        "surface2": "#f2edf8",
        "surface3": "#ebe3f3",
        "border": "#d3c7df",
        "border_strong": "#ab99bc",
        "text": "#2c213c",
        "muted": "#62566e",
        "faint": "#73667c",
        "accent": "#684095",
        "accent2": "#764e9f",
        "accent3": "#396c83",
        "accent_hover": "#583584",
        "accent_soft": "#ede2fa",
        "accent_ink": "#ffffff",
        "glow_left": "#dbc9f4",
        "glow_right": "#c4e3e7",
        "on": "#116b58",
        "on_soft": "#dcefe7",
        "warn": "#885c13",
        "warn_soft": "#f7ead3",
        "err": "#a13957",
        "err_soft": "#f9e0e6",
        "input": "#f2edf8",
        "knob": "#ffffff",
        "track_off": "#94869f",
        "disc_off_top": "#e2d8ed",
        "disc_off_side": "#cdc1da",
        "menu": "#fffaff",
    },
}

FONT = '"Segoe UI Variable Text", "Segoe UI", "Inter", "Noto Sans", sans-serif'
DISPLAY = '"Segoe UI Variable Display", "Segoe UI", "Inter", "Noto Sans", sans-serif'


def qss(p: dict, arrow: str = "", check: str = "") -> str:
    return f"""
* {{
    font-family: {FONT};
    font-size: 13px;
    color: {p['text']};
    outline: none;
}}
QMainWindow, #root, #content, QStackedWidget {{ background: transparent; }}
QLabel#autoProgress {{ color: {p['muted']}; }}
QLabel#autoDone {{ color: {p['on']}; font-weight: 600; }}
QLabel#autoError {{ color: {p['err']}; }}
QToolTip {{
    background: {p['menu']}; color: {p['text']};
    border: 1px solid {p['border_strong']}; border-radius: 8px; padding: 6px 9px;
}}

/* --- оболочка --- */
#rail {{ background: {p['rail']}; border-right: 1px solid {p['border']}; }}
QToolButton#railBtn {{
    background: transparent; border: none; border-radius: 10px; padding: 4px 10px;
    color: {p['muted']}; font-size: 12px; font-weight: 600; text-align: left;
}}
QToolButton#railBtn:hover {{ background: {p['surface2']}; color: {p['muted']}; }}
QToolButton#railBtn:checked {{ background: {p['accent_soft']}; color: {p['text']}; }}
#titleBar {{ background: transparent; }}
#titleText {{ font-family: {DISPLAY}; font-size: 28px; font-weight: 600; }}
#brandName {{ font-size: 18px; font-weight: 650; }}
#titleSub {{ color: {p['muted']}; font-size: 12px; }}
QPushButton#winBtn {{ background: transparent; border: none; border-radius: 8px; padding: 0; }}
QPushButton#winBtn:hover {{ background: {p['surface3']}; }}
QPushButton#winClose {{ background: transparent; border: none; border-radius: 8px; padding: 0; }}
QPushButton#winClose:hover {{ background: #e8455f; }}

/* --- карточки и тексты --- */
#card, #moduleCard {{ background: {p['surface']}; border: 1px solid {p['border']}; border-radius: 15px; }}
#moduleCard[active="true"] {{ background: {p['accent_soft']}; border-color: {p['accent']}; }}
#moduleTitle {{ font-size: 18px; font-weight: 650; }}
#moduleStatus {{ color: {p['muted']}; font-size: 12px; }}
#moduleCard[active="true"] #moduleStatus {{ color: {p['on']}; }}
QPushButton#moduleLink {{ color: {p['accent']}; background: transparent; border: none; padding: 0; font-size: 20px; }}
QPushButton#moduleLink:hover, QPushButton#moduleLink:focus {{ background: {p['surface3']}; }}
#cardTitle {{ font-size: 15px; font-weight: 650; }}
#sectionTitle {{ font-size: 14px; font-weight: 650; }}
#heroTitle {{ font-family: {DISPLAY}; font-size: 24px; font-weight: 700; }}
#display {{ font-family: {DISPLAY}; font-size: 30px; font-weight: 700; }}
#muted {{ color: {p['muted']}; }}
#faint {{ color: {p['faint']}; font-size: 12px; }}
#hint {{ color: {p['muted']}; font-size: 12px; }}
#tiny {{ color: {p['faint']}; font-size: 11px; }}
#statValue {{ font-size: 17px; font-weight: 650; }}
#statLabel {{ color: {p['muted']}; font-size: 11px; }}
#statBox {{ background: {p['surface2']}; border: 1px solid {p['border']}; border-radius: 12px; }}
#pill {{ border-radius: 10px; padding: 3px 10px; font-size: 12px; font-weight: 600; }}
#pill[state="on"] {{ background: {p['on_soft']}; color: {p['on']}; }}
#pill[state="off"] {{ background: {p['surface3']}; color: {p['muted']}; }}
#pill[state="warn"] {{ background: {p['warn_soft']}; color: {p['warn']}; }}
#pill[state="err"] {{ background: {p['err_soft']}; color: {p['err']}; }}
#pill[state="accent"] {{ background: transparent; color: {p['accent']}; border: 1px solid {p['accent']}; }}
#moduleRow {{ background: {p['surface2']}; border: 1px solid {p['border']}; border-radius: 14px; }}
#moduleRow:hover {{ border: 1px solid {p['border_strong']}; }}
#diagRow {{ background: {p['surface2']}; border: 1px solid {p['border']}; border-radius: 12px; }}
#divider {{ background: {p['border']}; max-height: 1px; min-height: 1px; }}
#tile {{ background: {p['surface2']}; border: 1px solid {p['border']}; border-radius: 14px; }}
#tile:hover {{ border: 1px solid {p['border_strong']}; }}
#tile[selected="true"] {{ background: {p['accent_soft']}; border: 1px solid {p['accent']}; }}

/* --- кнопки --- */
QPushButton {{
    background: {p['surface3']}; border: 1px solid {p['border']}; border-radius: 11px;
    padding: 8px 15px; font-weight: 600;
}}
QPushButton:hover {{ background: {p['border_strong']}; }}
QPushButton:pressed {{ background: {p['surface2']}; }}
QPushButton:disabled {{ color: {p['faint']}; }}
QPushButton#primary {{
    border: none; color: {p['accent_ink']}; padding: 9px 18px; background: {p['accent']};
}}
QPushButton#primary:hover {{
    background: {p['accent_hover']};
}}
QPushButton#primary:disabled {{ background: {p['surface3']}; color: {p['faint']}; }}
QPushButton#danger {{ color: {p['err']}; }}
QPushButton#ghost {{ background: transparent; border: 1px solid {p['border_strong']}; }}
QPushButton#ghost:hover {{ background: {p['surface2']}; }}
QPushButton#heroPower {{
    border-radius: 51px; border: 1px solid {p['border_strong']};
    background: {p['surface_solid']}; color: {p['text']}; font-size: 38px; padding: 0;
}}
QPushButton#heroPower:hover {{ border: 1px solid {p['accent']}; background: {p['surface3']}; }}
QPushButton#link {{ background: transparent; border: none; color: {p['accent']}; padding: 2px 4px; font-weight: 600; }}
QPushButton#link:hover {{ color: {p['accent_hover']}; }}
QPushButton#seg {{
    border-radius: 0; border: 1px solid {p['border']}; border-right: none; padding: 7px 14px;
    background: {p['surface2']}; color: {p['muted']};
}}
QPushButton#seg:hover {{ color: {p['text']}; }}
QPushButton#seg[first="true"] {{ border-top-left-radius: 10px; border-bottom-left-radius: 10px; }}
QPushButton#seg[last="true"] {{ border-top-right-radius: 10px; border-bottom-right-radius: 10px; border-right: 1px solid {p['border']}; }}
QPushButton#seg:checked {{
    color: {p['accent_ink']}; border-color: transparent;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {p['accent']}, stop:1 {p['accent2']});
}}

/* --- поля ввода --- */
QLineEdit, QPlainTextEdit, QSpinBox, QComboBox {{
    background: {p['input']}; border: 1px solid {p['border']}; border-radius: 10px;
    padding: 7px 10px; selection-background-color: {p['accent']}; selection-color: {p['accent_ink']};
    min-height: 20px;
}}
QPlainTextEdit {{ padding: 6px; }}
QSpinBox {{ min-width: 90px; }}
QLineEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QComboBox:focus {{ border: 1px solid {p['accent']}; }}
QLineEdit:read-only {{ color: {p['muted']}; }}
QPlainTextEdit#mono, QLineEdit#mono {{ font-family: "Cascadia Mono", "Consolas", "DejaVu Sans Mono", monospace; font-size: 12px; }}
QComboBox {{ padding-right: 30px; }}
QComboBox::drop-down {{ border: none; width: 28px; subcontrol-origin: padding; subcontrol-position: center right; }}
QComboBox::down-arrow {{ image: url({arrow}); width: 12px; height: 12px; }}
QComboBox QAbstractItemView {{
    background: {p['menu']}; border: 1px solid {p['border_strong']}; border-radius: 10px; padding: 5px;
    selection-background-color: {p['accent_soft']}; selection-color: {p['text']}; outline: none;
}}
QComboBox QAbstractItemView::item {{ min-height: 28px; padding: 0 8px; border-radius: 6px; }}
QSpinBox::up-button, QSpinBox::down-button {{ width: 0; border: none; }}
QCheckBox {{ spacing: 9px; }}
QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 6px; border: 1px solid {p['border_strong']}; background: {p['input']}; }}
QCheckBox::indicator:checked {{ image: url({check}); border: none;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {p['accent']}, stop:1 {p['accent2']}); }}

/* --- прокрутка, вкладки, меню --- */
QScrollArea {{ background: transparent; border: none; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 4px 2px; }}
QScrollBar::handle:vertical {{ background: {p['surface3']}; border-radius: 3px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {p['faint']}; }}
QScrollBar::add-line, QScrollBar::sub-line, QScrollBar::add-page, QScrollBar::sub-page {{ height: 0; width: 0; background: none; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px 4px; }}
QScrollBar::handle:horizontal {{ background: {p['surface3']}; border-radius: 3px; min-width: 30px; }}
QTabWidget::pane {{ border: none; }}
QTabBar::tab {{
    background: transparent; color: {p['muted']}; padding: 8px 14px; border: none;
    border-bottom: 2px solid transparent; font-weight: 600;
}}
QTabBar::tab:selected {{ color: {p['text']}; border-bottom: 2px solid {p['accent']}; }}
QTabBar::tab:hover {{ color: {p['text']}; }}
QMenu {{ background: {p['menu']}; border: 1px solid {p['border_strong']}; border-radius: 12px; padding: 6px; }}
QMenu::item {{ padding: 8px 28px 8px 14px; border-radius: 7px; }}
QMenu::item:selected {{ background: {p['accent_soft']}; }}
QMenu::item:disabled {{ color: {p['faint']}; }}
QMenu::separator {{ height: 1px; background: {p['border']}; margin: 5px 8px; }}
QMenu::indicator {{ width: 14px; height: 14px; margin-left: 6px; }}
QMenu::right-arrow {{ width: 10px; height: 10px; }}

#toast {{ background: {p['menu']}; border: 1px solid {p['border_strong']}; border-radius: 14px; }}
#toast QLabel {{ font-size: 13px; background: transparent; }}
#dialog {{ background: {p['menu']}; border: 1px solid {p['border_strong']}; border-radius: 18px; }}
"""

from PySide6.QtGui import QFont

WINDOW_W, WINDOW_H = 440, 640

BG = "#F3F3F3"
CARD = "#FFFFFF"
BORDER = "#E5E5E5"
DIVIDER = "#EFEFEF"
TEXT = "#1A1A1A"
TEXT_SUB = "#616161"
TEXT_MUTED = "#8A8A8A"
ACCENT = "#0078D4"
ACCENT_HOVER = "#106EBE"
ACCENT_SOFT = "#EEF3FB"
RED = "#D13438"
RED_SOFT = "#FDECEC"
TITLEBAR = "#202020"
DONE_BG, DONE_FG = "#E6F4EA", "#1A7F37"
ING_BG, ING_FG = "#FFF4CE", "#8A6D00"


def app_font() -> QFont:
    f = QFont()
    f.setFamilies(["Segoe UI", "Malgun Gothic"])
    f.setPixelSize(13)
    return f


QSS = f"""
* {{ color: {TEXT}; }}
#Root {{ background: {BG}; }}
QWidget#Page {{ background: {BG}; }}

#TitleBar {{ background: {TITLEBAR}; }}
#TitleBar QLabel#TitleText {{ color: #FFFFFF; font-size: 12px; font-weight: 600; }}
#TitleBar QPushButton {{
    background: transparent; border: none; color: #C9C9C9; font-size: 11px;
    min-width: 32px; max-width: 32px; min-height: 28px; max-height: 28px;
}}
#TitleBar QPushButton:hover {{ background: #3A3A3A; color: #FFFFFF; }}
#TitleBar QPushButton#CloseBtn {{ color: #F3A3A3; }}
#TitleBar QPushButton#CloseBtn:hover {{ background: #C42B1C; color: #FFFFFF; }}
#TitleBar QPushButton#BackBtn {{
    min-width: 0; max-width: 16777215; color: #FFFFFF; font-size: 12px; font-weight: 600;
    text-align: left; padding: 0;
}}
#TitleBar QPushButton#BackBtn:hover {{ background: transparent; color: #CFE4F7; }}
#TitleBar QPushButton#RecIndicator {{
    min-width: 0; max-width: 16777215; min-height: 20px; max-height: 20px;
    background: {RED}; color: #FFFFFF; font-size: 11px; font-weight: 600;
    border-radius: 10px; padding: 0 10px; margin: 0 8px;
}}
#TitleBar QPushButton#RecIndicator:hover {{ background: #B92B2E; }}

QFrame#Card {{ background: {CARD}; border: 1px solid {BORDER}; border-radius: 8px; }}
QFrame#CardHeader {{ border: none; border-bottom: 1px solid {DIVIDER}; background: transparent; }}
QLabel#CardTitle {{ font-size: 12px; font-weight: 600; }}
QFrame#Row {{ border: none; border-bottom: 1px solid {DIVIDER}; background: transparent; }}
QFrame#Row[last="true"] {{ border-bottom: none; }}
QFrame#Row[clickable="true"]:hover {{ background: #F7F9FC; }}
QLabel#RowTitle {{ font-weight: 600; }}
QLabel#RowSub {{ color: {TEXT_MUTED}; font-size: 11px; }}
QLabel#Empty {{ color: {TEXT_MUTED}; font-size: 12px; padding: 16px; }}

QLabel#Link, QPushButton#Link {{
    color: {ACCENT}; font-size: 12px; font-weight: 600; background: transparent; border: none;
}}
QPushButton#Link:hover {{ color: {ACCENT_HOVER}; text-decoration: underline; }}

QLabel#BtnLabel {{ font-size: 13px; font-weight: 600; }}
QLabel#Meta {{ color: {TEXT_SUB}; font-size: 12px; }}

QComboBox {{
    background: {CARD}; border: 1px solid {BORDER}; border-radius: 8px;
    padding: 4px 10px; font-size: 12px; min-height: 18px;
}}
QComboBox:disabled {{ color: {TEXT_MUTED}; }}
QComboBox::drop-down {{ border: none; width: 18px; }}
QComboBox QAbstractItemView {{
    background: {CARD}; border: 1px solid {BORDER}; selection-background-color: {ACCENT_SOFT};
    selection-color: {TEXT}; outline: none;
}}

QLineEdit {{
    background: #FFFFFF; border: 1px solid #D9D9D9; border-radius: 6px;
    padding: 5px 10px; font-size: 12px;
}}
QLineEdit:focus {{ border: 1px solid {ACCENT}; }}

QPushButton#Primary {{
    background: {ACCENT}; color: #FFFFFF; border: none; border-radius: 6px;
    padding: 6px 12px; font-size: 12px; font-weight: 600;
}}
QPushButton#Primary:hover {{ background: {ACCENT_HOVER}; }}
QPushButton#Primary:disabled {{ background: #9CC3E6; }}
QPushButton#Danger {{
    background: {RED_SOFT}; color: {RED}; border: none; border-radius: 6px;
    padding: 8px 6px; font-size: 12px; font-weight: 600;
}}
QPushButton#Danger:hover {{ background: #F9D6D7; }}
QPushButton#Action {{ padding: 8px 6px; }}

QFrame#ToolStrip {{ background: #FFFFFF; border: none; border-bottom: 1px solid {BORDER}; }}
QFrame#ActionBar {{ background: #FAFAFA; border: none; border-top: 1px solid {BORDER}; }}

QPushButton#Ctrl {{
    background: {ACCENT_SOFT}; color: {ACCENT}; border: none; border-radius: 14px;
    min-width: 28px; max-width: 28px; min-height: 28px; max-height: 28px; font-size: 11px;
}}
QPushButton#Ctrl:hover {{ background: #DCE8F7; }}
QPushButton#Play {{
    background: {ACCENT}; color: #FFFFFF; border: none; border-radius: 17px;
    min-width: 34px; max-width: 34px; min-height: 34px; max-height: 34px; font-size: 12px;
}}
QPushButton#Play:hover {{ background: {ACCENT_HOVER}; }}
QPushButton#Play:disabled, QPushButton#Ctrl:disabled {{ background: #D6D6D6; color: #FFFFFF; }}
QLabel#Clock {{ color: {TEXT_SUB}; font-size: 11px; }}

QSlider::groove:horizontal {{ height: 5px; background: #EAEAEA; border-radius: 2px; }}
QSlider::sub-page:horizontal {{ background: {ACCENT}; border-radius: 2px; }}
QSlider::handle:horizontal {{
    background: {ACCENT}; width: 11px; height: 11px; margin: -3px 0; border-radius: 5px;
}}

QLabel#Pager {{ color: {TEXT_SUB}; font-size: 11px; }}
QPushButton#PagerBtn {{ color: {TEXT_SUB}; font-size: 11px; background: transparent; border: none; padding: 2px 4px; }}
QPushButton#PagerBtn:hover {{ color: {ACCENT}; }}
QPushButton#PagerBtn:disabled {{ color: #C4C4C4; }}

QTextBrowser#Transcript {{ background: #FFFFFF; border: none; padding: 4px 8px; }}

QScrollArea {{ background: transparent; border: none; }}
QScrollBar:vertical {{ background: transparent; width: 8px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: #C8C8C8; border-radius: 3px; min-height: 24px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}

QMenu {{ background: #FFFFFF; border: 1px solid {BORDER}; padding: 4px; }}
QMenu::item {{ padding: 6px 18px; border-radius: 4px; font-size: 12px; }}
QMenu::item:selected {{ background: {ACCENT_SOFT}; }}
QMenu::separator {{ height: 1px; background: {DIVIDER}; margin: 4px 6px; }}

QDialog {{ background: {BG}; }}
QMessageBox {{ background: {BG}; }}
"""

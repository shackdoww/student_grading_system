"""Shared white desktop theme with the dashboard reference layout."""

from pathlib import Path

from PySide6.QtGui import QColor, QPalette

BG = '#F6F7F5'
SURFACE = '#FFFFFF'
SURFACE_2 = '#F1F3EF'
SURFACE_3 = '#EDEFEA'
TEXT = '#202824'
MUTED = '#68756C'
ACCENT = '#17775D'
ACCENT_HOVER = '#105D48'
ACCENT_SOFT = '#E5F2E9'
ON_ACCENT = '#FFFFFF'
BORDER = '#E0E6DF'
DANGER = '#B93845'
WARNING = '#946000'
CHART_COLORS = (ACCENT, '#4B8D71', '#75A58F', '#A3BFB0')
CHEVRON_PATH = (Path(__file__).parent / 'assets/icons/chevron-down.svg').as_posix()


STYLE = f'''
QWidget {{ color: {TEXT}; font-family: "Segoe UI"; font-size: 13px; }}
QWidget#window, QWidget#workspacePage, QStackedWidget, QScrollArea {{ background: {BG}; }}
QWidget#window {{ border: 1px solid {BORDER}; border-radius: 16px; }}
QLabel {{ background: transparent; }}
QFrame#sidebar {{ background: {SURFACE_2}; border: 1px solid {BORDER}; border-radius: 18px; }}
QScrollArea#sidebarScroll {{ background: transparent; }}
QFrame#content {{ background: {BG}; border: 0; }}
QFrame#topbar {{ background: {SURFACE}; border-bottom: 1px solid {BORDER}; min-height: 62px; max-height: 62px; }}
QLabel#topbarContext {{ color: {MUTED}; font-size: 10px; font-weight: 700; letter-spacing: 1px; }}
QLabel#topbarDate {{ color: {MUTED}; font-size: 12px; }}
QLabel#brandMark {{ background: {ACCENT}; color: {ON_ACCENT}; border-radius: 13px; min-width: 40px; max-width: 40px; min-height: 40px; max-height: 40px; font-size: 12px; font-weight: 800; qproperty-alignment: AlignCenter; }}
QLabel#brandTitle {{ color: {TEXT}; font-size: 18px; font-weight: 650; padding: 2px 0; }}
QLabel#pageTitle {{ color: {TEXT}; font-size: 26px; font-weight: 650; }}
QLabel#subtitle {{ color: {MUTED}; font-size: 12px; }}
QLabel#eyebrow {{ color: {MUTED}; font-size: 10px; font-weight: 600; letter-spacing: 0.8px; }}
QLabel#cardTitle, QLabel#sectionTitle {{ color: {TEXT}; font-size: 15px; font-weight: 650; }}
QLabel#statValue {{ color: {TEXT}; font-size: 30px; font-weight: 600; }}
QLabel#reportSummary {{ color: {ACCENT}; font-size: 16px; font-weight: 600; padding-top: 8px; }}
QLabel#heroGrade {{ color: {ACCENT}; font-size: 42px; font-weight: 600; padding-top: 4px; }}
QFrame#sidebarIdentity {{ background: transparent; border: 0; }}
QLabel#identityEyebrow {{ color: {MUTED}; font-size: 10px; font-weight: 600; letter-spacing: 1px; }}
QLabel#identityTitle {{ color: {TEXT}; font-size: 13px; font-weight: 600; }}
QLabel#identityMeta {{ color: {MUTED}; font-size: 11px; }}
QLabel#accountAvatar {{ background: {ACCENT_SOFT}; color: {ACCENT}; border: 1px solid #BED8C7; border-radius: 16px; font-size: 11px; font-weight: 700; }}
QFrame#card, QFrame#sectionCard {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 16px; }}
QFrame#statCard {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 16px; min-height: 96px; }}
QToolButton {{ background: transparent; color: {MUTED}; border: 1px solid transparent; border-radius: 13px; text-align: left; padding: 10px; font-size: 13px; font-weight: 500; }}
QToolButton:hover {{ background: {SURFACE_3}; color: {TEXT}; }}
QToolButton:checked {{ background: {ACCENT}; color: {ON_ACCENT}; }}
QToolButton:focus {{ border: 1px solid {ACCENT}; }}
QToolButton:checked:focus {{ border: 2px solid {TEXT}; padding: 9px; }}
QToolButton#sidebarToggle {{ background: {SURFACE_3}; }}
QPushButton {{ background: {SURFACE_3}; color: {TEXT}; border: 1px solid {BORDER}; border-radius: 16px; padding: 8px 14px; min-height: 18px; font-weight: 600; }}
QPushButton:hover {{ background: {ACCENT_SOFT}; border-color: #B6CDBF; }}
QPushButton:pressed {{ background: {ACCENT_SOFT}; }}
QPushButton:focus {{ border: 1px solid {ACCENT}; }}
QPushButton:disabled, QToolButton:disabled {{ color: #737D75; background: {SURFACE_2}; border-color: {BORDER}; }}
QPushButton[primary="true"] {{ background: {ACCENT}; color: {ON_ACCENT}; border-color: {ACCENT}; }}
QPushButton[primary="true"]:hover {{ background: {ACCENT_HOVER}; border-color: {ACCENT_HOVER}; }}
QPushButton[primary="true"]:focus {{ border: 2px solid {TEXT}; padding: 7px 13px; }}
QPushButton[primary="true"]:disabled {{ background: {ACCENT_SOFT}; color: {MUTED}; border-color: {BORDER}; }}
QPushButton[compact="true"] {{ padding: 6px 11px; border-radius: 14px; }}
QComboBox::drop-down {{ border: 0; width: 24px; background: transparent; }}
QComboBox::down-arrow {{ image: url("{CHEVRON_PATH}"); width: 14px; height: 14px; }}
QLineEdit, QComboBox, QAbstractSpinBox, QTextEdit, QPlainTextEdit {{ background: {SURFACE_2}; color: {TEXT}; border: 1px solid {BORDER}; border-radius: 11px; padding: 8px 12px; min-height: 18px; selection-background-color: {ACCENT}; selection-color: {ON_ACCENT}; }}
QLineEdit:focus, QComboBox:focus, QAbstractSpinBox:focus, QTextEdit:focus, QPlainTextEdit:focus {{ border: 1px solid {ACCENT}; background: {SURFACE}; }}
QAbstractSpinBox {{ padding-right: 28px; }}
QTimeEdit {{ min-width: 76px; }}
QAbstractSpinBox::up-button {{ subcontrol-origin: border; subcontrol-position: top right; width: 22px; border: 0; border-top-right-radius: 9px; background: {SURFACE_3}; }}
QAbstractSpinBox::down-button {{ subcontrol-origin: border; subcontrol-position: bottom right; width: 22px; border: 0; border-bottom-right-radius: 9px; background: {SURFACE_3}; }}
QAbstractSpinBox::up-button:hover, QAbstractSpinBox::down-button:hover {{ background: #DCEADB; }}
QAbstractSpinBox::up-arrow {{ image: url("{(Path(__file__).parent / 'assets/icons/chevron-up.svg').as_posix()}"); width: 12px; height: 12px; }}
QAbstractSpinBox::down-arrow {{ image: url("{CHEVRON_PATH}"); width: 12px; height: 12px; }}
QAbstractSpinBox::up-arrow:disabled, QAbstractSpinBox::down-arrow:disabled {{ width: 0; height: 0; }}
QLineEdit:disabled, QComboBox:disabled, QAbstractSpinBox:disabled {{ color: #737D75; background: {BG}; }}
QComboBox QAbstractItemView {{ background: {SURFACE}; color: {TEXT}; selection-background-color: {ACCENT_SOFT}; selection-color: {TEXT}; border: 1px solid {BORDER}; outline: 0; padding: 4px; }}
QComboBox QAbstractItemView::item {{ background: {SURFACE}; color: {TEXT}; min-height: 28px; padding: 5px 10px; }}
QComboBox QAbstractItemView::item:selected, QComboBox QAbstractItemView::item:hover {{ background: {ACCENT_SOFT}; color: {TEXT}; }}
QTableWidget {{ background: {SURFACE}; color: {TEXT}; border: 0; border-radius: 12px; alternate-background-color: #FAFBF9; selection-background-color: {ACCENT_SOFT}; selection-color: {TEXT}; gridline-color: transparent; outline: 0; }}
QHeaderView::section {{ background: {SURFACE_2}; color: {MUTED}; border: 0; border-bottom: 1px solid {BORDER}; padding: 11px 10px; font-size: 11px; font-weight: 600; }}
QTableWidget::item {{ padding: 10px; border-bottom: 1px solid {SURFACE_2}; }}
QTableWidget::item:hover {{ background: {SURFACE_3}; }}
QTableCornerButton::section {{ background: {SURFACE_2}; border: 0; }}
QTabWidget::pane {{ border: 1px solid {BORDER}; border-radius: 12px; background: {SURFACE}; top: -1px; }}
QTabBar::tab {{ background: transparent; color: {MUTED}; border: 0; border-bottom: 2px solid transparent; padding: 10px 14px; margin-right: 5px; font-weight: 600; }}
QTabBar::tab:selected {{ color: {ACCENT}; border-bottom-color: {ACCENT}; }}
QTabBar::tab:hover {{ color: {TEXT}; }}
QDialog, QMessageBox {{ background: {SURFACE}; }}
QWidget#titleBar {{ background: {SURFACE}; border-bottom: 1px solid {BORDER}; }}
QLabel#windowTitle {{ color: {TEXT}; font-size: 12px; font-weight: 600; }}
QLabel#loadStatus {{ color: {MUTED}; font-size: 11px; }}
QWidget#titleBar QToolButton {{ padding: 0; border-radius: 8px; }}
QToolButton#windowClose:hover {{ background: #FCE5E8; }}
QScrollBar:vertical {{ background: transparent; width: 7px; border: 0; }}
QScrollBar::handle:vertical {{ background: #C5CDC4; border-radius: 3px; min-height: 30px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ background: transparent; height: 7px; border: 0; }}
QScrollBar::handle:horizontal {{ background: #C5CDC4; border-radius: 3px; min-width: 30px; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QDialogButtonBox QPushButton {{ min-width: 88px; }}
QCheckBox {{ spacing: 8px; background: transparent; }}
QCheckBox::indicator {{ width: 16px; height: 16px; border: 1px solid #9EAEA1; border-radius: 5px; background: {SURFACE_2}; }}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; image: url("{(Path(__file__).parent / 'assets/icons/check.svg').as_posix()}"); }}
QCheckBox::indicator:focus {{ border-color: {ACCENT}; }}
QCheckBox::indicator:disabled {{ background: {SURFACE_3}; border-color: {BORDER}; }}
QToolTip {{ background: {SURFACE_3}; color: {TEXT}; border: 1px solid #BAC7BD; padding: 7px; border-radius: 6px; }}
QMenu {{ background: {SURFACE}; color: {TEXT}; border: 1px solid {BORDER}; padding: 6px; }}
QMenu::item:selected {{ background: {ACCENT_SOFT}; }}
QGroupBox {{ border: 1px solid {BORDER}; border-radius: 12px; margin-top: 12px; padding-top: 14px; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 5px; color: {MUTED}; }}
'''


def apply_theme(app):
    """Set native fallback colors as well as stylesheet colors (menus, dialogs)."""
    app.setStyle('Fusion')
    palette = QPalette()
    colors = {
        QPalette.Window: BG, QPalette.WindowText: TEXT,
        QPalette.Base: SURFACE_2, QPalette.AlternateBase: SURFACE,
        QPalette.Text: TEXT, QPalette.Button: SURFACE_3,
        QPalette.ButtonText: TEXT, QPalette.Highlight: ACCENT_SOFT,
        QPalette.HighlightedText: TEXT, QPalette.ToolTipBase: SURFACE_3,
        QPalette.ToolTipText: TEXT, QPalette.PlaceholderText: MUTED,
        QPalette.Light: BORDER, QPalette.Mid: BORDER, QPalette.Dark: BG,
        QPalette.Link: ACCENT, QPalette.BrightText: DANGER,
    }
    for role, value in colors.items():
        palette.setColor(role, QColor(value))
    for role in (QPalette.Text, QPalette.WindowText, QPalette.ButtonText):
        palette.setColor(QPalette.Disabled, role, QColor('#737D75'))
    app.setPalette(palette)
    app.setStyleSheet(STYLE)

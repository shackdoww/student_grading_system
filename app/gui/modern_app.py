"""Compatibility entry point for the PySide6 application.

The GUI was migrated from Tkinter/CustomTkinter to PySide6.  Keeping this
module lets existing launch commands continue to work.
"""

from app.gui.pyside_app import StudentHub, run


StudentGradingGUI = StudentHub


if __name__ == "__main__":
    raise SystemExit(run())

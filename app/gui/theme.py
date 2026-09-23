import tkinter as tk
from tkinter import ttk

BG = "#111820"
PANEL = "#1B252E"
PANEL_ALT = "#222E38"
ACCENT = "#F99E1A"
ACCENT_HOVER = "#FFB84D"
TEXT = "#F2F2F2"
MUTED = "#AEB8C2"
DARK = "#0B1015"
BORDER = "#35424D"
SELECT = "#3A4650"


def apply_theme(root):
    root.configure(bg=BG)

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(".", font=("Segoe UI", 9), foreground=TEXT)
    style.configure("TFrame", background=BG)
    style.configure("Panel.TFrame", background=PANEL)
    style.configure("TLabel", background=BG, foreground=TEXT)
    style.configure("Muted.TLabel", background=BG, foreground=MUTED)
    style.configure("Title.TLabel", background=BG, foreground=TEXT,
                    font=("Segoe UI", 17, "bold"))
    style.configure("Subtitle.TLabel", background=BG, foreground=ACCENT,
                    font=("Segoe UI", 9, "bold"))
    style.configure("Section.TLabelframe", background=PANEL,
                    foreground=ACCENT, bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=DARK, borderwidth=1)
    style.configure("Section.TLabelframe.Label", background=PANEL,
                    foreground=ACCENT, font=("Segoe UI", 9, "bold"))

    style.configure("TButton", background=PANEL_ALT, foreground=TEXT,
                    bordercolor=BORDER, lightcolor=BORDER, darkcolor=DARK,
                    padding=(10, 5), font=("Segoe UI", 9, "bold"))
    style.map("TButton",
              background=[("active", ACCENT), ("pressed", ACCENT)],
              foreground=[("active", DARK), ("pressed", DARK)])

    style.configure("Accent.TButton", background=ACCENT, foreground=DARK,
                    bordercolor=ACCENT, padding=(11, 6),
                    font=("Segoe UI", 9, "bold"))
    style.map("Accent.TButton",
              background=[("active", ACCENT_HOVER), ("pressed", ACCENT_HOVER)])

    style.configure("TEntry", fieldbackground=PANEL_ALT, foreground=TEXT,
                    insertcolor=TEXT, bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=DARK, padding=5)
    style.configure("TCombobox", fieldbackground=PANEL_ALT,
                    foreground=TEXT, background=PANEL_ALT,
                    arrowcolor=ACCENT, bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=DARK, padding=4)
    style.map("TCombobox",
              fieldbackground=[("readonly", PANEL_ALT)],
              foreground=[("readonly", TEXT)])

    style.configure("Treeview", background=PANEL, fieldbackground=PANEL,
                    foreground=TEXT, rowheight=25,
                    bordercolor=BORDER, lightcolor=BORDER,
                    darkcolor=BORDER, font=("Segoe UI", 9))
    style.map("Treeview",
              background=[("selected", ACCENT)],
              foreground=[("selected", DARK)])
    style.configure("Treeview.Heading", background=DARK,
                    foreground=ACCENT, bordercolor=BORDER,
                    font=("Segoe UI", 9, "bold"), padding=(6, 5))
    style.map("Treeview.Heading",
              background=[("active", PANEL_ALT)])

    style.configure("TScrollbar", background=PANEL_ALT,
                    troughcolor=DARK, bordercolor=DARK,
                    arrowcolor=ACCENT)

    style.configure("TSeparator", background=BORDER)

    return style

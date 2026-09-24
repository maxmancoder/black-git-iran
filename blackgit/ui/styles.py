"""Black Git Iran — modern dark theme (GitHub-dark inspired)."""

BG = "#0b0e14"
BG2 = "#12161f"
BG3 = "#1a2030"
BG4 = "#232a3b"
FG = "#e8eef7"
FG_DIM = "#8b95a8"
FG_FAINT = "#5c6578"
ACCENT = "#ff7a45"
ACCENT_DIM = "#e86a38"
ACCENT_HOVER = "#ff9466"
ACCENT_ACTIVE = "#d45a2a"
BLUE = "#4dabf7"
OK = "#3dd68c"
ERR = "#ff6b6b"
WARN = "#ffc857"
BORDER = "#2a3142"
BORDER_LIGHT = "#343d52"
SHADOW = "#000000"

CARD = BG2
CARD_HOVER = BG3

RADIUS_HINT = 12  # visual spacing guide (tkinter has no real radius)

FONT = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_SUB = ("Segoe UI", 11)
FONT_SMALL = ("Segoe UI", 9)
FONT_TINY = ("Segoe UI", 8)
FONT_MONO = ("Consolas", 10)
FONT_BTN = ("Segoe UI", 11, "bold")
FONT_BTN_SMALL = ("Segoe UI", 10)


def apply_ttk(root):
    """Map ttk colors so native widgets (scrollbars etc.) match the theme."""
    from tkinter import ttk

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure(
        "TFrame", background=BG
    )
    style.configure(
        "Card.TFrame", background=CARD
    )
    style.configure(
        "TLabel", background=BG, foreground=FG
    )
    style.configure(
        "TCheckbutton", background=BG, foreground=FG
    )
    style.map(
        "TCheckbutton",
        background=[("active", BG)],
        foreground=[("active", FG)],
    )
    style.configure(
        "Horizontal.TProgressbar",
        background=ACCENT,
        troughcolor=BG3,
        bordercolor=BG,
        lightcolor=ACCENT,
        darkcolor=ACCENT,
    )
    return style

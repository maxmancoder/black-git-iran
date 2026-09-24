"""Black Git Iran — dark dashboard theme (based on project design)."""

# backgrounds
BG = "#0a0d13"          # window deep background
SIDEBAR = "#0d1117"     # left sidebar
BG2 = "#0d1117"         # legacy alias (dialogs)
CARD = "#10141d"        # card surface
CARD_HOVER = "#151a26"  # card hover / elevated
BG3 = "#151a26"
BG4 = "#1c2233"         # inputs
PANEL = "#131826"       # inner panel (transports box)

# text
FG = "#e6edf3"
FG_DIM = "#8b95a8"
FG_FAINT = "#5c6578"
FG_LOG = "#c9d1d9"

# accents
ACCENT = "#4d8aff"        # blue (toggles / primary)
ACCENT_HOVER = "#6a9dff"
ACCENT_ACTIVE = "#3a72e0"
ACCENT_PURPLE = "#8b5cf6"  # toggle gradient end
OK = "#3dd68c"            # green status
BLUE = "#4dabf7"
WARN = "#ffc857"
ERR = "#ff6b6b"
DOT_GRAY = "#4a5568"

# pills / badges
PILL_GREEN_BG = "#0f2a1e"
PILL_GREEN_FG = "#3dd68c"
PILL_GREEN_BORDER = "#1e4a35"
PILL_AMBER_BG = "#2a2210"
PILL_AMBER_FG = "#ffc857"
PILL_AMBER_BORDER = "#4a3c18"
PILL_GRAY_BG = "#151a26"
PILL_GRAY_FG = "#5c6578"
PILL_GRAY_BORDER = "#252c3d"

# borders
BORDER = "#1f2533"
BORDER_LIGHT = "#2a3142"

# toggles
TOGGLE_ON = "#5b6ef5"
TOGGLE_OFF = "#2a3142"
TOGGLE_KNOB = "#ffffff"

# logs
LOG_BG = "#0b0f17"
LOG_FG = "#c9d1d9"
LOG_INFO = "#3dd68c"
LOG_ERR = "#ff6b6b"
LOG_TIME = "#6e7681"
LOG_HIGHLIGHT = "#4d8aff"

# fonts
FONT = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_SUB = ("Segoe UI", 11)
FONT_SMALL = ("Segoe UI", 9)
FONT_TINY = ("Segoe UI", 8)
FONT_MONO = ("Consolas", 10)
FONT_BTN = ("Segoe UI", 11, "bold")
FONT_BTN_SMALL = ("Segoe UI", 10)
FONT_LOG = ("Consolas", 9)
FONT_SECTION = ("Segoe UI", 9, "bold")   # uppercase card titles
FONT_BIG_STATUS = ("Segoe UI", 18, "bold")
FONT_SIDE_TITLE = ("Segoe UI", 13, "bold")


def apply_ttk(root):
    """Map ttk colors so native widgets match the theme."""
    from tkinter import ttk

    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=CARD)
    style.configure("TLabel", background=BG, foreground=FG)
    style.configure("TCheckbutton", background=BG, foreground=FG)
    style.map("TCheckbutton", background=[("active", BG)], foreground=[("active", FG)])
    style.configure(
        "Horizontal.TProgressbar",
        background=ACCENT,
        troughcolor=BG3,
        bordercolor=BG,
        lightcolor=ACCENT,
        darkcolor=ACCENT,
    )
    return style

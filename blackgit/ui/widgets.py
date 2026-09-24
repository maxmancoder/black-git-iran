"""Reusable dashboard widgets for Black Git Iran."""

import tkinter as tk

from . import styles as S


# ── helpers ──────────────────────────────────────────────────────────
def round_rect(canvas: tk.Canvas, x1, y1, x2, y2, r, **kw):
    """Rounded rectangle via smooth polygon."""
    r = max(0, min(r, (x2 - x1) // 2, (y2 - y1) // 2))
    points = [
        x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
        x2, y2 - r, x2 - r, y2, x1 + r, y2, x1, y2,
        x1, y2 - r, x1, y1 + r, x1, y1, x1 + r, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kw)


# ── buttons ──────────────────────────────────────────────────────────
class HoverButton(tk.Label):
    """Flat label-button with hover/active states."""

    def __init__(
        self,
        parent,
        text="",
        command=None,
        *,
        kind="default",  # default | primary | ghost | danger
        font=None,
        pady=10,
        padx=16,
        width=0,
        bg=None,
        fg=None,
        **kw,
    ):
        self._kind = kind
        self._command = command
        self._enabled = True

        palette = {
            "primary": (S.ACCENT, "#08111f", S.ACCENT_HOVER, S.ACCENT_ACTIVE, S.ACCENT),
            "default": (S.BG3, S.FG, S.BG4, S.BORDER_LIGHT, S.BORDER),
            "ghost": (S.CARD, S.FG_DIM, S.BG3, S.BG4, S.BORDER),
            "danger": (S.BG3, S.ERR, "#3d1f1f", "#4a2222", S.BORDER),
        }
        (
            self._bg_normal,
            self._fg_normal,
            self._bg_hover,
            self._bg_active,
            self._border,
        ) = palette.get(kind, palette["default"])

        super().__init__(
            parent,
            text=text,
            bg=bg or self._bg_normal,
            fg=fg or self._fg_normal,
            font=font or (S.FONT_BTN if kind == "primary" else S.FONT_BTN_SMALL),
            pady=pady,
            padx=padx,
            cursor="hand2",
            justify="center",
            anchor="center",
            highlightthickness=1,
            highlightbackground=self._border,
            highlightcolor=self._border,
            **kw,
        )
        if width:
            self.configure(width=width)
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<ButtonRelease-1>", self._release)

    def _enter(self, _e=None):
        if self._enabled:
            self.configure(bg=self._bg_hover)

    def _leave(self, _e=None):
        if self._enabled:
            self.configure(bg=self._bg_normal)

    def _press(self, _e=None):
        if self._enabled:
            self.configure(bg=self._bg_active)

    def _release(self, _e=None):
        if not self._enabled:
            return
        self.configure(bg=self._bg_hover)
        if self._command:
            self._command()

    def set_enabled(self, on: bool) -> None:
        self._enabled = bool(on)
        if on:
            self.configure(bg=self._bg_normal, fg=self._fg_normal, cursor="hand2")
        else:
            self.configure(bg=S.BG2, fg=S.FG_FAINT, cursor="arrow")


# ── toggle switch (pill) ─────────────────────────────────────────────
class ToggleSwitch(tk.Canvas):
    """ON/OFF pill switch like the design mockup."""

    def __init__(self, parent, command=None, value=True, width=54, height=28, bg=None):
        super().__init__(
            parent,
            width=width,
            height=height,
            highlightthickness=0,
            bd=0,
            bg=bg or parent.cget("bg"),
            cursor="hand2",
        )
        self._cw = width   # canvas width (do NOT use _w — that's the Tk widget path)
        self._ch = height
        self._on = bool(value)
        self._command = command
        self._enabled = True
        self._draw()
        self.bind("<Button-1>", self._click)

    def _click(self, _e=None):
        if not self._enabled:
            return
        self._on = not self._on
        self._draw()
        if self._command:
            self._command(self._on)

    def get(self) -> bool:
        return self._on

    def set(self, value: bool, fire: bool = False) -> None:
        self._on = bool(value)
        self._draw()
        if fire and self._command:
            self._command(self._on)

    def set_enabled(self, on: bool) -> None:
        self._enabled = bool(on)

    def _draw(self):
        self.delete("all")
        pad = 2
        x1, y1 = pad, pad
        x2, y2 = self._cw - pad, self._ch - pad
        r = (y2 - y1) // 2
        if self._on:
            # blue -> purple gradient approximation (two halves)
            round_rect(self, x1, y1, x2, y2, r, fill=S.TOGGLE_ON, outline="")
            self.create_rectangle(
                (x1 + x2) / 2, y1 + 1, x2 - 1, y2 - 1, fill=S.ACCENT_PURPLE, outline=""
            )
            # re-round right side
            round_rect(
                self, (x1 + x2) / 2, y1, x2, y2, r, fill=S.ACCENT_PURPLE, outline=""
            )
            # re-round left side
            round_rect(self, x1, y1, (x1 + x2) / 2, y2, r, fill=S.TOGGLE_ON, outline="")
        else:
            round_rect(self, x1, y1, x2, y2, r, fill=S.TOGGLE_OFF, outline="")
        kr = r - 4
        cy = (y1 + y2) / 2
        kx = (x2 - kr - 3) if self._on else (x1 + kr + 3)
        self.create_oval(kx - kr, cy - kr, kx + kr, cy + kr, fill=S.TOGGLE_KNOB, outline="")


# ── status dot ───────────────────────────────────────────────────────
class StatusDot(tk.Canvas):
    def __init__(self, parent, color=S.DOT_GRAY, size=9, bg=None):
        super().__init__(
            parent,
            width=size,
            height=size,
            highlightthickness=0,
            bd=0,
            bg=bg or parent.cget("bg"),
        )
        self._color = color
        self._size = size
        self._draw()

    def set(self, color: str):
        self._color = color
        self._draw()

    def _draw(self):
        self.delete("all")
        s = self._size
        self.create_oval(1, 1, s - 1, s - 1, fill=self._color, outline="")


# ── sidebar navigation item ──────────────────────────────────────────
class SidebarItem(tk.Frame):
    def __init__(
        self,
        parent,
        icon: str,
        text: str,
        command=None,
        dot: bool = True,
        dot_color: str = S.DOT_GRAY,
    ):
        super().__init__(parent, bg=S.SIDEBAR, padx=16, pady=11, cursor="hand2")
        self._command = command
        self._enabled = True
        self._normal_bg = S.SIDEBAR

        left = tk.Frame(self, bg=S.SIDEBAR)
        left.pack(side="left", fill="x", expand=True)
        tk.Label(
            left, text=icon, font=("Segoe UI", 13), fg=S.FG_DIM, bg=S.SIDEBAR,
            width=2, anchor="w",
        ).pack(side="right")
        self._lbl = tk.Label(
            left, text=text, font=S.FONT, fg=S.FG, bg=S.SIDEBAR, anchor="e"
        )
        self._lbl.pack(side="right", padx=(0, 4))

        self._dot = None
        if dot:
            dwrap = tk.Frame(self, bg=S.SIDEBAR, width=14)
            dwrap.pack(side="left")
            dwrap.pack_propagate(False)
            self._dot = StatusDot(dwrap, color=dot_color, size=9, bg=S.SIDEBAR)
            self._dot.place(relx=0.5, rely=0.5, anchor="center")

        for w in (self, left, self._lbl):
            w.bind("<Button-1>", self._on_click)
            w.bind("<Enter>", self._enter)
            w.bind("<Leave>", self._leave)
        if self._dot:
            self._dot.bind("<Button-1>", self._on_click)

    def _enter(self, _e=None):
        if self._enabled:
            self.configure(bg=S.CARD)
            self._lbl.configure(bg=S.CARD, fg=S.FG)
            # reparent children bg not needed for paint-on-hover of frame only

    def _leave(self, _e=None):
        self.configure(bg=self._normal_bg)
        self._lbl.configure(bg=self._normal_bg, fg=self._fg_current())

    def _fg_current(self):
        return S.FG_FAINT if not self._enabled else S.FG

    def _on_click(self, _e=None):
        if self._enabled and self._command:
            self._command()

    def set_dot(self, color: str):
        if self._dot:
            self._dot.set(color)

    def set_enabled(self, on: bool):
        self._enabled = bool(on)
        self._lbl.configure(fg=S.FG if on else S.FG_FAINT)
        self.configure(cursor="hand2" if on else "arrow")


# ── card with uppercase section title ────────────────────────────────
class Card(tk.Frame):
    def __init__(self, parent, title: str = "", **kw):
        kw.setdefault("bg", S.CARD)
        kw.setdefault("highlightthickness", 1)
        kw.setdefault("highlightbackground", S.BORDER)
        kw.setdefault("highlightcolor", S.BORDER)
        super().__init__(parent, **kw)
        self._inner = tk.Frame(self, bg=S.CARD, padx=16, pady=14)
        self._inner.pack(fill="both", expand=True)
        if title:
            tk.Label(
                self._inner,
                text=title.upper(),
                font=S.FONT_SECTION,
                fg=S.FG_DIM,
                bg=S.CARD,
                anchor="w",
            ).pack(fill="x", pady=(0, 10))
        self.body = tk.Frame(self._inner, bg=S.CARD)
        self.body.pack(fill="both", expand=True)

    def set_highlight(self, color: str):
        self.configure(highlightbackground=color)


# ── status pill (provider row) ───────────────────────────────────────
class StatusPill(tk.Frame):
    """Colored pill like 'Shecan (Active)' in the design."""

    STYLES = {
        "active": (S.PILL_GREEN_BG, S.PILL_GREEN_FG, S.PILL_GREEN_BORDER, S.OK),
        "backup": (S.PILL_AMBER_BG, S.PILL_AMBER_FG, S.PILL_AMBER_BORDER, S.WARN),
        "disabled": (S.PILL_GRAY_BG, S.PILL_GRAY_FG, S.PILL_GRAY_BORDER, S.DOT_GRAY),
        "error": ("#2a1215", S.ERR, "#4a1e22", S.ERR),
    }

    def __init__(self, parent, text: str, state: str = "active", **kw):
        bg, fg, border, dot = self.STYLES.get(state, self.STYLES["disabled"])
        super().__init__(parent, bg=bg, padx=10, pady=6,
                         highlightthickness=1, highlightbackground=border, **kw)
        self._fg = fg
        self._dot_color = dot
        self._lbl = tk.Label(self, text=text, font=S.FONT_SMALL, fg=fg, bg=bg, anchor="e")
        self._lbl.pack(side="right")
        dwrap = tk.Frame(self, bg=bg, width=12)
        dwrap.pack(side="left")
        dwrap.pack_propagate(False)
        self._dot = StatusDot(dwrap, color=dot, size=8, bg=bg)
        self._dot.place(relx=0.5, rely=0.5, anchor="center")

    def set_state(self, state: str, text: str | None = None):
        bg, fg, border, dot = self.STYLES.get(state, self.STYLES["disabled"])
        self.configure(bg=bg, highlightbackground=border)
        if text is not None:
            self._lbl.configure(text=text)
        self._lbl.configure(bg=bg, fg=fg)
        # rebuild dot
        self._dot.set(dot)


# ── live log panel ───────────────────────────────────────────────────
class LogPanel(tk.Frame):
    def __init__(self, parent, max_lines: int = 500, **kw):
        super().__init__(parent, bg=S.LOG_BG, **kw)
        self.max_lines = max_lines
        wrap = tk.Frame(self, bg=S.LOG_BG)
        wrap.pack(fill="both", expand=True)
        self.text = tk.Text(
            wrap,
            bg=S.LOG_BG,
            fg=S.LOG_FG,
            font=S.FONT_LOG,
            relief="flat",
            padx=10,
            pady=8,
            state="disabled",
            wrap="word",
            insertbackground=S.LOG_FG,
            selectbackground=S.LOG_HIGHLIGHT,
            highlightthickness=0,
            spacing1=2,
            spacing3=2,
        )
        scroll = tk.Scrollbar(wrap, command=self.text.yview, width=10)
        self.text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="left", fill="y")
        self.text.pack(side="right", fill="both", expand=True)

        self.text.tag_configure("info", foreground=S.LOG_INFO)
        self.text.tag_configure("err", foreground=S.LOG_ERR)
        self.text.tag_configure("warn", foreground=S.WARN)
        self.text.tag_configure("time", foreground=S.LOG_TIME)
        self.text.tag_configure("ok", foreground=S.OK)
        self.text.tag_configure("dim", foreground=S.FG_FAINT)

    def log(self, message: str, level: str = "info", timestamp: str = "") -> None:
        from datetime import datetime

        ts = timestamp or datetime.now().strftime("%H:%M:%S")
        tag = level if level in ("info", "err", "warn", "ok", "dim") else "info"
        label = {"info": "[INFO]", "err": "[ERR ]", "warn": "[WARN]",
                 "ok": "[ OK ]", "dim": "[....]"}.get(tag, "[INFO]")
        self.text.configure(state="normal")
        self.text.insert("end", f"{label} ", tag)
        self.text.insert("end", f"{ts} - ", "time")
        self.text.insert("end", f"{message}\n", tag)
        # trim
        lines = int(self.text.index("end-1c").split(".")[0])
        if lines > self.max_lines:
            self.text.delete("1.0", f"{lines - self.max_lines}.0")
        self.text.see("end")
        self.text.configure(state="disabled")

    def clear(self):
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")


# ── misc form helpers ────────────────────────────────────────────────
def card(parent, **kw) -> tk.Frame:
    kw.setdefault("bg", S.CARD)
    kw.setdefault("highlightthickness", 1)
    kw.setdefault("highlightbackground", S.BORDER)
    kw.setdefault("highlightcolor", S.ACCENT)
    return tk.Frame(parent, **kw)


def entry(parent, textvariable=None, mono=True, justify="right", **kw) -> tk.Entry:
    return tk.Entry(
        parent,
        textvariable=textvariable,
        font=S.FONT_MONO if mono else S.FONT,
        bg=S.BG4,
        fg=S.FG,
        insertbackground=S.FG,
        relief="flat",
        highlightthickness=1,
        highlightcolor=S.ACCENT,
        highlightbackground=S.BORDER,
        justify=justify,
        **kw,
    )


def status_pill(parent, textvariable=None) -> tk.Label:
    return tk.Label(
        parent,
        textvariable=textvariable,
        font=S.FONT_SMALL,
        fg=S.OK,
        bg=S.CARD,
        anchor="e",
        justify="right",
        wraplength=460,
        padx=10,
        pady=6,
        highlightthickness=1,
        highlightbackground=S.BORDER,
    )


def field_row(parent, label: str, value: str, key: str, entries: dict) -> tk.Frame:
    row = tk.Frame(parent, bg=S.BG)
    row.pack(fill="x", pady=6)
    tk.Label(
        row, text=label, font=S.FONT, fg=S.FG_DIM, bg=S.BG, anchor="e", width=20
    ).pack(side="right")
    e = entry(row)
    e.insert(0, value)
    e.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 4))
    entries[key] = e
    return row

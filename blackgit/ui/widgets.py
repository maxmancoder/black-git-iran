"""Reusable modern-looking tkinter widgets for Black Git Iran."""

import tkinter as tk

from . import styles as S


class HoverButton(tk.Label):
    """Flat label-button with hover/active states (modern look)."""

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
            "primary": (S.ACCENT, "#1a0f08", S.ACCENT_HOVER, S.ACCENT_ACTIVE, S.BORDER),
            "default": (S.BG3, S.FG, S.BG4, S.BORDER_LIGHT, S.BORDER),
            "ghost": (S.BG, S.FG_DIM, S.BG2, S.BG3, S.BORDER),
            "danger": (S.BG3, S.ERR, "#3d1f1f", "#4a2222", S.BORDER),
        }
        (
            self._bg_normal,
            self._fg_normal,
            self._bg_hover,
            self._bg_active,
            self._border,
        ) = palette.get(kind, palette["default"])

        if kind == "primary":
            self._fg_normal = "#1a0f08"

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


def card(parent, **kw) -> tk.Frame:
    kw.setdefault("bg", S.CARD)
    kw.setdefault("highlightthickness", 1)
    kw.setdefault("highlightbackground", S.BORDER)
    kw.setdefault("highlightcolor", S.ACCENT)
    return tk.Frame(parent, **kw)


def section_title(parent, text: str) -> tk.Label:
    return tk.Label(
        parent,
        text=text,
        font=S.FONT_BOLD,
        fg=S.FG,
        bg=parent.cget("bg"),
        anchor="e",
    )


def entry(parent, textvariable=None, mono=True, justify="right", **kw) -> tk.Entry:
    e = tk.Entry(
        parent,
        textvariable=textvariable,
        font=S.FONT_MONO if mono else S.FONT,
        bg=S.BG3,
        fg=S.FG,
        insertbackground=S.FG,
        relief="flat",
        highlightthickness=1,
        highlightcolor=S.ACCENT,
        highlightbackground=S.BORDER,
        justify=justify,
        **kw,
    )
    return e


def status_pill(parent, textvariable=None) -> tk.Label:
    return tk.Label(
        parent,
        textvariable=textvariable,
        font=S.FONT_SMALL,
        fg=S.OK,
        bg=S.BG2,
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
        row,
        text=label,
        font=S.FONT,
        fg=S.FG_DIM,
        bg=S.BG,
        anchor="e",
        width=20,
    ).pack(side="right")
    e = entry(row)
    e.insert(0, value)
    e.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 4))
    entries[key] = e
    return row

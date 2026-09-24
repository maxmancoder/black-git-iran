import tkinter as tk
from tkinter import filedialog, messagebox

from ..config import Settings
from . import styles as S
from .widgets import HoverButton, entry, field_row


class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, settings: Settings, on_save=None):
        super().__init__(parent)
        self.title("تنظیمات — Black Git Iran")
        self.configure(bg=S.BG)
        self.resizable(False, False)
        self.settings = settings
        self.on_save = on_save
        self.transient(parent)
        self.grab_set()
        self._entries: dict[str, tk.Entry] = {}

        body = tk.Frame(self, bg=S.BG, padx=22, pady=18)
        body.pack(fill="both", expand=True)

        hdr = tk.Frame(body, bg=S.BG)
        hdr.pack(fill="x", pady=(0, 6))
        tk.Label(
            hdr, text="تنظیمات", font=S.FONT_TITLE, fg=S.FG, bg=S.BG, anchor="e"
        ).pack(side="right")
        tk.Label(
            hdr, text="⚙", font=("Segoe UI", 20), fg=S.ACCENT, bg=S.BG
        ).pack(side="left")

        tk.Frame(body, bg=S.BORDER, height=1).pack(fill="x", pady=(8, 12))

        # fields
        field_row(body, "آدرس گروه/کانال:", settings.rubika_group_url, "rubika_url", self._entries)

        row_p = field_row(body, "مسیر پروژه:", settings.project_path, "project", self._entries)
        HoverButton(
            row_p, text="…", command=self._browse_project, kind="default",
            padx=10, pady=4, font=S.FONT_BOLD,
        ).pack(side="right", padx=(6, 0))

        row_t = field_row(body, "پوشه موقت:", settings.temp_path, "temp", self._entries)
        HoverButton(
            row_t, text="…", command=self._browse_temp, kind="default",
            padx=10, pady=4, font=S.FONT_BOLD,
        ).pack(side="right", padx=(6, 0))

        field_row(body, "نام شما (تاریخچه):", settings.author, "author", self._entries)

        # receive mode
        tk.Label(
            body, text="حالت دریافت", font=S.FONT_BOLD, fg=S.FG, bg=S.BG, anchor="e"
        ).pack(fill="x", pady=(16, 6))

        mode_card = tk.Frame(
            body, bg=S.CARD, highlightthickness=1, highlightbackground=S.BORDER
        )
        mode_card.pack(fill="x")
        mode_inner = tk.Frame(mode_card, bg=S.CARD, padx=12, pady=10)
        mode_inner.pack(fill="x")

        self.mode_var = tk.StringVar(value=settings.receive_mode)
        modes = [
            ("full", "جایگزینی کامل پروژه (Restore)"),
            ("merge", "جایگزینی فایل‌های موجود"),
            ("new_only", "فقط فایل‌های جدید"),
        ]
        for val, label in modes:
            tk.Radiobutton(
                mode_inner,
                text=label,
                variable=self.mode_var,
                value=val,
                bg=S.CARD,
                fg=S.FG,
                selectcolor=S.BG4,
                activebackground=S.CARD,
                activeforeground=S.ACCENT,
                font=S.FONT,
                anchor="e",
                cursor="hand2",
                highlightthickness=0,
            ).pack(fill="x", padx=4, pady=3)

        # buttons
        btns = tk.Frame(body, bg=S.BG)
        btns.pack(fill="x", pady=(18, 0))

        HoverButton(
            btns, text="ورود به Rubika", command=self._login, kind="primary",
            pady=8, padx=14,
        ).pack(side="left", padx=(0, 8))
        HoverButton(
            btns, text="تست اتصال", command=self._test, kind="ghost",
            pady=8, padx=12,
        ).pack(side="left")

        HoverButton(
            btns, text="انصراف", command=self.destroy, kind="default",
            pady=8, padx=14,
        ).pack(side="right", padx=(8, 0))
        HoverButton(
            btns, text="ذخیره", command=self._save, kind="primary",
            pady=8, padx=20,
        ).pack(side="right")

        self.geometry("560x560")

    def _browse_project(self):
        path = filedialog.askdirectory(title="انتخاب مسیر پروژه")
        if path:
            self._entries["project"].delete(0, "end")
            self._entries["project"].insert(0, path)

    def _browse_temp(self):
        path = filedialog.askdirectory(title="انتخاب پوشه موقت")
        if path:
            self._entries["temp"].delete(0, "end")
            self._entries["temp"].insert(0, path)

    def _collect(self) -> Settings:
        s = self.settings
        s.rubika_group_url = self._entries["rubika_url"].get().strip()
        s.project_path = self._entries["project"].get().strip()
        s.temp_path = self._entries["temp"].get().strip()
        s.author = self._entries["author"].get().strip()
        s.receive_mode = self.mode_var.get()
        return s

    def _save(self):
        s = self._collect()
        s.save()
        if self.on_save:
            self.on_save(s)
        messagebox.showinfo("Black Git Iran", "تنظیمات ذخیره شد", parent=self)
        self.destroy()

    def _find_app(self):
        parent = self.master
        while parent is not None and not hasattr(parent, "login_to_rubika"):
            parent = getattr(parent, "master", None)
        return parent

    def _login(self):
        s = self._collect()
        s.save()
        if self.on_save:
            self.on_save(s)
        app = self._find_app()
        if app is not None:
            self.destroy()
            app.login_to_rubika()

    def _test(self):
        s = self._collect()
        s.save()
        if self.on_save:
            self.on_save(s)
        parent = self._find_app()
        if parent is None:
            parent = self.master
            while parent is not None and not hasattr(parent, "test_connection"):
                parent = getattr(parent, "master", None)
        if parent is not None:
            self.destroy()
            parent.test_connection()
        else:
            messagebox.showwarning(
                "Black Git Iran",
                "تست اتصال از پنجره اصلی در دسترس است",
                parent=self,
            )

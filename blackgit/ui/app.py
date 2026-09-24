import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from .. import APP_NAME, APP_VERSION
from ..config import Settings
from . import styles as S
from .receive_dialog import ReceiveDialog
from .send_dialog import SendDialog
from .settings_dialog import SettingsDialog
from .widgets import HoverButton, card
from .worker import Worker


class BlackGitApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("560x640")
        self.resizable(False, False)
        self.configure(bg=S.BG)
        self.settings = Settings.load()
        self.worker = Worker(poll_ms=100)
        S.apply_ttk(self)
        self._build()

    def _build(self):
        root = tk.Frame(self, bg=S.BG)
        root.pack(fill="both", expand=True, padx=22, pady=18)

        # ── header ────────────────────────────────────────────────
        hdr = tk.Frame(root, bg=S.BG)
        hdr.pack(fill="x", pady=(0, 4))

        left = tk.Frame(hdr, bg=S.BG)
        left.pack(side="left")
        tk.Label(
            left, text="v" + APP_VERSION, font=S.FONT_TINY, fg=S.FG_FAINT, bg=S.BG
        ).pack(anchor="w")
        tk.Label(
            left,
            text="BLACK GIT IRAN",
            font=S.FONT_TITLE,
            fg=S.ACCENT,
            bg=S.BG,
            anchor="w",
        ).pack(anchor="w")
        tk.Label(
            left,
            text="همگام‌سازی پروژه · بدون API · روبیکا وب",
            font=S.FONT_SMALL,
            fg=S.FG_DIM,
            bg=S.BG,
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        # logo mark
        mark = tk.Label(
            hdr,
            text="◆",
            font=("Segoe UI", 26),
            fg=S.ACCENT,
            bg=S.BG,
        )
        mark.pack(side="right", padx=(8, 0))

        tk.Frame(root, bg=S.BORDER, height=1).pack(fill="x", pady=(16, 14))

        # ── config card ───────────────────────────────────────────
        cfg = card(root)
        cfg.pack(fill="x", pady=(0, 16))
        inner = tk.Frame(cfg, bg=S.CARD, padx=14, pady=12)
        inner.pack(fill="x")

        tk.Label(
            inner,
            text="پیکربندی فعلی",
            font=S.FONT_SMALL,
            fg=S.ACCENT,
            bg=S.CARD,
            anchor="e",
        ).pack(fill="x", pady=(0, 8))

        self.lbl_project = self._kv(inner, "پروژه")
        self.lbl_group = self._kv(inner, "کانال")
        self.lbl_mode = self._kv(inner, "حالت دریافت")
        self.refresh_status()

        # ── action cards (side by side) ───────────────────────────
        actions = tk.Frame(root, bg=S.BG)
        actions.pack(fill="x", pady=(0, 12))
        actions.columnconfigure(0, weight=1)
        actions.columnconfigure(1, weight=1)

        self.btn_recv = self._action_card(
            actions,
            "↓",
            "دریافت نسخه جدید",
            "دانلود و جایگزینی",
            self.open_receive,
        )
        self.btn_recv.grid(row=0, column=0, sticky="nsew", padx=(0, 6))

        self.btn_send = self._action_card(
            actions,
            "↑",
            "ارسال نسخه جدید",
            "زیپ و آپلود",
            self.open_send,
        )
        self.btn_send.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        # ── secondary ─────────────────────────────────────────────
        self.btn_test = HoverButton(
            root,
            text="تست اتصال به Rubika",
            command=self.test_connection,
            kind="ghost",
            pady=12,
        )
        self.btn_test.pack(fill="x", pady=(4, 0))

        # ── bottom bar ────────────────────────────────────────────
        tk.Frame(root, bg=S.BORDER, height=1).pack(fill="x", side="bottom", pady=(14, 10))

        bottom = tk.Frame(root, bg=S.BG)
        bottom.pack(fill="x", side="bottom")

        self.btn_settings = HoverButton(
            bottom,
            text="⚙  تنظیمات",
            command=self.open_settings,
            kind="primary",
            pady=8,
            padx=16,
        )
        self.btn_settings.pack(side="right")

        status_box = tk.Frame(bottom, bg=S.BG2, highlightthickness=1,
                              highlightbackground=S.BORDER)
        status_box.pack(side="right", fill="x", expand=True, padx=(0, 10))
        self.lbl_status = tk.Label(
            status_box,
            text="آماده",
            font=S.FONT_SMALL,
            fg=S.OK,
            bg=S.BG2,
            anchor="e",
            padx=10,
            pady=7,
        )
        self.lbl_status.pack(fill="x")

        self.worker.bind(on_status=self._on_status, on_error=self._on_error)

    def _kv(self, parent, title: str) -> tk.Label:
        row = tk.Frame(parent, bg=S.CARD)
        row.pack(fill="x", pady=2)
        tk.Label(
            row, text=title, font=S.FONT_SMALL, fg=S.FG_FAINT, bg=S.CARD,
            anchor="e", width=14,
        ).pack(side="right")
        lbl = tk.Label(
            row, text="—", font=S.FONT_MONO, fg=S.FG, bg=S.CARD,
            anchor="w", justify="left",
        )
        lbl.pack(side="left", fill="x", expand=True)
        return lbl

    def _action_card(self, parent, icon: str, title: str, sub: str, cmd):
        frame = tk.Frame(
            parent,
            bg=S.CARD,
            highlightthickness=1,
            highlightbackground=S.BORDER,
            cursor="hand2",
        )
        icon_lbl = tk.Label(
            frame, text=icon, font=("Segoe UI", 28), fg=S.ACCENT, bg=S.CARD
        )
        icon_lbl.pack(pady=(16, 4))
        t = tk.Label(
            frame, text=title, font=S.FONT_BOLD, fg=S.FG, bg=S.CARD, anchor="center"
        )
        t.pack(pady=(0, 2))
        s = tk.Label(
            frame, text=sub, font=S.FONT_SMALL, fg=S.FG_DIM, bg=S.CARD, anchor="center"
        )
        s.pack(pady=(0, 16))

        parts = [frame, icon_lbl, t, s]

        def on_enter(_e):
            frame.configure(bg=S.CARD_HOVER, highlightbackground=S.ACCENT)
            for w in parts:
                try:
                    w.configure(bg=S.CARD_HOVER)
                except Exception:
                    pass

        def on_leave(_e):
            frame.configure(bg=S.CARD, highlightbackground=S.BORDER)
            for w in parts:
                try:
                    w.configure(bg=S.CARD)
                except Exception:
                    pass

        def on_click(_e=None):
            cmd()

        for w in parts:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", on_click)
        frame.bind("<Button-1>", on_click)
        return frame

    def refresh_status(self):
        s = self.settings
        proj = s.project_path or "—"
        try:
            if s.project_path:
                proj = str(Path(s.project_path))
        except Exception:
            pass
        if len(proj) > 46:
            proj = "…" + proj[-45:]
        group = s.rubika_group_url or "—"
        if len(group) > 46:
            group = group[:43] + "..."
        modes = {
            "full": "جایگزینی کامل (Restore)",
            "merge": "جایگزینی فایل‌های موجود",
            "new_only": "فقط فایل‌های جدید",
        }
        self.lbl_project.config(text=proj)
        self.lbl_group.config(text=group)
        self.lbl_mode.config(text=modes.get(s.receive_mode, s.receive_mode))

    def _set_status(self, text: str, color: str):
        self.lbl_status.config(text=text, fg=color)

    def _on_status(self, msg: str):
        self._set_status(msg, S.FG_DIM)

    def _on_error(self, msg: str):
        first = msg.splitlines()[0] if msg else "خطای ناشناخته"
        if len(first) > 90:
            first = first[:87] + "..."
        self._set_status(f"✕ {first}", S.ERR)
        messagebox.showerror(APP_NAME, msg, parent=self)

    def _guard_busy(self) -> bool:
        if self.worker.busy:
            messagebox.showwarning(
                APP_NAME, "یک عملیات در حال اجراست؛ لطفاً صبر کنید", parent=self
            )
            return False
        return True

    def _guard_config(self) -> bool:
        s = self.settings
        if not s.project_dir:
            messagebox.showwarning(
                APP_NAME, "ابتدا مسیر پروژه را در تنظیمات انتخاب کنید", parent=self
            )
            self.open_settings()
            return False
        if not s.rubika_group_url:
            messagebox.showwarning(
                APP_NAME, "لینک گروه/کانال را در تنظیمات وارد کنید", parent=self
            )
            self.open_settings()
            return False
        return True

    def open_settings(self):
        SettingsDialog(
            self,
            self.settings,
            on_save=lambda s: (setattr(self, "settings", s), self.refresh_status()),
        )

    def open_receive(self):
        if not (self._guard_busy() and self._guard_config()):
            return
        ReceiveDialog(self, self.settings, self.worker, on_done=self._op_done)

    def open_send(self):
        if not (self._guard_busy() and self._guard_config()):
            return
        SendDialog(self, self.settings, self.worker, on_done=self._op_done)

    def _op_done(self, result: dict):
        self._set_status("✓ عملیات با موفقیت انجام شد", S.OK)

    def test_connection(self):
        if not self._guard_busy():
            return
        s = self.settings
        if not s.rubika_group_url:
            messagebox.showwarning(
                APP_NAME, "لینک گروه/کانال خالی است", parent=self
            )
            return

        group_url = s.rubika_group_url
        profile = s.browser_profile_dir
        self.btn_test.set_enabled(False)

        def job(status):
            from ..transport.rubika.web import RubikaWebTransport

            t = RubikaWebTransport(profile, group_url)
            try:
                ok = t.test_connection(on_status=status)
                if not ok:
                    raise RuntimeError("اتصال برقرار نشد")
                return {"ok": True}
            finally:
                t.close()

        def on_ok(_r):
            self._set_status("✓ اتصال برقرار شد", S.OK)

        def on_finished():
            self.btn_test.set_enabled(True)

        self.worker.bind(
            on_status=self._on_status,
            on_error=self._on_error,
            on_result=on_ok,
            on_finished=on_finished,
        )
        if not self.worker.start(job):
            self.btn_test.set_enabled(True)


def run_app():
    app = BlackGitApp()

    def loop():
        try:
            app.worker.poll(app)
        except Exception:
            pass
        if app.winfo_exists():
            app.after(100, loop)

    app.after(100, loop)
    app.mainloop()

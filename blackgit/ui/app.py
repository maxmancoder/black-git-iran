import tkinter as tk
from pathlib import Path
from tkinter import messagebox

from .. import APP_NAME, APP_VERSION
from ..config import Settings
from . import styles as S
from .receive_dialog import ReceiveDialog
from .send_dialog import SendDialog
from .settings_dialog import SettingsDialog
from .widgets import (
    Card,
    HoverButton,
    LogPanel,
    SidebarItem,
    StatusDot,
    StatusPill,
    ToggleSwitch,
)
from .worker import Worker


class BlackGitApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.geometry("1060x700")
        self.minsize(980, 640)
        self.configure(bg=S.BG)
        self.settings = Settings.load()
        self.worker = Worker(poll_ms=100)
        self.worker.log_hook = self._log_hook
        self.engine_on = True
        self._conn_ok = False
        self._last_status = "آماده"
        S.apply_ttk(self)
        self._build()
        self.refresh_status()
        self._log("info", f"{APP_NAME} v{APP_VERSION} started")

    # ── layout ───────────────────────────────────────────────────────
    def _build(self):
        # sidebar
        self.sidebar = tk.Frame(self, bg=S.SIDEBAR, width=250, highlightthickness=1,
                                highlightbackground=S.BORDER, highlightcolor=S.BORDER)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self._build_sidebar()

        # main area
        main = tk.Frame(self, bg=S.BG)
        main.pack(side="right", fill="both", expand=True, padx=18, pady=16)
        self._build_main(main)

        self.worker.bind(on_status=self._on_status, on_error=self._on_error)

    def _build_sidebar(self):
        sb = self.sidebar

        # logo
        logo = tk.Frame(sb, bg=S.SIDEBAR, padx=16, pady=16)
        logo.pack(fill="x")
        tk.Label(
            logo, text="▣", font=("Segoe UI", 18), fg=S.FG, bg=S.SIDEBAR
        ).pack(side="right", padx=(0, 8))
        tk.Label(
            logo, text="black-git-iran", font=S.FONT_SIDE_TITLE, fg=S.FG,
            bg=S.SIDEBAR, anchor="e",
        ).pack(side="right")

        # master toggle block
        tog_wrap = tk.Frame(sb, bg=S.SIDEBAR, padx=16, pady=8)
        tog_wrap.pack(fill="x")
        tk.Label(
            tog_wrap, text="MASTER SYNC TOGGLE", font=S.FONT_TINY, fg=S.FG_FAINT,
            bg=S.SIDEBAR, anchor="w",
        ).pack(fill="x", pady=(0, 8))

        tog_row = tk.Frame(tog_wrap, bg=S.SIDEBAR)
        tog_row.pack(fill="x")
        self.engine_toggle = ToggleSwitch(
            tog_row, value=self.engine_on, command=self._on_engine_toggle, width=96, height=34
        )
        self.engine_toggle.pack(side="left")
        self.lbl_engine_state = tk.Label(
            tog_row,
            text="ON" if self.engine_on else "OFF",
            font=("Segoe UI", 14, "bold"),
            fg=S.OK if self.engine_on else S.FG_FAINT,
            bg=S.SIDEBAR,
            padx=10,
        )
        self.lbl_engine_state.pack(side="left", padx=(10, 0))

        self.lbl_engine_sub = tk.Label(
            tog_wrap,
            text="GLOBAL SYNC: ENABLED" if self.engine_on else "GLOBAL SYNC: DISABLED",
            font=S.FONT_TINY,
            fg=S.FG_DIM if self.engine_on else S.FG_FAINT,
            bg=S.SIDEBAR,
            anchor="w",
        )
        self.lbl_engine_sub.pack(fill="x", pady=(8, 0))

        # separator
        tk.Frame(sb, bg=S.BORDER, height=1).pack(fill="x", padx=16, pady=14)

        # nav items
        nav = tk.Frame(sb, bg=S.SIDEBAR)
        nav.pack(fill="x")

        self.item_receive = SidebarItem(
            nav, "⬇", "دریافت نسخه", command=self.open_receive, dot_color=S.BLUE
        )
        self.item_receive.pack(fill="x")

        self.item_send = SidebarItem(
            nav, "⬆", "ارسال نسخه", command=self.open_send, dot_color=S.OK
        )
        self.item_send.pack(fill="x")

        self.item_test = SidebarItem(
            nav, "⇄", "تست اتصال", command=self.test_connection, dot_color=S.DOT_GRAY
        )
        self.item_test.pack(fill="x")

        tk.Frame(sb, bg=S.BORDER, height=1).pack(fill="x", padx=16, pady=10)

        self.item_settings = SidebarItem(
            nav, "⚙", "تنظیمات", command=self.open_settings, dot=False
        )
        self.item_settings.pack(fill="x")

        # footer
        tk.Frame(sb, bg=S.SIDEBAR).pack(fill="both", expand=True)
        foot = tk.Frame(sb, bg=S.SIDEBAR, padx=16, pady=14)
        foot.pack(fill="x")
        tk.Label(
            foot, text=f"v{APP_VERSION}  ·  Rubika Web",
            font=S.FONT_TINY, fg=S.FG_FAINT, bg=S.SIDEBAR, anchor="w",
        ).pack(fill="x")

    def _build_main(self, main):
        # ── card 1: SYSTEM STATUS ────────────────────────────────────
        self.card_status = Card(main, "System Status")
        self.card_status.pack(fill="x", pady=(0, 12))

        st = self.card_status.body
        self.lbl_big_status = tk.Label(
            st,
            text="SYSTEM STATUS: READY",
            font=S.FONT_BIG_STATUS,
            fg=S.OK,
            bg=S.CARD,
            anchor="center",
        )
        self.lbl_big_status.pack(fill="x", pady=(4, 12))

        metrics = tk.Frame(st, bg=S.CARD)
        metrics.pack(fill="x")
        metrics.columnconfigure(0, weight=1)
        metrics.columnconfigure(1, weight=1)

        left_m = tk.Frame(metrics, bg=S.CARD)
        left_m.grid(row=0, column=0, sticky="ew")
        right_m = tk.Frame(metrics, bg=S.CARD)
        right_m.grid(row=0, column=1, sticky="ew")

        self.lbl_m_project = self._metric(left_m, "Project")
        self.lbl_m_mode = self._metric(left_m, "Receive Mode")
        self.lbl_m_channel = self._metric(right_m, "Channel")
        self.lbl_m_last = self._metric(right_m, "Last Operation")

        # ── card 2: ACTIVE SERVICES ──────────────────────────────────
        self.card_services = Card(main, "Active Services & Transports")
        self.card_services.pack(fill="x", pady=(0, 12))

        sv = self.card_services.body
        rows = tk.Frame(sv, bg=S.CARD)
        rows.pack(side="left", fill="both", expand=True)

        # row 1: rubika transport
        r1 = tk.Frame(rows, bg=S.CARD, pady=8)
        r1.pack(fill="x")
        tk.Label(
            r1, text="RUBIKA TRANSPORT", font=S.FONT_BOLD, fg=S.FG, bg=S.CARD,
            anchor="e",
        ).pack(side="right")
        HoverButton(
            r1, text="Config Registry", command=self.open_settings, kind="default",
            pady=7, padx=14,
        ).pack(side="left", padx=(0, 10))
        self.tog_rubika = ToggleSwitch(
            r1, value=True, command=lambda on: self._on_transport_toggle("rubika", on)
        )
        self.tog_rubika.pack(side="left")
        tk.Frame(r1, bg=S.CARD, width=14).pack(side="left")

        # divider
        tk.Frame(rows, bg=S.BORDER, height=1).pack(fill="x", pady=6)

        # row 2: auto cleanup
        r2 = tk.Frame(rows, bg=S.CARD, pady=8)
        r2.pack(fill="x")
        tk.Label(
            r2, text="AUTO CLEANUP (TEMP)", font=S.FONT_BOLD, fg=S.FG, bg=S.CARD,
            anchor="e",
        ).pack(side="right")
        HoverButton(
            r2, text="Test Connection", command=self.test_connection, kind="default",
            pady=7, padx=14,
        ).pack(side="left", padx=(0, 10))
        self.tog_cleanup = ToggleSwitch(
            r2,
            value=bool(self.settings.auto_cleanup),
            command=self._on_cleanup_toggle,
        )
        self.tog_cleanup.pack(side="left")
        tk.Frame(r2, bg=S.CARD, width=14).pack(side="left")

        # right: transports list (inner panel)
        panel_wrap = tk.Frame(sv, bg=S.CARD)
        panel_wrap.pack(side="right", fill="y", padx=(14, 0))
        tk.Frame(panel_wrap, bg=S.BORDER, width=1).pack(side="left", fill="y", padx=(0, 14))
        panel = tk.Frame(
            panel_wrap, bg=S.PANEL, padx=12, pady=10,
            highlightthickness=1, highlightbackground=S.BORDER,
        )
        panel.pack(fill="y")
        tk.Label(
            panel, text="TRANSPORTS", font=S.FONT_SECTION, fg=S.FG_DIM, bg=S.PANEL,
            anchor="center",
        ).pack(pady=(0, 8))
        self.pill_rubika = StatusPill(panel, "Rubika (Active)", state="active")
        self.pill_rubika.pack(fill="x", pady=3)
        self.pill_lan = StatusPill(panel, "LAN (disabled)", state="disabled")
        self.pill_lan.pack(fill="x", pady=3)
        self.pill_usb = StatusPill(panel, "USB (planned)", state="disabled")
        self.pill_usb.pack(fill="x", pady=3)

        # ── card 3: LIVE LOGS ────────────────────────────────────────
        self.card_logs = Card(main, "Live Logs")
        self.card_logs.pack(fill="both", expand=True)
        self.log_panel = LogPanel(self.card_logs.body, height=180)
        self.log_panel.pack(fill="both", expand=True)

    def _metric(self, parent, title: str) -> tk.Label:
        row = tk.Frame(parent, bg=S.CARD)
        row.pack(fill="x", pady=2)
        tk.Label(
            row, text=title + ":", font=S.FONT_SMALL, fg=S.FG_FAINT, bg=S.CARD,
            anchor="e", width=14,
        ).pack(side="right")
        lbl = tk.Label(
            row, text="—", font=S.FONT_MONO, fg=S.FG, bg=S.CARD, anchor="w"
        )
        lbl.pack(side="left", fill="x", expand=True)
        return lbl

    # ── logging ──────────────────────────────────────────────────────
    def _log(self, level: str, msg: str):
        if hasattr(self, "log_panel"):
            # truncate very long messages in the panel
            if len(msg) > 220:
                msg = msg[:217] + "..."
            self.log_panel.log(msg, level=level)

    def _log_hook(self, level: str, msg: str):
        self._log(level, msg)

    # ── engine / toggles ─────────────────────────────────────────────
    def _on_engine_toggle(self, on: bool):
        self.engine_on = on
        self.lbl_engine_state.configure(
            text="ON" if on else "OFF", fg=S.OK if on else S.FG_FAINT
        )
        self.lbl_engine_sub.configure(
            text="GLOBAL SYNC: ENABLED" if on else "GLOBAL SYNC: DISABLED",
            fg=S.FG_DIM if on else S.FG_FAINT,
        )
        for item in (self.item_receive, self.item_send, self.item_test):
            item.set_enabled(on)
        self._set_big_status(
            "READY" if on else "OFFLINE", S.OK if on else S.FG_FAINT
        )
        self._log("info" if on else "warn",
                  "Sync engine turned ON" if on else "Sync engine turned OFF")

    def _on_transport_toggle(self, name: str, on: bool):
        state = "active" if on else "disabled"
        self.pill_rubika.set_state(state, "Rubika (Active)" if on else "Rubika (off)")
        self._log("info", f"Transport {name}: {'enabled' if on else 'disabled'}")

    def _on_cleanup_toggle(self, on: bool):
        self.settings.auto_cleanup = bool(on)
        self.settings.save()
        self._log("info", f"Auto cleanup: {'enabled' if on else 'disabled'}")

    def _set_big_status(self, text: str, color: str):
        self.lbl_big_status.configure(text=f"SYSTEM STATUS: {text}", fg=color)

    # ── status / errors ──────────────────────────────────────────────
    def refresh_status(self):
        s = self.settings
        proj = s.project_path or "—"
        try:
            if s.project_path:
                proj = Path(s.project_path).name or s.project_path
        except Exception:
            pass
        if len(proj) > 34:
            proj = "…" + proj[-33:]

        channel = "—"
        if s.rubika_group_url:
            channel = "✓ configured"
        if len(s.rubika_group_url or "") > 0:
            host = (s.rubika_group_url or "").split("//")[-1].split("/")[0]
            if host:
                channel = host

        modes = {
            "full": "Full Replace",
            "merge": "Merge Files",
            "new_only": "New Files Only",
        }
        self.lbl_m_project.config(text=proj)
        self.lbl_m_channel.config(text=channel)
        self.lbl_m_mode.config(text=modes.get(s.receive_mode, s.receive_mode))
        self.lbl_m_last.config(text=self._last_status[:36])

        # config dots
        cfg_ok = bool(s.project_dir and s.rubika_group_url)
        dot = S.OK if cfg_ok else S.ERR
        self.item_receive.set_dot(dot)
        self.item_send.set_dot(dot)
        self.item_test.set_dot(S.OK if self._conn_ok else (S.WARN if self._conn_ok is None else S.DOT_GRAY))

        if self.engine_on and cfg_ok and not self.worker.busy:
            self._set_big_status("READY", S.OK)
        elif self.engine_on and not cfg_ok and not self.worker.busy:
            self._set_big_status("NOT CONFIGURED", S.WARN)

    def _on_status(self, msg: str):
        self._last_status = msg
        self._set_big_status("WORKING", S.ACCENT)
        self.card_status.set_highlight(S.ACCENT)

    def _on_error(self, msg: str):
        first = msg.splitlines()[0] if msg else "خطای ناشناخته"
        self._last_status = f"ERROR: {first}"[:40]
        self._set_big_status("ERROR", S.ERR)
        self.card_status.set_highlight(S.ERR)
        self.item_test.set_dot(S.ERR)
        self._conn_ok = False
        messagebox.showerror(APP_NAME, msg, parent=self)

    def _on_done_status(self, result: dict):
        self._set_big_status("READY", S.OK)
        self.card_status.set_highlight(S.BORDER)
        summary = str(result.get("version") or result.get("filename") or "done")
        self._last_status = summary[:40]
        self.refresh_status()

    # ── guards ───────────────────────────────────────────────────────
    def _guard_busy(self) -> bool:
        if self.worker.busy:
            messagebox.showwarning(
                APP_NAME, "یک عملیات در حال اجراست؛ لطفاً صبر کنید", parent=self
            )
            return False
        return True

    def _guard_engine(self) -> bool:
        if not self.engine_on:
            messagebox.showwarning(
                APP_NAME, "موتور همگام‌سازی خاموش است (تگل ON)", parent=self
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

    # ── actions ──────────────────────────────────────────────────────
    def open_settings(self):
        SettingsDialog(
            self,
            self.settings,
            on_save=lambda s: (setattr(self, "settings", s), self.refresh_status()),
        )

    def open_receive(self):
        if not (self._guard_busy() and self._guard_engine() and self._guard_config()):
            return
        ReceiveDialog(self, self.settings, self.worker, on_done=self._op_done)

    def open_send(self):
        if not (self._guard_busy() and self._guard_engine() and self._guard_config()):
            return
        SendDialog(self, self.settings, self.worker, on_done=self._op_done)

    def _op_done(self, result: dict):
        self._on_done_status(result)

    def test_connection(self):
        if not (self._guard_busy() and self._guard_engine()):
            return
        s = self.settings
        if not s.rubika_group_url:
            messagebox.showwarning(APP_NAME, "لینک گروه/کانال خالی است", parent=self)
            return

        group_url = s.rubika_group_url
        profile = s.browser_profile_dir
        self.item_test.set_enabled(False)

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
            self._conn_ok = True
            self.item_test.set_dot(S.OK)
            self._set_big_status("CONNECTED", S.OK)
            self._log("ok", "Rubika connection OK")

        def on_finished():
            self.item_test.set_enabled(True)
            if self.engine_on and self._conn_ok:
                self._set_big_status("READY", S.OK)

        self.worker.bind(
            on_status=self._on_status,
            on_error=self._on_error,
            on_result=on_ok,
            on_finished=on_finished,
        )
        if not self.worker.start(job):
            self.item_test.set_enabled(True)


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

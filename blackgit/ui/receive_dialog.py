import tkinter as tk

from ..config import Settings
from . import styles as S
from .widgets import HoverButton, entry, status_pill
from .worker import Worker


class ReceiveDialog(tk.Toplevel):
    def __init__(self, parent, settings: Settings, worker: Worker, on_done=None):
        super().__init__(parent)
        self.title("دریافت نسخه جدید")
        self.configure(bg=S.BG)
        self.resizable(False, False)
        self.settings = settings
        self.worker = worker
        self.on_done = on_done
        self.transient(parent)
        self.grab_set()

        body = tk.Frame(self, bg=S.BG, padx=24, pady=22)
        body.pack(fill="both", expand=True)

        hdr = tk.Frame(body, bg=S.BG)
        hdr.pack(fill="x", pady=(0, 4))
        tk.Label(
            hdr, text="↓", font=("Segoe UI", 24), fg=S.BLUE, bg=S.BG
        ).pack(side="left")
        tk.Label(
            hdr, text="دریافت نسخه جدید", font=S.FONT_TITLE, fg=S.FG, bg=S.BG,
            anchor="e",
        ).pack(side="right")

        tk.Label(
            body,
            text="نام نسخه را بدون پسوند .zip وارد کنید  ·  مثال: my-project-v12",
            font=S.FONT_SMALL,
            fg=S.FG_DIM,
            bg=S.BG,
            anchor="e",
        ).pack(fill="x", pady=(6, 14))

        name_card = tk.Frame(
            body, bg=S.CARD, highlightthickness=1, highlightbackground=S.BORDER
        )
        name_card.pack(fill="x", pady=(0, 14))
        self.name_var = tk.StringVar()
        e = entry(name_card, textvariable=self.name_var, justify="center")
        e.pack(fill="x", ipady=8, padx=2, pady=2)
        e.focus_set()

        self.status_var = tk.StringVar(value="آماده — منتظر نام نسخه")
        pill = status_pill(body, self.status_var)
        pill.pack(fill="x", pady=(0, 16))

        btns = tk.Frame(body, bg=S.BG)
        btns.pack(fill="x")
        self.btn_go = HoverButton(
            btns, text="دریافت", command=self._go, kind="primary",
            pady=10, padx=32, font=S.FONT_BTN,
        )
        self.btn_go.pack(side="right")
        HoverButton(
            btns, text="بستن", command=self.destroy, kind="default",
            pady=10, padx=16,
        ).pack(side="right", padx=(0, 10))

        self.geometry("520x340")
        self.worker.bind(
            on_status=self._status,
            on_result=self._done,
            on_error=self._error,
            on_finished=self._finished,
        )
        e.bind("<Return>", lambda _e: self._go())

    def destroy(self):
        try:
            parent = self.master
            if hasattr(parent, "worker"):
                parent.worker.bind(
                    on_status=getattr(parent, "_on_status", None),
                    on_error=getattr(parent, "_on_error", None),
                    on_result=None,
                    on_finished=None,
                )
        except Exception:
            pass
        super().destroy()

    def _status(self, msg: str):
        if self.winfo_exists():
            self.status_var.set(msg)

    def _finished(self):
        if self.winfo_exists():
            self.btn_go.set_enabled(True)

    def _error(self, msg: str):
        if not self.winfo_exists():
            return
        first = msg.splitlines()[0] if msg else "خطا"
        self.status_var.set(f"✕ {first}")
        try:
            self.status_pill_fg(S.ERR)
        except Exception:
            pass
        self.btn_go.set_enabled(True)

    def status_pill_fg(self, color: str):
        for child in self.winfo_children():
            pass
        # update pill label color via status_var's widget
        # pill is packed in body — find labels with status_var
        def walk(w):
            for c in w.winfo_children():
                if isinstance(c, tk.Label) and str(c.cget("textvariable")) == str(self.status_var):
                    c.configure(fg=color)
                    return True
                if walk(c):
                    return True
            return False
        walk(self)

    def _done(self, result: dict):
        if not self.winfo_exists():
            return
        self.status_var.set(
            f"✓ دریافت شد — نسخه {result.get('version', '')} · "
            f"{result.get('files', '?')} فایل"
        )
        self.status_pill_fg(S.OK)
        if self.on_done:
            self.on_done(result)
        self.after(1600, self.destroy)

    def _go(self):
        name = self.name_var.get().strip()
        if not name:
            self.status_var.set("نام نسخه را وارد کنید")
            self.status_pill_fg(S.WARN)
            return
        if name.lower().endswith(".zip"):
            name = name[:-4]
        s = self.settings
        if not s.project_dir:
            self.status_var.set("مسیر پروژه در تنظیمات تنظیم نشده")
            self.status_pill_fg(S.ERR)
            return
        if not s.rubika_group_url:
            self.status_var.set("لینک گروه/کانال در تنظیمات خالی است")
            self.status_pill_fg(S.ERR)
            return

        self.btn_go.set_enabled(False)
        self.status_var.set("شروع عملیات دریافت...")
        self.status_pill_fg(S.FG_DIM)

        filename = f"{name}.zip"
        project = s.project_dir
        temp = s.temp_dir
        profile = s.browser_profile_dir
        group_url = s.rubika_group_url
        mode = s.receive_mode
        backup_dir = s.backup_dir

        def job(status):
            from ..core import zip_handler
            from ..core.atomic_replace import atomic_replace, cleanup_dir
            from ..transport.rubika.web import RubikaWebTransport

            status(f"اتصال به Rubika برای {filename}...")
            transport = RubikaWebTransport(profile, group_url)
            try:
                zip_path = transport.download(filename, temp, on_status=status)
                status("استخراج زیپ در پوشه موقت...")
                extracted = temp / "_extracted"
                cleanup_dir(extracted)
                zip_handler.extract_zip(zip_path, extracted)
                status("بررسی صحت فایل‌ها...")
                meta = zip_handler.verify_extracted(extracted)
                status("ساخت بکاپ و جایگزینی پروژه...")
                result = atomic_replace(project, extracted, backup_dir, mode=mode)
                if getattr(s, "auto_cleanup", True):
                    status("پاک‌سازی پوشه موقت...")
                    cleanup_dir(temp)
                else:
                    status("پوشه موقت حفظ شد (auto cleanup خاموش)")
                return {
                    "version": name,
                    "files": result["copied"],
                    "backup": result["backup"],
                    "meta": meta,
                }
            finally:
                transport.close()

        self.worker.start(job)

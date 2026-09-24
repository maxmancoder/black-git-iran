import tkinter as tk

from ..config import Settings
from . import styles as S
from .widgets import HoverButton, entry, status_pill
from .worker import Worker


class SendDialog(tk.Toplevel):
    def __init__(self, parent, settings: Settings, worker: Worker, on_done=None):
        super().__init__(parent)
        self.title("ارسال نسخه جدید")
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
            hdr, text="↑", font=("Segoe UI", 24), fg=S.OK, bg=S.BG
        ).pack(side="left")
        tk.Label(
            hdr, text="ارسال نسخه جدید", font=S.FONT_TITLE, fg=S.FG, bg=S.BG,
            anchor="e",
        ).pack(side="right")

        tk.Label(
            body,
            text="فایل‌های اصلی پروژه دست نمی‌خورند · فقط زیپ ساخته و آپلود می‌شود",
            font=S.FONT_SMALL,
            fg=S.FG_DIM,
            bg=S.BG,
            anchor="e",
        ).pack(fill="x", pady=(6, 14))

        # version name
        tk.Label(
            body, text="نام نسخه (بدون .zip)", font=S.FONT_SMALL,
            fg=S.FG_FAINT, bg=S.BG, anchor="e",
        ).pack(fill="x", pady=(0, 4))
        name_card = tk.Frame(
            body, bg=S.CARD, highlightthickness=1, highlightbackground=S.BORDER
        )
        name_card.pack(fill="x", pady=(0, 12))
        self.name_var = tk.StringVar()
        e = entry(name_card, textvariable=self.name_var, justify="center")
        e.pack(fill="x", ipady=8, padx=2, pady=2)
        e.focus_set()

        # commit message
        tk.Label(
            body, text="پیام (Commit Message) — اختیاری", font=S.FONT_SMALL,
            fg=S.FG_FAINT, bg=S.BG, anchor="e",
        ).pack(fill="x", pady=(0, 4))
        msg_card = tk.Frame(
            body, bg=S.CARD, highlightthickness=1, highlightbackground=S.BORDER
        )
        msg_card.pack(fill="x", pady=(0, 14))
        self.msg_var = tk.StringVar()
        m = entry(msg_card, textvariable=self.msg_var, mono=False, justify="right")
        m.pack(fill="x", ipady=7, padx=2, pady=2)

        self.status_var = tk.StringVar(value="آماده — منتظر نام نسخه")
        pill = status_pill(body, self.status_var)
        pill.pack(fill="x", pady=(0, 16))

        btns = tk.Frame(body, bg=S.BG)
        btns.pack(fill="x")
        self.btn_go = HoverButton(
            btns, text="ارسال", command=self._go, kind="primary",
            pady=10, padx=32, font=S.FONT_BTN,
        )
        self.btn_go.pack(side="right")
        HoverButton(
            btns, text="بستن", command=self.destroy, kind="default",
            pady=10, padx=16,
        ).pack(side="right", padx=(0, 10))

        self.geometry("520x460")
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

    def _set_pill_color(self, color: str):
        def walk(w):
            for c in w.winfo_children():
                if isinstance(c, tk.Label) and str(c.cget("textvariable")) == str(
                    self.status_var
                ):
                    c.configure(fg=color)
                    return True
                if walk(c):
                    return True
            return False
        walk(self)

    def _status(self, msg: str):
        if self.winfo_exists():
            self.status_var.set(msg)
            self._set_pill_color(S.FG_DIM)

    def _finished(self):
        if self.winfo_exists():
            self.btn_go.set_enabled(True)

    def _error(self, msg: str):
        if not self.winfo_exists():
            return
        first = msg.splitlines()[0] if msg else "خطا"
        self.status_var.set(f"✕ {first}")
        self._set_pill_color(S.ERR)
        self.btn_go.set_enabled(True)

    def _done(self, result: dict):
        if not self.winfo_exists():
            return
        kb = int(result.get("size", 0)) // 1024
        self.status_var.set(
            f"✓ ارسال شد — {result.get('filename', '')} · {kb} KB"
        )
        self._set_pill_color(S.OK)
        if self.on_done:
            self.on_done(result)
        self.after(1600, self.destroy)

    def _go(self):
        name = self.name_var.get().strip()
        if not name:
            self.status_var.set("نام نسخه را وارد کنید")
            self._set_pill_color(S.WARN)
            return
        if name.lower().endswith(".zip"):
            name = name[:-4]
        s = self.settings
        if not s.project_dir:
            self.status_var.set("مسیر پروژه در تنظیمات تنظیم نشده")
            self._set_pill_color(S.ERR)
            return
        if not s.rubika_group_url:
            self.status_var.set("لینک گروه/کانال در تنظیمات خالی است")
            self._set_pill_color(S.ERR)
            return

        self.btn_go.set_enabled(False)
        self.status_var.set("شروع عملیات ارسال...")
        self._set_pill_color(S.FG_DIM)

        project = s.project_dir
        temp = s.temp_dir
        profile = s.browser_profile_dir
        group_url = s.rubika_group_url
        author = s.author
        message = self.msg_var.get().strip()
        zip_name = f"{name}.zip"
        zip_path = temp / zip_name

        def job(status):
            from ..core.zip_handler import create_project_zip
            from ..transport.rubika.web import RubikaWebTransport

            status("زیپ‌کردن پروژه (فایل‌های اصلی دست‌نخورده می‌مانند)...")
            meta = create_project_zip(
                project, zip_path, version=name, author=author, message=message
            )
            size = zip_path.stat().st_size
            status(f"زیپ آماده شد ({size // 1024} KB) — باز کردن Rubika...")
            transport = RubikaWebTransport(profile, group_url)
            try:
                transport.upload(zip_path, on_status=status)
            finally:
                transport.close()
            if getattr(s, "auto_cleanup", True):
                status("پاک‌سازی زیپ موقت...")
                try:
                    zip_path.unlink(missing_ok=True)
                except OSError:
                    pass
            else:
                status("زیپ موقت حفظ شد (auto cleanup خاموش)")
            return {
                "filename": zip_name,
                "size": size,
                "files": meta.get("files"),
                "sha256": meta.get("zipSha256"),
                "version": name,
            }

        self.worker.start(job)

"""
Rubika Web transport via Playwright (no API).

Flow:
  launch persistent profile -> open web.rubika.ir -> wait login if needed
  -> open configured group/channel -> search file / attach file

Selectors are best-effort: Rubika changes its DOM often.
If automation breaks, update the SEL_* constants below
(debug screenshots are saved to temp dir on failure).
"""

import time
from pathlib import Path

from playwright.sync_api import (
    TimeoutError as PWTimeout,
    sync_playwright,
    Page,
    BrowserContext,
)

from ..base import NotLoggedInError, StatusCb, Transport, TransportError

RUBIKA_URL = "https://web.rubika.ir/"

# ── selectors (update these if Rubika UI changes) ──────────────────
SEL_CHAT_LIST = '[data-testid="chat-list"], .chat-list, #chat-list'
SEL_SEARCH_INPUT = (
    'input[placeholder*="Search"], input[placeholder*="جستجو"], '
    'input[type="search"], [aria-label*="Search"], [aria-label*="جستجو"]'
)
SEL_ATTACH_INPUT = 'input[type="file"]'
SEL_ATTACH_BUTTON = (
    '[aria-label*="attach" i], [aria-label*="Attach" i], '
    '[aria-label*="فایل"], [title*="attach" i], [title*="فایل"], '
    'button[aria-label*="clip" i]'
)
SEL_SEND_BUTTON = (
    'button[aria-label*="send" i], [title*="send" i], [title*="ارسال"]'
)
SEL_MESSAGE_INPUT = (
    'textarea, [contenteditable="true"], '
    'input[placeholder*="Message"], input[placeholder*="پیام"]'
)
SEL_DOWNLOAD = (
    'button[aria-label*="download" i], a[download], '
    '[title*="download" i], [title*="دانلود"]'
)
# Strong positive: user is inside the messenger (not a login/OTP screen)
SEL_LOGGED_IN = (
    '[data-testid="chat-list"], .chat-list, #chat-list, '
    '[data-testid="message-input"], .message-input, '
    'div[contenteditable="true"]'
)
# Strong negative: still on phone / password / OTP login screens
SEL_LOGIN_FORM = (
    'input[type="password"], input[type="tel"], '
    'input[name*="phone" i], input[name*="mobile" i], '
    'input[autocomplete="one-time-code"], '
    'input[placeholder*="کد تایید" i], input[placeholder*="کد تأیید" i], '
    'input[placeholder*="verification" i], '
    '[class*="qr-code" i], [class*="qrcode" i], canvas'
)
# ───────────────────────────────────────────────────────────────────


class RubikaWebTransport(Transport):
    def __init__(self, profile_dir: Path, group_url: str, headless: bool = False):
        self.profile_dir = Path(profile_dir)
        self.group_url = (group_url or "").strip()
        self.headless = headless
        self._pw = None
        self._ctx: BrowserContext | None = None
        self._page: Page | None = None

    # ── lifecycle ──────────────────────────────────────────────────
    def _start(self, on_status: StatusCb | None = None) -> Page:
        if self._page is not None:
            return self._page
        if not self.group_url:
            raise TransportError("لینک گروه/کانال در تنظیمات خالی است")

        def st(m):
            if on_status:
                on_status(m)

        st("باز کردن مرورگر Rubika...")
        self._pw = sync_playwright().start()
        self._ctx = self._launch_context()
        self._ctx.set_default_timeout(30_000)
        pages = self._ctx.pages
        self._page = pages[0] if pages else self._ctx.new_page()
        try:
            self._page.goto(RUBIKA_URL, wait_until="domcontentloaded", timeout=45_000)
        except PWTimeout:
            st("بارگذاری کند بود — ادامه...")
        return self._page

    def _launch_context(self) -> BrowserContext:
        """Try bundled Chromium first; fall back to system Edge/Chrome
        (Playwright CDN may be blocked — channel mode needs no download)."""
        base = dict(
            user_data_dir=str(self.profile_dir),
            headless=self.headless,
            viewport={"width": 1280, "height": 800},
            args=["--disable-blink-features=AutomationControlled"],
        )
        attempts: list[dict] = [{}, {"channel": "msedge"}, {"channel": "chrome"}]
        for win_path in (
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ):
            if Path(win_path).exists():
                attempts.append({"executable_path": win_path})
        last_err: Exception | None = None
        for extra in attempts:
            try:
                return self._pw.chromium.launch_persistent_context(**base, **extra)
            except Exception as e:
                last_err = e
                continue
        raise TransportError(
            "مرورگری برای اجرا پیدا نشد. Edge یا Chrome ویندوز را نصب کنید "
            f"یا `playwright install chromium` را اجرا کنید. خطا: {last_err}"
        )

    def close(self) -> None:
        try:
            if self._ctx:
                try:
                    self._ctx.close(timeout=10_000)
                except TypeError:
                    self._ctx.close()  # older Playwright without timeout kw
                except Exception:
                    pass
        finally:
            self._ctx = None
            self._page = None
            if self._pw:
                try:
                    self._pw.stop()
                except Exception:
                    pass
                self._pw = None

    def _screenshot(self, name: str) -> Path | None:
        if not self._page:
            return None
        p = self.profile_dir / f"debug-{name}-{int(time.time())}.png"
        try:
            self._page.screenshot(path=str(p), full_page=False)
            return p
        except Exception:
            return None

    # ── login / navigation ─────────────────────────────────────────
    def _page_alive(self, page: Page) -> bool:
        try:
            return not page.is_closed()
        except Exception:
            return False

    def _is_logged_in(self, page: Page) -> bool:
        """Detect a real logged-in messenger — never trust loose text.

        Old bug: Persian OTP screens contain 'پیامک' which matched 'پیام'
        and made us think login finished too early.
        """
        if not self._page_alive(page):
            return False

        # 1) login/OTP form visible -> definitely NOT logged in
        try:
            login = page.locator(SEL_LOGIN_FORM)
            for i in range(min(login.count(), 12)):
                try:
                    if login.nth(i).is_visible():
                        return False
                except Exception:
                    continue
        except Exception:
            pass

        # 2) messenger UI visible -> logged in
        try:
            inside = page.locator(SEL_LOGGED_IN)
            for i in range(min(inside.count(), 8)):
                try:
                    if inside.nth(i).is_visible():
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        # 3) URL still on an auth path -> not logged in
        try:
            url = (page.url or "").lower()
            if any(x in url for x in ("/login", "signin", "sign-in", "/auth", "otp", "verify")):
                return False
        except Exception:
            pass

        return False

    def _ensure_login(self, page: Page, on_status: StatusCb | None = None) -> None:
        def st(m):
            if on_status:
                on_status(m)

        st("بررسی ورود به Rubika...")
        # First login may take a while: phone + password + SMS code.
        # Keep the browser open; do NOT navigate away until truly logged in.
        deadline = time.time() + 600  # 10 minutes
        hint_shown = False
        last_msg = ""
        while time.time() < deadline:
            if not self._page_alive(page):
                shot = self._screenshot("browser-closed")
                raise NotLoggedInError(
                    "پنجره مرورگر بسته شد؛ ورود کامل نشد. دوباره تلاش کنید. "
                    f"اسکرین‌شات: {shot}"
                )
            if self._is_logged_in(page):
                st("ورود تأیید شد — آماده‌سازی...")
                page.wait_for_timeout(1500)  # let SPA finish bootstrapping
                if self._is_logged_in(page):
                    st("ورود موفق")
                    return
                # false positive during bootstrap — keep waiting
            remaining = max(0, int(deadline - time.time()))
            msg = (
                f"در پنجره مرورگر وارد Rubika شوید "
                f"(کد تایید پیامک را هم بزنید)... {remaining}s"
            )
            if msg != last_msg:
                st(msg)
                last_msg = msg
            if not hint_shown:
                hint_shown = True
            time.sleep(2)

        shot = self._screenshot("login-timeout")
        raise NotLoggedInError(
            "ورود به Rubika انجام نشد (مهلت ۱۰ دقیقه تمام شد). "
            f"اسکرین‌شات: {shot}"
        )

    def _open_group(self, page: Page, on_status: StatusCb | None = None) -> None:
        def st(m):
            if on_status:
                on_status(m)

        st(f"رفتن به گروه/کانال: {self.group_url}")
        try:
            page.goto(self.group_url, wait_until="domcontentloaded", timeout=30_000)
        except PWTimeout:
            pass
        except Exception as e:
            # SPA may intercept; soft-fail and let search/download handle it
            st(f"ناوبری مستقیم ممکن نشد ({e}) — تلاش ادامه دارد...")
        time.sleep(2)
        # If navigation bounced back to login, wait again (session refresh)
        if not self._is_logged_in(page):
            st("نشست هنوز کامل نشد؛ منتظر تکمیل ورود...")
            self._ensure_login(page, on_status)
            try:
                page.goto(self.group_url, wait_until="domcontentloaded", timeout=30_000)
                time.sleep(2)
            except Exception:
                pass

    def _open_channel(self, on_status: StatusCb | None = None) -> Page:
        page = self._start(on_status)
        self._ensure_login(page, on_status)
        self._open_group(page, on_status)
        return page

    # ── search helper ──────────────────────────────────────────────
    def _open_search(self, page: Page) -> None:
        # try visible search input; otherwise click a search icon first
        box = page.locator(SEL_SEARCH_INPUT)
        if box.count() == 0 or not box.first.is_visible():
            icon = page.locator(
                '[aria-label*="search" i], [title*="search" i], '
                '[aria-label*="جستجو"], .icon-search, button:has(svg)'
            )
            for i in range(min(icon.count(), 8)):
                try:
                    icon.nth(i).click(timeout=2000)
                    page.wait_for_timeout(500)
                    if page.locator(SEL_SEARCH_INPUT).count() and page.locator(
                        SEL_SEARCH_INPUT
                    ).first.is_visible():
                        break
                except Exception:
                    continue
        box = page.locator(SEL_SEARCH_INPUT)
        if not box.count():
            raise TransportError(
                "جعبه جستجو پیدا نشد — سلکتورهای SEL_SEARCH_INPUT را به‌روز کنید"
            )
        box.first.click()
        box.first.fill("")

    # ── Transport API ──────────────────────────────────────────────
    def download(
        self,
        filename: str,
        dest_dir: Path,
        on_status: StatusCb | None = None,
    ) -> Path:
        def st(m):
            if on_status:
                on_status(m)

        page = self._open_channel(on_status)
        dest_dir.mkdir(parents=True, exist_ok=True)
        st(f"جستجوی فایل: {filename}")

        # 1) search inside the open chat
        try:
            self._open_search(page)
            page.keyboard.type(filename, delay=40)
            page.wait_for_timeout(2500)
        except Exception as e:
            st(f"جستجو ممکن نشد ({e}) — تلاش برای پیمایش پیام‌ها...")

        # 2) find a message/row containing the filename
        target = None
        try:
            rows = page.locator(f"text={filename}")
            if rows.count():
                target = rows.first
                target.scroll_into_view_if_needed(timeout=5000)
        except Exception:
            pass

        if target is None:
            shot = self._screenshot("file-not-found")
            raise TransportError(
                f"فایل «{filename}» در گروه/کانال پیدا نشد. "
                f"اسکرین‌شات: {shot}"
            )

        # 3) click download on that message (or its parent row)
        clicked = False
        for scope in (target, target.locator("xpath=ancestor::*[3]")):
            try:
                dl = scope.locator(SEL_DOWNLOAD)
                if dl.count():
                    with page.expect_download(timeout=60_000) as dl_info:
                        dl.first.click()
                    download = dl_info.value
                    out = dest_dir / (download.suggested_filename or filename)
                    download.save_as(str(out))
                    st(f"دانلود شد: {out.name}")
                    return out
                # maybe whole attachment is clickable and triggers download
                with page.expect_download(timeout=15_000) as dl_info:
                    scope.first.click()
                download = dl_info.value
                out = dest_dir / (download.suggested_filename or filename)
                download.save_as(str(out))
                st(f"دانلود شد: {out.name}")
                return out
            except PWTimeout:
                clicked = False
                continue
            except Exception:
                continue

        # 4) fallback: some UIs download on direct attachment click only
        try:
            with page.expect_download(timeout=30_000) as dl_info:
                target.first.click()
            download = dl_info.value
            out = dest_dir / (download.suggested_filename or filename)
            download.save_as(str(out))
            st(f"دانلود شد: {out.name}")
            return out
        except Exception as e:
            shot = self._screenshot("download-failed")
            raise TransportError(
                f"دانلود فایل ناموفق بود: {e}. اسکرین‌شات: {shot}"
            ) from e

    def upload(
        self,
        file_path: Path,
        on_status: StatusCb | None = None,
    ) -> None:
        def st(m):
            if on_status:
                on_status(m)

        if not file_path.exists():
            raise TransportError(f"فایل برای ارسال پیدا نشد: {file_path}")

        page = self._open_channel(on_status)
        st(f"آپلود: {file_path.name}")

        # most reliable: hidden <input type="file">
        file_inputs = page.locator(SEL_ATTACH_INPUT)
        attached = False
        if file_inputs.count():
            try:
                # input may be hidden; set_input_files works on hidden inputs
                file_inputs.first.set_input_files(str(file_path))
                attached = True
            except Exception:
                attached = False

        if not attached:
            # click attach button, wait for input to appear, then set files
            try:
                btn = page.locator(SEL_ATTACH_BUTTON)
                if btn.count():
                    btn.first.click(timeout=5000)
                    page.wait_for_timeout(800)
                    file_inputs = page.locator(SEL_ATTACH_INPUT)
                    file_inputs.first.wait_for(state="attached", timeout=5000)
                    file_inputs.first.set_input_files(str(file_path))
                    attached = True
            except Exception:
                attached = False

        if not attached:
            shot = self._screenshot("attach-failed")
            raise TransportError(
                f"دکمه/ورودی پیوست فایل پیدا نشد. اسکرین‌شات: {shot}"
            )

        st("ارسال فایل...")
        page.wait_for_timeout(1000)
        # try send button; Enter often works too
        sent = False
        try:
            sb = page.locator(SEL_SEND_BUTTON)
            if sb.count() and sb.first.is_visible():
                sb.first.click()
                sent = True
        except Exception:
            sent = False
        if not sent:
            try:
                page.keyboard.press("Enter")
                sent = True
            except Exception:
                pass
        if not sent:
            shot = self._screenshot("send-failed")
            raise TransportError(f"دکمه ارسال پیدا نشد. اسکرین‌شات: {shot}")

        page.wait_for_timeout(2500)
        st(f"ارسال شد: {file_path.name}")

    def test_connection(self, on_status: StatusCb | None = None) -> bool:
        try:
            page = self._open_channel(on_status)
            return page is not None
        except Exception:
            return False

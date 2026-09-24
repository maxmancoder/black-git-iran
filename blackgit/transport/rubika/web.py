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

# ── selectors (from Rubika Web Angular bundle fa-ir v4.4.34) ───────
SEL_CHAT_LIST = (
    '[rb-chat-item], .chatlist-chat, .chatlist, .chatlist-container, '
    'rb-chats-list, page-chats'
)
SEL_SEARCH_INPUT = (
    '.input-search-input, .input-search input, '
    'input[placeholder="جستجو"], input[placeholder*="جستجو"], '
    'input[placeholder*="Search"]'
)
SEL_ATTACH_INPUT = 'input[type="file"]'
SEL_ATTACH_BUTTON = (
    '[aria-label*="attach" i], [aria-label*="Attach" i], '
    '[aria-label*="فایل"], [title*="attach" i], [title*="فایل"], '
    'button[aria-label*="clip" i], .rbico-attach, .rbico-paperclip'
)
SEL_SEND_BUTTON = (
    '.btn-send, .btn-send-container .btn-icon, '
    'button[aria-label*="send" i], [title*="send" i], [title*="ارسال"]'
)
SEL_MESSAGE_INPUT = (
    'textarea.input-message-input, .input-message-input, '
    'textarea[name="draftMessage"], textarea, [contenteditable="true"]'
)
SEL_DOWNLOAD = (
    'button[aria-label*="download" i], a[download], '
    '[title*="download" i], [title*="دانلود"], .rbico-download'
)
# Exact locale string from assets/locales/fa-ir.json (plain spaces!)
SEL_SAVED_TITLE = "پیام های ذخیره شده"
SEL_SAVED_KEYWORDS = [
    "پیام های ذخیره شده",  # fa-ir: user_name_saved_msgs
    "پیام‌های ذخیره شده",
    "ذخیره شده",
    "Saved Messages",
]
# sidebar chat-list item that holds Saved Messages (CSS-only: no text= mixing)
SEL_SAVED_CHAT_ITEM = (
    f'[rb-chat-item]:has-text("{SEL_SAVED_TITLE}"), '
    f'.chatlist-chat:has-text("{SEL_SAVED_TITLE}"), '
    f'.peer-title:has-text("{SEL_SAVED_TITLE}")'
)
# main-menu entry (rb-app-menu): key user_name_saved_msgs
SEL_MAIN_MENU = (
    '[title="منوی اصلی"], [aria-label="منوی اصلی"], '
    '[title*="منو"], [aria-label*="منو"], .rbico-menu'
)
SEL_MENU_SAVED = (
    '[rb-localize="user_name_saved_msgs"], .btn-menu-item.rbico-saved, '
    '.btn-menu-item:has-text("ذخیره شده")'
)
SEL_JOIN_BUTTON = (
    '.chat-join, button:has-text("عضویت در گروه"), '
    'button:has-text("عضویت در کانال"), button:has-text("پیوستن"), '
    'button:has-text("Join"), [class*="join-btn" i]'
)
# sent-message body / link inside it
SEL_MESSAGE_TEXT = '[rb-message-text], .rb-message-text'
SEL_INVITE_LINK = (
    'a[href*="rubika.ir/joing"], a[rb-abs-link], [rb-abs-link], '
    'a[href*="/joing/"]'
)
# Strong positive: user is inside the messenger (not a login/OTP screen)
SEL_LOGGED_IN = (
    '[rb-chat-item], .chatlist-chat, .chatlist-container, '
    'rb-chats-list, page-chats, .input-message-input, '
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

    def _on_login_wall(self, page: Page) -> bool:
        """True only if a real login/OTP form is visible on screen."""
        if not self._page_alive(page):
            return False
        try:
            wall = page.locator(SEL_LOGIN_FORM)
            for i in range(min(wall.count(), 12)):
                try:
                    if wall.nth(i).is_visible():
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        try:
            url = (page.url or "").lower()
            if any(x in url for x in ("/login", "signin", "sign-in", "/auth", "otp")):
                return True
        except Exception:
            pass
        return False

    def login(self, on_status: StatusCb | None = None) -> None:
        """Manual login flow — ONLY this waits for the user (OTP etc.).

        Operations (upload/download) never wait; they fail fast instead.
        """
        def st(m):
            if on_status:
                on_status(m)

        st("باز کردن صفحه ورود Rubika...")
        page = self._start(on_status)
        deadline = time.time() + 600  # 10 min, only for this button
        last_msg = ""
        while time.time() < deadline:
            if not self._page_alive(page):
                shot = self._screenshot("browser-closed")
                raise NotLoggedInError(
                    f"پنجره مرورگر بسته شد. دوباره تلاش کنید. اسکرین‌شات: {shot}"
                )
            if self._is_logged_in(page):
                st("ورود تأیید شد — آماده‌سازی...")
                page.wait_for_timeout(1200)
                if self._is_logged_in(page):
                    st("ورود موفق — نشست ذخیره شد")
                    return
            remaining = max(0, int(deadline - time.time()))
            msg = f"در مرورگر وارد Rubika شوید (شماره + کد تایید)... {remaining}s"
            if msg != last_msg:
                st(msg)
                last_msg = msg
            time.sleep(2)

        shot = self._screenshot("login-timeout")
        raise NotLoggedInError(
            f"ورود کامل نشد (مهلت ۱۰ دقیقه). اسکرین‌شات: {shot}"
        )

    def _require_session(self, page: Page, on_status: StatusCb | None = None) -> None:
        """Fail FAST if not logged in — never wait for OTP during operations."""
        if self._on_login_wall(page):
            shot = self._screenshot("not-logged-in")
            raise NotLoggedInError(
                "نشست Rubika معتبر نیست و صفحه ورود باز شد.\n"
                "برای ورود یک‌باره: دکمه «ورود به Rubika» را بزنید و کد تایید را وارد کنید.\n"
                "بعد از آن، ارسال/دریافت بدون انتظار اجرا می‌شود.\n"
                f"اسکرین‌شات: {shot}"
            )

    # ── enter group via Saved Messages (send link -> click link) ────
    def _composer_visible(self, page: Page) -> bool:
        """True when the message composer of an OPEN chat is on screen."""
        try:
            loc = page.locator(SEL_MESSAGE_INPUT)
            for i in range(min(loc.count(), 6)):
                try:
                    if loc.nth(i).is_visible(timeout=800):
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    def _try_click_saved(self, page: Page, sel: str) -> bool:
        """Click `sel` (Saved Messages entry); True if chat composer opened."""
        try:
            loc = page.locator(sel)
            if not loc.count():
                return False
            for i in range(min(loc.count(), 6)):
                el = loc.nth(i)
                try:
                    if not el.is_visible(timeout=800):
                        continue
                    el.click(timeout=4000)
                    page.wait_for_timeout(1500)
                    if self._composer_visible(page):
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    def _open_saved_messages(self, page: Page, on_status: StatusCb | None = None) -> None:
        """Open the «پیام های ذخیره شده» chat.

        Strategies (in order):
          1) click it in the sidebar chat list
          2) type «ذخیره» in sidebar search and pick the result
          3) main menu (منوی اصلی) -> Saved Messages entry
        """
        def st(m):
            if on_status:
                on_status(m)

        st("باز کردن پیام های ذخیره شده...")

        # 1) direct hit in the chat list
        for sel in (
            SEL_SAVED_CHAT_ITEM,
            f'[rb-chat-item]:has(.rbico-saved)',
            f'.chatlist-chat:has(.rbico-saved)',
        ):
            if self._try_click_saved(page, sel):
                st("پیام های ذخیره شده باز شد")
                return

        # 2) sidebar search: «ذخیره»
        try:
            self._open_search(page)
            page.keyboard.type("ذخیره", delay=50)
            page.wait_for_timeout(2000)
            for kw in SEL_SAVED_KEYWORDS:
                if self._try_click_saved(page, f'text={kw}'):
                    st("پیام های ذخیره شده باز شد (از جستجو)")
                    return
        except Exception:
            pass

        # 3) main menu -> saved entry
        try:
            menu = page.locator(SEL_MAIN_MENU)
            for i in range(min(menu.count(), 6)):
                try:
                    if menu.nth(i).is_visible(timeout=800):
                        menu.nth(i).click(timeout=3000)
                        page.wait_for_timeout(800)
                        break
                except Exception:
                    continue
            if self._try_click_saved(page, SEL_MENU_SAVED):
                st("پیام های ذخیره شده باز شد (از منو)")
                return
        except Exception:
            pass

        shot = self._screenshot("saved-not-found")
        raise TransportError(
            "چت «پیام های ذخیره شده» پیدا نشد. "
            f"سلکتورها را بررسی کنید. اسکرین‌شات: {shot}"
        )

    def _compose_and_send(self, page: Page, text: str) -> None:
        """Type `text` into the open chat composer and send it."""
        box = page.locator(SEL_MESSAGE_INPUT)
        if not box.count():
            raise TransportError(
                "جعبه نوشتن پیام پیدا نشد — سلکتور SEL_MESSAGE_INPUT را به‌روز کنید"
            )
        box.first.click(timeout=5000)
        page.wait_for_timeout(300)
        # clear composer (works for textarea and contenteditable)
        page.keyboard.press("Control+A")
        page.keyboard.press("Delete")
        page.keyboard.type(text, delay=12)
        page.wait_for_timeout(400)
        sent = False
        try:
            sb = page.locator(SEL_SEND_BUTTON)
            if sb.count() and sb.first.is_visible():
                sb.first.click()
                sent = True
        except Exception:
            sent = False
        if not sent:
            page.keyboard.press("Enter")
        page.wait_for_timeout(1500)

    def _click_sent_link(self, page: Page, url: str) -> None:
        """Click the link we just sent in Saved Messages to enter the group."""
        # prefer invite anchors / message-body links, last message first
        selectors = [
            f'a[href*="rubika.ir/joing"]',
            f'a[href*="/joing/"]',
            f'{SEL_MESSAGE_TEXT} a[href="{url}"]',
            f'a[href="{url}"]',
            f'a[href*="{url}"]',
            f'{SEL_MESSAGE_TEXT}:has-text("{url}")',
            f'a:has-text("{url}")',
            f'text={url}',
        ]
        target = None
        for sel in selectors:
            try:
                loc = page.locator(sel)
                if loc.count():
                    target = loc.last
                    target.scroll_into_view_if_needed(timeout=4000)
                    break
            except Exception:
                continue
        if target is None:
            shot = self._screenshot("link-not-clicked")
            raise TransportError(
                f"لینک ارسال‌شده در چت پیدا نشد. اسکرین‌شات: {shot}"
            )
        try:
            target.click(timeout=6000)
        except Exception:
            # some UIs need force click on the message bubble
            target.click(timeout=6000, force=True)
        page.wait_for_timeout(2500)

    def _join_if_prompt(self, page: Page, on_status: StatusCb | None = None) -> None:
        """If Rubika shows a Join confirmation, click it."""
        try:
            btn = page.locator(SEL_JOIN_BUTTON)
            for i in range(min(btn.count(), 4)):
                try:
                    if btn.nth(i).is_visible(timeout=1500):
                        if on_status:
                            on_status("تأیید عضویت در گروه/کانال...")
                        btn.nth(i).click(timeout=4000)
                        page.wait_for_timeout(1500)
                        return
                except Exception:
                    continue
        except Exception:
            pass

    def _open_group(self, page: Page, on_status: StatusCb | None = None) -> None:
        """Enter the group/channel the new way:

        Saved Messages -> type group link -> send -> click the sent link.
        Direct goto is only a fallback if this flow fails.
        """
        def st(m):
            if on_status:
                on_status(m)

        if not self.group_url:
            raise TransportError("لینک گروه/کانال در تنظیمات خالی است")

        try:
            self._open_saved_messages(page, on_status)
            st(f"ارسال لینک: {self.group_url}")
            self._compose_and_send(page, self.group_url)
            st("کلیک روی لینک و ورود به گروه/کانال...")
            self._click_sent_link(page, self.group_url)
            self._join_if_prompt(page, on_status)
            st("وارد گروه/کانال شد")
        except NotLoggedInError:
            raise
        except Exception as e:
            # fallback: direct navigation (legacy path)
            st(f"روش پیام ذخیره ممکن نشد ({e}) — تلاش مستقیم...")
            shot = self._screenshot("saved-fallback")
            try:
                page.goto(self.group_url, wait_until="domcontentloaded", timeout=30_000)
            except PWTimeout:
                pass
            if shot:
                st("از روش مستقیم استفاده شد")

        time.sleep(2)
        # bounced to login? fail immediately — do NOT wait for OTP
        self._require_session(page, on_status)

    def _open_channel(self, on_status: StatusCb | None = None) -> Page:
        """Open browser and enter the group via Saved Messages link flow.

        No login waiting: if the session is dead, raise immediately.
        """
        page = self._start(on_status)
        self._require_session(page, on_status)
        self._open_group(page, on_status)
        return page

    # ── search helper ──────────────────────────────────────────────
    def _open_search(self, page: Page) -> None:
        # try visible search input; otherwise click a search icon first
        box = page.locator(SEL_SEARCH_INPUT)
        if box.count() == 0 or not box.first.is_visible():
            icon = page.locator(
                '[aria-label*="search" i], [title*="search" i], '
                '[aria-label*="جستجو"], .rbico-search, .icon-search, '
                'button:has(svg)'
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

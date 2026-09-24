"""Background worker + status polling for tkinter (thread-safe).

The app's main loop calls poll() periodically; this class never schedules
its own `after` callbacks. `log_hook` is invoked for every status message
even while a dialog has bound its own handlers.
"""

import queue
import threading
import traceback
from typing import Any, Callable


class Worker:
    def __init__(self, poll_ms: int = 100):
        self.queue: queue.Queue = queue.Queue()
        self.poll_ms = poll_ms
        self.log_hook: Callable[[str, str], None] | None = None  # (level, msg)
        self._thread: threading.Thread | None = None
        self._active = False
        self._finish_notified = True
        self._on_result: Callable[[Any], None] | None = None
        self._on_status: Callable[[str], None] | None = None
        self._on_error: Callable[[str], None] | None = None
        self._on_finished: Callable[[], None] | None = None

    @property
    def busy(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def bind(
        self,
        on_result: Callable[[Any], None] | None = None,
        on_status: Callable[[str], None] | None = None,
        on_error: Callable[[str], None] | None = None,
        on_finished: Callable[[], None] | None = None,
    ) -> None:
        self._on_result = on_result
        self._on_status = on_status
        self._on_error = on_error
        self._on_finished = on_finished

    def status(self, msg: str) -> None:
        """Call from worker thread."""
        self.queue.put(("status", msg))

    def start(self, fn: Callable[[Callable[[str], None]], Any]) -> bool:
        if self.busy or self._active:
            return False

        def runner():
            try:
                result = fn(self.status)
                self.queue.put(("result", result))
            except Exception as e:
                tb = traceback.format_exc()
                self.queue.put(("error", f"{e}\n{tb}"))

        self._active = True
        self._finish_notified = False
        self._thread = threading.Thread(target=runner, daemon=True)
        self._thread.start()
        return True

    def _emit(self, kind: str, payload: Any) -> None:
        if kind == "status":
            if self.log_hook:
                try:
                    self.log_hook("info", payload)
                except Exception:
                    pass
            if self._on_status:
                self._on_status(payload)
        elif kind == "result":
            if self.log_hook:
                try:
                    self.log_hook("ok", "عملیات با موفقیت انجام شد")
                except Exception:
                    pass
            if self._on_result:
                self._on_result(payload)
        elif kind == "error":
            first = str(payload).splitlines()[0] if payload else "خطا"
            if self.log_hook:
                try:
                    self.log_hook("err", first)
                except Exception:
                    pass
            if self._on_error:
                self._on_error(payload)

    def poll(self, widget=None) -> None:
        while True:
            try:
                kind, payload = self.queue.get_nowait()
            except queue.Empty:
                break
            self._emit(kind, payload)

        if self._active and not self.busy:
            self._active = False
            if not self._finish_notified:
                self._finish_notified = True
                if self._on_finished:
                    self._on_finished()

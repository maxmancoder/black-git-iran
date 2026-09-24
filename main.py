"""Black Git Iran — entry point."""

import sys
import traceback


def main() -> int:
    try:
        from blackgit.ui import run_app

        run_app()
        return 0
    except Exception:
        traceback.print_exc()
        try:
            from tkinter import messagebox
            import tkinter as tk

            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Black Git Iran",
                "خطای راه‌اندازی:\n\n" + traceback.format_exc(limit=3),
            )
            root.destroy()
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())

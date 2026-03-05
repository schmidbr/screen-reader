from __future__ import annotations

import ctypes
import tkinter as tk
from typing import Tuple

from snap_narrate.capture import Bounds, normalize_bounds


SM_XVIRTUALSCREEN = 76
SM_YVIRTUALSCREEN = 77
SM_CXVIRTUALSCREEN = 78
SM_CYVIRTUALSCREEN = 79


def virtual_screen_bounds() -> Tuple[int, int, int, int]:
    user32 = ctypes.windll.user32
    x = int(user32.GetSystemMetrics(SM_XVIRTUALSCREEN))
    y = int(user32.GetSystemMetrics(SM_YVIRTUALSCREEN))
    w = int(user32.GetSystemMetrics(SM_CXVIRTUALSCREEN))
    h = int(user32.GetSystemMetrics(SM_CYVIRTUALSCREEN))
    return x, y, w, h


def select_region_bounds() -> Bounds | None:
    left, top, width, height = virtual_screen_bounds()
    result: dict[str, Bounds | None] = {"bounds": None}

    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.attributes("-alpha", 0.2)
    root.configure(bg="black")
    root.geometry(f"{width}x{height}+{left}+{top}")
    root.lift()
    root.focus_force()

    canvas = tk.Canvas(root, cursor="cross", bg="black", highlightthickness=0)
    canvas.pack(fill=tk.BOTH, expand=True)

    start: dict[str, int] = {"x": 0, "y": 0}
    rect = {"id": None}

    def on_press(event: tk.Event) -> None:
        start["x"] = int(event.x_root)
        start["y"] = int(event.y_root)
        if rect["id"] is not None:
            canvas.delete(rect["id"])
        rect["id"] = canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="#2fd4ff", width=2)

    def on_move(event: tk.Event) -> None:
        if rect["id"] is None:
            return
        x0 = start["x"] - left
        y0 = start["y"] - top
        x1 = int(event.x_root) - left
        y1 = int(event.y_root) - top
        canvas.coords(rect["id"], x0, y0, x1, y1)

    def on_release(event: tk.Event) -> None:
        end_x = int(event.x_root)
        end_y = int(event.y_root)
        result["bounds"] = normalize_bounds(start["x"] - left, start["y"] - top, end_x - left, end_y - top)
        root.quit()

    def on_escape(event: tk.Event) -> None:  # noqa: ARG001
        result["bounds"] = None
        root.quit()

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_move)
    canvas.bind("<ButtonRelease-1>", on_release)
    root.bind("<Escape>", on_escape)

    try:
        root.mainloop()
    finally:
        root.destroy()

    return result["bounds"]

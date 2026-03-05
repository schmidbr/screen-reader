from __future__ import annotations

import io
import time
from pathlib import Path
from typing import Tuple

from mss import mss
from PIL import Image


Bounds = Tuple[int, int, int, int]


class ScreenCapturer:
    def __init__(self, cooldown_ms: int, save_debug: bool = False, debug_dir: str = "debug_screenshots") -> None:
        self.cooldown_ms = cooldown_ms
        self.save_debug = save_debug
        self.debug_dir = Path(debug_dir)
        self._last_capture_ms = 0

    def can_capture(self) -> bool:
        now_ms = int(time.time() * 1000)
        return (now_ms - self._last_capture_ms) >= self.cooldown_ms

    def capture_png(self) -> bytes:
        return self.capture_fullscreen_png()

    def capture_fullscreen_png(self) -> bytes:
        if not self.can_capture():
            raise RuntimeError("Capture cooldown active")

        with mss() as sct:
            monitor = sct.monitors[1]
            image_bytes = self._capture_monitor_png(sct, monitor)

        self._after_capture(image_bytes)
        return image_bytes

    def capture_region_png(self, bounds: Bounds) -> bytes:
        if not self.can_capture():
            raise RuntimeError("Capture cooldown active")
        x, y, width, height = bounds
        if width <= 0 or height <= 0:
            raise RuntimeError("Invalid capture region")

        with mss() as sct:
            virtual = sct.monitors[0]
            left = int(virtual["left"]) + int(x)
            top = int(virtual["top"]) + int(y)
            monitor = {"left": left, "top": top, "width": int(width), "height": int(height)}
            image_bytes = self._capture_monitor_png(sct, monitor)

        self._after_capture(image_bytes)
        return image_bytes

    def _capture_monitor_png(self, sct: mss, monitor: dict) -> bytes:
        shot = sct.grab(monitor)
        image = Image.frombytes("RGB", shot.size, shot.rgb)
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()

    def _after_capture(self, image_bytes: bytes) -> None:
        self._last_capture_ms = int(time.time() * 1000)
        if self.save_debug:
            self.debug_dir.mkdir(parents=True, exist_ok=True)
            timestamp = int(time.time())
            (self.debug_dir / f"capture_{timestamp}.png").write_bytes(image_bytes)


def normalize_bounds(x1: int, y1: int, x2: int, y2: int) -> Bounds:
    left = min(int(x1), int(x2))
    top = min(int(y1), int(y2))
    width = abs(int(x2) - int(x1))
    height = abs(int(y2) - int(y1))
    return left, top, width, height


def is_valid_bounds(bounds: Bounds | None, min_region_px: int) -> bool:
    if bounds is None:
        return False
    _, _, width, height = bounds
    return int(width) >= int(min_region_px) and int(height) >= int(min_region_px)

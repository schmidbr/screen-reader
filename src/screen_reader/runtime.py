from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from pathlib import Path

import keyboard
import pystray
from PIL import Image, ImageDraw
from pystray import Menu, MenuItem

from screen_reader.capture import ScreenCapturer
from screen_reader.pipeline import NarrationPipeline


@dataclass
class RuntimeState:
    paused: bool = False


class ScreenReaderRuntime:
    def __init__(
        self,
        capturer: ScreenCapturer,
        pipeline: NarrationPipeline,
        hotkey: str,
        stop_hotkey: str,
        log_path: Path,
        game_profile: str = "default",
    ) -> None:
        self.capturer = capturer
        self.pipeline = pipeline
        self.hotkey = hotkey
        self.stop_hotkey = stop_hotkey
        self.log_path = log_path
        self.game_profile = game_profile

        self.state = RuntimeState(paused=False)
        self.logger = logging.getLogger("screen_reader")

        self._running = threading.Event()
        self._running.set()
        self._work_event = threading.Event()
        self._lock = threading.Lock()
        self._pending_capture: bytes | None = None
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._icon: pystray.Icon | None = None
        self._capture_hotkey_ok = False
        self._stop_hotkey_ok = False

    def start(self) -> None:
        self._worker.start()
        self._register_hotkeys()
        self._icon = pystray.Icon("ScreenReader", self._make_icon(), "Screen Reader", self._tray_menu())
        self._icon.run_detached()

        self.logger.info(
            "event=runtime_started hotkey=%s stop_hotkey=%s hotkey_ok=%s stop_hotkey_ok=%s",
            self.hotkey,
            self.stop_hotkey,
            self._capture_hotkey_ok,
            self._stop_hotkey_ok,
        )
        print(
            f"Screen Reader running. Capture: {self.hotkey}. Stop speaking: {self.stop_hotkey}. "
            "Use tray icon to pause or exit."
        )

        try:
            while self._running.is_set():
                time.sleep(0.2)
        except KeyboardInterrupt:
            self.stop()

    def stop(self) -> None:
        self._running.clear()
        self._work_event.set()
        keyboard.clear_all_hotkeys()
        if self._icon:
            self._icon.stop()
        self.logger.info("event=runtime_stopped")

    def test_voice(self) -> None:
        dummy = b"dummy"
        result = self.pipeline.process_capture(dummy, self.game_profile)
        self._notify(f"Test voice: {result.message}")

    def _on_hotkey(self) -> None:
        self.logger.info("event=capture_hotkey_pressed paused=%s", self.state.paused)
        if self.state.paused:
            self.logger.info("event=capture_ignored reason=paused")
            return

        try:
            image_bytes = self.capturer.capture_png()
        except Exception as exc:  # noqa: BLE001
            self.logger.warning("event=capture_failed error=%s", exc)
            self._notify(f"Capture failed: {exc}")
            return

        with self._lock:
            self._pending_capture = image_bytes
            self._work_event.set()
        self.logger.info("event=capture_enqueued bytes=%s", len(image_bytes))

    def _worker_loop(self) -> None:
        while self._running.is_set():
            self._work_event.wait()
            self._work_event.clear()
            if not self._running.is_set():
                break

            with self._lock:
                capture = self._pending_capture
                self._pending_capture = None

            if not capture:
                continue

            result = self.pipeline.process_capture(capture, self.game_profile)
            self.logger.info("event=pipeline_result status=%s message=%s chars=%s", result.status, result.message, result.chars)
            if result.status != "played":
                self._notify(result.message)

    def _tray_menu(self) -> Menu:
        return Menu(
            MenuItem(lambda _: "Resume" if self.state.paused else "Pause", self._toggle_pause),
            MenuItem("Capture Now", self._tray_capture_now),
            MenuItem("Test Voice", self._tray_test_voice),
            MenuItem("Stop Speaking", self._tray_stop_speaking),
            MenuItem("Show Hotkeys", self._tray_show_hotkeys),
            MenuItem("Open Logs", self._open_logs),
            MenuItem("Exit", self._tray_exit),
        )

    def _tray_capture_now(self, icon: pystray.Icon, item: MenuItem) -> None:  # noqa: ARG002
        self._on_hotkey()

    def _tray_test_voice(self, icon: pystray.Icon, item: MenuItem) -> None:  # noqa: ARG002
        try:
            test_tone = self.pipeline.tts.synthesize("Screen Reader voice test.")
            self.pipeline.player.play(test_tone)
            self._notify("Voice test played")
        except Exception as exc:  # noqa: BLE001
            self.logger.warning("event=voice_test_failed error=%s", exc)
            self._notify(f"Voice test failed: {exc}")

    def _toggle_pause(self, icon: pystray.Icon, item: MenuItem) -> None:  # noqa: ARG002
        self.state.paused = not self.state.paused
        self.logger.info("event=pause_toggled paused=%s", self.state.paused)
        self._notify("Paused" if self.state.paused else "Resumed")

    def _on_stop_hotkey(self) -> None:
        self.logger.info("event=stop_hotkey_pressed")
        self._stop_speaking()

    def _tray_stop_speaking(self, icon: pystray.Icon, item: MenuItem) -> None:  # noqa: ARG002
        self._stop_speaking()

    def _stop_speaking(self) -> None:
        stop_fn = getattr(self.pipeline.player, "stop", None)
        if not callable(stop_fn):
            self._notify("Stop not supported by current audio player")
            return
        try:
            stop_fn()
            self.logger.info("event=playback_stopped")
            self._notify("Stopped speaking")
        except Exception as exc:  # noqa: BLE001
            self.logger.warning("event=playback_stop_failed error=%s", exc)
            self._notify(f"Stop failed: {exc}")

    def _open_logs(self, icon: pystray.Icon, item: MenuItem) -> None:  # noqa: ARG002
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.log_path.exists():
            self.log_path.write_text("", encoding="utf-8")
        import os

        os.startfile(str(self.log_path))

    def _tray_exit(self, icon: pystray.Icon, item: MenuItem) -> None:  # noqa: ARG002
        self.stop()

    def _notify(self, message: str) -> None:
        if self._icon:
            try:
                self._icon.notify(message, "Screen Reader")
            except Exception:  # noqa: BLE001
                pass

    def _tray_show_hotkeys(self, icon: pystray.Icon, item: MenuItem) -> None:  # noqa: ARG002
        msg = (
            f"Capture: {self.hotkey} ({'OK' if self._capture_hotkey_ok else 'FAILED'})\n"
            f"Stop: {self.stop_hotkey} ({'OK' if self._stop_hotkey_ok else 'FAILED'})"
        )
        self._notify(msg)

    def _register_hotkeys(self) -> None:
        self._capture_hotkey_ok = False
        self._stop_hotkey_ok = False

        try:
            keyboard.add_hotkey(self.hotkey, self._on_hotkey)
            self._capture_hotkey_ok = True
        except Exception as exc:  # noqa: BLE001
            self.logger.warning("event=hotkey_register_failed kind=capture hotkey=%s error=%s", self.hotkey, exc)
            self._notify(f"Capture hotkey failed: {self.hotkey}")

        try:
            keyboard.add_hotkey(self.stop_hotkey, self._on_stop_hotkey)
            self._stop_hotkey_ok = True
        except Exception as exc:  # noqa: BLE001
            self.logger.warning("event=hotkey_register_failed kind=stop hotkey=%s error=%s", self.stop_hotkey, exc)
            self._notify(f"Stop hotkey failed: {self.stop_hotkey}")

    @staticmethod
    def _make_icon() -> Image.Image:
        image = Image.new("RGB", (64, 64), color=(35, 50, 70))
        draw = ImageDraw.Draw(image)
        draw.rectangle((16, 16, 48, 48), fill=(220, 220, 220))
        draw.rectangle((22, 22, 42, 42), fill=(70, 120, 180))
        return image

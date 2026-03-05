from __future__ import annotations

from pathlib import Path

from snap_narrate.runtime import SnapNarrateRuntime


class _DummyPipeline:
    pass


class _DummyCapturer:
    def capture_fullscreen_png(self) -> bytes:
        return b"full"

    def capture_region_png(self, bounds) -> bytes:  # noqa: ANN001
        return b"region"


def _runtime(region_selector):
    return SnapNarrateRuntime(
        capturer=_DummyCapturer(),  # type: ignore[arg-type]
        pipeline=_DummyPipeline(),  # type: ignore[arg-type]
        hotkey="ctrl+shift+n",
        region_hotkey="ctrl+shift+r",
        stop_hotkey="ctrl+shift+s",
        capture_mode="fullscreen",
        min_region_px=64,
        log_path=Path("logs/test.log"),
        region_selector=region_selector,
    )


def test_runtime_registers_region_hotkey(monkeypatch) -> None:
    calls = []

    def fake_add_hotkey(combo, cb):  # noqa: ANN001
        calls.append(combo)
        return None

    monkeypatch.setattr("keyboard.add_hotkey", fake_add_hotkey)
    rt = _runtime(lambda: None)
    rt._register_hotkeys()
    assert "ctrl+shift+n" in calls
    assert "ctrl+shift+r" in calls
    assert "ctrl+shift+s" in calls


def test_region_capture_cancelled_does_not_enqueue() -> None:
    rt = _runtime(lambda: None)
    rt._capture_region_once()
    assert rt._pending_capture is None


def test_region_capture_valid_enqueues() -> None:
    rt = _runtime(lambda: (10, 10, 200, 120))
    rt._capture_region_once()
    assert rt._pending_capture == b"region"
    assert rt._work_event.is_set()

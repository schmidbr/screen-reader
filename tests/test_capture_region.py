from __future__ import annotations

import io

from PIL import Image

from snap_narrate.capture import ScreenCapturer, is_valid_bounds, normalize_bounds


def test_normalize_bounds_supports_negative_coords() -> None:
    bounds = normalize_bounds(-200, 50, -20, 170)
    assert bounds == (-200, 50, 180, 120)


def test_is_valid_bounds_rejects_tiny_or_none() -> None:
    assert is_valid_bounds(None, 64) is False
    assert is_valid_bounds((10, 10, 20, 20), 64) is False
    assert is_valid_bounds((10, 10, 64, 63), 64) is False
    assert is_valid_bounds((10, 10, 64, 64), 64) is True


def test_prepare_image_downscales_large_capture() -> None:
    capturer = ScreenCapturer(cooldown_ms=0, max_dimension=1200)
    image = Image.new("RGB", (2400, 1200), "white")

    prepared = capturer._prepare_image(image)

    assert prepared.size == (1200, 600)


def test_capture_monitor_uses_jpeg_encoding_and_resize() -> None:
    class FakeShot:
        size = (200, 100)
        rgb = b"\x80" * (200 * 100 * 3)

    class FakeMSS:
        def grab(self, monitor):  # noqa: ANN001
            return FakeShot()

    capturer = ScreenCapturer(cooldown_ms=0, max_dimension=100, image_format="jpeg", jpeg_quality=70)

    payload = capturer._capture_monitor_png(FakeMSS(), {"left": 0, "top": 0, "width": 200, "height": 100})
    decoded = Image.open(io.BytesIO(payload))

    assert decoded.format == "JPEG"
    assert decoded.size == (100, 50)

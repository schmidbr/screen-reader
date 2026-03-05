from __future__ import annotations

from snap_narrate.capture import is_valid_bounds, normalize_bounds


def test_normalize_bounds_supports_negative_coords() -> None:
    bounds = normalize_bounds(-200, 50, -20, 170)
    assert bounds == (-200, 50, 180, 120)


def test_is_valid_bounds_rejects_tiny_or_none() -> None:
    assert is_valid_bounds(None, 64) is False
    assert is_valid_bounds((10, 10, 20, 20), 64) is False
    assert is_valid_bounds((10, 10, 64, 63), 64) is False
    assert is_valid_bounds((10, 10, 64, 64), 64) is True

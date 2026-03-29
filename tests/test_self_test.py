from __future__ import annotations

import io

from PIL import Image

from snap_narrate.self_test import SELF_TEST_TITLE, create_self_test_image_bytes


def test_create_self_test_image_bytes_png() -> None:
    payload = create_self_test_image_bytes(max_dimension=1000, image_format="png")
    image = Image.open(io.BytesIO(payload))

    assert image.format == "PNG"
    assert image.size[0] == 1000


def test_create_self_test_image_bytes_jpeg() -> None:
    payload = create_self_test_image_bytes(max_dimension=900, image_format="jpeg", jpeg_quality=75)
    image = Image.open(io.BytesIO(payload))

    assert image.format == "JPEG"
    assert image.size[0] == 900
    assert SELF_TEST_TITLE

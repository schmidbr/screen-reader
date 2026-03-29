from __future__ import annotations

from snap_narrate.models import ExtractResult
from snap_narrate.openai_client import (
    build_extraction_prompt,
    build_initial_extraction_prompt,
    build_paragraph_collection_prompt,
    infer_image_media_type,
    is_likely_truncated,
    merge_text_blocks,
    parse_paragraph_collection_payload,
    parse_extraction_payload,
)


def test_parse_extraction_payload_json() -> None:
    result = parse_extraction_payload(
        '{"text":"Hello there","confidence":0.88,"dropped_reason":null,"more_text_likely":true}'
    )
    assert result.text == "Hello there"
    assert result.confidence == 0.88
    assert result.dropped_reason is None
    assert result.more_text_likely is True


def test_parse_extraction_payload_noisy_wrapper() -> None:
    raw = (
        "Model output:\n```json\n"
        "{\"text\":\"Story block\",\"confidence\":0.72,\"dropped_reason\":null,\"more_text_likely\":\"false\"}\n```"
    )
    result = parse_extraction_payload(raw)
    assert result.text == "Story block"
    assert result.confidence == 0.72
    assert result.more_text_likely is False


def test_parse_extraction_payload_malformed() -> None:
    result = parse_extraction_payload("not-json-at-all")
    assert result.text == ""
    assert result.dropped_reason == "malformed_json"


def test_prompt_requires_all_paragraphs() -> None:
    prompt = build_extraction_prompt(4, "default")
    assert "Return all visible narrative paragraphs" in prompt
    assert "Do not stop after the first paragraph" in prompt


def test_fast_prompt_includes_speed_hint() -> None:
    prompt = build_extraction_prompt(4, "default", fast_mode=True)
    assert "Prioritize speed over completeness" in prompt


def test_initial_prompt_targets_first_paragraph() -> None:
    prompt = build_initial_extraction_prompt(4, "default", ultra_fast_mode=True)
    assert "first long-form narrative paragraph" in prompt
    assert "Return quickly" in prompt
    assert "more_text_likely" in prompt


def test_infer_image_media_type_detects_jpeg() -> None:
    assert infer_image_media_type(b"\xff\xd8\xff\xe0rest") == "image/jpeg"
    assert infer_image_media_type(b"\x89PNG\r\n\x1a\nrest") == "image/png"


def test_truncation_detection_by_done_reason() -> None:
    result = ExtractResult(text="Some text", confidence=0.8, dropped_reason=None)
    assert is_likely_truncated("{}", result, {"done_reason": "length"}) is True


def test_merge_text_blocks_avoids_overlap_duplication() -> None:
    base = "First paragraph.\n\nSecond paragraph starts here and continues"
    continuation = "Second paragraph starts here and continues to the end."
    merged = merge_text_blocks(base, continuation)
    assert merged.count("Second paragraph starts here") == 1


def test_parse_paragraph_collection_payload_valid() -> None:
    raw = (
        '{"paragraphs":[{"index":0,"text":"P1","confidence":0.9},{"index":1,"text":"P2","confidence":0.8}],'
        '"dropped_reason":null}'
    )
    paragraphs, dropped = parse_paragraph_collection_payload(raw)
    assert len(paragraphs) == 2
    assert paragraphs[0]["text"] == "P1"
    assert dropped is None


def test_paragraph_collection_prompt_requires_ordering() -> None:
    prompt = build_paragraph_collection_prompt(4, "default", strict=True)
    assert "ordered top-to-bottom and left-to-right" in prompt
    assert "Include every visible narrative paragraph" in prompt


from __future__ import annotations

from screen_reader.openai_client import parse_extraction_payload


def test_parse_extraction_payload_json() -> None:
    result = parse_extraction_payload('{"text":"Hello there","confidence":0.88,"dropped_reason":null}')
    assert result.text == "Hello there"
    assert result.confidence == 0.88
    assert result.dropped_reason is None


def test_parse_extraction_payload_noisy_wrapper() -> None:
    raw = "Model output:\n```json\n{\"text\":\"Story block\",\"confidence\":0.72,\"dropped_reason\":null}\n```"
    result = parse_extraction_payload(raw)
    assert result.text == "Story block"
    assert result.confidence == 0.72


def test_parse_extraction_payload_malformed() -> None:
    result = parse_extraction_payload("not-json-at-all")
    assert result.text == ""
    assert result.dropped_reason == "malformed_json"

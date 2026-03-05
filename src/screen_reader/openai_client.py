from __future__ import annotations

import json
import logging
import re
from typing import Any

from screen_reader.models import ExtractResult


def parse_extraction_payload(raw_content: str) -> ExtractResult:
    content = raw_content.strip()
    if not content:
        return ExtractResult(text="", confidence=0.0, dropped_reason="empty_response")

    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", content)
        if not match:
            return ExtractResult(text="", confidence=0.0, dropped_reason="malformed_json")
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            return ExtractResult(text="", confidence=0.0, dropped_reason="malformed_json")

    text = str(parsed.get("text", "")).strip()
    confidence = parsed.get("confidence", 0.0)
    dropped_reason = parsed.get("dropped_reason")

    try:
        confidence_val = float(confidence)
    except (TypeError, ValueError):
        confidence_val = 0.0

    if dropped_reason is not None:
        dropped_reason = str(dropped_reason)

    return ExtractResult(text=text, confidence=confidence_val, dropped_reason=dropped_reason)


class OpenAIVisionExtractor:
    def __init__(self, api_key: str, model: str, ignore_short_lines: int, timeout_sec: int = 60) -> None:
        self.api_key = api_key
        self.model = model
        self.ignore_short_lines = ignore_short_lines
        self.timeout_sec = timeout_sec

    def extract_narrative_text(self, image_bytes: bytes, game_profile: str = "default") -> ExtractResult:
        import base64

        import requests

        if not self.api_key:
            raise ValueError("OpenAI API key is missing")

        prompt = (
            "You are a strict OCR filter for games. Read the screenshot and return only long-form narrative text "
            "(dialogue, lore, quest narrative, books/journals). Exclude menus, HUD labels, minimap text, button "
            "hints, health/ammo counters, and short subtitles. Keep verbatim wording."
            f" Ignore lines with fewer than {self.ignore_short_lines} words unless they are part of a larger paragraph. "
            "Return JSON exactly with keys: text (string), confidence (number 0-1), dropped_reason (string or null)."
        )

        image_b64 = base64.b64encode(image_bytes).decode("ascii")

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You output strict JSON only.",
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt + f" Profile: {game_profile}."},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                        },
                    ],
                },
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=self.timeout_sec,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"OpenAI extraction failed ({response.status_code}): {response.text[:200]}")

        data = response.json()
        raw_content = data["choices"][0]["message"]["content"]
        result = parse_extraction_payload(raw_content)
        logging.getLogger("screen_reader").info(
            "event=extract_result chars=%s confidence=%.2f dropped_reason=%s",
            len(result.text),
            result.confidence,
            result.dropped_reason,
        )
        return result

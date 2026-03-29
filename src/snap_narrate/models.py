from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ExtractResult:
    text: str
    confidence: float
    dropped_reason: Optional[str] = None
    more_text_likely: Optional[bool] = None


@dataclass
class PipelineTimings:
    extract_ms: int = 0
    tts_ms: int = 0
    playback_ms: int = 0
    total_ms: int = 0


@dataclass
class PipelineResult:
    status: str
    message: str
    chars: int = 0
    timings: Optional[PipelineTimings] = None

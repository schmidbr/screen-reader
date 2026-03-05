from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = Path("config.toml")


@dataclass
class OpenAIConfig:
    api_key: str = ""
    model: str = "gpt-4.1-mini"


@dataclass
class ElevenLabsConfig:
    api_key: str = ""
    voice_id: str = ""
    model_id: str = "eleven_turbo_v2_5"
    output_format: str = "mp3_44100_128"


@dataclass
class CaptureConfig:
    hotkey: str = "ctrl+shift+n"
    stop_hotkey: str = "ctrl+shift+s"
    cooldown_ms: int = 1500


@dataclass
class FilterConfig:
    min_block_chars: int = 140
    ignore_short_lines: int = 4


@dataclass
class DedupConfig:
    enabled: bool = True
    similarity_threshold: float = 0.95


@dataclass
class PlaybackConfig:
    retry_count: int = 2
    retry_backoff_ms: int = 700


@dataclass
class DebugConfig:
    save_screenshots: bool = False
    screenshot_dir: str = "debug_screenshots"


@dataclass
class AppConfig:
    openai: OpenAIConfig
    elevenlabs: ElevenLabsConfig
    capture: CaptureConfig
    filter: FilterConfig
    dedup: DedupConfig
    playback: PlaybackConfig
    debug: DebugConfig
    log_file: str = "logs/screen-reader.log"


def _section(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key, {})
    return value if isinstance(value, dict) else {}


def load_config(path: Path) -> AppConfig:
    content: dict[str, Any] = {}
    if path.exists():
        with path.open("rb") as f:
            content = tomllib.load(f)

    openai_data = _section(content, "openai")
    eleven_data = _section(content, "elevenlabs")
    capture_data = _section(content, "capture")
    filter_data = _section(content, "filter")
    dedup_data = _section(content, "dedup")
    playback_data = _section(content, "playback")
    debug_data = _section(content, "debug")

    cfg = AppConfig(
        openai=OpenAIConfig(
            api_key=str(openai_data.get("api_key", "")),
            model=str(openai_data.get("model", OpenAIConfig.model)),
        ),
        elevenlabs=ElevenLabsConfig(
            api_key=str(eleven_data.get("api_key", "")),
            voice_id=str(eleven_data.get("voice_id", "")),
            model_id=str(eleven_data.get("model_id", ElevenLabsConfig.model_id)),
            output_format=str(eleven_data.get("output_format", ElevenLabsConfig.output_format)),
        ),
        capture=CaptureConfig(
            hotkey=str(capture_data.get("hotkey", CaptureConfig.hotkey)),
            stop_hotkey=str(capture_data.get("stop_hotkey", CaptureConfig.stop_hotkey)),
            cooldown_ms=int(capture_data.get("cooldown_ms", CaptureConfig.cooldown_ms)),
        ),
        filter=FilterConfig(
            min_block_chars=int(filter_data.get("min_block_chars", FilterConfig.min_block_chars)),
            ignore_short_lines=int(filter_data.get("ignore_short_lines", FilterConfig.ignore_short_lines)),
        ),
        dedup=DedupConfig(
            enabled=bool(dedup_data.get("enabled", DedupConfig.enabled)),
            similarity_threshold=float(dedup_data.get("similarity_threshold", DedupConfig.similarity_threshold)),
        ),
        playback=PlaybackConfig(
            retry_count=int(playback_data.get("retry_count", PlaybackConfig.retry_count)),
            retry_backoff_ms=int(playback_data.get("retry_backoff_ms", PlaybackConfig.retry_backoff_ms)),
        ),
        debug=DebugConfig(
            save_screenshots=bool(debug_data.get("save_screenshots", DebugConfig.save_screenshots)),
            screenshot_dir=str(debug_data.get("screenshot_dir", DebugConfig.screenshot_dir)),
        ),
        log_file=str(content.get("log_file", "logs/screen-reader.log")),
    )

    cfg.openai.api_key = os.getenv("OPENAI_API_KEY", cfg.openai.api_key)
    cfg.openai.model = os.getenv("OPENAI_MODEL", cfg.openai.model)

    cfg.elevenlabs.api_key = os.getenv("ELEVENLABS_API_KEY", cfg.elevenlabs.api_key)
    cfg.elevenlabs.voice_id = os.getenv("ELEVENLABS_VOICE_ID", cfg.elevenlabs.voice_id)
    cfg.elevenlabs.model_id = os.getenv("ELEVENLABS_MODEL_ID", cfg.elevenlabs.model_id)
    cfg.elevenlabs.output_format = os.getenv("ELEVENLABS_OUTPUT_FORMAT", cfg.elevenlabs.output_format)

    hotkey = os.getenv("SCREEN_READER_HOTKEY")
    if hotkey:
        cfg.capture.hotkey = hotkey
    stop_hotkey = os.getenv("SCREEN_READER_STOP_HOTKEY")
    if stop_hotkey:
        cfg.capture.stop_hotkey = stop_hotkey

    return cfg


def init_config(path: Path, force: bool = False) -> Path:
    if path.exists() and not force:
        raise FileExistsError(f"Config already exists: {path}")

    template = """# Screen Reader v2 config
log_file = "logs/screen-reader.log"

[openai]
api_key = ""
model = "gpt-4.1-mini"

[elevenlabs]
api_key = ""
voice_id = ""
model_id = "eleven_turbo_v2_5"
output_format = "mp3_44100_128"

[capture]
hotkey = "ctrl+shift+n"
stop_hotkey = "ctrl+shift+s"
cooldown_ms = 1500

[filter]
min_block_chars = 140
ignore_short_lines = 4

[dedup]
enabled = true
similarity_threshold = 0.95

[playback]
retry_count = 2
retry_backoff_ms = 700

[debug]
save_screenshots = false
screenshot_dir = "debug_screenshots"
"""
    path.write_text(template, encoding="utf-8")
    return path


def _toml_str(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f"\"{escaped}\""


def render_config(cfg: AppConfig) -> str:
    return f"""# Screen Reader v2 config
log_file = {_toml_str(cfg.log_file)}

[openai]
api_key = {_toml_str(cfg.openai.api_key)}
model = {_toml_str(cfg.openai.model)}

[elevenlabs]
api_key = {_toml_str(cfg.elevenlabs.api_key)}
voice_id = {_toml_str(cfg.elevenlabs.voice_id)}
model_id = {_toml_str(cfg.elevenlabs.model_id)}
output_format = {_toml_str(cfg.elevenlabs.output_format)}

[capture]
hotkey = {_toml_str(cfg.capture.hotkey)}
stop_hotkey = {_toml_str(cfg.capture.stop_hotkey)}
cooldown_ms = {cfg.capture.cooldown_ms}

[filter]
min_block_chars = {cfg.filter.min_block_chars}
ignore_short_lines = {cfg.filter.ignore_short_lines}

[dedup]
enabled = {"true" if cfg.dedup.enabled else "false"}
similarity_threshold = {cfg.dedup.similarity_threshold}

[playback]
retry_count = {cfg.playback.retry_count}
retry_backoff_ms = {cfg.playback.retry_backoff_ms}

[debug]
save_screenshots = {"true" if cfg.debug.save_screenshots else "false"}
screenshot_dir = {_toml_str(cfg.debug.screenshot_dir)}
"""


def save_config(path: Path, cfg: AppConfig) -> Path:
    path.write_text(render_config(cfg), encoding="utf-8")
    return path

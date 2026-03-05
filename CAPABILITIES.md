# Screen Reader Capabilities

Last updated: 2026-03-05

## Overview

Screen Reader v2 is a Windows-first game narrator that captures screenshots, extracts long-form narrative text with OpenAI vision, and plays speech with ElevenLabs.

## Core Capabilities

- Global capture hotkey (default `ctrl+shift+n`)
- Global stop-speaking hotkey (default `ctrl+shift+s`)
- Full-screen screenshot capture with cooldown control
- AI text extraction focused on long-form story/dialog/lore
- Filtering to ignore short UI noise (`ignore_short_lines`, `min_block_chars`)
- Text normalization + deduplication (hash/similarity)
- ElevenLabs synthesis with configurable model and output format
- Retry with exponential backoff, then skip on persistent TTS failure
- Audio playback interruption support (`Stop Speaking`)
- Tray controls:
  - Pause/Resume
  - Capture Now
  - Test Voice
  - Stop Speaking
  - Show Hotkeys
  - Open Logs
  - Exit
- Desktop settings UI (`ui`) for editing API keys and runtime settings
- CLI workflow:
  - `run`
  - `doctor`
  - `voices`
  - `test-capture`
  - `ui`
  - `config init`

## Configuration Surface

Managed via `config.toml`:

- `openai.api_key`, `openai.model`
- `elevenlabs.api_key`, `elevenlabs.voice_id`, `elevenlabs.model_id`, `elevenlabs.output_format`
- `capture.hotkey`, `capture.stop_hotkey`, `capture.cooldown_ms`
- `filter.min_block_chars`, `filter.ignore_short_lines`
- `dedup.enabled`, `dedup.similarity_threshold`
- `playback.retry_count`, `playback.retry_backoff_ms`
- `debug.save_screenshots`, `debug.screenshot_dir`
- `log_file`

## Diagnostics and Reliability

- Structured runtime log file at `logs/screen-reader.log`
- Hotkey registration status surfaced via tray notification and log entries
- `doctor` validates required settings and warns when not elevated
- Unit tests cover parser, dedup, pipeline retries, config round-trip, and audio payload handling

## Current Limitations

- Windows-focused implementation
- Capture mode is full-screen only (no per-window targeting yet)
- Requires network access for OpenAI and ElevenLabs
- API keys are currently file/env based (not yet in OS credential vault)
- Output quality depends on game UI readability and model extraction confidence


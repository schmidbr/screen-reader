# SnapNarrate

Windows game narrator that:
1. Captures the screen on hotkey press
2. Extracts long-form narrative text with OpenAI or Ollama vision
3. Speaks it with ElevenLabs

## What It Can Do

- Capture hotkey: `ctrl+shift+n` (default)
- Region capture hotkey: `ctrl+shift+r` (default, click-drag selection)
- Stop-speaking hotkey: `ctrl+shift+s` (default)
- Ignore menu/HUD noise and focus on long text blocks
- Faster default path with resized JPEG captures, non-blocking playback, and optional fast extraction mode
- Ultra-fast trigger mode with a speech-first first chunk and queued follow-up narration
- Ollama two-pass paragraph extraction to improve multi-paragraph coverage
- Retry transient TTS failures, then skip
- Deduplicate repeated text between captures
- Usage and credits snapshot (OpenAI + ElevenLabs) via CLI and tray
- App version visible in tray menu, settings window, and CLI
- Tray controls: Version, Capture Now, Capture Region Now, Capture Mode toggle, Stop Speaking, Pause/Resume, Settings, Run At Startup toggle, Show Hotkeys, Test Voice, Run Self-Test, Usage & Credits, Open Logs, Exit
- Built-in self-test to verify extraction, TTS, and playback with a fixture image
- Settings window for keys and runtime config
- Selectable vision provider (`openai` or `ollama`)

## Requirements

- Windows 10/11
- Python 3.11+
- OpenAI API key (if provider = `openai`)
- ElevenLabs API key
- ElevenLabs `voice_id` (not voice name)
- Ollama local server + model (if provider = `ollama`)

## Install

```powershell
cd C:\Users\brend\OneDrive\Documents\Projects\snapnarrate
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -e ".[dev]"
```

## First-Time Setup

1. Create config file:

```powershell
py -m snap_narrate config init --config config.toml
```

2. Open settings UI:

```powershell
py -m snap_narrate ui --config config.toml
```

3. Fill in:
- Vision provider (`openai` or `ollama`)
- OpenAI API key/model/base URL (if using OpenAI)
- Optional OpenAI ultra-fast model for the first trigger pass
- Optional OpenAI admin API key for org-level usage/cost endpoints
- Ollama base URL/model (if using Ollama)
- Optional Ollama ultra-fast model for the first trigger pass
- Ollama extraction settings: `num_predict`, `min_paragraphs`, `coverage_retry_attempts`
- Vision speed setting: `fast_mode`
- Trigger speed setting: `ultra_fast_mode`
- Capture mode settings: `mode`, `region_hotkey`, `min_region_px`
- Capture speed settings: `max_dimension`, `image_format`, `jpeg_quality`
- ElevenLabs API key
- ElevenLabs Voice ID
- Optional ElevenLabs speech-fast model for the first spoken chunk
- Keep `output_format = mp3_44100_128` unless you have a tier that supports PCM
- Playback speed settings: `speech_first_enabled`, `initial_chunk_chars`, `followup_chunk_chars`, `followup_min_chars`
- Optional usage settings: monthly OpenAI budget and usage cache seconds

4. Validate setup:

```powershell
py -m snap_narrate doctor --config config.toml
```

## Run

```powershell
cd C:\Users\brend\OneDrive\Documents\Projects\snapnarrate
py -m snap_narrate run --config config.toml --game-profile default
```

Then:
- Press `ctrl+shift+n` to capture and narrate
- Press `ctrl+shift+r` then click-drag to capture a region once
- Press `ctrl+shift+s` to interrupt speaking
- Open `Settings` from tray while running; saved changes auto-reload within ~1 second
- Version is shown in tray and at the top of the settings window

### EXE Zero-Click Behavior

- Launching `snapnarrate.exe` with no arguments now auto-starts tray runtime.
- Config resolution order for no-arg launch:
  1. `config.toml` next to the EXE
  2. `%APPDATA%\SnapNarrate\config.toml`
  3. If missing, auto-create `%APPDATA%\SnapNarrate\config.toml`
- If required settings are missing, Settings UI opens automatically for first-run setup.

## Useful Commands

Installed CLI form:

```powershell
# List available ElevenLabs voices (name + voice_id)
snapnarrate voices --config config.toml

# One-shot screenshot extraction preview (prints extracted text)
snapnarrate test-capture --config config.toml

# Full roundtrip fixture self-test
snapnarrate self-test --config config.toml

# Open settings window
snapnarrate ui --config config.toml

# Install desktop shortcut
snapnarrate install-shortcut --config config.toml

# Startup control
snapnarrate startup --status --config config.toml
snapnarrate startup --enable --config config.toml
snapnarrate startup --disable --config config.toml

# Usage and remaining credits
snapnarrate usage --config config.toml
snapnarrate usage --config config.toml --json

# Version
snapnarrate version
snapnarrate --version
```

Module form equivalents:

```powershell
py -m snap_narrate voices --config config.toml
py -m snap_narrate test-capture --config config.toml
py -m snap_narrate self-test --config config.toml
py -m snap_narrate ui --config config.toml
py -m snap_narrate startup --status --config config.toml
py -m snap_narrate usage --config config.toml
py -m snap_narrate version
py -m snap_narrate --version
```

Shortcuts created by these commands include the explicit run/config arguments so they relaunch the same setup you created them from.

## Tests

```powershell
py -m pytest -q
```

## Build EXE

```powershell
cd C:\Users\brend\OneDrive\Documents\Projects\snapnarrate
.\scripts\build.ps1 -InstallDeps
```

Output:
- `dist\snapnarrate.exe`
- Uses icon asset: `assets\snapnarrate.ico`

## Hotkey Troubleshooting

- If hotkeys fail only inside a game, run PowerShell as Administrator and start the app again.
- Use tray menu:
  - `Show Hotkeys` to verify registration status
  - `Capture Now` to test pipeline without keyboard hook
  - `Run Self-Test` to verify extractor, TTS, and playback with the built-in fixture
- Check logs at `logs/snapnarrate.log`.

## Config Reference

`config.toml` fields:
- `vision.provider`, `vision.timeout_sec`
- `vision.fast_mode`, `vision.ultra_fast_mode`
- `openai.api_key`, `openai.model`
- `openai.admin_api_key`, `openai.ultra_fast_model`, `openai.base_url`
- `ollama.base_url`, `ollama.model`, `ollama.ultra_fast_model`, `ollama.keep_alive`
- `ollama.num_predict`, `ollama.temperature`, `ollama.top_p`, `ollama.continuation_attempts`
- `ollama.min_paragraphs`, `ollama.coverage_retry_attempts`
- `elevenlabs.api_key`, `elevenlabs.voice_id`, `elevenlabs.model_id`, `elevenlabs.speech_fast_model_id`, `elevenlabs.output_format`
- `capture.hotkey`, `capture.stop_hotkey`, `capture.cooldown_ms`
- `capture.mode`, `capture.region_hotkey`, `capture.min_region_px`
- `capture.max_dimension`, `capture.image_format`, `capture.jpeg_quality`
- `filter.min_block_chars`, `filter.ignore_short_lines`
- `dedup.enabled`, `dedup.similarity_threshold`
- `playback.retry_count`, `playback.retry_backoff_ms`, `playback.speech_first_enabled`, `playback.initial_chunk_chars`
- `playback.followup_chunk_chars`, `playback.followup_min_chars`
- `debug.save_screenshots`, `debug.screenshot_dir`
- `app.run_at_startup`
- `usage.openai_monthly_budget_usd`, `usage.cache_seconds`
- `log_file`

## Security Notes

- API keys in `config.toml` are plain text. Prefer environment variables if needed.
- Screenshots are only saved when `debug.save_screenshots = true`.
- If keys were exposed in logs/chat/history, rotate them.

## Project Docs

- [CAPABILITIES.md](CAPABILITIES.md)
- [CHANGELOG.md](CHANGELOG.md)


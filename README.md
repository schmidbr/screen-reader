# Screen Reader v2

Windows game narrator that:
1. Captures the screen on hotkey press
2. Extracts long-form narrative text with OpenAI vision
3. Speaks it with ElevenLabs

## What It Can Do

- Capture hotkey: `ctrl+shift+n` (default)
- Stop-speaking hotkey: `ctrl+shift+s` (default)
- Ignore menu/HUD noise and focus on long text blocks
- Retry transient TTS failures, then skip
- Deduplicate repeated text between captures
- Tray controls: Pause/Resume, Capture Now, Test Voice, Stop Speaking, Open Logs, Exit
- Settings window for keys and runtime config

## Requirements

- Windows 10/11
- Python 3.11+
- OpenAI API key
- ElevenLabs API key
- ElevenLabs `voice_id` (not voice name)

## Install

```powershell
cd C:\Users\brend\OneDrive\Documents\Projects\screen-reader
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

## First-Time Setup

1. Create config file:

```powershell
$env:PYTHONPATH="src"
py -m screen_reader config init --config config.toml
```

2. Open settings UI:

```powershell
$env:PYTHONPATH="src"
py -m screen_reader ui --config config.toml
```

3. Fill in:
- OpenAI API key
- ElevenLabs API key
- ElevenLabs Voice ID
- Keep `output_format = mp3_44100_128` unless you have a tier that supports PCM

4. Validate setup:

```powershell
$env:PYTHONPATH="src"
py -m screen_reader doctor --config config.toml
```

## Run

```powershell
cd C:\Users\brend\OneDrive\Documents\Projects\screen-reader
$env:PYTHONPATH="src"
py -m screen_reader run --config config.toml --game-profile default
```

Then:
- Press `ctrl+shift+n` to capture and narrate
- Press `ctrl+shift+s` to interrupt speaking

## Useful Commands

```powershell
# List available ElevenLabs voices (name + voice_id)
py -m screen_reader voices --config config.toml

# One-shot screenshot extraction preview (prints extracted text)
py -m screen_reader test-capture --config config.toml

# Open settings window
py -m screen_reader ui --config config.toml
```

## Hotkey Troubleshooting

- If hotkeys fail only inside a game, run PowerShell as Administrator and start the app again.
- Use tray menu:
  - `Show Hotkeys` to verify registration status
  - `Capture Now` to test pipeline without keyboard hook
- Check logs at `logs/screen-reader.log`.

## Config Reference

`config.toml` fields:
- `openai.api_key`, `openai.model`
- `elevenlabs.api_key`, `elevenlabs.voice_id`, `elevenlabs.model_id`, `elevenlabs.output_format`
- `capture.hotkey`, `capture.stop_hotkey`, `capture.cooldown_ms`
- `filter.min_block_chars`, `filter.ignore_short_lines`
- `dedup.enabled`, `dedup.similarity_threshold`
- `playback.retry_count`, `playback.retry_backoff_ms`
- `debug.save_screenshots`, `debug.screenshot_dir`
- `log_file`

## Security Notes

- API keys in `config.toml` are plain text. Prefer environment variables if needed.
- Screenshots are only saved when `debug.save_screenshots = true`.
- If keys were exposed in logs/chat/history, rotate them.

## Project Docs

- [CAPABILITIES.md](CAPABILITIES.md)
- [CHANGELOG.md](CHANGELOG.md)

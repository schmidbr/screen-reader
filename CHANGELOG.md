# Changelog

All notable changes to this project are documented in this file.

## [Unreleased]

- No unreleased entries.

## [0.2.0] - 2026-03-05

### Added

- Full v2 architecture for game narration:
  - screenshot capture service
  - OpenAI vision extraction client
  - ElevenLabs TTS client
  - narration pipeline with filtering and dedup
  - runtime orchestration with worker thread
- System tray app controls and global hotkeys.
- Stop-speaking workflow with dedicated hotkey and tray action.
- Desktop settings UI (`screen-reader ui`) for editing API keys and app settings.
- Config read/write helpers and richer `config.toml` surface.
- Expanded CLI commands: `run`, `doctor`, `voices`, `test-capture`, `ui`, `config init`.
- Test suite for parser, audio handling, dedup, pipeline behavior, and config round-trip.
- Packaging metadata (`pyproject.toml`).

### Changed

- Migrated from local `pyttsx3` starter behavior to OpenAI + ElevenLabs pipeline.
- Switched ElevenLabs default output format to `mp3_44100_128` for broader plan compatibility.
- Added MP3 decoding playback path and PCM fallback handling.
- Improved runtime diagnostics:
  - hotkey registration status
  - hotkey press/capture queue logs
  - admin/elevation advisory in `doctor`
- Improved UI close behavior (`Close` button + window-close handler).

### Fixed

- `py -m screen_reader.cli ...` no-op behavior by adding CLI module entrypoint.
- Audio payload handling for non-PCM outputs and malformed payload lengths.
- Settings window close flow requiring force kill.
- Hotkey observability and fallback tray actions for capture troubleshooting.

## [0.1.0] - 2026-03-04

### Added

- Initial project scaffold.
- Basic text-to-speech CLI using local `pyttsx3`.
- Starter files: README, requirements, sample text, git setup.


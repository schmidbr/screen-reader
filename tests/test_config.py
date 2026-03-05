from __future__ import annotations

from pathlib import Path

from screen_reader.config import load_config, save_config


def test_load_config_reads_stop_hotkey(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
[capture]
hotkey = "ctrl+shift+n"
stop_hotkey = "ctrl+shift+x"
cooldown_ms = 1500
""".strip(),
        encoding="utf-8",
    )

    cfg = load_config(config_path)
    assert cfg.capture.hotkey == "ctrl+shift+n"
    assert cfg.capture.stop_hotkey == "ctrl+shift+x"


def test_save_config_round_trip(tmp_path: Path) -> None:
    config_path = tmp_path / "config.toml"
    cfg = load_config(config_path)
    cfg.openai.api_key = "k1"
    cfg.elevenlabs.api_key = "k2"
    cfg.elevenlabs.voice_id = "voice-123"
    cfg.capture.hotkey = "ctrl+shift+n"
    cfg.capture.stop_hotkey = "ctrl+shift+s"
    cfg.capture.cooldown_ms = 1800
    cfg.filter.min_block_chars = 160
    cfg.dedup.similarity_threshold = 0.9
    cfg.playback.retry_count = 3
    cfg.debug.save_screenshots = True
    cfg.log_file = "logs/custom.log"

    save_config(config_path, cfg)
    loaded = load_config(config_path)

    assert loaded.openai.api_key == "k1"
    assert loaded.elevenlabs.api_key == "k2"
    assert loaded.elevenlabs.voice_id == "voice-123"
    assert loaded.capture.hotkey == "ctrl+shift+n"
    assert loaded.capture.stop_hotkey == "ctrl+shift+s"
    assert loaded.capture.cooldown_ms == 1800
    assert loaded.filter.min_block_chars == 160
    assert loaded.dedup.similarity_threshold == 0.9
    assert loaded.playback.retry_count == 3
    assert loaded.debug.save_screenshots is True
    assert loaded.log_file == "logs/custom.log"

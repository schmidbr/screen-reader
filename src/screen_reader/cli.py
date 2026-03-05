from __future__ import annotations

import argparse
import ctypes
from pathlib import Path

from screen_reader.config import DEFAULT_CONFIG_PATH, init_config, load_config
from screen_reader.logging_utils import setup_logging
from screen_reader.ui import launch_settings_ui


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="screen-reader", description="Game narrator screen reader")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run the hotkey + tray narrator")
    run.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    run.add_argument("--game-profile", default="default")

    doctor = sub.add_parser("doctor", help="Validate local setup")
    doctor.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)

    voices = sub.add_parser("voices", help="List TTS voices")
    voices.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    voices.add_argument("--provider", choices=["elevenlabs"], default="elevenlabs")

    test_capture = sub.add_parser("test-capture", help="Take one screenshot and print extraction output")
    test_capture.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    test_capture.add_argument("--game-profile", default="default")

    ui = sub.add_parser("ui", help="Open desktop settings UI")
    ui.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)

    cfg = sub.add_parser("config", help="Config helpers")
    cfg_sub = cfg.add_subparsers(dest="config_command", required=True)
    cfg_init = cfg_sub.add_parser("init", help="Create config.toml")
    cfg_init.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    cfg_init.add_argument("--force", action="store_true")

    return parser


def run_command(config_path: Path, game_profile: str) -> int:
    from screen_reader.capture import ScreenCapturer
    from screen_reader.elevenlabs_client import ElevenLabsClient, TempFileAudioPlayer
    from screen_reader.openai_client import OpenAIVisionExtractor
    from screen_reader.pipeline import NarrationPipeline
    from screen_reader.runtime import ScreenReaderRuntime

    cfg = load_config(config_path)
    log_path = setup_logging(cfg.log_file)

    extractor = OpenAIVisionExtractor(
        api_key=cfg.openai.api_key,
        model=cfg.openai.model,
        ignore_short_lines=cfg.filter.ignore_short_lines,
    )
    tts = ElevenLabsClient(
        api_key=cfg.elevenlabs.api_key,
        voice_id=cfg.elevenlabs.voice_id,
        model_id=cfg.elevenlabs.model_id,
        output_format=cfg.elevenlabs.output_format,
    )
    player = TempFileAudioPlayer()
    pipeline = NarrationPipeline(
        extractor=extractor,
        tts=tts,
        player=player,
        min_block_chars=cfg.filter.min_block_chars,
        dedup_enabled=cfg.dedup.enabled,
        dedup_similarity_threshold=cfg.dedup.similarity_threshold,
        retry_count=cfg.playback.retry_count,
        retry_backoff_ms=cfg.playback.retry_backoff_ms,
    )
    capturer = ScreenCapturer(
        cooldown_ms=cfg.capture.cooldown_ms,
        save_debug=cfg.debug.save_screenshots,
        debug_dir=cfg.debug.screenshot_dir,
    )
    runtime = ScreenReaderRuntime(
        capturer=capturer,
        pipeline=pipeline,
        hotkey=cfg.capture.hotkey,
        stop_hotkey=cfg.capture.stop_hotkey,
        log_path=Path(cfg.log_file),
        game_profile=game_profile,
    )
    runtime.start()
    return 0


def doctor_command(config_path: Path) -> int:
    cfg = load_config(config_path)

    checks: list[tuple[str, bool, str, bool]] = []
    checks.append(("Config file exists", config_path.exists(), str(config_path), True))
    checks.append(("OPENAI key", bool(cfg.openai.api_key), "Set openai.api_key or OPENAI_API_KEY", True))
    checks.append(("ELEVENLABS key", bool(cfg.elevenlabs.api_key), "Set elevenlabs.api_key or ELEVENLABS_API_KEY", True))
    checks.append(("ELEVENLABS voice_id", bool(cfg.elevenlabs.voice_id), "Set elevenlabs.voice_id or ELEVENLABS_VOICE_ID", True))
    checks.append(("Capture hotkey configured", bool(cfg.capture.hotkey), cfg.capture.hotkey, True))
    checks.append(("Stop hotkey configured", bool(cfg.capture.stop_hotkey), cfg.capture.stop_hotkey, True))
    try:
        is_admin = bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:  # noqa: BLE001
        is_admin = False
    checks.append(
        (
            "Elevated privileges",
            is_admin,
            "Run terminal as Administrator if hotkeys fail in elevated games",
            False,
        )
    )

    all_ok = True
    for name, ok, detail, required in checks:
        status = "OK" if ok else ("FAIL" if required else "WARN")
        print(f"[{status}] {name}: {detail}")
        if required:
            all_ok = all_ok and ok

    return 0 if all_ok else 1


def voices_command(config_path: Path) -> int:
    from screen_reader.elevenlabs_client import ElevenLabsClient

    cfg = load_config(config_path)
    client = ElevenLabsClient(
        api_key=cfg.elevenlabs.api_key,
        voice_id=cfg.elevenlabs.voice_id,
        model_id=cfg.elevenlabs.model_id,
        output_format=cfg.elevenlabs.output_format,
    )
    voices = client.list_voices()
    for voice_id, name in voices:
        print(f"{name}\t{voice_id}")
    return 0


def test_capture_command(config_path: Path, game_profile: str) -> int:
    from screen_reader.capture import ScreenCapturer
    from screen_reader.openai_client import OpenAIVisionExtractor

    cfg = load_config(config_path)
    capturer = ScreenCapturer(
        cooldown_ms=0,
        save_debug=cfg.debug.save_screenshots,
        debug_dir=cfg.debug.screenshot_dir,
    )
    image_bytes = capturer.capture_png()

    extractor = OpenAIVisionExtractor(
        api_key=cfg.openai.api_key,
        model=cfg.openai.model,
        ignore_short_lines=cfg.filter.ignore_short_lines,
    )
    result = extractor.extract_narrative_text(image_bytes=image_bytes, game_profile=game_profile)
    print(f"Confidence: {result.confidence:.2f}")
    if result.dropped_reason:
        print(f"Dropped: {result.dropped_reason}")
    print("Text:")
    print(result.text)
    return 0


def config_init_command(config_path: Path, force: bool) -> int:
    init_config(config_path, force=force)
    print(f"Wrote config: {config_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        return run_command(args.config, args.game_profile)
    if args.command == "doctor":
        return doctor_command(args.config)
    if args.command == "voices":
        return voices_command(args.config)
    if args.command == "test-capture":
        return test_capture_command(args.config, args.game_profile)
    if args.command == "ui":
        return launch_settings_ui(args.config)
    if args.command == "config" and args.config_command == "init":
        return config_init_command(args.config, args.force)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

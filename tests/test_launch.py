from __future__ import annotations

from pathlib import Path

from snap_narrate.launch import appdata_config_path, launch_command, resolve_default_config_path


def test_appdata_config_path_ends_with_snapnarrate_config() -> None:
    path = appdata_config_path()
    assert path.name == "config.toml"
    assert "SnapNarrate" in str(path)


def test_resolve_default_config_prefers_existing_file(tmp_path: Path, monkeypatch) -> None:
    exe_path = tmp_path / "snapnarrate.exe"
    exe_path.write_text("x", encoding="utf-8")
    config = tmp_path / "config.toml"
    config.write_text("x", encoding="utf-8")
    monkeypatch.setattr("snap_narrate.launch.executable_target", lambda: exe_path)
    path = resolve_default_config_path()
    assert path == config


def test_launch_command_non_frozen_uses_src_entrypoint_and_config(tmp_path: Path, monkeypatch) -> None:
    python_exe = tmp_path / "Python313" / "python.exe"
    python_exe.parent.mkdir(parents=True, exist_ok=True)
    python_exe.write_text("x", encoding="utf-8")
    config = tmp_path / "custom.toml"
    config.write_text("x", encoding="utf-8")

    monkeypatch.setattr("snap_narrate.launch.is_frozen", lambda: False)
    monkeypatch.setattr("snap_narrate.launch.executable_target", lambda: python_exe)
    monkeypatch.setattr("pathlib.Path.cwd", lambda: tmp_path)

    target, args, workdir = launch_command(config)

    expected_entrypoint = Path(__file__).resolve().parents[1] / "src" / "main.py"
    assert target == str(python_exe)
    assert args == f'"{expected_entrypoint}" run --config "{config.resolve()}" --game-profile default'
    assert workdir == str(tmp_path)


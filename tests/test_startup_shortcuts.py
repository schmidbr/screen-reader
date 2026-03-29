from __future__ import annotations

from pathlib import Path

from snap_narrate import cli
from snap_narrate.shortcuts import ShortcutManager
from snap_narrate.startup import StartupManager


def test_shortcut_paths_have_expected_names() -> None:
    manager = ShortcutManager("SnapNarrate")
    assert manager.desktop_shortcut_path().name == "SnapNarrate.lnk"
    assert manager.startup_shortcut_path().name == "SnapNarrate.lnk"


class FakeShortcutManager:
    def __init__(self, path: Path) -> None:
        self._path = path

    def startup_shortcut_path(self) -> Path:
        return self._path

    def create_startup_shortcut(self, target: str, arguments: str, working_dir: str, icon_path: str | None = None) -> Path:  # noqa: ARG002
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text("fake shortcut", encoding="utf-8")
        return self._path

    def remove_shortcut(self, destination: Path) -> bool:  # noqa: ARG002
        if self._path.exists():
            self._path.unlink()
            return True
        return False


def test_startup_manager_enable_disable(tmp_path: Path) -> None:
    fake = FakeShortcutManager(tmp_path / "SnapNarrate.lnk")
    manager = StartupManager(
        shortcut_manager=fake,  # type: ignore[arg-type]
        target="C:\\snapnarrate.exe",
        arguments="run --config config.toml",
        working_dir="C:\\",
        icon_path=None,
    )

    assert manager.is_enabled() is False
    path = manager.enable()
    assert str(path).endswith("SnapNarrate.lnk")
    assert manager.is_enabled() is True
    assert manager.disable() is True
    assert manager.is_enabled() is False


def test_install_shortcut_command_uses_explicit_launch_args(tmp_path: Path, monkeypatch, capsys) -> None:
    captured: dict[str, object] = {}

    def fake_launch_command(config_path: Path, include_args: bool = True) -> tuple[str, str, str]:
        captured["config_path"] = config_path
        captured["include_args"] = include_args
        return ("python.exe", "launch args", str(tmp_path))

    class FakeShortcutCreator:
        def create_desktop_shortcut(
            self,
            target: str,
            arguments: str,
            working_dir: str,
            icon_path: str | None = None,
        ) -> Path:
            captured["target"] = target
            captured["arguments"] = arguments
            captured["working_dir"] = working_dir
            captured["icon_path"] = icon_path
            return tmp_path / "SnapNarrate.lnk"

    monkeypatch.setattr("snap_narrate.cli.launch_command", fake_launch_command)
    monkeypatch.setattr("snap_narrate.cli.ShortcutManager", lambda: FakeShortcutCreator())
    monkeypatch.setattr("snap_narrate.cli.icon_asset_path", lambda: tmp_path / "missing.ico")

    config = tmp_path / "custom.toml"
    result = cli.install_shortcut_command(config)

    assert result == 0
    assert captured["config_path"] == config
    assert captured["include_args"] is True
    assert captured["arguments"] == "launch args"
    assert "Desktop shortcut created" in capsys.readouterr().out


def test_startup_command_enable_uses_explicit_launch_args(tmp_path: Path, monkeypatch, capsys) -> None:
    captured: dict[str, object] = {}

    def fake_launch_command(config_path: Path, include_args: bool = True) -> tuple[str, str, str]:
        captured["config_path"] = config_path
        captured["include_args"] = include_args
        return ("python.exe", "launch args", str(tmp_path))

    class FakeStartup:
        def __init__(
            self,
            shortcut_manager,  # noqa: ANN001
            target: str,
            arguments: str,
            working_dir: str,
            icon_path: str | None = None,
        ) -> None:
            captured["target"] = target
            captured["arguments"] = arguments
            captured["working_dir"] = working_dir
            captured["icon_path"] = icon_path

        def enable(self) -> Path:
            return tmp_path / "SnapNarrate.lnk"

        def disable(self) -> bool:
            return True

        def is_enabled(self) -> bool:
            return False

    monkeypatch.setattr("snap_narrate.cli.launch_command", fake_launch_command)
    monkeypatch.setattr("snap_narrate.cli.StartupManager", FakeStartup)
    monkeypatch.setattr("snap_narrate.cli.ShortcutManager", lambda: object())
    monkeypatch.setattr("snap_narrate.cli.icon_asset_path", lambda: tmp_path / "missing.ico")

    config = tmp_path / "custom.toml"
    result = cli.startup_command(config, enable=True, disable=False, status=False)

    assert result == 0
    assert captured["config_path"] == config
    assert captured["include_args"] is True
    assert captured["arguments"] == "launch args"
    assert "Run-at-startup enabled" in capsys.readouterr().out

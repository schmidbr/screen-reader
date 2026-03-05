from __future__ import annotations

import pytest

from snap_narrate import cli


def test_version_subcommand_prints_version(monkeypatch, capsys) -> None:
    monkeypatch.setattr("snap_narrate.cli.get_app_version", lambda: "1.2.3")
    result = cli.main(["version"])
    out = capsys.readouterr().out
    assert result == 0
    assert "SnapNarrate 1.2.3" in out


def test_parser_version_flag_prints_and_exits(monkeypatch, capsys) -> None:
    monkeypatch.setattr("snap_narrate.cli.get_app_version", lambda: "1.2.3")
    with pytest.raises(SystemExit) as exc:
        cli.main(["--version"])
    out = capsys.readouterr().out
    assert exc.value.code == 0
    assert "SnapNarrate 1.2.3" in out

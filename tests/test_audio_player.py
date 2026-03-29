from __future__ import annotations

import sys
import types

import numpy as np
import pytest

from snap_narrate.elevenlabs_client import TempFileAudioPlayer


def test_audio_from_bytes_valid_even_length_pcm() -> None:
    samples, samplerate = TempFileAudioPlayer.audio_from_bytes((1).to_bytes(2, "little", signed=True) * 4)
    assert isinstance(samples, np.ndarray)
    assert samples.dtype == np.float32
    assert samples.size == 4
    assert samplerate == 44100


def test_audio_from_bytes_odd_length_trims_last_byte() -> None:
    payload = (1).to_bytes(2, "little", signed=True) * 3 + b"\x00"
    samples, _ = TempFileAudioPlayer.audio_from_bytes(payload)
    assert samples.size == 3


def test_audio_from_bytes_invalid_mp3_payload() -> None:
    with pytest.raises(RuntimeError, match="Failed to decode MP3 payload"):
        TempFileAudioPlayer.audio_from_bytes(b"ID3" + b"\x00" * 10)


def test_play_starts_worker_with_new_token(monkeypatch) -> None:
    calls: list[str] = []
    fake_sd = types.SimpleNamespace(stop=lambda: calls.append("stop"))
    monkeypatch.setitem(sys.modules, "sounddevice", fake_sd)
    monkeypatch.setattr(
        TempFileAudioPlayer,
        "_decode_audio",
        lambda self, audio_bytes: (np.array([0.1, -0.1], dtype=np.float32), 22050, 5),
    )

    player = TempFileAudioPlayer()
    started: list[int] = []
    monkeypatch.setattr(player, "_start_worker", lambda token: started.append(token))

    player.play(b"pcm")

    assert calls == ["stop"]
    assert started == [1]
    assert player._is_playing is True
    assert len(player._pending_chunks) == 1


def test_queue_appends_without_interrupting_current_playback(monkeypatch) -> None:
    monkeypatch.setattr(
        TempFileAudioPlayer,
        "_decode_audio",
        lambda self, audio_bytes: (np.array([0.1, -0.1], dtype=np.float32), 22050, 5),
    )

    player = TempFileAudioPlayer()
    player._playback_token = 4
    player._worker = types.SimpleNamespace(is_alive=lambda: True)

    player.queue(b"tail")

    assert player._playback_token == 4
    assert player._is_playing is True
    assert len(player._pending_chunks) == 1


def test_stop_clears_playback_state(monkeypatch) -> None:
    calls: list[str] = []
    fake_sd = types.SimpleNamespace(stop=lambda: calls.append("stop"))
    monkeypatch.setitem(sys.modules, "sounddevice", fake_sd)

    player = TempFileAudioPlayer()
    player._is_playing = True
    player._playback_token = 3
    player._pending_chunks = [(np.array([0.0], dtype=np.float32), 44100, 0)]

    player.stop()

    assert calls == ["stop"]
    assert player._is_playing is False
    assert player._playback_token == 4
    assert player._pending_chunks == []

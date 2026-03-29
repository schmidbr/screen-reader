from __future__ import annotations

import io
import logging
import threading
import time

import numpy as np


class ElevenLabsClient:
    def __init__(
        self,
        api_key: str,
        voice_id: str,
        model_id: str,
        speech_fast_model_id: str = "",
        output_format: str = "mp3_44100_128",
        timeout_sec: int = 60,
    ) -> None:
        self.api_key = api_key
        self.voice_id = voice_id
        self.model_id = model_id
        self.speech_fast_model_id = speech_fast_model_id.strip()
        self.output_format = output_format
        self.timeout_sec = timeout_sec
        self._session = None

    def _requests_session(self):
        import requests

        if self._session is None:
            self._session = requests.Session()
        return self._session

    def synthesize(self, text: str, model_id_override: str | None = None) -> bytes:
        if not self.api_key:
            raise ValueError("ElevenLabs API key is missing")
        if not self.voice_id:
            raise ValueError("ElevenLabs voice_id is missing")

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/octet-stream",
        }
        payload = {
            "text": text,
            "model_id": model_id_override or self.model_id,
        }
        response = self._requests_session().post(
            url,
            headers=headers,
            params={"output_format": self.output_format},
            json=payload,
            timeout=self.timeout_sec,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"ElevenLabs synthesis failed ({response.status_code}): {response.text[:200]}")
        return response.content

    def synthesize_speech_fast(self, text: str) -> bytes:
        return self.synthesize(text, model_id_override=self.speech_fast_model_id or self.model_id)

    def list_voices(self) -> list[tuple[str, str]]:
        if not self.api_key:
            raise ValueError("ElevenLabs API key is missing")

        response = self._requests_session().get(
            "https://api.elevenlabs.io/v1/voices",
            headers={"xi-api-key": self.api_key},
            timeout=self.timeout_sec,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"ElevenLabs voices failed ({response.status_code}): {response.text[:200]}")

        voices = response.json().get("voices", [])
        return [(str(v.get("voice_id", "")), str(v.get("name", ""))) for v in voices]

    def get_subscription_usage(self) -> dict[str, int | None]:
        if not self.api_key:
            raise ValueError("ElevenLabs API key is missing")

        response = self._requests_session().get(
            "https://api.elevenlabs.io/v1/user/subscription",
            headers={"xi-api-key": self.api_key},
            timeout=self.timeout_sec,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"ElevenLabs subscription failed ({response.status_code}): {response.text[:200]}")

        payload = response.json()
        character_count = int(payload.get("character_count", 0))
        character_limit = int(payload.get("character_limit", 0))
        next_reset = payload.get("next_character_count_reset_unix")
        next_reset_unix = int(next_reset) if next_reset is not None else None
        return {
            "character_count": character_count,
            "character_limit": character_limit,
            "remaining_characters": max(character_limit - character_count, 0),
            "next_reset_unix": next_reset_unix,
        }


class TempFileAudioPlayer:
    def __init__(self) -> None:
        self._is_playing = False
        self._lock = threading.Lock()
        self._playback_token = 0
        self._pending_chunks: list[tuple[np.ndarray, int, int]] = []
        self._worker: threading.Thread | None = None

    @staticmethod
    def _is_mp3(audio_bytes: bytes) -> bool:
        return audio_bytes.startswith(b"ID3") or audio_bytes[:2] == b"\xff\xfb"

    @staticmethod
    def audio_from_bytes(audio_bytes: bytes) -> tuple[np.ndarray, int]:
        if not audio_bytes:
            raise RuntimeError("Empty audio payload from ElevenLabs")

        if TempFileAudioPlayer._is_mp3(audio_bytes):
            import soundfile as sf

            try:
                samples, samplerate = sf.read(io.BytesIO(audio_bytes), dtype="float32", always_2d=False)
            except Exception as exc:  # noqa: BLE001
                raise RuntimeError(f"Failed to decode MP3 payload: {exc}") from exc

            if samples is None or len(samples) == 0:
                raise RuntimeError("Decoded MP3 payload has no samples")
            return samples, int(samplerate)

        if len(audio_bytes) % 2 != 0:
            audio_bytes = audio_bytes[:-1]

        if not audio_bytes:
            raise RuntimeError("Audio payload became empty after PCM normalization")

        pcm = np.frombuffer(audio_bytes, dtype=np.int16)
        if pcm.size == 0:
            raise RuntimeError("No PCM samples decoded from ElevenLabs payload")
        samples = pcm.astype(np.float32) / 32768.0
        return samples, 44100

    def _decode_audio(self, audio_bytes: bytes) -> tuple[np.ndarray, int, int]:
        decode_start = time.perf_counter()
        samples, samplerate = self.audio_from_bytes(audio_bytes)
        decode_ms = int(round((time.perf_counter() - decode_start) * 1000))
        return samples, samplerate, decode_ms

    def play(self, audio_bytes: bytes) -> None:
        import sounddevice as sd

        chunk = self._decode_audio(audio_bytes)
        with self._lock:
            self._playback_token += 1
            token = self._playback_token
            self._pending_chunks = [chunk]
            self._is_playing = True
        sd.stop()
        self._start_worker(token)

    def queue(self, audio_bytes: bytes) -> None:
        chunk = self._decode_audio(audio_bytes)
        with self._lock:
            if self._playback_token == 0:
                self._playback_token = 1
            token = self._playback_token
            self._pending_chunks.append(chunk)
            self._is_playing = True
            worker_alive = self._worker is not None and self._worker.is_alive()
        if not worker_alive:
            self._start_worker(token)

    def _start_worker(self, token: int) -> None:
        def playback_loop() -> None:
            import sounddevice as sd

            while True:
                with self._lock:
                    if token != self._playback_token:
                        return
                    if not self._pending_chunks:
                        self._is_playing = False
                        return
                    samples, samplerate, decode_ms = self._pending_chunks.pop(0)

                try:
                    logging.getLogger("snap_narrate").info(
                        "event=audio_playback_start decode_ms=%s samplerate=%s sample_count=%s",
                        decode_ms,
                        samplerate,
                        len(samples),
                    )
                    sd.play(samples, samplerate=samplerate, blocking=False)
                    sd.wait()
                except Exception as exc:  # noqa: BLE001
                    logging.getLogger("snap_narrate").warning("event=audio_wait_failed error=%s", exc)
                finally:
                    with self._lock:
                        if token == self._playback_token and not self._pending_chunks:
                            self._is_playing = False

        worker = threading.Thread(target=playback_loop, daemon=True)
        self._worker = worker
        worker.start()

    def stop(self) -> None:
        import sounddevice as sd

        with self._lock:
            self._playback_token += 1
            self._pending_chunks.clear()
            self._is_playing = False
        sd.stop()

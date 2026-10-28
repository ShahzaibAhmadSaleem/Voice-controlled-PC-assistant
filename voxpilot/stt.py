"""Online speech-to-text using Groq's hosted Whisper models."""

from __future__ import annotations

from . import config


class TranscriptionError(RuntimeError):
    """Raised when speech could not be transcribed."""


MIN_AUDIO_BYTES = 2000  # a WAV header alone is 44 bytes; this rejects accidental clicks


def transcribe(
    client,
    audio_bytes: bytes,
    model: str = config.DEFAULT_STT_MODEL,
    language: str | None = None,
    filename: str = "command.wav",
) -> str:
    """Send recorded audio to Groq Whisper and return the recognised text."""
    if not audio_bytes or len(audio_bytes) < MIN_AUDIO_BYTES:
        raise TranscriptionError("The recording was too short. Try again and speak for a second or two.")

    kwargs = {
        "file": (filename, audio_bytes),
        "model": model,
        "prompt": config.STT_PROMPT,
        "response_format": "json",
        "temperature": 0.0,
    }
    if language:  # only send when set; omit for auto-detect
        kwargs["language"] = language

    try:
        response = client.audio.transcriptions.create(**kwargs)
    except Exception as exc:  # noqa: BLE001 - surface any API/network error to the UI
        raise TranscriptionError(f"Speech recognition failed: {exc}") from exc

    text = response if isinstance(response, str) else getattr(response, "text", "")
    text = (text or "").strip()
    if not text:
        raise TranscriptionError("I couldn't hear anything. Check your microphone and try again.")
    return text

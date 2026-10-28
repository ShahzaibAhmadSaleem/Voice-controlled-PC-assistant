"""Thin factory for the Groq client (imported lazily so tests don't need it)."""

from __future__ import annotations


class MissingApiKeyError(RuntimeError):
    """Raised when no Groq API key is available."""


def make_client(api_key: str | None):
    key = (api_key or "").strip()
    if not key:
        raise MissingApiKeyError("No Groq API key provided.")
    from groq import Groq  # imported here so the rest of the package works without it

    return Groq(api_key=key, timeout=30.0, max_retries=2)

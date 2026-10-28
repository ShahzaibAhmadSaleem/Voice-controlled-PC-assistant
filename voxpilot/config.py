"""Central configuration for VoxPilot.

Everything here can be overridden with environment variables (or a local
``.env`` file) so nothing sensitive or machine-specific is hard-coded.
"""

from __future__ import annotations

import os
from pathlib import Path

try:  # python-dotenv is optional at runtime
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover
    pass

APP_NAME = "VoxPilot"

# Groq model IDs. Groq retires models from time to time, so these are
# overridable. Check https://console.groq.com/docs/models for current IDs.
STT_MODELS = ["whisper-large-v3-turbo", "whisper-large-v3"]
LLM_MODELS = ["openai/gpt-oss-20b", "openai/gpt-oss-120b"]

DEFAULT_STT_MODEL = os.getenv("VOXPILOT_STT_MODEL", STT_MODELS[0])
DEFAULT_LLM_MODEL = os.getenv("VOXPILOT_LLM_MODEL", LLM_MODELS[0])

# Seconds Windows waits before shutting down / restarting. During this window
# the user can say "cancel shutdown" (or press the button) to abort.
SHUTDOWN_DELAY_SECONDS = int(os.getenv("VOXPILOT_SHUTDOWN_DELAY", "30"))

# Where screenshots are saved.
SCREENSHOT_DIR = Path(
    os.getenv("VOXPILOT_SCREENSHOT_DIR", str(Path.home() / "Pictures" / "VoxPilot"))
)

# Short hint that nudges Whisper toward PC-command vocabulary.
STT_PROMPT = (
    "Computer voice commands: open Chrome, open File Explorer, volume up, "
    "take a screenshot, shut down the computer, lock the PC, search for."
)

MAX_HISTORY = 50

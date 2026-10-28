"""VoxPilot - voice-controlled Windows 10 PC assistant (Streamlit dashboard).

Run locally:   streamlit run app.py --server.address 127.0.0.1
"""

from __future__ import annotations

import datetime as dt
import os

import streamlit as st

from voxpilot import actions, brain, config, stt
from voxpilot.groq_client import MissingApiKeyError, make_client

st.set_page_config(page_title="VoxPilot", page_icon="🎙️", layout="centered")


# --------------------------------------------------------------------------
# State helpers
# --------------------------------------------------------------------------

def _init_state() -> None:
    st.session_state.setdefault("history", [])  # newest first
    st.session_state.setdefault("pending", None)  # dict(action, params, heard)
    st.session_state.setdefault("mic_key", 0)


def _secret_api_key() -> str:
    """Key from env / .env / Streamlit secrets (never shown in the UI)."""
    key = os.getenv("GROQ_API_KEY", "").strip()
    if key:
        return key
    try:
        return str(st.secrets.get("GROQ_API_KEY", "")).strip()
    except Exception:  # noqa: BLE001 - no secrets file is perfectly normal
        return ""


@st.cache_resource(show_spinner=False)
def _cached_client(api_key: str):
    return make_client(api_key)


def _log(via: str, heard: str, reply: str, status: str = "ok") -> None:
    history: list = st.session_state.history
    history.insert(
        0,
        {"time": dt.datetime.now().strftime("%H:%M:%S"), "via": via, "heard": heard, "reply": reply, "status": status},
    )
    del history[config.MAX_HISTORY:]


# --------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------

def render_sidebar() -> dict:
    with st.sidebar:
        st.header("⚙️ Settings")

        env_key = _secret_api_key()
        if env_key:
            st.success("Groq API key loaded from environment / secrets.", icon="🔑")
        override = st.text_input(
            "Groq API key" if not env_key else "Override API key (optional)",
            type="password",
            placeholder="gsk_...",
            help="Get a free key at https://console.groq.com/keys. It is kept only in this browser session.",
        ).strip()
        api_key = override or env_key

        stt_model = st.selectbox("Speech model", config.STT_MODELS, index=config.STT_MODELS.index(config.DEFAULT_STT_MODEL)
                                 if config.DEFAULT_STT_MODEL in config.STT_MODELS else 0)
        llm_options = list(config.LLM_MODELS)
        if config.DEFAULT_LLM_MODEL not in llm_options:
            llm_options.insert(0, config.DEFAULT_LLM_MODEL)
        llm_model = st.selectbox("Understanding model", llm_options, index=llm_options.index(config.DEFAULT_LLM_MODEL))
        language_label = st.selectbox(
            "Spoken language",
            ["Auto-detect", "English", "Urdu", "Hindi", "Arabic", "Pashto"],
        )
        language = {"English": "en", "Urdu": "ur", "Hindi": "hi", "Arabic": "ar", "Pashto": "ps"}.get(language_label)
        confirm_power = st.checkbox(
            "Ask before shutdown / restart / sleep / sign out",
            value=True,
            help="Strongly recommended. Windows also waits "
                 f"{config.SHUTDOWN_DELAY_SECONDS}s before shutting down so you can cancel.",
        )

        if st.button("Test Groq connection", use_container_width=True):
            try:
                _cached_client(api_key).models.list()
                st.success("Connected to Groq.")
            except MissingApiKeyError:
                st.error("Enter a Groq API key first.")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Connection failed: {exc}")

        st.divider()
        st.subheader("⚡ Quick actions")
        quick = [
            ("📁 File Explorer", "open_app", {"name": "file explorer"}),
            ("📝 Notepad", "open_app", {"name": "notepad"}),
            ("📸 Screenshot", "screenshot", {}),
            ("🔒 Lock PC", "lock_pc", {}),
            ("📊 System status", "system_status", {}),
            ("🛑 Cancel shutdown", "cancel_shutdown", {}),
        ]
        for label, action, params in quick:
            if st.button(label, use_container_width=True, key=f"quick_{action}_{label}"):
                result = actions.execute(action, params)
                _log("button", label, result.message, "ok" if result.ok else "error")

        st.divider()
        if st.button("Clear history", use_container_width=True):
            st.session_state.history = []
            st.session_state.pending = None

    return {
        "api_key": api_key,
        "stt_model": stt_model,
        "llm_model": llm_model,
        "language": language,
        "confirm_power": confirm_power,
    }


# --------------------------------------------------------------------------
# Command handling
# --------------------------------------------------------------------------

def _get_client(api_key: str):
    if not api_key:
        return None
    try:
        return _cached_client(api_key)
    except MissingApiKeyError:
        return None


def process_text(text: str, via: str, settings: dict) -> None:
    text = text.strip()
    if not text:
        return
    client = _get_client(settings["api_key"])
    with st.spinner("Thinking..."):
        intent = brain.parse(text, client, settings["llm_model"])

    if intent.action == "chat":
        _log(via, text, intent.reply or "I'm not sure how to help with that.", "info")
        return

    if intent.dangerous and settings["confirm_power"]:
        st.session_state.pending = {"action": intent.action, "params": intent.params, "heard": text}
        _log(via, text, f"⚠️ '{intent.action}' needs your confirmation below.", "info")
        return

    result = actions.execute(intent.action, intent.params)
    _log(via, text, result.message, "ok" if result.ok else "error")


def process_audio(audio_bytes: bytes, settings: dict) -> None:
    client = _get_client(settings["api_key"])
    if client is None:
        _log("voice", "(voice recording)", "Add your Groq API key in the sidebar to use voice commands.", "error")
        return
    try:
        with st.spinner("Transcribing..."):
            text = stt.transcribe(client, audio_bytes, settings["stt_model"], settings["language"])
    except stt.TranscriptionError as exc:
        _log("voice", "(voice recording)", str(exc), "error")
        return
    process_text(text, "voice", settings)


# --------------------------------------------------------------------------
# UI pieces
# --------------------------------------------------------------------------

def render_pending() -> None:
    pending = st.session_state.pending
    if not pending:
        return
    with st.container(border=True):
        st.warning(f"**Confirm:** you asked me to run **{pending['action']}**.\n\n> {pending['heard']}", icon="⚠️")
        col_yes, col_no = st.columns(2)
        if col_yes.button("✅ Yes, do it", type="primary", use_container_width=True):
            result = actions.execute(pending["action"], pending["params"])
            _log("confirm", pending["action"], result.message, "ok" if result.ok else "error")
            st.session_state.pending = None
            st.rerun()
        if col_no.button("❌ Cancel", use_container_width=True):
            _log("confirm", pending["action"], "Cancelled. Nothing was changed.", "info")
            st.session_state.pending = None
            st.rerun()


def render_history() -> None:
    history = st.session_state.history
    if not history:
        st.info("No commands yet. Click the microphone, speak, then click it again to stop - or type below.", icon="💡")
        return
    icons = {"voice": "🎙️", "text": "⌨️", "button": "🖱️", "confirm": "✔️"}
    for entry in history:
        with st.container(border=True):
            st.markdown(f"{icons.get(entry['via'], '•')} **{entry['heard']}**")
            st.caption(entry["time"])
            if entry["status"] == "ok":
                st.success(entry["reply"], icon="✅")
            elif entry["status"] == "error":
                st.error(entry["reply"], icon="🚫")
            else:
                st.info(entry["reply"], icon="💬")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> None:
    _init_state()
    settings = render_sidebar()

    st.title("🎙️ VoxPilot")
    st.caption("Voice-controlled Windows 10 assistant · speech by Groq Whisper · runs on your PC")

    if not actions.IS_WINDOWS:
        st.warning(
            "VoxPilot is running on a non-Windows machine (for example Streamlit Community Cloud), "
            "so PC actions are disabled. Run it locally on your Windows 10 PC to control it.",
            icon="🖥️",
        )
    if not settings["api_key"]:
        st.info("Add your Groq API key in the sidebar to enable voice and AI understanding. "
                "Typed commands like 'open notepad' work without it.", icon="🔑")

    st.subheader("1 · Speak a command")
    audio = st.audio_input(
        "Click the mic (allow access when your browser asks), speak, then click stop.",
        key=f"mic_{st.session_state.mic_key}",
    )
    typed = st.chat_input("...or type a command, e.g. 'open downloads', 'volume up', 'shut down'")

    if audio is not None:
        process_audio(audio.getvalue(), settings)
        st.session_state.mic_key += 1  # fresh recorder for the next command
        st.rerun()
    if typed:
        process_text(typed, "text", settings)

    render_pending()
    st.subheader("2 · Activity")
    render_history()


main()

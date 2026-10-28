# 🎙️ VoxPilot

A voice-controlled assistant for **Windows 10**. Speak or type a command in a local
browser dashboard and VoxPilot does it: open File Explorer, launch apps, search the web,
change the volume, take screenshots, lock the PC, shut it down, and more.

* **Speech recognition:** online, via [Groq](https://console.groq.com) hosted Whisper
* **Understanding:** fast built-in rules first, then a Groq LLM for free-form requests
* **Interface:** local [Streamlit](https://streamlit.io) dashboard with a microphone button
* **Safe by design:** the AI can only choose from a fixed list of actions - it can never run arbitrary commands

---

## ⚠️ Read this first: where it has to run

VoxPilot controls the computer **it is running on**. If you deploy it to Streamlit Community
Cloud (a remote Linux server), it can transcribe your voice but **cannot** open File Explorer or
shut down *your* laptop. In that case the dashboard shows a warning and disables PC actions.

To control your Windows 10 PC, run VoxPilot **locally on that PC** (instructions below).
The server is bound to `127.0.0.1`, so nobody else on your network can reach it.
Do not expose it to the internet through tunnels or port-forwarding: anyone who could open the
page could control your PC.

---

## Features

| Say or type | What happens |
|---|---|
| "Open Notepad" / "open calculator" / "open file explorer" | Launches the app from an allow-list |
| "Open downloads" / "open my documents" | Opens the folder in File Explorer |
| "Open YouTube" / "go to github.com" | Opens the site in your default browser |
| "Search for python tutorials" | Google search |
| "Search for lo-fi music on YouTube" | YouTube search |
| "Volume up" / "lower the volume by 20 percent" / "mute" | Controls system volume |
| "Take a screenshot" | Saves a PNG to `Pictures\VoxPilot` |
| "Show desktop" | Minimises all windows |
| "Type Hello World" | Types into the focused window |
| "Close Notepad" | Politely closes an allow-listed app (no force-kill) |
| "Lock the computer" | Locks Windows |
| "Shut down the computer" / "restart" / "sleep" / "sign out" | Asks you to **confirm**, then runs |
| "Cancel shutdown" | Aborts a pending shutdown or restart |
| "What time is it" / "system status" / "battery" | Reports time, CPU, RAM, disk, battery |
| Anything else ("I'm too hot, turn the sound down a bit") | The Groq LLM maps it to one of the actions above |

Commands starting with a wake phrase such as "VoxPilot, ..." or "please ..." work too.
Non-English speech is supported through the *Spoken language* setting (the AI layer handles it).

---

## Quick start (Windows 10)

**Requirements:** Windows 10, [Python 3.10+](https://www.python.org/downloads/) (tick *Add python.exe to PATH*),
a microphone, and a free [Groq API key](https://console.groq.com/keys).

```bat
git clone https://github.com/<your-username>/voxpilot.git
cd voxpilot
setup.bat
```

`setup.bat` creates a virtual environment, installs `requirements.txt`, and creates a `.env` file.
Open `.env` and paste your key:

```
GROQ_API_KEY=gsk_your_key_here
```

Then start it:

```bat
run_voxpilot.bat
```

Your browser opens `http://localhost:8501`. Click the microphone, **allow access** when the browser asks,
speak, and click stop. The command is transcribed, understood and executed.

### Manual install (if you prefer)

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
streamlit run app.py --server.address 127.0.0.1
```

---

## Running in the background

Double-click **`run_voxpilot_background.vbs`**. It starts the server with no console window and opens
the dashboard. Close the browser tab whenever you like; the server keeps running and you can come back to
`http://localhost:8501` at any time. Stop it with **`stop_voxpilot.bat`**.

**Start automatically when you log in:** press `Win + R`, type `shell:startup`, and put a shortcut to
`run_voxpilot_background.vbs` in that folder.

> The microphone is **push-to-talk**: browsers only allow microphone access while a page is open, and
> Streamlit records when you press the button. VoxPilot does not listen continuously, which is also a
> privacy benefit.

---

## Deploying with Streamlit

* **Locally (recommended, full functionality):** `streamlit run app.py --server.address 127.0.0.1`
* **Streamlit Community Cloud (demo only):** push to GitHub, create the app at
  [share.streamlit.io](https://share.streamlit.io) with `app.py` as the entry point, and add this under
  *Settings → Secrets*:
  ```toml
  GROQ_API_KEY = "gsk_your_key_here"
  ```
  The dashboard, microphone and speech recognition work, but PC actions are disabled because the server is
  not your PC. Anyone with the URL could use your Groq quota, so set the app to private
  (*Settings → Sharing*) or leave the key out and let visitors paste their own.

---

## How it works

```
 Browser mic ──► st.audio_input ──► Groq Whisper ──► text ─┐
 Typed command ───────────────────────────────────────────┤
                                                           ▼
                                     rule parser (instant, offline)
                                              │ no match
                                              ▼
                              Groq LLM → JSON {action, params}
                                              │ validated against registry
                                              ▼
                      dangerous? ── yes ─► confirmation buttons
                                              │ no / confirmed
                                              ▼
                                   voxpilot/actions.py → Windows
```

### Safety model

* **Allow-lists:** apps, folders and websites come from fixed tables in `voxpilot/actions.py`.
* **No shell:** subprocesses receive argument lists, never `shell=True`; web searches are URL-encoded.
* **LLM output is untrusted:** unknown actions become plain chat replies and unknown parameters are dropped.
* **Confirmation:** shutdown, restart, sleep and sign out always ask first (toggle in the sidebar), whether
  they came from the rules or the AI. Windows also waits 30 s (`VOXPILOT_SHUTDOWN_DELAY`) so you can say
  "cancel shutdown".
* **Local only:** the launchers bind to `127.0.0.1`.
* **Privacy:** audio recordings and your command text are sent to Groq for processing. Nothing is stored by VoxPilot.

---

## Configuration

All optional; set in `.env` or the environment.

| Variable | Default | Purpose |
|---|---|---|
| `GROQ_API_KEY` | - | Your Groq key (also supported via Streamlit secrets or the sidebar) |
| `VOXPILOT_STT_MODEL` | `whisper-large-v3-turbo` | Speech-to-text model |
| `VOXPILOT_LLM_MODEL` | `openai/gpt-oss-20b` | Model that interprets free-form requests |
| `VOXPILOT_SHUTDOWN_DELAY` | `30` | Seconds before shutdown/restart takes effect |
| `VOXPILOT_SCREENSHOT_DIR` | `~/Pictures/VoxPilot` | Where screenshots go |

Groq retires models periodically (for example `llama-3.3-70b-versatile` was deprecated on 16 Aug 2026).
If you get a "model not found" error, pick a current ID from <https://console.groq.com/docs/models>
and set `VOXPILOT_LLM_MODEL` / `VOXPILOT_STT_MODEL`.

---

## Adding your own command

1. Write a function in `voxpilot/actions.py` that returns a message (raise `ActionError` on failure).
2. Register it in the `_SPECS` list with a description and parameter hints (set `dangerous=True` for
   anything destructive). The LLM prompt is generated from this list automatically.
3. Optionally add a phrase pattern in `voxpilot/brain.py` → `parse_rules` for instant, offline handling.
4. Add a test in `tests/test_brain.py`.

To allow another app, add it to the `APPS` (and `CLOSABLE`) dictionaries.

---

## Project structure

```
voxpilot/
├── app.py                  # Streamlit dashboard
├── voxpilot/
│   ├── actions.py          # Windows actions + registry + allow-lists
│   ├── brain.py            # rule parser + Groq LLM intent parser
│   ├── stt.py              # Groq Whisper transcription
│   ├── groq_client.py      # Groq client factory
│   └── config.py           # settings / env vars
├── tests/test_brain.py     # unit tests (no network, no real PC actions)
├── .streamlit/             # theme + secrets template
├── setup.bat               # one-time setup
├── run_voxpilot.bat        # start with a console window
├── run_voxpilot_background.vbs  # start hidden
├── stop_voxpilot.bat       # stop the background server
├── requirements.txt
└── .env.example
```

## Tests

```bash
python -m unittest discover -s tests -v
```

The tests cover the command parser, LLM-output validation, the safety rules and the exact Windows commands
that would be issued (with the OS layer mocked). They run on any OS; GitHub Actions runs them on every push.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| Browser never asks for the microphone | Use `http://localhost:8501` (not your LAN IP). Check the padlock icon → allow Microphone, and Windows *Settings → Privacy → Microphone*. |
| "The recording was too short" | Speak for at least a second before clicking stop. |
| "Speech recognition failed: ... model ..." | The model ID may be retired; see *Configuration*. |
| "Connection failed" in *Test Groq connection* | Check the key and your internet connection / proxy. |
| An app does not open | It may not be installed or not registered with Windows. Edit its entry in `APPS`. |
| "Sleep" actually hibernates | Windows does this when hibernation is on. Run `powercfg -h off` as admin to get true sleep. |
| `streamlit` not recognised | Use `run_voxpilot.bat` (it uses the virtual environment). |
| Volume changes are small | Each step is about 2%; say "volume up by 20 percent". |

## Known limitations

* Push-to-talk only; there is no always-on wake word.
* Volume uses the media keys, so it changes in 2% steps and cannot set an exact level.
* Closing apps is a graceful request; apps with unsaved work may ask what to do.
* Tested logic-wise on Linux with the Windows layer mocked; the real Windows calls (`os.startfile`,
  `shutdown`, `taskkill`, media keys) use standard Windows APIs, but please try the commands on your own PC
  first - start with "open notepad" and "take a screenshot" before the power commands.

## License

MIT - see [LICENSE](LICENSE).

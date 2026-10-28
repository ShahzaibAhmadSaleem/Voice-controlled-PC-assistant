"""Windows actions VoxPilot can perform.

Design rules
------------
* Every action is registered in ``ACTIONS`` with a description and a parameter
  spec. The LLM may only pick from this registry - it can never run arbitrary
  commands.
* No ``shell=True`` anywhere. Subprocesses get argument lists.
* Apps, folders and websites come from fixed allow-lists below.
* Power actions (shutdown, restart, sleep, sign out) are flagged
  ``dangerous`` so the UI asks for confirmation first.
* On non-Windows systems the handlers return a friendly message instead of
  crashing, so the dashboard can still be opened for testing.
"""

from __future__ import annotations

import ctypes
import datetime as dt
import os
import subprocess
import sys
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable
from urllib.parse import quote_plus

from . import config

IS_WINDOWS = sys.platform == "win32"


class ActionError(Exception):
    """Raised when an action cannot be completed; message is shown to the user."""


@dataclass(frozen=True)
class Result:
    ok: bool
    message: str


# --------------------------------------------------------------------------
# Allow-lists
# --------------------------------------------------------------------------

# alias -> (launch target for os.startfile, friendly name)
APPS: dict[str, tuple[str, str]] = {
    "file explorer": ("explorer.exe", "File Explorer"),
    "explorer": ("explorer.exe", "File Explorer"),
    "files": ("explorer.exe", "File Explorer"),
    "this pc": ("shell:MyComputerFolder", "This PC"),
    "my computer": ("shell:MyComputerFolder", "This PC"),
    "notepad": ("notepad.exe", "Notepad"),
    "calculator": ("calc.exe", "Calculator"),
    "calc": ("calc.exe", "Calculator"),
    "paint": ("mspaint.exe", "Paint"),
    "task manager": ("taskmgr.exe", "Task Manager"),
    "command prompt": ("cmd.exe", "Command Prompt"),
    "cmd": ("cmd.exe", "Command Prompt"),
    "terminal": ("cmd.exe", "Command Prompt"),
    "powershell": ("powershell.exe", "PowerShell"),
    "control panel": ("control.exe", "Control Panel"),
    "settings": ("ms-settings:", "Settings"),
    "windows settings": ("ms-settings:", "Settings"),
    "wordpad": ("write.exe", "WordPad"),
    "snipping tool": ("snippingtool.exe", "Snipping Tool"),
    "chrome": ("chrome.exe", "Google Chrome"),
    "google chrome": ("chrome.exe", "Google Chrome"),
    "edge": ("msedge.exe", "Microsoft Edge"),
    "microsoft edge": ("msedge.exe", "Microsoft Edge"),
    "firefox": ("firefox.exe", "Firefox"),
    "word": ("winword.exe", "Microsoft Word"),
    "excel": ("excel.exe", "Microsoft Excel"),
    "powerpoint": ("powerpnt.exe", "Microsoft PowerPoint"),
    "spotify": ("spotify.exe", "Spotify"),
    "vs code": ("code.exe", "VS Code"),
    "vscode": ("code.exe", "VS Code"),
    "visual studio code": ("code.exe", "VS Code"),
}

# alias -> (process image name for taskkill, friendly name)
CLOSABLE: dict[str, tuple[str, str]] = {
    "notepad": ("notepad.exe", "Notepad"),
    "calculator": ("CalculatorApp.exe", "Calculator"),
    "calc": ("CalculatorApp.exe", "Calculator"),
    "paint": ("mspaint.exe", "Paint"),
    "task manager": ("taskmgr.exe", "Task Manager"),
    "chrome": ("chrome.exe", "Google Chrome"),
    "google chrome": ("chrome.exe", "Google Chrome"),
    "edge": ("msedge.exe", "Microsoft Edge"),
    "microsoft edge": ("msedge.exe", "Microsoft Edge"),
    "firefox": ("firefox.exe", "Firefox"),
    "word": ("winword.exe", "Microsoft Word"),
    "excel": ("excel.exe", "Microsoft Excel"),
    "powerpoint": ("powerpnt.exe", "Microsoft PowerPoint"),
    "spotify": ("spotify.exe", "Spotify"),
    "vs code": ("code.exe", "VS Code"),
    "vscode": ("code.exe", "VS Code"),
    "command prompt": ("cmd.exe", "Command Prompt"),
    "cmd": ("cmd.exe", "Command Prompt"),
    "powershell": ("powershell.exe", "PowerShell"),
}

# alias -> folder name under the user's profile
FOLDERS: dict[str, str] = {
    "downloads": "Downloads",
    "download": "Downloads",
    "documents": "Documents",
    "document": "Documents",
    "desktop": "Desktop",
    "pictures": "Pictures",
    "photos": "Pictures",
    "music": "Music",
    "videos": "Videos",
}

SITES: dict[str, str] = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "github": "https://github.com",
    "facebook": "https://www.facebook.com",
    "twitter": "https://twitter.com",
    "x": "https://x.com",
    "instagram": "https://www.instagram.com",
    "linkedin": "https://www.linkedin.com",
    "reddit": "https://www.reddit.com",
    "whatsapp": "https://web.whatsapp.com",
    "chatgpt": "https://chatgpt.com",
    "wikipedia": "https://www.wikipedia.org",
    "amazon": "https://www.amazon.com",
    "netflix": "https://www.netflix.com",
    "stack overflow": "https://stackoverflow.com",
}


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

def _require_windows() -> None:
    if not IS_WINDOWS:
        raise ActionError(
            "This action only works when VoxPilot runs on Windows. "
            "Run the app locally on your Windows 10 PC."
        )


def _startfile(target: str) -> None:
    _require_windows()
    try:
        os.startfile(target)  # type: ignore[attr-defined]  # noqa: S606 - allow-listed
    except OSError as exc:
        raise ActionError(f"Could not open '{target}'. Is it installed? ({exc})") from exc


def _run(args: list[str]) -> None:
    _require_windows()
    try:
        subprocess.run(  # noqa: S603 - fixed argument lists, no shell
            args,
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except FileNotFoundError as exc:
        raise ActionError(f"Command not found: {args[0]}") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or "").strip()
        raise ActionError(detail or f"Command failed: {' '.join(args)}") from exc
    except subprocess.TimeoutExpired as exc:
        raise ActionError("The command timed out.") from exc


def _tap_key(vk_code: int, times: int = 1) -> None:
    """Press a virtual key using the Win32 keybd_event API."""
    _require_windows()
    user32 = ctypes.windll.user32  # type: ignore[attr-defined]
    keyeventf_keyup = 0x0002
    for _ in range(times):
        user32.keybd_event(vk_code, 0, 0, 0)
        user32.keybd_event(vk_code, 0, keyeventf_keyup, 0)


def _clean(value: object) -> str:
    return str(value or "").strip().lower()


# --------------------------------------------------------------------------
# Action handlers  (each returns a human-readable message)
# --------------------------------------------------------------------------

def open_app(name: str = "", **_: object) -> str:
    key = _clean(name)
    if key in FOLDERS:
        return open_folder(name=key)
    if key not in APPS:
        raise ActionError(
            f"I don't have '{name}' on my allowed app list. "
            f"Try: {', '.join(sorted({v[1] for v in APPS.values()}))}."
        )
    target, friendly = APPS[key]
    _startfile(target)
    return f"Opened {friendly}."


def close_app(name: str = "", **_: object) -> str:
    key = _clean(name)
    if key not in CLOSABLE:
        raise ActionError(f"I can't close '{name}'. Allowed: {', '.join(sorted(CLOSABLE))}.")
    image, friendly = CLOSABLE[key]
    _run(["taskkill", "/IM", image])  # graceful close, no /F so unsaved work is protected
    return f"Asked {friendly} to close."


def open_folder(name: str = "", **_: object) -> str:
    key = _clean(name)
    if key not in FOLDERS:
        raise ActionError(f"Unknown folder '{name}'. Try: {', '.join(sorted(set(FOLDERS.values())))}.")
    path = Path.home() / FOLDERS[key]
    if not path.exists():
        raise ActionError(f"Folder not found: {path}")
    _startfile(str(path))
    return f"Opened your {FOLDERS[key]} folder."


def open_website(name: str = "", **_: object) -> str:
    raw = _clean(name)
    if raw in SITES:
        url = SITES[raw]
    else:
        host = raw.replace(" ", "")
        if "." not in host or any(c in host for c in "/\\:?#@\"'<>"):
            raise ActionError(f"'{name}' doesn't look like a website. Try a name like 'youtube' or 'example.com'.")
        url = f"https://{host}"
    webbrowser.open(url)
    return f"Opened {url}."


def web_search(query: str = "", site: str = "google", **_: object) -> str:
    query = str(query or "").strip()
    if not query:
        raise ActionError("What should I search for?")
    if _clean(site) == "youtube":
        url = f"https://www.youtube.com/results?search_query={quote_plus(query)}"
    else:
        url = f"https://www.google.com/search?q={quote_plus(query)}"
    webbrowser.open(url)
    return f"Searching for '{query}'."


def volume_up(steps: int | str = 5, **_: object) -> str:
    steps = _coerce_steps(steps)
    _tap_key(0xAF, steps)  # VK_VOLUME_UP, each press is about 2%
    return f"Volume up (~{steps * 2}%)."


def volume_down(steps: int | str = 5, **_: object) -> str:
    steps = _coerce_steps(steps)
    _tap_key(0xAE, steps)  # VK_VOLUME_DOWN
    return f"Volume down (~{steps * 2}%)."


def volume_mute(**_: object) -> str:
    _tap_key(0xAD)  # VK_VOLUME_MUTE (toggle)
    return "Toggled mute."


def _coerce_steps(value: object) -> int:
    try:
        return max(1, min(50, int(value)))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 5


def screenshot(**_: object) -> str:
    _require_windows()
    try:
        from PIL import ImageGrab
    except ImportError as exc:  # pragma: no cover
        raise ActionError("Pillow is not installed. Run: pip install Pillow") from exc
    config.SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = config.SCREENSHOT_DIR / f"screenshot_{dt.datetime.now():%Y%m%d_%H%M%S}.png"
    ImageGrab.grab().save(path)
    return f"Screenshot saved to {path}."


def minimize_all(**_: object) -> str:
    _require_windows()
    user32 = ctypes.windll.user32  # type: ignore[attr-defined]
    keyup = 0x0002
    vk_lwin, vk_d = 0x5B, 0x44
    user32.keybd_event(vk_lwin, 0, 0, 0)
    user32.keybd_event(vk_d, 0, 0, 0)
    user32.keybd_event(vk_d, 0, keyup, 0)
    user32.keybd_event(vk_lwin, 0, keyup, 0)
    return "Toggled show desktop."


def type_text(text: str = "", **_: object) -> str:
    text = str(text or "")
    if not text.strip():
        raise ActionError("What should I type?")
    if len(text) > 500:
        raise ActionError("That's too long to type (500 characters max).")
    _require_windows()
    try:
        import pyautogui
    except ImportError as exc:  # pragma: no cover
        raise ActionError("pyautogui is not installed. Run: pip install pyautogui") from exc
    pyautogui.write(text, interval=0.02)
    return f"Typed: {text}"


def lock_pc(**_: object) -> str:
    _require_windows()
    if not ctypes.windll.user32.LockWorkStation():  # type: ignore[attr-defined]
        raise ActionError("Windows refused to lock the workstation.")
    return "Locked the PC."


def shutdown_pc(**_: object) -> str:
    delay = config.SHUTDOWN_DELAY_SECONDS
    _run(["shutdown", "/s", "/t", str(delay)])
    return f"Shutting down in {delay} seconds. Say 'cancel shutdown' to abort."


def restart_pc(**_: object) -> str:
    delay = config.SHUTDOWN_DELAY_SECONDS
    _run(["shutdown", "/r", "/t", str(delay)])
    return f"Restarting in {delay} seconds. Say 'cancel shutdown' to abort."


def cancel_shutdown(**_: object) -> str:
    _run(["shutdown", "/a"])
    return "Cancelled the pending shutdown/restart."


def sleep_pc(**_: object) -> str:
    # Note: if hibernation is enabled on the PC, this hibernates instead.
    _run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])
    return "Putting the PC to sleep."


def sign_out(**_: object) -> str:
    _run(["shutdown", "/l"])
    return "Signing out."


def get_time(**_: object) -> str:
    now = dt.datetime.now()
    return f"It's {now:%I:%M %p} on {now:%A, %d %B %Y}."


def system_status(**_: object) -> str:
    try:
        import psutil
    except ImportError as exc:  # pragma: no cover
        raise ActionError("psutil is not installed. Run: pip install psutil") from exc
    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage(Path.home().anchor or "/")
    parts = [
        f"CPU {cpu:.0f}%",
        f"RAM {mem.percent:.0f}% of {mem.total / 1024**3:.1f} GB",
        f"Disk {disk.percent:.0f}% of {disk.total / 1024**3:.0f} GB",
    ]
    battery = getattr(psutil, "sensors_battery", lambda: None)()
    if battery is not None:
        state = "charging" if battery.power_plugged else "on battery"
        parts.append(f"Battery {battery.percent:.0f}% ({state})")
    return " | ".join(parts)


def help_text(**_: object) -> str:
    return (
        "Try: 'open notepad', 'open downloads', 'open youtube', 'search for python tutorials', "
        "'volume up', 'mute', 'take a screenshot', 'show desktop', 'lock the computer', "
        "'what time is it', 'system status', 'shut down the computer'."
    )


# --------------------------------------------------------------------------
# Registry
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class ActionSpec:
    name: str
    handler: Callable[..., str]
    description: str
    params: dict[str, str] = field(default_factory=dict)
    dangerous: bool = False


_SPECS = [
    ActionSpec("open_app", open_app, "Open an application, File Explorer or Windows Settings.",
               {"name": "app name, e.g. 'notepad', 'file explorer', 'chrome', 'settings'"}),
    ActionSpec("close_app", close_app, "Close a running application.",
               {"name": "app name, e.g. 'notepad', 'chrome'"}),
    ActionSpec("open_folder", open_folder, "Open a user folder in File Explorer.",
               {"name": "one of: downloads, documents, desktop, pictures, music, videos"}),
    ActionSpec("open_website", open_website, "Open a website in the default browser.",
               {"name": "site name like 'youtube' or a domain like 'example.com'"}),
    ActionSpec("web_search", web_search, "Search the web (Google or YouTube).",
               {"query": "search text", "site": "'google' (default) or 'youtube'"}),
    ActionSpec("volume_up", volume_up, "Raise the system volume.",
               {"steps": "optional int 1-50, each step is ~2% (default 5)"}),
    ActionSpec("volume_down", volume_down, "Lower the system volume.",
               {"steps": "optional int 1-50, each step is ~2% (default 5)"}),
    ActionSpec("volume_mute", volume_mute, "Mute or unmute the system volume."),
    ActionSpec("screenshot", screenshot, "Take a screenshot and save it to the Pictures folder."),
    ActionSpec("minimize_all", minimize_all, "Minimize all windows / show the desktop."),
    ActionSpec("type_text", type_text, "Type text into the currently focused window.",
               {"text": "the text to type"}),
    ActionSpec("lock_pc", lock_pc, "Lock the computer."),
    ActionSpec("shutdown_pc", shutdown_pc, "Shut down the computer.", dangerous=True),
    ActionSpec("restart_pc", restart_pc, "Restart the computer.", dangerous=True),
    ActionSpec("cancel_shutdown", cancel_shutdown, "Cancel a pending shutdown or restart."),
    ActionSpec("sleep_pc", sleep_pc, "Put the computer to sleep.", dangerous=True),
    ActionSpec("sign_out", sign_out, "Sign out of Windows.", dangerous=True),
    ActionSpec("get_time", get_time, "Tell the current time and date."),
    ActionSpec("system_status", system_status, "Report CPU, RAM, disk and battery status."),
    ActionSpec("help", help_text, "List example commands."),
]

ACTIONS: dict[str, ActionSpec] = {spec.name: spec for spec in _SPECS}


def describe_actions() -> str:
    """Compact action list used inside the LLM system prompt."""
    lines = []
    for spec in ACTIONS.values():
        params = ", ".join(f"{k}: {v}" for k, v in spec.params.items()) or "no params"
        lines.append(f"- {spec.name}: {spec.description} Params: {params}")
    return "\n".join(lines)


def is_dangerous(action: str) -> bool:
    spec = ACTIONS.get(action)
    return bool(spec and spec.dangerous)


def execute(action: str, params: dict | None = None) -> Result:
    """Run a registered action. Never raises; always returns a Result."""
    spec = ACTIONS.get(action)
    if spec is None:
        return Result(False, f"Unknown action: {action}")
    try:
        message = spec.handler(**(params or {}))
        return Result(True, message)
    except ActionError as exc:
        return Result(False, str(exc))
    except TypeError as exc:
        return Result(False, f"Bad parameters for {action}: {exc}")
    except Exception as exc:  # noqa: BLE001 - last-resort guard for the UI
        return Result(False, f"{action} failed: {exc}")

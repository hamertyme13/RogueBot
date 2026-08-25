"""
Command history skill — lets the user query past commands.

Reads from the conversation history file used by LocalAI.
Also maintains a lightweight spoken-command log in data/command_history.json.
"""

import json
from datetime import datetime
from pathlib import Path

from logger import log


_COMMAND_LOG = Path("data/command_history.json")
_MAX_LOG_ENTRIES = 200


def log_command(command: str) -> None:
    """Append a command to the spoken command log."""

    entries = _load_log()
    entries.append({
        "time": datetime.now().isoformat(),
        "command": command,
    })

    # Keep rolling window
    entries = entries[-_MAX_LOG_ENTRIES:]

    _COMMAND_LOG.parent.mkdir(parents=True, exist_ok=True)
    try:
        with _COMMAND_LOG.open("w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2, ensure_ascii=False)
    except OSError as exc:
        log.warning("Could not save command history: %s", exc)


def _load_log() -> list[dict]:
    if not _COMMAND_LOG.exists():
        return []
    try:
        with _COMMAND_LOG.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def get_recent_commands(command: str) -> str:
    """
    Handle queries like:
    "what did I ask you before"
    "show my last 5 commands"
    "command history"
    "what was my last command"
    """

    entries = _load_log()

    if not entries:
        return "I don't have any command history yet."

    # Try to extract a count: "last 5 commands"
    import re
    count_match = re.search(r"last\s+(\d+)", command.lower())
    count = int(count_match.group(1)) if count_match else 5
    count = min(count, 20)  # cap at 20

    recent = entries[-count:]

    if len(recent) == 1:
        last = recent[-1]
        dt = datetime.fromisoformat(last["time"])
        formatted = dt.strftime("%I:%M %p").lstrip("0")
        return f"Your last command at {formatted} was: {last['command']}."

    lines = []
    for entry in reversed(recent):
        dt = datetime.fromisoformat(entry["time"])
        formatted = dt.strftime("%I:%M %p").lstrip("0")
        lines.append(f"{entry['command']} at {formatted}")

    return f"Your last {len(recent)} commands: " + "; ".join(lines) + "."

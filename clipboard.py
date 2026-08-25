"""
Shared clipboard utility for RogueBot.

Uses macOS `pbpaste` / `pbcopy` so there are no extra dependencies.
Falls back gracefully if the clipboard is empty or unavailable.
"""

import subprocess


def get_clipboard() -> str | None:
    """Return the current clipboard text, or None if empty/unavailable."""

    try:
        result = subprocess.run(
            ["pbpaste"],
            capture_output=True,
            text=True,
            timeout=3,
        )

        text = result.stdout.strip()
        return text if text else None

    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def set_clipboard(text: str) -> bool:
    """Write text to the clipboard. Returns True on success."""

    try:
        subprocess.run(
            ["pbcopy"],
            input=text,
            text=True,
            timeout=3,
            check=True,
        )
        return True

    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
        return False

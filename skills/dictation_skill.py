"""
Dictation mode — speak text and have it typed into the active window.

Uses macOS Accessibility / osascript keystroke injection.
Works in any text field that accepts keyboard input.

Commands:
  "start dictating" / "dictation mode" / "type what I say"
  While active: say your text.
  To stop:      "stop dictating" / "done" / "cancel"
"""

import subprocess

from logger import log


_STOP_WORDS = {"stop dictating", "stop", "done", "cancel", "finish", "end dictation"}


def _type_text(text: str) -> None:
    """Inject text into the currently focused app via osascript."""

    # Escape backslashes and double-quotes for AppleScript string
    safe = text.replace("\\", "\\\\").replace('"', '\\"')

    script = f'tell application "System Events" to keystroke "{safe}"'

    try:
        subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        log.warning("Dictation keystroke failed: %s", exc)


def run_dictation_session(listen_fn, speak_fn) -> str:
    """
    Run an interactive dictation session.

    `listen_fn`  — callable matching SpeechSystem.listen() signature,
                   returns str | None.
    `speak_fn`   — callable matching SpeechSystem.speak() signature.

    Returns a summary string for RogueBot to speak after the session ends.
    """

    speak_fn("Dictation mode active. Speak your text. Say stop when finished.")

    typed_count = 0

    while True:
        text = listen_fn(timeout=10, phrase_time_limit=15, show_status=True)

        if text is None:
            # Silence — keep waiting
            continue

        normalized = text.lower().strip().rstrip(".!?")

        if normalized in _STOP_WORDS:
            break

        # Type a space before each phrase (except the first)
        if typed_count > 0:
            _type_text(" ")

        _type_text(text)
        typed_count += 1

    if typed_count == 0:
        return "Dictation cancelled. Nothing was typed."

    return f"Dictation complete. I typed {typed_count} phrase{'s' if typed_count != 1 else ''}."

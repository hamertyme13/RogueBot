"""
macOS system notification skill.

Sends a banner notification via osascript so alerts appear even when
RogueBot's window is in the background or minimised.

Used by the timer and reminder systems in addition to speech.
"""

import subprocess

from logger import log


def send_notification(
    title: str,
    message: str,
    subtitle: str = "RogueBot",
) -> None:
    """
    Post a macOS banner notification.

    Falls back silently if osascript is unavailable (e.g. Linux).
    """

    script = (
        f'display notification "{message}" '
        f'with title "{title}" '
        f'subtitle "{subtitle}"'
    )

    try:
        subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            timeout=3,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        log.debug("Notification not sent: %s", exc)

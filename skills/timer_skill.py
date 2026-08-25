import re
import threading
import time
from queue import Queue


# Module-level notification queue — set by main.py after startup.
# When a timer fires it puts a spoken message here for robot_worker to read.
notification_queue: Queue | None = None

# Track active timers so we can report time remaining
_active_timers: list[dict] = []
_timers_lock = threading.Lock()


def set_timer(command: str) -> str:
    """
    Handle commands such as:
    'set a timer for 5 minutes'
    'set a timer for 30 seconds'
    'timer 2 minutes'
    """

    command = command.lower().strip()

    match = re.search(
        r"(\d+)\s*(second|seconds|sec|minute|minutes|min|hour|hours|hr)",
        command,
    )

    if not match:
        return (
            "I didn't catch the duration. "
            "Try saying 'set a timer for 5 minutes'."
        )

    amount = int(match.group(1))
    unit = match.group(2)

    if unit in ("second", "seconds", "sec"):
        total_seconds = amount
        label = f"{amount} second{'s' if amount != 1 else ''}"

    elif unit in ("minute", "minutes", "min"):
        total_seconds = amount * 60
        label = f"{amount} minute{'s' if amount != 1 else ''}"

    else:  # hour / hours / hr
        total_seconds = amount * 3600
        label = f"{amount} hour{'s' if amount != 1 else ''}"

    _start_timer(total_seconds, label)

    return f"Timer set for {label}."


def list_timers() -> str:
    """Return a spoken summary of all active timers."""

    with _timers_lock:
        active = [t for t in _active_timers if not t["fired"]]

    if not active:
        return "You have no active timers."

    parts = []
    now = time.monotonic()
    for t in active:
        remaining = max(0, t["end_time"] - now)
        mins, secs = divmod(int(remaining), 60)
        if mins > 0:
            parts.append(f"{t['label']} — {mins}m {secs}s left")
        else:
            parts.append(f"{t['label']} — {secs}s left")

    return "Active timers: " + "; ".join(parts) + "."


def cancel_timers() -> str:
    """Cancel all active timers."""

    with _timers_lock:
        count = sum(1 for t in _active_timers if not t["fired"])
        for t in _active_timers:
            t["cancelled"] = True
        _active_timers.clear()

    if count == 0:
        return "You have no active timers to cancel."

    return f"Cancelled {count} timer{'s' if count != 1 else ''}."


def _start_timer(total_seconds: int, label: str) -> None:
    """Fire a background thread that notifies when the timer expires."""

    entry: dict = {
        "label": label,
        "end_time": time.monotonic() + total_seconds,
        "fired": False,
        "cancelled": False,
    }

    with _timers_lock:
        _active_timers.append(entry)

    def _ring():
        entry["fired"] = True
        if entry.get("cancelled"):
            return
        message = f"Timer done. {label} have elapsed."
        print(f"\n⏰ {message}\n")
        # macOS banner notification
        try:
            from skills.notification_skill import send_notification
            send_notification("⏰ Timer", message)
        except Exception:
            pass
        if notification_queue is not None:
            notification_queue.put(message)

    t = threading.Timer(total_seconds, _ring)
    t.daemon = True
    t.start()

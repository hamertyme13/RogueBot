import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable


_REMINDERS_FILE = Path("data/reminders.json")
_CHECK_INTERVAL = 30  # seconds between checks


def _load() -> list[dict]:
    if not _REMINDERS_FILE.exists():
        return []
    try:
        with _REMINDERS_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save(reminders: list[dict]) -> None:
    _REMINDERS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with _REMINDERS_FILE.open("w", encoding="utf-8") as f:
        json.dump(reminders, f, indent=4, ensure_ascii=False)


def _parse_time(time_str: str) -> datetime | None:
    """
    Parse a time like '3pm', '3:30pm', '15:00' into today's datetime.
    Returns None if unparseable.
    """

    time_str = time_str.strip().lower().replace(" ", "")

    formats = [
        "%I%p",       # 3pm
        "%I:%M%p",    # 3:30pm
        "%H:%M",      # 15:00
        "%H:%M:%S",   # 15:00:00
    ]

    today = datetime.now().date()

    for fmt in formats:
        try:
            t = datetime.strptime(time_str, fmt)
            return datetime.combine(today, t.time())
        except ValueError:
            continue

    return None


def list_reminders() -> str:
    """Return all pending reminders as a spoken string."""

    reminders = _load()

    if not reminders:
        return "You have no reminders set."

    now = datetime.now()
    future = [
        r for r in reminders
        if datetime.fromisoformat(r["time"]) > now
    ]

    if not future:
        return "You have no upcoming reminders."

    parts = []
    for r in sorted(future, key=lambda x: x["time"]):
        dt = datetime.fromisoformat(r["time"])
        formatted = dt.strftime("%I:%M %p").lstrip("0")
        parts.append(f"{r['message']} at {formatted}")

    return "Your reminders: " + "; ".join(parts) + "."


def cancel_reminder(command: str) -> str:
    """
    Handle 'cancel my reminder to call the dentist' or
    'cancel all reminders'.
    """

    command = command.lower().strip()

    reminders = _load()

    if not reminders:
        return "You have no reminders to cancel."

    if "all" in command:
        _save([])
        return "All reminders cancelled."

    # Find by keyword match in message
    for prefix in ("cancel my reminder to ", "cancel reminder to ", "cancel reminder "):
        if command.startswith(prefix):
            keyword = command[len(prefix):].strip()
            break
    else:
        keyword = command.replace("cancel", "").strip()

    before = len(reminders)
    reminders = [
        r for r in reminders
        if keyword not in r["message"].lower()
    ]

    if len(reminders) == before:
        return f"I couldn't find a reminder matching '{keyword}'."

    _save(reminders)
    return f"Reminder cancelled."


def add_reminder(command: str) -> str:
    """
    Handle commands such as:
    'remind me at 3pm to call the dentist'
    'remind me at 3:30pm to take my medication'
    """

    command = command.lower().strip()

    # Strip trigger words
    for prefix in ("remind me at ", "set a reminder at ", "reminder at "):
        if command.startswith(prefix):
            remainder = command[len(prefix):]
            break
    else:
        return (
            "Try saying 'remind me at 3pm to call the dentist'."
        )

    # Split on " to " to get time and message
    if " to " not in remainder:
        return "Tell me what time and what to remind you. For example, 'remind me at 3pm to call the dentist'."

    time_part, message = remainder.split(" to ", 1)

    remind_dt = _parse_time(time_part)

    if remind_dt is None:
        return f"I couldn't understand the time '{time_part}'. Try '3pm' or '3:30pm'."

    # If the time has already passed today, don't add it
    if remind_dt < datetime.now():
        return f"That time has already passed today."

    reminders = _load()

    reminders.append({
        "time": remind_dt.isoformat(),
        "message": message.strip().rstrip(".!?"),
    })

    _save(reminders)

    formatted = remind_dt.strftime("%I:%M %p").lstrip("0")

    return f"Reminder set for {formatted}: {message.strip()}."


def check_reminders(speech_callback) -> None:
    """
    Called periodically by the robot worker.
    Fires any due reminders and removes them.
    `speech_callback` is a callable that accepts a string and speaks it.
    """

    reminders = _load()

    if not reminders:
        return

    now = datetime.now()
    pending = []
    fired = False

    for r in reminders:
        try:
            remind_dt = datetime.fromisoformat(r["time"])
        except (ValueError, KeyError):
            continue

        if remind_dt <= now:
            msg = f"Reminder: {r['message']}."
            try:
                from skills.notification_skill import send_notification
                send_notification("🔔 Reminder", r["message"])
            except Exception:
                pass
            speech_callback(msg)
            fired = True
        else:
            pending.append(r)

    if fired:
        _save(pending)


def start_reminder_checker(speech_callback) -> None:
    """
    Launch a daemon thread that checks for due reminders every
    CHECK_INTERVAL seconds.
    """

    def _loop():
        while True:
            threading.Event().wait(_CHECK_INTERVAL)
            check_reminders(speech_callback)

    t = threading.Thread(target=_loop, daemon=True, name="ReminderChecker")
    t.start()

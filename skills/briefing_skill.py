"""
Daily briefing skill — a spoken morning summary.

Combines: greeting, date, weather, today's reminders, top news headlines.

Triggered by: "good morning", "morning briefing", "daily briefing",
              "what's my briefing", "start my day"
"""

from datetime import datetime

from skills.news_skill import get_news
from skills.reminder_skill import _load as _load_reminders
from skills.time_skill import get_date
from skills.weather_skill import get_weather


def get_briefing() -> str:
    """Assemble and return a full morning briefing."""

    parts: list[str] = []

    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 17:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    parts.append(f"{greeting}. Here is your briefing.")
    parts.append(get_date())

    # Weather (non-fatal if offline)
    try:
        parts.append(get_weather())
    except Exception:
        pass

    # Reminders due today
    try:
        today = datetime.now().date()
        reminders = _load_reminders()
        due_today = [
            r for r in reminders
            if datetime.fromisoformat(r["time"]).date() == today
        ]
        if due_today:
            count = len(due_today)
            msgs = "; ".join(
                f"{r['message']} at "
                f"{datetime.fromisoformat(r['time']).strftime('%I:%M %p').lstrip('0')}"
                for r in sorted(due_today, key=lambda x: x["time"])
            )
            parts.append(
                f"You have {count} reminder{'s' if count != 1 else ''} today: {msgs}."
            )
        else:
            parts.append("You have no reminders scheduled for today.")
    except Exception:
        pass

    # Top news headlines
    try:
        parts.append(get_news())
    except Exception:
        pass

    parts.append("That's your briefing. Have a great day.")

    return " ".join(parts)

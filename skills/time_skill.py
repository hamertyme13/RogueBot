from datetime import datetime


def get_time() -> str:
    """Return the current local time."""

    now = datetime.now()

    formatted_time = now.strftime("%I:%M %p").lstrip("0")

    return f"It is {formatted_time}."


def get_date() -> str:
    """Return today's date."""

    today = datetime.now()

    formatted_date = today.strftime("%A, %B %d, %Y")

    return f"Today is {formatted_date}."
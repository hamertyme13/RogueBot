import json
from pathlib import Path


_NOTES_FILE = Path("data/notes.json")


def _load() -> dict[str, list[str]]:
    """Load all named lists from disk."""

    if not _NOTES_FILE.exists():
        return {}

    try:
        with _NOTES_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)

    except (json.JSONDecodeError, OSError):
        return {}


def _save(data: dict[str, list[str]]) -> None:
    """Persist all named lists to disk."""

    _NOTES_FILE.parent.mkdir(parents=True, exist_ok=True)

    with _NOTES_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def _parse_list_and_item(command: str, prefix: str) -> tuple[str, str]:
    """
    Extract list name and item from commands like:
    'add milk to my shopping list'  -> ('shopping', 'milk')
    'add call dentist to my to-do list' -> ('to-do', 'call dentist')
    """

    remainder = command[len(prefix):].strip()

    # "X to my Y list" or "X to Y list"
    for separator in (" to my ", " to "):
        if separator in remainder:
            parts = remainder.split(separator, 1)
            item = parts[0].strip()
            list_name = parts[1].removesuffix(" list").strip()
            return list_name, item

    return "notes", remainder


def add_note(command: str) -> str:
    """Handle 'add X to my Y list'."""

    list_name, item = _parse_list_and_item(command, "add ")

    if not item:
        return "Tell me what to add and to which list."

    data = _load()
    data.setdefault(list_name, [])

    if item not in data[list_name]:
        data[list_name].append(item)
        _save(data)

    return f"Added {item} to your {list_name} list."


def read_list(command: str) -> str:
    """Handle 'read my shopping list' / 'what's on my to-do list'."""

    command = command.lower().strip()

    data = _load()

    # Try to extract list name
    for separator in ("my ", "the "):
        if separator in command:
            list_name = command.split(separator, 1)[1].removesuffix(" list").strip()
            break
    else:
        list_name = "notes"

    items = data.get(list_name, [])

    if not items:
        return f"Your {list_name} list is empty."

    joined = ", ".join(items)

    return f"Your {list_name} list: {joined}."


def clear_list(command: str) -> str:
    """Handle 'clear my shopping list'."""

    command = command.lower().strip()

    for separator in ("my ", "the "):
        if separator in command:
            list_name = command.split(separator, 1)[1].removesuffix(" list").strip()
            break
    else:
        list_name = "notes"

    data = _load()

    if list_name not in data:
        return f"I don't have a {list_name} list."

    del data[list_name]
    _save(data)

    return f"Cleared your {list_name} list."

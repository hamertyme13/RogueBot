"""
Clipboard skill — lets RogueBot act on whatever text is on the clipboard.

Commands:
  "read this to me" / "read my clipboard"
  "summarise this" / "summarise my clipboard"
  "explain this"
  "fix the grammar" / "fix this"
  "translate this to Spanish" (or any language)
  "what's on my clipboard"
"""

from clipboard import get_clipboard


# Words that signal the user means the clipboard
_CLIPBOARD_WORDS = ("this", "it", "that", "my clipboard", "the clipboard")


def _refers_to_clipboard(command: str) -> bool:
    return any(w in command for w in _CLIPBOARD_WORDS)


def _truncate(text: str, max_chars: int = 3000) -> str:
    """Truncate clipboard text so it fits in a prompt."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n… [truncated]"


def read_clipboard() -> str:
    """Return the clipboard contents as a spoken string."""

    text = get_clipboard()

    if not text:
        return "Your clipboard is empty."

    # Limit reading to a sensible spoken length
    if len(text) > 500:
        spoken = text[:500].rsplit(" ", 1)[0]
        return f"Your clipboard says: {spoken} … and more."

    return f"Your clipboard says: {text}"


def clipboard_to_ai(command: str, ask_ai_fn) -> str:
    """
    Build a prompt from the clipboard content + the user's instruction
    and send it to the AI.

    `ask_ai_fn` is CommandProcessor._ask_ai (or equivalent).
    """

    text = get_clipboard()

    if not text:
        return "Your clipboard is empty. Copy something first."

    content = _truncate(text)
    command_lower = command.lower()

    # --- Summarise ---
    if any(w in command_lower for w in ("summarise", "summarize", "summary")):
        prompt = f"Summarise the following text concisely:\n\n{content}"

    # --- Explain ---
    elif "explain" in command_lower:
        prompt = f"Explain the following clearly and concisely:\n\n{content}"

    # --- Fix grammar ---
    elif any(w in command_lower for w in ("fix", "correct", "grammar", "spelling")):
        prompt = (
            f"Fix any grammar, spelling, or punctuation errors in the following "
            f"text. Return only the corrected text:\n\n{content}"
        )

    # --- Translate ---
    elif "translate" in command_lower:
        # Try to extract target language: "translate this to French"
        import re
        lang_match = re.search(r"to\s+([a-zA-Z]+)\s*$", command_lower)
        lang = lang_match.group(1).capitalize() if lang_match else "English"
        prompt = f"Translate the following text to {lang}:\n\n{content}"

    # --- Generic / "what is this" ---
    else:
        prompt = (
            f"The user asked: '{command}'\n\n"
            f"Here is the text from their clipboard:\n\n{content}"
        )

    return ask_ai_fn(prompt)

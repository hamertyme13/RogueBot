"""
Word definition and spell-check skill.

Uses the Free Dictionary API (https://api.dictionaryapi.dev) — no key needed.

Commands:
  "define serendipity"
  "what does ephemeral mean"
  "how do you spell necessary"
  "spell accommodation"
"""

import json
import re
import urllib.error
import urllib.parse
import urllib.request

from logger import log


_DICT_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/"


def _fetch_definition(word: str) -> dict | None:
    """Fetch dictionary entry for a word. Returns first result or None."""

    url = _DICT_URL + urllib.parse.quote(word.lower())

    try:
        with urllib.request.urlopen(url, timeout=6) as response:
            data = json.loads(response.read().decode("utf-8"))
            if isinstance(data, list) and data:
                return data[0]
    except (urllib.error.URLError, json.JSONDecodeError) as exc:
        log.warning("Dictionary lookup failed for '%s': %s", word, exc)

    return None


def define_word(command: str) -> str:
    """
    Handle 'define X' and 'what does X mean'.
    Returns the first definition found.
    """

    command = command.lower().strip()

    for prefix in (
        "define ",
        "what does ",
        "what is the definition of ",
        "what is the meaning of ",
        "meaning of ",
        "definition of ",
    ):
        if command.startswith(prefix):
            word = command[len(prefix):].strip().rstrip(".?!")
            # Strip trailing "mean" from "what does X mean"
            word = re.sub(r"\s+mean$", "", word).strip()
            break
    else:
        word = command

    if not word:
        return "Which word would you like me to define?"

    entry = _fetch_definition(word)

    if entry is None:
        return f"I couldn't find a definition for '{word}'."

    # Pull first meaning, first definition
    try:
        meanings = entry.get("meanings", [])
        if not meanings:
            return f"I found an entry for '{word}' but it had no definitions."

        first = meanings[0]
        part_of_speech = first.get("partOfSpeech", "word")
        definitions = first.get("definitions", [])

        if not definitions:
            return f"I found '{word}' as a {part_of_speech} but the definition was empty."

        definition = definitions[0].get("definition", "")
        example = definitions[0].get("example", "")

        response = f"{word.capitalize()}: {part_of_speech}. {definition}"

        if example:
            response += f" For example: {example}"

        return response

    except (KeyError, IndexError, TypeError):
        return f"I found an entry for '{word}' but couldn't read the definition."


def spell_word(command: str) -> str:
    """
    Handle 'how do you spell X' and 'spell X'.
    Looks up the word and returns the correct spelling from the API.
    If the API finds it, it's spelled correctly. If not, reports it.
    """

    command = command.lower().strip().rstrip(".?!")

    for prefix in ("how do you spell ", "how to spell ", "spell "):
        if command.startswith(prefix):
            word = command[len(prefix):].strip()
            break
    else:
        word = command

    if not word:
        return "Which word would you like me to spell?"

    entry = _fetch_definition(word)

    if entry is not None:
        # The API returns the canonical spelling
        canonical = entry.get("word", word)
        spelled = ", ".join(canonical.upper())
        return f"{canonical} is spelled: {spelled}."

    return (
        f"I couldn't verify the spelling of '{word}'. "
        "It may be misspelled or not in my dictionary."
    )

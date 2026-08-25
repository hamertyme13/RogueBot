import json
import urllib.error
import urllib.parse
import urllib.request


_DDG_URL = "https://api.duckduckgo.com/"


def web_search(command: str) -> str:
    """
    Handle commands such as:
    'search for the latest news on SpaceX'
    'look up Python programming language'
    'what is the Eiffel Tower'
    """

    command = command.lower().strip()

    # Strip common trigger phrases to get the raw query
    for prefix in (
        "search for ",
        "search ",
        "look up ",
        "look up information on ",
        "look up information about ",
        "find information on ",
        "find information about ",
        "what is ",
        "what are ",
        "tell me about ",
        "who is ",
        "who was ",
    ):
        if command.startswith(prefix):
            query = command[len(prefix):].strip()
            break
    else:
        query = command

    if not query:
        return "What would you like me to search for?"

    params = urllib.parse.urlencode({
        "q": query,
        "format": "json",
        "no_html": "1",
        "skip_disambig": "1",
    })

    try:
        with urllib.request.urlopen(
            f"{_DDG_URL}?{params}",
            timeout=8,
        ) as response:
            data = json.loads(response.read().decode("utf-8"))

    except (urllib.error.URLError, json.JSONDecodeError) as error:
        print(f"Web search error: {error}")
        return "I wasn't able to complete that search right now."

    # Prefer the Instant Answer abstract
    abstract = data.get("AbstractText", "").strip()
    if abstract:
        # Truncate to a speakable length (~300 chars / ~2 sentences)
        if len(abstract) > 300:
            abstract = abstract[:300].rsplit(". ", 1)[0] + "."
        return abstract

    # Fall back to a related topic snippet
    topics = data.get("RelatedTopics", [])
    for topic in topics:
        if isinstance(topic, dict) and topic.get("Text"):
            return topic["Text"][:300]

    return f"I couldn't find a quick answer for '{query}'. Try asking me directly."

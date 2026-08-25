"""
News headlines skill — reads top stories from a free RSS feed.
No API key required.

Default feed: BBC News World (configurable via NEWS_FEED_URL in .env).
"""

import os
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

load_dotenv()

_DEFAULT_FEED = "https://feeds.bbci.co.uk/news/world/rss.xml"
_FEED_URL = os.getenv("NEWS_FEED_URL", _DEFAULT_FEED)
_MAX_HEADLINES = int(os.getenv("NEWS_HEADLINES", "5"))


def _strip_tags(text: str) -> str:
    """Remove HTML tags from a string."""
    return re.sub(r"<[^>]+>", "", text).strip()


def get_news() -> str:
    """Fetch and return the top headlines as a spoken string."""

    try:
        req = urllib.request.Request(
            _FEED_URL,
            headers={"User-Agent": "RogueBot/1.0"},
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            xml_data = response.read()

    except urllib.error.URLError as error:
        return f"I couldn't fetch the news right now: {error.reason}."

    try:
        root = ET.fromstring(xml_data)
    except ET.ParseError:
        return "I had trouble reading the news feed."

    # RSS: items are under channel/item
    items = root.findall(".//item")[:_MAX_HEADLINES]

    if not items:
        return "I couldn't find any headlines in that feed."

    headlines = []
    for item in items:
        title_el = item.find("title")
        if title_el is not None and title_el.text:
            headlines.append(_strip_tags(title_el.text))

    if not headlines:
        return "The news feed didn't contain any readable headlines."

    intro = f"Here are the top {len(headlines)} headlines. "
    body = ". ".join(
        f"{i + 1}: {h}" for i, h in enumerate(headlines)
    )
    return intro + body + "."

import os

from dotenv import load_dotenv

load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ROGUEBOT_MODEL = os.getenv("ROGUEBOT_MODEL", "gpt-4.1-mini")
ROGUEBOT_NAME = os.getenv("ROGUEBOT_NAME", "RogueBot")
USER_NAME = os.getenv("USER_NAME", "Joshua")


def validate_config() -> None:
    """Validate required configuration values."""

    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY was not found. Add it to your .env file."
        )
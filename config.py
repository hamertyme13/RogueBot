import os

from dotenv import load_dotenv

load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ROGUEBOT_MODEL = os.getenv("ROGUEBOT_MODEL", "gpt-4.1-mini")
ROGUEBOT_NAME = os.getenv("ROGUEBOT_NAME", "RogueBot")
USER_NAME = os.getenv("USER_NAME", "Joshua")

WAKE_PHRASE = os.getenv("WAKE_PHRASE", "hey roguebot")

# Voice configuration — set VOICE_NAME in .env (e.g. "Ava", "Samantha", "Alex").
# Leave blank to use the system default.
VOICE_NAME = os.getenv("VOICE_NAME", "")

# Ollama (local AI) configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")

# Local STT via faster-whisper.
# Set USE_WHISPER=true in .env to enable offline transcription.
# Model sizes: tiny, base, small, medium, large (larger = more accurate, slower).
USE_WHISPER = os.getenv("USE_WHISPER", "false").lower() == "true"
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")

# Local wake-word detection via openwakeword.
# Set USE_LOCAL_WAKE_WORD=true in .env to enable it.
# Built-in model options: hey_jarvis, hey_mycroft, hey_rhasspy, alexa
USE_LOCAL_WAKE_WORD = os.getenv("USE_LOCAL_WAKE_WORD", "false").lower() == "true"
WAKE_WORD_MODEL = os.getenv("WAKE_WORD_MODEL", "hey_jarvis")
WAKE_WORD_THRESHOLD = float(os.getenv("WAKE_WORD_THRESHOLD", "0.5"))

# Face colour theming
FACE_EYE_COLOUR = os.getenv("FACE_EYE_COLOUR", "white")
FACE_PUPIL_COLOUR = os.getenv("FACE_PUPIL_COLOUR", "black")
FACE_MOUTH_COLOUR = os.getenv("FACE_MOUTH_COLOUR", "white")
FACE_BG_COLOUR = os.getenv("FACE_BG_COLOUR", "black")
FACE_LABEL_COLOUR = os.getenv("FACE_LABEL_COLOUR", "white")


def validate_config() -> None:
    """Validate required configuration values."""

    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY was not found. Add it to your .env file."
        )
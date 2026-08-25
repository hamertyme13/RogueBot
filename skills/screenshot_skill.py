"""
Screenshot + describe skill.

Takes a screenshot using macOS screencapture, encodes it as base64,
and sends it to OpenAI's gpt-4o (vision) model to describe.

Requirements: OPENAI_API_KEY must be set in .env.

Commands:
  "what's on my screen"
  "describe my screen"
  "take a screenshot and describe it"
  "read this screen"
  "what does this say" (when context implies screen)
"""

import base64
import subprocess
import tempfile
from pathlib import Path

from logger import log


def _take_screenshot() -> bytes | None:
    """Capture the screen to a temp PNG and return the raw bytes."""

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        result = subprocess.run(
            ["screencapture", "-x", str(tmp_path)],
            capture_output=True,
            timeout=5,
        )

        if result.returncode != 0:
            log.warning("screencapture failed: %s", result.stderr)
            return None

        data = tmp_path.read_bytes()
        return data

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
        log.warning("Screenshot error: %s", exc)
        return None

    finally:
        tmp_path.unlink(missing_ok=True)


def describe_screen(command: str) -> str:
    """
    Take a screenshot and ask GPT-4o to describe it.
    Returns the spoken description.
    """

    try:
        from config import OPENAI_API_KEY, ROGUEBOT_NAME, USER_NAME
        from openai import OpenAI
    except ImportError:
        return "The OpenAI library is not installed. Run: pip install openai"

    if not OPENAI_API_KEY:
        return "I need an OpenAI API key to describe screenshots. Add it to your .env file."

    screenshot = _take_screenshot()

    if screenshot is None:
        return "I wasn't able to take a screenshot."

    b64 = base64.standard_b64encode(screenshot).decode("utf-8")

    # Tailor the prompt to the command
    command_lower = command.lower()
    if any(w in command_lower for w in ("read", "say", "what does it say", "text")):
        instruction = "Read all visible text on this screen, top to bottom. Be concise."
    elif "error" in command_lower:
        instruction = "Identify and explain any error messages visible on this screen."
    else:
        instruction = (
            "Describe what is visible on this screen in 2-3 short sentences "
            "suitable for being read aloud. Focus on the main content."
        )

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are {ROGUEBOT_NAME}, a desktop assistant built by {USER_NAME}. "
                        "Give clear, concise spoken descriptions. No markdown."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": instruction},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{b64}",
                                "detail": "low",
                            },
                        },
                    ],
                },
            ],
            max_tokens=200,
        )

        return response.choices[0].message.content.strip()

    except Exception as exc:
        log.error("Screenshot describe failed: %s", exc)
        return "I had trouble analysing the screenshot."

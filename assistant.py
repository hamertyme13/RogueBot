from openai import OpenAI

from config import (
    OPENAI_API_KEY,
    ROGUEBOT_MODEL,
    ROGUEBOT_NAME,
    USER_NAME,
    validate_config,
)
from memory import MemoryManager


class RogueBotAssistant:
    """Handles RogueBot's AI conversations via OpenAI."""

    def __init__(self) -> None:
        validate_config()

        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.previous_response_id: str | None = None
        self.memory = MemoryManager()

    def _build_instructions(self) -> str:
        """Build the system instructions including current memories."""

        memories = self.memory.get_all()

        if memories:
            memory_lines = "\n".join(
                f"- {key}: {value}"
                for key, value in memories.items()
            )
            memory_text = f"Known persistent memories:\n{memory_lines}"
        else:
            memory_text = "No persistent memories are currently stored."

        return (
            f"You are {ROGUEBOT_NAME}, a friendly desktop robot "
            f"assistant built by {USER_NAME}. "
            "Keep spoken responses clear, helpful, and fairly brief. "
            "Do not use markdown unless the user asks for formatted text. "
            f"{memory_text}"
        )

    def get_response(self, user_message: str) -> str:
        """Send a message to the AI model and return its answer."""

        if not user_message.strip():
            return "I didn't hear a question."

        try:
            request = {
                "model": ROGUEBOT_MODEL,
                "instructions": self._build_instructions(),
                "input": user_message,
            }

            if self.previous_response_id:
                request["previous_response_id"] = self.previous_response_id

            response = self.client.responses.create(**request)

            self.previous_response_id = response.id

            answer = response.output_text.strip()

            if not answer:
                return "I wasn't able to create a response."

            return answer

        except Exception as error:
            print(f"\nRogueBot OpenAI error: {error}")
            return None

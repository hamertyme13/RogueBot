from openai import OpenAI

from config import (
    OPENAI_API_KEY,
    ROGUEBOT_MODEL,
    ROGUEBOT_NAME,
    USER_NAME,
    validate_config,
)


class RogueBotAssistant:
    """Handles RogueBot's AI conversations."""

    def __init__(self) -> None:
        validate_config()

        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.previous_response_id: str | None = None

    def get_response(self, user_message: str) -> str:
        """Send a message to the AI model and return its answer."""

        if not user_message.strip():
            return "I didn't hear a question."

        try:
            request = {
                "model": ROGUEBOT_MODEL,
                "instructions": (
                    f"You are {ROGUEBOT_NAME}, a friendly desktop robot "
                    f"assistant built by {USER_NAME}. "
                    "Keep spoken responses clear, helpful, and fairly brief. "
                    "Do not use markdown unless the user asks for formatted text."
                ),
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
            print(f"\nRogueBot API error: {error}")
            return "I encountered an error while trying to answer."
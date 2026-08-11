import json
import urllib.error
import urllib.request

from memory import MemoryManager


class LocalAI:
    """Handles RogueBot conversations using a local Ollama model."""

    def __init__(
        self,
        model: str = "llama3.2",
        url: str = "http://localhost:11434/api/chat",
    ) -> None:
        self.model = model
        self.url = url
        self.memory = MemoryManager()

        self.messages = []

    def _build_system_prompt(self) -> str:
        """Create RogueBot's personality and memory context."""

        memories = self.memory.get_all()

        memory_lines = []

        for key, value in memories.items():
            memory_lines.append(f"- {key}: {value}")

        if memory_lines:
            memory_text = "\n".join(memory_lines)
        else:
            memory_text = "No persistent memories are currently stored."

        return f"""
You are RogueBot, a programmable desktop robot assistant built by Joshua.

Personality:
- Friendly
- Intelligent
- Curious
- Concise
- Slightly robotic, but natural
- Helpful without being overly verbose

You are currently running locally on Joshua's computer.

Known persistent memories:
{memory_text}

Respond conversationally.
Keep spoken answers fairly short unless more detail is requested.
Do not use markdown formatting unless specifically requested.
""".strip()

    def ask(self, user_message: str) -> str:
        """Send a message to the local Ollama model."""

        system_message = {
            "role": "system",
            "content": self._build_system_prompt(),
        }

        conversation = [
            system_message,
            *self.messages,
            {
                "role": "user",
                "content": user_message,
            },
        ]

        payload = {
            "model": self.model,
            "messages": conversation,
            "stream": False,
        }

        encoded_payload = json.dumps(payload).encode("utf-8")

        request = urllib.request.Request(
            self.url,
            data=encoded_payload,
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=120,
            ) as response:

                data = json.loads(
                    response.read().decode("utf-8")
                )

            answer = data["message"]["content"].strip()

            self.messages.append(
                {
                    "role": "user",
                    "content": user_message,
                }
            )

            self.messages.append(
                {
                    "role": "assistant",
                    "content": answer,
                }
            )

            # Prevent unlimited conversation growth
            self.messages = self.messages[-12:]

            return answer

        except urllib.error.URLError:
            return (
                "My local AI system is unavailable. "
                "Make sure Ollama is running."
            )

        except Exception as error:
            print(f"Local AI error: {error}")

            return (
                "I encountered an error while processing that request."
            )
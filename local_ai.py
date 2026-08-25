import json
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

from config import OLLAMA_MODEL, OLLAMA_URL
from memory import MemoryManager


_HISTORY_FILE = Path("data/conversation.json")
_MAX_HISTORY = 20  # turns kept on disk


class LocalAI:
    """Handles RogueBot conversations using a local Ollama model."""

    def __init__(
        self,
        model: str = OLLAMA_MODEL,
        url: str = OLLAMA_URL,
    ) -> None:
        self.model = model
        self.url = url
        self.url_stream = url  # same endpoint, different payload
        self.memory = MemoryManager()

        self.messages = self._load_history()

    def _load_history(self) -> list[dict]:
        """Load persisted conversation turns from disk."""

        if not _HISTORY_FILE.exists():
            return []

        try:
            with _HISTORY_FILE.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []

    def _save_history(self) -> None:
        """Persist the current conversation window to disk."""

        _HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)

        try:
            with _HISTORY_FILE.open("w", encoding="utf-8") as f:
                json.dump(self.messages, f, indent=2, ensure_ascii=False)
        except OSError as error:
            print(f"Could not save conversation history: {error}")

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

    def _build_conversation(self, user_message: str) -> list[dict]:
        return [
            {"role": "system", "content": self._build_system_prompt()},
            *self.messages,
            {"role": "user", "content": user_message},
        ]

    def _record_turn(self, user_message: str, answer: str) -> None:
        self.messages.append({"role": "user", "content": user_message})
        self.messages.append({"role": "assistant", "content": answer})
        self.messages = self.messages[-_MAX_HISTORY:]
        self._save_history()

    # ------------------------------------------------------------------
    # Non-streaming ask (used as fallback / simple queries)
    # ------------------------------------------------------------------

    def ask(self, user_message: str) -> str | None:
        """Send a message and return the complete response string."""

        payload = {
            "model": self.model,
            "messages": self._build_conversation(user_message),
            "stream": False,
        }

        req = urllib.request.Request(
            self.url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                data = json.loads(response.read().decode("utf-8"))

            answer = data["message"]["content"].strip()
            self._record_turn(user_message, answer)
            return answer

        except urllib.error.URLError:
            return None
        except Exception as error:
            print(f"Local AI error: {error}")
            return None

    # ------------------------------------------------------------------
    # Streaming ask — yields sentences as they arrive
    # ------------------------------------------------------------------

    def ask_streaming(
        self,
        user_message: str,
        sentence_callback: Callable[[str], None],
    ) -> str | None:
        """
        Stream the response from Ollama.

        Calls `sentence_callback(sentence)` each time a complete sentence
        is available so the speech system can start speaking immediately.

        Returns the full response string on success, None on failure.
        """

        payload = {
            "model": self.model,
            "messages": self._build_conversation(user_message),
            "stream": True,
        }

        req = urllib.request.Request(
            self.url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            full_text = ""
            buffer = ""

            with urllib.request.urlopen(req, timeout=120) as response:
                for raw_line in response:
                    line = raw_line.decode("utf-8").strip()
                    if not line:
                        continue

                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    token = chunk.get("message", {}).get("content", "")
                    buffer += token
                    full_text += token

                    # Emit complete sentences to the callback
                    while True:
                        # Find the earliest sentence-ending punctuation
                        end = -1
                        for punct in (".", "!", "?", "\n"):
                            idx = buffer.find(punct)
                            if idx != -1 and (end == -1 or idx < end):
                                end = idx

                        if end == -1:
                            break

                        sentence = buffer[: end + 1].strip()
                        buffer = buffer[end + 1:]

                        if sentence:
                            sentence_callback(sentence)

                    if chunk.get("done"):
                        break

            # Emit any leftover text
            if buffer.strip():
                sentence_callback(buffer.strip())

            answer = full_text.strip()
            if answer:
                self._record_turn(user_message, answer)
            return answer or None

        except urllib.error.URLError:
            return None
        except Exception as error:
            print(f"Local AI streaming error: {error}")
            return None
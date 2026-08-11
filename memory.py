import json
from pathlib import Path


class MemoryManager:
    """Handles RogueBot's persistent memory."""

    def __init__(self, memory_file: str = "data/memory.json") -> None:
        self.memory_file = Path(memory_file)
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)

        if not self.memory_file.exists():
            self._save({})

    def _load(self) -> dict:
        """Load memory from disk."""

        try:
            with self.memory_file.open("r", encoding="utf-8") as file:
                return json.load(file)

        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save(self, memory: dict) -> None:
        """Save memory to disk."""

        with self.memory_file.open("w", encoding="utf-8") as file:
            json.dump(
                memory,
                file,
                indent=4,
                ensure_ascii=False,
            )

    def remember(self, key: str, value: str) -> None:
        """Store a fact."""

        memory = self._load()

        memory[key.lower().strip()] = value.strip()

        self._save(memory)

    def recall(self, key: str) -> str | None:
        """Recall a stored fact."""

        memory = self._load()

        return memory.get(key.lower().strip())

    def forget(self, key: str) -> bool:
        """Forget a stored fact."""

        memory = self._load()

        normalized_key = key.lower().strip()

        if normalized_key not in memory:
            return False

        del memory[normalized_key]

        self._save(memory)

        return True

    def get_all(self) -> dict:
        """Return all stored memories."""

        return self._load()
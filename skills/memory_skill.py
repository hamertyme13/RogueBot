from memory import MemoryManager


memory = MemoryManager()


def remember_fact(command: str) -> str:
    """
    Handle commands such as:
    'remember that my favorite color is blue'
    """

    command = command.strip()

    prefix = "remember that "

    if not command.lower().startswith(prefix):
        return "Tell me what you want me to remember."

    fact = command[len(prefix):].strip()

    if " is " not in fact.lower():
        return (
            "I can remember simple facts in the format "
            "'remember that something is something.'"
        )

    parts = fact.split(" is ", 1)

    if len(parts) != 2:
        return "I could not understand that memory."

    key = parts[0].strip()
    value = parts[1].strip().rstrip(".!?")

    if not key or not value:
        return "I could not understand that memory."

    memory.remember(key, value)

    return f"Okay. I'll remember that {key} is {value}."


def recall_fact(command: str) -> str:
    """
    Handle commands such as:
    'what is my favorite color'
    """

    command = command.lower().strip().rstrip(".!?")

    prefixes = (
        "what is ",
        "what's ",
        "do you remember ",
    )

    key = None

    for prefix in prefixes:
        if command.startswith(prefix):
            key = command[len(prefix):].strip()
            break

    if not key:
        return "I'm not sure what you want me to remember."

    value = memory.recall(key)

    if value is None:
        return f"I don't remember anything about {key}."

    return f"{key.capitalize()} is {value}."


def list_memories() -> str:
    """Return a summary of everything RogueBot remembers."""

    memories = memory.get_all()

    if not memories:
        return "I don't have any saved memories yet."

    items = [
        f"{key} is {value}"
        for key, value in memories.items()
    ]

    return "I remember that " + ", ".join(items) + "."


def forget_fact(command: str) -> str:
    """
    Handle commands such as:
    'forget my favorite color'
    """

    command = command.lower().strip().rstrip(".!?")

    prefix = "forget "

    if not command.startswith(prefix):
        return "Tell me what you want me to forget."

    key = command[len(prefix):].strip()

    if memory.forget(key):
        return f"Okay. I forgot {key}."

    return f"I don't have a memory stored for {key}."
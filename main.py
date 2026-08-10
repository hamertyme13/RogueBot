from assistant import RogueBotAssistant
from config import ROGUEBOT_NAME, USER_NAME
from speech import SpeechSystem


EXIT_COMMANDS = {
    "goodbye",
    "goodbye roguebot",
    "exit",
    "quit",
    "shut down",
    "shutdown",
    "stop listening",
}


def should_exit(command: str) -> bool:
    """Return True when the user asks RogueBot to stop."""

    normalized_command = command.lower().strip().rstrip(".!?")

    return normalized_command in EXIT_COMMANDS


def main() -> None:
    """Run the RogueBot voice-assistant loop."""

    print("=" * 50)
    print(f"{ROGUEBOT_NAME} Desktop Assistant")
    print("=" * 50)

    try:
        assistant = RogueBotAssistant()
        speech = SpeechSystem()

    except Exception as error:
        print(f"Startup error: {error}")
        return

    speech.speak(
        f"Hello {USER_NAME}. {ROGUEBOT_NAME} is online. "
        "What can I help you with?"
    )

    while True:
        command = speech.listen()

        if command is None:
            continue

        if should_exit(command):
            speech.speak(
                f"Goodbye {USER_NAME}. Shutting down."
            )
            break

        speech.speak("Let me think about that.")

        response = assistant.get_response(command)

        speech.speak(response)


if __name__ == "__main__":
    main()
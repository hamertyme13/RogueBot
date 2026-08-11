from commands import CommandProcessor
from config import ROGUEBOT_NAME, USER_NAME, WAKE_PHRASE
import face
from speech import SpeechSystem
from face import FaceState, RogueBotFace


EXIT_COMMANDS = {
    "goodbye",
    "goodbye roguebot",
    "exit",
    "quit",
    "shutdown",
    "shut down",
}


def should_exit(command: str) -> bool:
    """Check whether RogueBot should shut down."""

    normalized = command.lower().strip().rstrip(".!?")

    return normalized in EXIT_COMMANDS


def wake_phrase_detected(text: str) -> bool:
    """Check for common versions of RogueBot's wake phrase."""

    text = text.lower().strip()

    print(f'DEBUG wake input: "{text}"')

    wake_phrases = {
        "hey roguebot",
        "hey rogue bot",
        "hey robot",
        "roguebot",
        "rogue bot",
    }

    return any(
        phrase in text
        for phrase in wake_phrases
    )


def main() -> None:
    """Run RogueBot."""

    print("=" * 50)
    print(f"{ROGUEBOT_NAME} Desktop Assistant")
    print("=" * 50)

    speech = SpeechSystem()
    commands = CommandProcessor()
    face = RogueBotFace()

    speech.calibrate_microphone()

    speech.speak(
        f"{ROGUEBOT_NAME} is online. "
        f"Say {WAKE_PHRASE} when you need me."
    )

    print(f'\nWaiting for wake phrase: "{WAKE_PHRASE}"\n')

    face.set_state(FaceState.SLEEPING)

    while True:

        # -------------------------
        # IDLE MODE
        # -------------------------

        face.set_state(FaceState.SLEEPING)
        face.update()

        wake_input = speech.listen(
            timeout=5,
            phrase_time_limit=4,
            show_status=False,
        )

        if wake_input is None:
            continue

        # Allow shutdown even while idle
        if should_exit(wake_input):

            face.set_state(FaceState.SLEEPING)
            face.update()

            speech.speak(f"Goodbye {USER_NAME}. RogueBot is shutting down.")
            face.close()
            break

        if not wake_phrase_detected(wake_input):
            continue

        print(f"Wake phrase detected: {wake_input}")

        face.set_state(FaceState.LISTENING)
        face.update()

        speech.speak("I'm listening.")

        # -------------------------
        # COMMAND MODE
        # -------------------------

        command = speech.listen(
            timeout=12,
            phrase_time_limit=12,
            show_status=True,
        )

        if command is None:
            speech.speak(
                "I didn't hear a command."
            )

            print(
                f'Waiting for wake phrase: "{WAKE_PHRASE}"'
            )

            continue

        # -------------------------
        # SHUTDOWN
        # -------------------------

        if should_exit(command):

            face.set_state(FaceState.SLEEPING)
            face.update()

            speech.speak(
                f"Goodbye {USER_NAME}. RogueBot is shutting down."
            )

            face.close()

            break

        # -------------------------
        # PROCESS COMMAND
        # -------------------------
        face.set_state(FaceState.THINKING)
        face.update()

        response = commands.process(command)

        face.set_state(FaceState.SPEAKING)
        face.update()

        speech.speak(response)

        print(
            f'\nWaiting for wake phrase: "{WAKE_PHRASE}"\n'
        )

        face.set_state(FaceState.SLEEPING)
        face.update()


if __name__ == "__main__":
    main()
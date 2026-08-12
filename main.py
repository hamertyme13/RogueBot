from queue import Queue
from threading import Event, Thread

from commands import CommandProcessor
from config import (
    ROGUEBOT_NAME,
    USER_NAME,
    WAKE_PHRASE,
)
from face import FaceState, RogueBotFace
from speech import SpeechSystem


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

    normalized = (
        command
        .lower()
        .strip()
        .rstrip(".!?")
    )

    return normalized in EXIT_COMMANDS


def wake_phrase_detected(text: str) -> bool:
    """Check common versions of RogueBot's wake phrase."""

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


def robot_worker(
    state_queue: Queue,
    shutdown_event: Event,
) -> None:
    """
    Run RogueBot's voice and command processing.

    This runs on a background thread.
    """

    speech = SpeechSystem()
    commands = CommandProcessor()

    speech.calibrate_microphone()

    speech.speak(
        f"{ROGUEBOT_NAME} is online. "
        f"Say {WAKE_PHRASE} when you need me."
    )

    state_queue.put(
        FaceState.SLEEPING
    )

    print(
        f'\nWaiting for wake phrase: '
        f'"{WAKE_PHRASE}"\n'
    )

    while not shutdown_event.is_set():

        # --------------------------------
        # SLEEPING / WAKE WORD MODE
        # --------------------------------

        state_queue.put(
            FaceState.SLEEPING
        )

        wake_input = speech.listen(
            timeout=2,
            phrase_time_limit=4,
            show_status=False,
        )

        if wake_input is None:
            continue

        # Allow shutdown without wake phrase
        if should_exit(wake_input):

            state_queue.put(
                FaceState.SLEEPING
            )

            speech.speak(
                f"Goodbye {USER_NAME}. "
                "RogueBot is shutting down."
            )

            shutdown_event.set()

            return

        if not wake_phrase_detected(wake_input):
            continue

        print(
            f"Wake phrase detected: {wake_input}"
        )

        # --------------------------------
        # LISTENING MODE
        # --------------------------------

        state_queue.put(
            FaceState.LISTENING
        )

        speech.speak(
            "I'm listening."
        )

        command = speech.listen(
            timeout=12,
            phrase_time_limit=12,
            show_status=True,
        )

        if command is None:

            speech.speak(
                "I didn't hear a command."
            )

            state_queue.put(
                FaceState.SLEEPING
            )

            print(
                f'Waiting for wake phrase: '
                f'"{WAKE_PHRASE}"'
            )

            continue

        # --------------------------------
        # SHUTDOWN
        # --------------------------------

        if should_exit(command):

            state_queue.put(
                FaceState.SLEEPING
            )

            speech.speak(
                f"Goodbye {USER_NAME}. "
                "RogueBot is shutting down."
            )

            shutdown_event.set()

            return

        # --------------------------------
        # THINKING
        # --------------------------------

        state_queue.put(
            FaceState.THINKING
        )

        response = commands.process(
            command
        )

        # --------------------------------
        # SPEAKING
        # --------------------------------

        state_queue.put(
            FaceState.SPEAKING
        )

        speech.speak(
            response
        )

        # --------------------------------
        # RETURN TO SLEEP
        # --------------------------------

        state_queue.put(
            FaceState.SLEEPING
        )

        print(
            f'\nWaiting for wake phrase: '
            f'"{WAKE_PHRASE}"\n'
        )


def main() -> None:
    """Start RogueBot."""

    print("=" * 50)
    print(
        f"{ROGUEBOT_NAME} Desktop Assistant"
    )
    print("=" * 50)

    state_queue = Queue()
    shutdown_event = Event()

    # Tkinter must be created on main thread.
    face = RogueBotFace()

    worker = Thread(
        target=robot_worker,
        args=(
            state_queue,
            shutdown_event,
        ),
        daemon=True,
        name="RogueBotWorker",
    )

    worker.start()

    # Main thread belongs to Tkinter.
    face.run(
        state_queue,
        shutdown_event,
    )

    # If the face window is manually closed,
    # tell the worker to stop.
    shutdown_event.set()

    worker.join(
        timeout=3,
    )

    print(
        "RogueBot process terminated."
    )


if __name__ == "__main__":
    main()
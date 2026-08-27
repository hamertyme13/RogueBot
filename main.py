import time
from vision import VisionSystem
from queue import Empty, Queue
from threading import Event, Thread

from commands import CommandProcessor
from config import (
    ROGUEBOT_NAME,
    USE_LOCAL_WAKE_WORD,
    USER_NAME,
    WAKE_PHRASE,
    WAKE_WORD_MODEL,
    WAKE_WORD_THRESHOLD,
)
from face import FaceState, RogueBotFace
from logger import log
from speech import SpeechSystem
from startup_check import run_startup_checks
import skills.timer_skill as timer_skill


EXIT_COMMANDS = {
    "goodbye",
    "goodbye roguebot",
    "exit",
    "quit",
    "shutdown",
    "shut down",
}

# How long (seconds) RogueBot stays alert after the last response
# before going back to sleep and waiting for the wake phrase again.
CONVERSATION_TIMEOUT = 30


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

    wake_phrases = {
        "hey roguebot",
        "hey rogue bot",
        "hey robot",
        "roguebot",
        "rogue bot",
        "hey rogue",
    }

    return any(
        phrase in text
        for phrase in wake_phrases
    )


def _run_conversation(
    speech: SpeechSystem,
    commands: CommandProcessor,
    state_queue: Queue,
    shutdown_event: Event,
    notification_queue: Queue,
) -> bool:
    """
    Run a single conversation session — listen for commands until
    the user goes silent for CONVERSATION_TIMEOUT seconds or says
    a shutdown phrase.

    Returns True if shutdown was requested, False otherwise.
    """

    state_queue.put(FaceState.LISTENING)
    speech.speak("I'm listening.")

    last_interaction = time.monotonic()

    while not shutdown_event.is_set():

        # --------------------------------
        # DRAIN NOTIFICATION QUEUE
        # (timer / reminder alerts)
        # --------------------------------

        try:
            while True:
                notification = notification_queue.get_nowait()
                state_queue.put(FaceState.SPEAKING)
                speech.speak(notification)
                last_interaction = time.monotonic()
        except Empty:
            pass

        elapsed = time.monotonic() - last_interaction

        if elapsed >= CONVERSATION_TIMEOUT:
            speech.speak("Going back to sleep. Say the wake phrase when you need me.")
            return False

        # --------------------------------
        # LISTEN FOR NEXT COMMAND
        # --------------------------------

        state_queue.put(FaceState.LISTENING)

        command = speech.listen(
            timeout=10,
            phrase_time_limit=12,
            show_status=True,
        )

        if command is None:
            # Silence — keep waiting until timeout
            continue

        # --------------------------------
        # SHUTDOWN
        # --------------------------------

        if should_exit(command):

            state_queue.put(FaceState.SLEEPING)

            speech.speak(
                f"Goodbye {USER_NAME}. "
                "RogueBot is shutting down."
            )

            shutdown_event.set()
            return True

        # Reset interaction timer as soon as we hear a command,
        # so processing / speaking time doesn't eat into the window.
        last_interaction = time.monotonic()

        # --------------------------------
        # THINKING
        # --------------------------------

        state_queue.put(FaceState.THINKING)

        response = commands.process(command)

        # --------------------------------
        # SPEAKING
        # --------------------------------

        state_queue.put(FaceState.SPEAKING)

        # Skip speaking if streaming AI already delivered the response
        # sentence-by-sentence via speak_fn during processing.
        if not commands._streamed_last:
            speech.speak(response)
        commands._streamed_last = False

    return False


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

    # Inject speech callbacks so streaming AI and dictation work.
    commands._speak_fn = speech.speak
    commands._listen_fn = speech.listen

    # Give the timer skill a queue so expired timers speak aloud.
    notification_queue: Queue = Queue()
    timer_skill.notification_queue = notification_queue

    # Start the reminder checker — it speaks via the same queue.
    from skills.reminder_skill import start_reminder_checker
    start_reminder_checker(notification_queue.put)

    speech.calibrate_microphone()

    # Run startup diagnostics and speak a brief summary.
    log.info("Running startup checks.")
    status_summary = run_startup_checks()
    log.info("Startup summary: %s", status_summary)

    speech.speak(
        f"{ROGUEBOT_NAME} is online. "
        f"{status_summary} "
        f"Say {WAKE_PHRASE} when you need me."
    )

    state_queue.put(FaceState.SLEEPING)
    log.info('Waiting for wake phrase: "%s"', WAKE_PHRASE)

    if USE_LOCAL_WAKE_WORD:
        from wake_word import WakeWordDetector

        detector = WakeWordDetector(
            model_name=WAKE_WORD_MODEL,
            threshold=WAKE_WORD_THRESHOLD,
        )
        log.info(
            "Local wake-word detection active (model: %s, threshold: %s)",
            WAKE_WORD_MODEL, WAKE_WORD_THRESHOLD,
        )
    else:
        detector = None

    while not shutdown_event.is_set():

        # --------------------------------
        # SLEEPING / WAKE WORD MODE
        # --------------------------------

        state_queue.put(FaceState.SLEEPING)

        if detector is not None:
            # --- LOCAL WAKE-WORD PATH ---
            # Blocks until the model fires; no cloud calls.
            detector.wait_for_wake_word()

            if shutdown_event.is_set():
                break

            print(f"Wake word detected (model: {WAKE_WORD_MODEL})")

        else:
            # --- GOOGLE STT WAKE-PHRASE PATH ---
            wake_input = speech.listen(
                timeout=2,
                phrase_time_limit=4,
                show_status=False,
            )

            if wake_input is None:
                continue

            # Allow shutdown without wake phrase
            if should_exit(wake_input):

                state_queue.put(FaceState.SLEEPING)

                speech.speak(
                    f"Goodbye {USER_NAME}. "
                    "RogueBot is shutting down."
                )

                shutdown_event.set()
                return

            if not wake_phrase_detected(wake_input):
                continue

            print(f"Wake phrase detected: {wake_input}")

        # --------------------------------
        # CONVERSATION MODE
        # --------------------------------

        shutdown_requested = _run_conversation(
            speech,
            commands,
            state_queue,
            shutdown_event,
            notification_queue,
        )

        if shutdown_requested:
            return

        state_queue.put(FaceState.SLEEPING)

        print(
            f'\nWaiting for wake phrase: '
            f'"{WAKE_PHRASE}"\n'
        )

def vision_worker(
    state_queue: Queue,
    shutdown_event: Event,
) -> None:
    """Track faces and send eye-position events to the GUI."""

    vision = VisionSystem(
        camera_index=1
    )

    if not vision.start():
        print("Vision worker could not start.")
        return
    
    print("Vision worker online.")

    try:
        while not shutdown_event.is_set():
            frame = vision.read_frame()

            if frame is None:
                time.sleep(0.05)
                continue

            faces = vision.detect_faces(frame)

            primary_face = vision.get_primary_face(faces)

            if primary_face is not None:
                direction = (
                    vision.get_horizontal_direction(
                        frame,
                        primary_face
                    )
                )

                state_queue.put(("look", direction))

            time.sleep(0.05)

    finally:
        vision.stop()
        print("Vision worker stopped.")


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

    # Voice / assistant thread

    worker = Thread(
        target=robot_worker,
        args=(
            state_queue,
            shutdown_event,
        ),
        daemon=True,
        name="RogueBotWorker",
    )

    # Camera / vision thread

    vision_thread = Thread(
        target=vision_worker,
        args=(
            state_queue,
            shutdown_event,
        ),
        daemon=True,
        name="RogueBotVision",
    )

    worker.start()
    vision_thread.start()

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

    vision_thread.join(
        timeout=3,
    )

    print(
        "RogueBot process terminated."
    )


if __name__ == "__main__":
    main()

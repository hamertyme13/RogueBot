import random
import tkinter as tk
from enum import Enum
from queue import Empty, Queue
from threading import Event


class FaceState(Enum):
    SLEEPING = "sleeping"
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"


class RogueBotFace:
    """Graphical face and animation system for RogueBot."""

    def __init__(self) -> None:
        self.root = tk.Tk()

        self.root.title("RogueBot")
        self.root.geometry("600x400")
        self.root.configure(bg="black")

        self.canvas = tk.Canvas(
            self.root,
            width=600,
            height=320,
            bg="black",
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        self.status_label = tk.Label(
            self.root,
            text="ROGUEBOT",
            font=("Helvetica", 18, "bold"),
            fg="white",
            bg="black",
        )
        self.status_label.pack(pady=10)

        self.state = FaceState.IDLE
        self.closed = False

        self.left_eye = None
        self.right_eye = None

        self._draw_face()

        self.set_state(FaceState.IDLE)

        # Start animation systems
        self._schedule_blink()

        self.thinking_direction = 1
        self.thinking_animation_id = None

    def _draw_face(self) -> None:
        """Create RogueBot's eyes."""

        self.canvas.delete("all")

        self.left_eye = self.canvas.create_oval(
            140,
            110,
            240,
            210,
            fill="white",
            outline="",
        )

        self.right_eye = self.canvas.create_oval(
            360,
            110,
            460,
            210,
            fill="white",
            outline="",
        )

    def _stop_thinking_animation(self) -> None:
        """Stop the thinking animation."""

        if self.thinking_animation_id is None:
            return

        try:
            self.root.after_cancel(
                self.thinking_animation_id
            )
        except tk.TclError:
            pass

        self.thinking_animation_id = None

    def set_state(self, state: FaceState) -> None:
        """Change RogueBot's visual state."""

        if state != FaceState.THINKING:
            self._stop_thinking_animation()

        if self.closed:
            return

        self.state = state

        if state == FaceState.SLEEPING:
            self._sleeping_face()
            self.status_label.config(text="SLEEPING")

        elif state == FaceState.IDLE:
            self._idle_face()
            self.status_label.config(text="ROGUEBOT")

        elif state == FaceState.LISTENING:
            self._listening_face()
            self.status_label.config(text="LISTENING")

        elif state == FaceState.THINKING:
            self._thinking_face()
            self.status_label.config(text="THINKING")

        elif state == FaceState.SPEAKING:
            self._speaking_face()
            self.status_label.config(text="SPEAKING")

    def _idle_face(self) -> None:
        self._open_eyes()

    def _sleeping_face(self) -> None:
        self._close_eyes()

    def _listening_face(self) -> None:
        self.canvas.coords(
            self.left_eye,
            125,
            95,
            250,
            220,
        )

        self.canvas.coords(
            self.right_eye,
            350,
            95,
            475,
            220,
        )

    def _thinking_face(self) -> None:
        """Animate eyes moving left and right."""
        self.canvas.coords(
            self.left_eye,
            150,
            125,
            240,
            190,
        )

        self.canvas.coords(
            self.right_eye,
            360,
            125,
            450,
            190,
        )

        self._start_thinking_animation()

    def _start_thinking_animation(self) -> None:
        """Animate RogueBot's eyes while thinking."""

        if self.state != FaceState.THINKING:
            return

        offset = 10 * self.thinking_direction

        self.canvas.move(
            self.left_eye,
            offset,
            0,
        )

        self.canvas.move(
            self.right_eye,
            offset,
            0,
        )

        self.thinking_direction *= -1

        self.thinking_animation_id = (
            self.root.after(
                400,
                self._start_thinking_animation,
            )
        )

    def _speaking_face(self) -> None:
        self.canvas.coords(
            self.left_eye,
            135,
            105,
            245,
            215,
        )

        self.canvas.coords(
            self.right_eye,
            355,
            105,
            465,
            215,
        )

    def _open_eyes(self) -> None:
        self.canvas.coords(
            self.left_eye,
            140,
            110,
            240,
            210,
        )

        self.canvas.coords(
            self.right_eye,
            360,
            110,
            460,
            210,
        )

    def _close_eyes(self) -> None:
        self.canvas.coords(
            self.left_eye,
            140,
            155,
            240,
            165,
        )

        self.canvas.coords(
            self.right_eye,
            360,
            155,
            460,
            165,
        )

    # --------------------------------------------------
    # BLINK ANIMATION
    # --------------------------------------------------

    def _schedule_blink(self) -> None:
        """Schedule the next automatic blink."""

        if self.closed:
            return

        delay = random.randint(2500, 6000)

        self.root.after(
            delay,
            self._blink,
        )

    def _blink(self) -> None:
        """Perform a quick eye blink."""

        if self.closed:
            return

        # Sleeping eyes are already closed.
        if self.state != FaceState.SLEEPING:
            self._close_eyes()

            self.root.after(
                150,
                self._restore_current_state,
            )

        self._schedule_blink()

    def _restore_current_state(self) -> None:
        """Restore expression after a blink."""

        self.set_state(self.state)

    # --------------------------------------------------
    # THREAD COMMUNICATION
    # --------------------------------------------------

    def _process_state_queue(
        self,
        state_queue: Queue,
        shutdown_event: Event,
    ) -> None:
        """Read state changes sent by the robot worker."""

        if self.closed:
            return

        try:
            while True:
                state = state_queue.get_nowait()

                if isinstance(state, FaceState):
                    self.set_state(state)

        except Empty:
            pass

        if shutdown_event.is_set():
            self.close()
            return

        self.root.after(
            50,
            self._process_state_queue,
            state_queue,
            shutdown_event,
        )

    def run(
        self,
        state_queue: Queue,
        shutdown_event: Event,
    ) -> None:
        """Run the Tkinter event loop."""

        self.root.protocol(
            "WM_DELETE_WINDOW",
            lambda: self._handle_window_close(
                shutdown_event
            ),
        )

        self.root.after(
            50,
            self._process_state_queue,
            state_queue,
            shutdown_event,
        )

        self.root.mainloop()

    def _handle_window_close(
        self,
        shutdown_event: Event,
    ) -> None:
        """Handle the user manually closing the face."""

        shutdown_event.set()

        self.close()

    def close(self) -> None:
        """Close RogueBot's display."""

        if self.closed:
            return

        self.closed = True

        try:
            self.root.destroy()

        except tk.TclError:
            pass
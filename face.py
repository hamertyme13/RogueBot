import random
import tkinter as tk
from enum import Enum
from queue import Empty, Queue
from threading import Event

from config import (
    FACE_BG_COLOUR,
    FACE_EYE_COLOUR,
    FACE_LABEL_COLOUR,
    FACE_MOUTH_COLOUR,
    FACE_PUPIL_COLOUR,
)


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
        self.root.geometry("600x420")
        self.root.configure(bg=FACE_BG_COLOUR)

        self.canvas = tk.Canvas(
            self.root,
            width=600,
            height=340,
            bg=FACE_BG_COLOUR,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        self.status_label = tk.Label(
            self.root,
            text="ROGUEBOT",
            font=("Helvetica", 18, "bold"),
            fg=FACE_LABEL_COLOUR,
            bg=FACE_BG_COLOUR,
        )
        self.status_label.pack(pady=10)

        self.state = FaceState.IDLE
        self.closed = False

        self.left_eye = None
        self.right_eye = None
        self.left_pupil = None
        self.right_pupil = None
        self.mouth = None

        # Thinking animation state
        self.thinking_direction = 1
        self.thinking_animation_id = None

        # Speaking mouth animation state
        self.speaking_open = False
        self.speaking_animation_id = None

        self._draw_face()

        self.set_state(FaceState.IDLE)

        # Blink animation
        self._schedule_blink()

        

    # --------------------------------------------------
    # DRAWING
    # --------------------------------------------------

    def _draw_face(self) -> None:
        """Create RogueBot's eyes, pupils, and mouth."""

        self.canvas.delete("all")

        self.left_eye = self.canvas.create_oval(
            140, 110, 240, 210,
            fill=FACE_EYE_COLOUR, outline="",
        )

        self.right_eye = self.canvas.create_oval(
            360, 110, 460, 210,
            fill=FACE_EYE_COLOUR, outline="",
        )

        self.left_pupil = self.canvas.create_oval(
            180, 145, 205, 170,
            fill=FACE_PUPIL_COLOUR, outline="",
        )

        self.right_pupil = self.canvas.create_oval(
            400, 145, 425, 170,
            fill=FACE_PUPIL_COLOUR, outline="",
        )

        # Mouth: idle smile arc
        self.mouth = self.canvas.create_arc(
            220, 245, 380, 305,
            start=200, extent=140,
            style=tk.ARC,
            outline=FACE_MOUTH_COLOUR,
            width=4,
        )

    # --------------------------------------------------
    # PUPIL HELPERS
    # --------------------------------------------------

    def _show_pupils(self) -> None:
        self.canvas.itemconfig(self.left_pupil, state="normal")
        self.canvas.itemconfig(self.right_pupil, state="normal")

    def _hide_pupils(self) -> None:
        self.canvas.itemconfig(self.left_pupil, state="hidden")
        self.canvas.itemconfig(self.right_pupil, state="hidden")

    def _center_pupils(self) -> None:
        self.canvas.coords(self.left_pupil, 180, 145, 205, 170)
        self.canvas.coords(self.right_pupil, 400, 145, 425, 170)

    # --------------------------------------------------
    # THINKING EYE ANIMATION
    # --------------------------------------------------

    def _stop_thinking_animation(self) -> None:
        if self.thinking_animation_id is None:
            return
        try:
            self.root.after_cancel(self.thinking_animation_id)
        except tk.TclError:
            pass
        self.thinking_animation_id = None

    # --------------------------------------------------
    # SPEAKING MOUTH ANIMATION
    # --------------------------------------------------

    def _stop_speaking_animation(self) -> None:
        if self.speaking_animation_id is None:
            return
        try:
            self.root.after_cancel(self.speaking_animation_id)
        except tk.TclError:
            pass
        self.speaking_animation_id = None

    def _animate_speaking_mouth(self) -> None:
        """Alternate the mouth between open and closed while speaking."""

        if self.state != FaceState.SPEAKING:
            self.speaking_animation_id = None
            return

        if self.speaking_open:
            # Open mouth: tall oval
            self.canvas.coords(self.mouth, 230, 248, 370, 300)
            self.canvas.itemconfig(
                self.mouth,
                style=tk.ARC,
                start=200,
                extent=140,
                outline=FACE_MOUTH_COLOUR,
                fill="",
                width=4,
            )
        else:
            # Closed mouth: horizontal line (very flat arc)
            self.canvas.coords(self.mouth, 230, 268, 370, 280)
            self.canvas.itemconfig(
                self.mouth,
                style=tk.ARC,
                start=0,
                extent=180,
                outline=FACE_MOUTH_COLOUR,
                fill="",
                width=4,
            )

        self.speaking_open = not self.speaking_open

        self.speaking_animation_id = self.root.after(
            280,
            self._animate_speaking_mouth,
        )

    # --------------------------------------------------
    # STATE TRANSITIONS
    # --------------------------------------------------

    def set_state(self, state: FaceState) -> None:
        """Change RogueBot's visual state."""

        if state != FaceState.THINKING:
            self._stop_thinking_animation()

        if state != FaceState.SPEAKING:
            self._stop_speaking_animation()

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
        self._show_pupils()
        self._center_pupils()
        # Gentle smile
        self.canvas.coords(self.mouth, 220, 245, 380, 305)
        self.canvas.itemconfig(
            self.mouth,
            style=tk.ARC, start=200, extent=140,
            outline=FACE_MOUTH_COLOUR, fill="", width=4,
        )
        self.canvas.itemconfig(self.mouth, state="normal")

    def _sleeping_face(self) -> None:
        self._hide_pupils()
        self._close_eyes()
        # Flat / neutral mouth
        self.canvas.coords(self.mouth, 230, 268, 370, 278)
        self.canvas.itemconfig(
            self.mouth,
            style=tk.ARC, start=0, extent=180,
            outline=FACE_MOUTH_COLOUR, fill="", width=3,
        )
        self.canvas.itemconfig(self.mouth, state="normal")

    def _listening_face(self) -> None:
        # Wide open eyes
        self.canvas.coords(self.left_eye, 125, 95, 250, 220)
        self.canvas.coords(self.right_eye, 350, 95, 475, 220)
        self._show_pupils()
        self._center_pupils()
        # Small open "O" mouth
        self.canvas.coords(self.mouth, 265, 255, 335, 295)
        self.canvas.itemconfig(
            self.mouth,
            style=tk.ARC, start=0, extent=359,
            outline=FACE_MOUTH_COLOUR, fill="", width=4,
        )
        self.canvas.itemconfig(self.mouth, state="normal")

    def _thinking_face(self) -> None:
        """Display RogueBot's thinking face and start the eye animation."""

        self.canvas.coords(self.left_eye, 150, 125, 240, 190)
        self.canvas.coords(self.right_eye, 360, 125, 450, 190)
        self._show_pupils()
        self._center_pupils()
        # Slight frown / flat mouth
        self.canvas.coords(self.mouth, 235, 258, 365, 288)
        self.canvas.itemconfig(
            self.mouth,
            style=tk.ARC, start=0, extent=180,
            outline=FACE_MOUTH_COLOUR, fill="", width=3,
        )
        self.canvas.itemconfig(self.mouth, state="normal")
        self._start_thinking_animation()

    def _start_thinking_animation(self) -> None:
        """Animate RogueBot's pupils while thinking."""

        if self.state != FaceState.THINKING:
            self.thinking_animation_id = None
            return

        self._center_pupils()

        offset = 12 * self.thinking_direction
        self.canvas.move(self.left_pupil, offset, 0)
        self.canvas.move(self.right_pupil, offset, 0)
        self.thinking_direction *= -1

        self.thinking_animation_id = self.root.after(
            400,
            self._start_thinking_animation,
        )

    def _speaking_face(self) -> None:
        self.canvas.coords(self.left_eye, 135, 105, 245, 215)
        self.canvas.coords(self.right_eye, 355, 105, 465, 215)
        self._show_pupils()
        self._center_pupils()
        self.canvas.itemconfig(self.mouth, state="normal")
        # Start mouth animation
        self.speaking_open = True
        self._animate_speaking_mouth()

    def _open_eyes(self) -> None:
        self.canvas.coords(self.left_eye, 140, 110, 240, 210)
        self.canvas.coords(self.right_eye, 360, 110, 460, 210)

    def _close_eyes(self) -> None:
        self.canvas.coords(self.left_eye, 140, 155, 240, 165)
        self.canvas.coords(self.right_eye, 360, 155, 460, 165)

    # --------------------------------------------------
    # BLINK ANIMATION
    # --------------------------------------------------

    def _schedule_blink(self) -> None:
        if self.closed:
            return
        delay = random.randint(2500, 6000)
        self.root.after(delay, self._blink)

    def _blink(self) -> None:
        if self.closed:
            return
        if self.state != FaceState.SLEEPING:
            self._hide_pupils()
            self._close_eyes()
            self.root.after(150, self._restore_current_state)
        self._schedule_blink()

    def _restore_current_state(self) -> None:
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
            lambda: self._handle_window_close(shutdown_event),
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

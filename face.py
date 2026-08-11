import tkinter as tk
from enum import Enum


class FaceState(Enum):
    SLEEPING = "sleeping"
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"


class RogueBotFace:
    """Graphical face and visual state system for RogueBot."""

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

        self.left_eye = None
        self.right_eye = None

        self._draw_face()
        self.set_state(FaceState.IDLE)

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

    def set_state(self, state: FaceState) -> None:
        """Change RogueBot's visual state."""

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

        self.root.update_idletasks()

    def _idle_face(self) -> None:
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

    def _sleeping_face(self) -> None:
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

    def update(self) -> None:
        """Process pending GUI events."""

        try:
            self.root.update()

        except tk.TclError:
            pass

    def close(self) -> None:
        """Close RogueBot's display."""

        try:
            self.root.destroy()

        except tk.TclError:
            pass
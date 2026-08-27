from pathlib import Path

import cv2


class VisionSystem:
    """Handles RogueBot camera input and YuNet face detection."""

    def __init__(
        self,
        camera_index: int = 0,
        model_path: str = "models/face_detection_yunet_2023mar.onnx",
    ) -> None:

        self.camera_index = camera_index
        self.camera = None

        self.model_path = Path(model_path)

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"YuNet model not found: {self.model_path}"
            )

        self.face_detector = cv2.FaceDetectorYN.create(
            str(self.model_path),
            "",
            (320, 320),
            0.7,
            0.3,
            5000,
        )

    def start(self) -> bool:
        """Open the camera."""

        self.camera = cv2.VideoCapture(
            self.camera_index,
            cv2.CAP_AVFOUNDATION,
        )

        if not self.camera.isOpened():
            print("Could not open camera.")
            return False

        print("RogueBot vision online.")

        return True

    def read_frame(self):
        """Capture one camera frame."""

        if self.camera is None:
            return None

        success, frame = self.camera.read()

        if not success:
            return None

        return frame

    def detect_faces(self, frame):
        """Detect faces using YuNet."""

        height, width = frame.shape[:2]

        self.face_detector.setInputSize(
            (width, height)
        )

        _, faces = self.face_detector.detect(
            frame
        )

        if faces is None:
            return []

        return faces

    def get_primary_face(self, faces):
        """Return the largest detected face."""

        if len(faces) == 0:
            return None

        return max(
            faces,
            key=lambda face: face[2] * face[3],
        )

    def get_face_center(
        self,
        face,
    ) -> tuple[int, int]:
        """Return the center of a detected face."""

        x = int(face[0])
        y = int(face[1])
        width = int(face[2])
        height = int(face[3])

        center_x = x + width // 2
        center_y = y + height // 2

        return center_x, center_y

    def get_horizontal_direction(
        self,
        frame,
        face,
    ) -> str:
        """Return left, center, or right."""

        frame_width = frame.shape[1]

        center_x, _ = self.get_face_center(
            face
        )

        left_boundary = frame_width * 0.4
        right_boundary = frame_width * 0.6

        if center_x < left_boundary:
            return "left"

        if center_x > right_boundary:
            return "right"

        return "center"

    def stop(self) -> None:
        """Release camera resources."""

        if self.camera is not None:
            self.camera.release()
            self.camera = None
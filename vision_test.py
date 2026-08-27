import cv2

from vision import VisionSystem


def main() -> None:
    vision = VisionSystem(camera_index=1)

    if not vision.start():
        return

    print("Press Q to close the vision test.")

    while True:

        frame = vision.read_frame()

        if frame is None:
            continue

        faces = vision.detect_faces(frame)

        print(f"Faces detected: {len(faces)}")

        primary_face = vision.get_primary_face(
            faces
        )

        for face in faces:

            x = int(face[0])
            y = int(face[1])
            width = int(face[2])
            height = int(face[3])

            confidence = float(face[14])

            cv2.rectangle(
                frame,
                (x, y),
                (x + width, y + height),
                (0, 255, 0),
                2,
            )

            cv2.putText(
                frame,
                f"{confidence:.2f}",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
            )

        if primary_face is not None:

            center_x, center_y = (
                vision.get_face_center(
                    primary_face
                )
            )

            direction = (
                vision.get_horizontal_direction(
                    frame,
                    primary_face,
                )
            )

            print(
                f"Face center: "
                f"x={center_x}, y={center_y} "
                f"| Direction: {direction}"
            )

            cv2.circle(
                frame,
                (center_x, center_y),
                5,
                (255, 0, 0),
                -1,
            )

        cv2.imshow(
            "RogueBot Vision Test",
            frame,
        )

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    vision.stop()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
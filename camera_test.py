import cv2


camera = cv2.VideoCapture(0)

print("Camera opened:", camera.isOpened())

for i in range(30):
    success, frame = camera.read()

    if success:
        print(
            f"Frame {i}:",
            frame.shape,
            "min:",
            frame.min(),
            "max:",
            frame.max(),
            "mean:",
            frame.mean(),
        )

        cv2.imshow(
            "Raw Camera Test",
            frame,
        )

    if cv2.waitKey(100) & 0xFF == ord("q"):
        break

camera.release()
cv2.destroyAllWindows()
import cv2
import time


for index in range(6):
    print(f"\nTesting camera index {index}...")

    camera = cv2.VideoCapture(
        index,
        cv2.CAP_AVFOUNDATION,
    )

    if not camera.isOpened():
        print("  Could not open.")
        camera.release()
        continue

    # Give the camera a moment to initialize
    time.sleep(1)

    best_mean = 0
    frame_shape = None

    for _ in range(10):
        success, frame = camera.read()

        if not success or frame is None:
            continue

        frame_shape = frame.shape
        best_mean = max(
            best_mean,
            float(frame.mean()),
        )

    print("  Opened: True")
    print("  Shape:", frame_shape)
    print("  Brightness:", best_mean)

    camera.release()
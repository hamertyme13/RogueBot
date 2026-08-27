import time

from face import FaceState, RogueBotFace


face = RogueBotFace()

states = [
    FaceState.IDLE,
    FaceState.LISTENING,
    FaceState.THINKING,
    FaceState.SPEAKING,
    FaceState.SLEEPING,
]

for state in states:
    face.set_state(state)

    start = time.time()

    while time.time() - start < 2:
        face.update()

        time.sleep(0.01)

face.close()
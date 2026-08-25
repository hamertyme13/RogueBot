"""
Local wake-word detection using openwakeword + PyAudio.

The WakeWordDetector streams raw audio from the microphone and scores
each 80 ms chunk through the openwakeword ONNX model.  When the score
for the configured model exceeds the threshold it returns True from
`wait_for_wake_word()`.

Supported built-in model names (no custom training required):
  hey_jarvis, hey_mycroft, hey_rhasspy, alexa, timer, weather

The default model is "hey_jarvis" because it is acoustically similar
to "hey roguebot".  To use a different model set WAKE_WORD_MODEL in
.env, or train a custom model with openwakeword and pass its path.
"""

import numpy as np
import pyaudio
from openwakeword.model import Model


# Audio settings required by openwakeword.
_SAMPLE_RATE = 16000
_CHUNK_SIZE = 1280   # 80 ms at 16 kHz


class WakeWordDetector:
    """Stream audio through openwakeword and detect the wake word."""

    def __init__(
        self,
        model_name: str = "hey_jarvis",
        threshold: float = 0.5,
        inference_framework: str = "onnx",
    ) -> None:
        self.model_name = model_name
        self.threshold = threshold

        self._oww = Model(
            wakeword_models=[model_name],
            inference_framework=inference_framework,
        )

        self._pa = pyaudio.PyAudio()

    def wait_for_wake_word(self) -> None:
        """
        Block until the wake word is detected.

        Opens the microphone, streams audio through the model, and
        returns as soon as the score crosses the threshold.
        """

        stream = self._pa.open(
            rate=_SAMPLE_RATE,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=_CHUNK_SIZE,
        )

        try:
            while True:
                raw = stream.read(
                    _CHUNK_SIZE,
                    exception_on_overflow=False,
                )

                audio = np.frombuffer(raw, dtype=np.int16)

                scores = self._oww.predict(audio)

                score = scores.get(self.model_name, 0.0)

                if score >= self.threshold:
                    # Reset internal state so it doesn't fire again
                    # immediately after returning.
                    self._oww.reset()
                    return

        finally:
            stream.stop_stream()
            stream.close()

    def close(self) -> None:
        """Release the PyAudio instance."""

        self._pa.terminate()

import pyttsx3
import speech_recognition as sr


class SpeechSystem:
    """Handles RogueBot microphone input and spoken output."""

    def __init__(self) -> None:
        self.recognizer = sr.Recognizer()

        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 180)
        self.engine.setProperty("volume", 1.0)

        self._select_voice()

    def _select_voice(self) -> None:
        """Select an available English voice."""

        voices = self.engine.getProperty("voices")

        for voice in voices:
            voice_name = voice.name.lower()

            if "samantha" in voice_name or "alex" in voice_name:
                self.engine.setProperty("voice", voice.id)
                return

    def speak(self, message: str) -> None:
        """Print and speak a message."""

        print(f"\nRogueBot: {message}\n")

        self.engine.say(message)
        self.engine.runAndWait()

    def listen(
        self,
        timeout: int | None = None,
        phrase_time_limit: int = 10,
        show_status: bool = True,
    ) -> str | None:
        """
        Listen through the microphone and return recognized speech.
        """

        try:
            with sr.Microphone() as source:

                if show_status:
                    print("Listening...")

                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )

            text = self.recognizer.recognize_google(audio)

            text = text.lower().strip()

            if show_status:
                print(f"You: {text}")

            return text

        except sr.WaitTimeoutError:
            return None

        except sr.UnknownValueError:
            return None

        except sr.RequestError as error:
            print(f"Speech recognition service error: {error}")
            return None

        except OSError as error:
            print(f"Microphone error: {error}")
            return None

    def calibrate_microphone(self) -> None:
        """Calibrate the microphone for ambient noise."""

        print("Calibrating microphone...")

        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(
                source,
                duration=1,
            )

        print("Microphone ready.")
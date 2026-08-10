import pyttsx3
import speech_recognition as sr


class SpeechSystem:
    """Handles microphone input and spoken output."""

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
        """Speak and print a message."""

        print(f"\nRogueBot: {message}\n")

        self.engine.say(message)
        self.engine.runAndWait()

    def listen(self) -> str | None:
        """Listen through the microphone and return recognized speech."""

        try:
            with sr.Microphone() as source:
                print("Listening...")

                self.recognizer.adjust_for_ambient_noise(
                    source,
                    duration=0.7,
                )

                audio = self.recognizer.listen(
                    source,
                    timeout=8,
                    phrase_time_limit=15,
                )

            print("Processing speech...")

            spoken_text = self.recognizer.recognize_google(audio)

            print(f"You: {spoken_text}")

            return spoken_text

        except sr.WaitTimeoutError:
            print("I did not hear anything.")
            return None

        except sr.UnknownValueError:
            print("I could not understand what was said.")
            return None

        except sr.RequestError as error:
            print(f"Speech recognition service error: {error}")
            return None

        except OSError as error:
            print(f"Microphone error: {error}")
            return None
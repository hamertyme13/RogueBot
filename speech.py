import io
import pyttsx3
import speech_recognition as sr

from config import VOICE_NAME, USE_WHISPER, WHISPER_MODEL
from logger import log


class SpeechSystem:
    """Handles RogueBot microphone input and spoken output."""

    def __init__(self) -> None:
        self.recognizer = sr.Recognizer()

        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 180)
        self.engine.setProperty("volume", 1.0)

        self._select_voice()

        # Load faster-whisper if enabled
        self._whisper = None
        if USE_WHISPER:
            self._load_whisper()

    def _load_whisper(self) -> None:
        """Load the faster-whisper model. Falls back to Google STT on failure."""

        try:
            from faster_whisper import WhisperModel
            log.info("Loading faster-whisper model '%s'…", WHISPER_MODEL)
            self._whisper = WhisperModel(
                WHISPER_MODEL,
                device="cpu",
                compute_type="int8",
            )
            log.info("faster-whisper ready.")
            print(f"faster-whisper loaded (model: {WHISPER_MODEL})")
        except ImportError:
            log.warning(
                "faster-whisper not installed. "
                "Run: pip install faster-whisper  — falling back to Google STT."
            )
            print(
                "faster-whisper not installed. "
                "Run: pip install faster-whisper"
            )

    def _select_voice(self) -> None:
        """Select a voice by name from config, falling back to Samantha/Alex."""

        voices = self.engine.getProperty("voices")
        configured = VOICE_NAME.lower().strip()

        if configured:
            for voice in voices:
                if configured in voice.name.lower():
                    self.engine.setProperty("voice", voice.id)
                    print(f"Voice selected: {voice.name}")
                    return
            print(
                f"Voice '{VOICE_NAME}' not found. "
                "Falling back to default voice selection."
            )

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
        """Listen through the microphone and return recognised speech."""

        if self._whisper is not None:
            return self._listen_whisper(
                timeout=timeout,
                phrase_time_limit=phrase_time_limit,
                show_status=show_status,
            )

        return self._listen_google(
            timeout=timeout,
            phrase_time_limit=phrase_time_limit,
            show_status=show_status,
        )

    # ------------------------------------------------------------------
    # Google STT backend
    # ------------------------------------------------------------------

    def _listen_google(
        self,
        timeout: int | None,
        phrase_time_limit: int,
        show_status: bool,
    ) -> str | None:

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
            log.error("Speech recognition service error: %s", error)
            return None
        except OSError as error:
            log.error("Microphone error: %s", error)
            return None

    # ------------------------------------------------------------------
    # faster-whisper backend
    # ------------------------------------------------------------------

    def _listen_whisper(
        self,
        timeout: int | None,
        phrase_time_limit: int,
        show_status: bool,
    ) -> str | None:
        """Record audio then transcribe locally with faster-whisper."""

        try:
            with sr.Microphone() as source:
                if show_status:
                    print("Listening (Whisper)...")

                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )

        except sr.WaitTimeoutError:
            return None
        except OSError as error:
            log.error("Microphone error: %s", error)
            return None

        # Convert SpeechRecognition AudioData → WAV bytes → file-like
        wav_bytes = audio.get_wav_data()
        wav_file = io.BytesIO(wav_bytes)

        try:
            segments, _ = self._whisper.transcribe(
                wav_file,
                language="en",
                beam_size=5,
            )
            text = " ".join(seg.text for seg in segments).strip().lower()

            if not text:
                return None

            if show_status:
                print(f"You (Whisper): {text}")

            return text

        except Exception as error:
            log.error("Whisper transcription error: %s", error)
            return None

    def calibrate_microphone(self) -> None:
        """Calibrate the microphone for ambient noise."""

        print("Calibrating microphone...")
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Microphone ready.")

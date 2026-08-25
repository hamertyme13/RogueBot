from assistant import RogueBotAssistant
from config import OPENAI_API_KEY
from local_ai import LocalAI
from logger import log
from plugin_loader import dispatch_plugins, load_plugins
from skills.battery import get_battery_status
from skills.briefing_skill import get_briefing
from skills.calc_skill import calculate
from skills.clipboard_skill import clipboard_to_ai, read_clipboard
from skills.dictionary_skill import define_word, spell_word
from skills.dictation_skill import run_dictation_session
from skills.help_skill import get_help
from skills.history_skill import get_recent_commands, log_command
from skills.media_skill import media_control, set_volume
from skills.memory_skill import (
    forget_fact,
    list_memories,
    recall_fact,
    remember_fact,
)
from skills.news_skill import get_news
from skills.notes_skill import add_note, clear_list, read_list
from skills.open_skill import open_app_or_url
from skills.reminder_skill import (
    add_reminder,
    cancel_reminder,
    list_reminders,
)
from skills.screenshot_skill import describe_screen
from skills.search_skill import web_search
from skills.status import get_system_status
from skills.temperature import get_temperature
from skills.time_skill import get_date, get_time
from skills.timer_skill import cancel_timers, list_timers, set_timer
from skills.weather_skill import get_weather


class CommandProcessor:
    """Routes spoken commands to RogueBot skills."""

    def __init__(self) -> None:
        self.local_ai = LocalAI()
        self.openai = RogueBotAssistant() if OPENAI_API_KEY else None
        self.plugins = load_plugins()
        self._last_response: str = ""

        # Injected by main.py so streaming AI can speak sentence-by-sentence
        self._speak_fn = None
        self._listen_fn = None

    # --------------------------------------------------
    # AI FALLBACK  (with streaming)
    # --------------------------------------------------

    def _ask_ai(self, command: str) -> str:
        """
        Try streaming local AI first (sentences spoken as they arrive),
        then non-streaming OpenAI as fallback.

        When streaming succeeds, speech is already delivered sentence-by-sentence
        via _speak_fn — the returned string is the full text for _last_response,
        and main.py must NOT speak it again. We signal this by setting
        self._streamed_last = True before returning.
        """

        self._streamed_last = False

        # --- Streaming local AI ---
        if self._speak_fn is not None:
            spoken_sentences: list[str] = []

            def _on_sentence(sentence: str) -> None:
                spoken_sentences.append(sentence)
                self._speak_fn(sentence)

            result = self.local_ai.ask_streaming(command, _on_sentence)

            if result is not None:
                self._streamed_last = True
                return " ".join(spoken_sentences) if spoken_sentences else result

        else:
            result = self.local_ai.ask(command)
            if result is not None:
                return result

        log.warning("Ollama unavailable — falling back to OpenAI.")

        if self.openai is not None:
            answer = self.openai.get_response(command)
            if answer is not None:
                return answer

        return (
            "My AI systems are currently unavailable. "
            "Make sure Ollama is running or an OpenAI key is configured."
        )

    # --------------------------------------------------
    # PLUGIN HOT-RELOAD
    # --------------------------------------------------

    def reload_plugins(self) -> str:
        self.plugins = load_plugins()
        count = len(self.plugins)
        return f"Plugins reloaded. {count} plugin{'s' if count != 1 else ''} loaded."

    # --------------------------------------------------
    # MAIN DISPATCH
    # --------------------------------------------------

    def process(self, command: str) -> str:
        """Determine which skill handles this command and return the response."""

        command = command.lower().strip()
        log.debug("Processing command: %s", command)

        # Record every command to history (skip meta commands)
        log_command(command)

        response = self._dispatch(command)

        self._last_response = response
        return response

    def _dispatch(self, command: str) -> str:  # noqa: PLR0911,PLR0912
        """Inner dispatch — returns the spoken response."""

        # -------------------------
        # REPEAT LAST RESPONSE
        # -------------------------

        if command in ("repeat that", "say that again", "what did you say"):
            return self._last_response or "I haven't said anything yet."

        # -------------------------
        # PLUGIN HOT-RELOAD
        # -------------------------

        if command in ("reload skills", "reload plugins", "refresh skills"):
            return self.reload_plugins()

        # -------------------------
        # COMMAND HISTORY
        # -------------------------

        if any(w in command for w in (
            "command history", "what did i ask", "what have i asked",
            "recent commands", "last command",
        )):
            return get_recent_commands(command)

        # -------------------------
        # DAILY BRIEFING
        # -------------------------

        if any(w in command for w in (
            "good morning", "morning briefing", "daily briefing",
            "what's my briefing", "start my day", "good afternoon",
            "good evening",
        )):
            return get_briefing()

        # -------------------------
        # CLIPBOARD
        # -------------------------

        if command in ("read my clipboard", "what's on my clipboard",
                       "show my clipboard"):
            return read_clipboard()

        if any(w in command for w in (
            "summarise", "summarize", "summarise this", "summarize this",
            "explain this", "explain it",
            "fix the grammar", "fix this", "correct this",
            "translate this", "translate it",
        )):
            # Only send to clipboard skill if the command references "this"/"it"
            from skills.clipboard_skill import _refers_to_clipboard
            if _refers_to_clipboard(command):
                return clipboard_to_ai(command, self._ask_ai)

        # -------------------------
        # SCREENSHOT
        # -------------------------

        if any(w in command for w in (
            "what's on my screen", "describe my screen", "describe the screen",
            "take a screenshot", "read my screen", "read the screen",
            "what does this say",
        )):
            return describe_screen(command)

        # -------------------------
        # DICTATION
        # -------------------------

        if any(w in command for w in (
            "start dictating", "dictation mode", "type what i say",
            "start dictation",
        )):
            if self._listen_fn and self._speak_fn:
                return run_dictation_session(self._listen_fn, self._speak_fn)
            return "Dictation mode is not available right now."

        # -------------------------
        # MEMORY
        # -------------------------

        if command.startswith("remember that "):
            return remember_fact(command)

        if command.startswith("forget "):
            return forget_fact(command)

        if command in {"what do you remember", "show memories", "list memories"}:
            return list_memories()

        if (
            command.startswith("what is ")
            or command.startswith("what's ")
            or command.startswith("do you remember ")
        ):
            memory_response = recall_fact(command)
            if "don't remember anything" not in memory_response:
                return memory_response

        # -------------------------
        # NOTES / LISTS
        # -------------------------

        if command.startswith("add ") and " list" in command:
            return add_note(command)

        if (
            command.startswith("read my ")
            or command.startswith("what's on my ")
            or command.startswith("show my ")
        ) and "list" in command:
            return read_list(command)

        if (
            command.startswith("clear my ")
            or command.startswith("delete my ")
        ) and "list" in command:
            return clear_list(command)

        # -------------------------
        # REMINDERS
        # -------------------------

        if (
            command.startswith("remind me")
            or command.startswith("set a reminder")
        ):
            return add_reminder(command)

        if command in ("list reminders", "what reminders do i have",
                       "show reminders", "my reminders"):
            return list_reminders()

        if "cancel" in command and "reminder" in command:
            return cancel_reminder(command)

        # -------------------------
        # TIMERS
        # -------------------------

        if "timer" in command or "set a timer" in command:
            if "cancel" in command:
                return cancel_timers()
            if any(w in command for w in ("list", "how much", "how long", "my timers")):
                return list_timers()
            return set_timer(command)

        if command in ("my timers", "list timers", "active timers"):
            return list_timers()

        if "cancel" in command and "timer" in command:
            return cancel_timers()

        # -------------------------
        # TIME
        # -------------------------

        if (
            "what time" in command
            or "tell me the time" in command
            or command == "time"
        ):
            return get_time()

        # -------------------------
        # DATE
        # -------------------------

        if "what day" in command or "what date" in command or command == "date":
            return get_date()

        # -------------------------
        # SYSTEM STATUS
        # -------------------------

        if (
            "system status" in command
            or "status report" in command
            or command == "status"
        ):
            return get_system_status()

        # -------------------------
        # BATTERY
        # -------------------------

        if "battery" in command:
            return get_battery_status()

        # -------------------------
        # TEMPERATURE
        # -------------------------

        if "temperature" in command or "how hot" in command:
            return get_temperature()

        # -------------------------
        # WEATHER
        # -------------------------

        if "weather" in command or "forecast" in command:
            return get_weather(command=command)

        # -------------------------
        # OPEN APP / URL
        # -------------------------

        if (
            command.startswith("open ")
            or command.startswith("launch ")
            or command.startswith("start ")
        ):
            return open_app_or_url(command)

        # -------------------------
        # MEDIA CONTROLS
        # -------------------------

        if any(w in command for w in (
            "volume up", "volume down", "turn it up", "turn it down",
            "set volume", "mute", "unmute",
        )):
            return set_volume(command)

        if any(w in command for w in (
            "next track", "previous track", "skip track",
            "pause the music", "play music", "resume music",
            "pause", "resume",
        )):
            return media_control(command)

        # -------------------------
        # NEWS
        # -------------------------

        if "news" in command or "headlines" in command:
            return get_news()

        # -------------------------
        # CALCULATOR / CONVERSION
        # -------------------------

        if any(w in command for w in (
            "calculate", "compute", "convert",
            "how many", "how much is", "percent of",
            "times", "divided by", "plus", "minus",
            "fahrenheit", "celsius", "kilometre", "kilometer",
            "miles", "kilograms", "pounds",
        )):
            result = calculate(command)
            if "couldn't work that out" not in result:
                return result

        # -------------------------
        # DICTIONARY
        # -------------------------

        if any(w in command for w in (
            "define ", "what does ", "definition of ", "meaning of ",
        )):
            return define_word(command)

        if any(w in command for w in ("how do you spell ", "spell ")):
            return spell_word(command)

        # -------------------------
        # WEB SEARCH
        # -------------------------

        if (
            command.startswith("search for ")
            or command.startswith("search ")
            or command.startswith("look up ")
            or command.startswith("find information")
        ):
            return web_search(command)

        # -------------------------
        # HELP
        # -------------------------

        if "what can you do" in command or "help" in command or "commands" in command:
            return get_help()

        # -------------------------
        # IDENTITY
        # -------------------------

        if "who are you" in command:
            return (
                "I am RogueBot, a programmable robot assistant "
                "currently under development."
            )

        if "who made you" in command or "who built you" in command:
            return "Joshua built me."

        # -------------------------
        # GREETING
        # -------------------------

        if (
            command in ("hello", "hi")
            or "hello roguebot" in command
            or "hi roguebot" in command
        ):
            return "Hello Joshua."

        if "how are you" in command:
            return "All systems are functioning normally."

        # -------------------------
        # PLUGIN SKILLS
        # -------------------------

        plugin_response = dispatch_plugins(self.plugins, command)
        if plugin_response is not None:
            return plugin_response

        # -------------------------
        # UNKNOWN COMMAND — AI
        # -------------------------

        return self._ask_ai(command)

from skills.battery import get_battery_status
from skills.help_skill import get_help
from skills.status import get_system_status
from skills.temperature import get_temperature
from skills.time_skill import get_date, get_time


class CommandProcessor:
    """Routes spoken commands to RogueBot skills."""

    def process(self, command: str) -> str:
        """Determine which RogueBot skill should handle a command."""

        command = command.lower().strip()

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

        if (
            "what day" in command
            or "what date" in command
            or command == "date"
        ):
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

        if (
            "temperature" in command
            or "how hot" in command
        ):
            return get_temperature()

        # -------------------------
        # HELP
        # -------------------------

        if (
            "what can you do" in command
            or "help" in command
            or "commands" in command
        ):
            return get_help()

        # -------------------------
        # IDENTITY
        # -------------------------

        if "who are you" in command:
            return (
                "I am RogueBot, a programmable robot assistant "
                "currently under development."
            )

        if (
            "who made you" in command
            or "who built you" in command
        ):
            return "Joshua built me."

        # -------------------------
        # GREETING
        # -------------------------

        if (
            command == "hello"
            or command == "hi"
            or "hello roguebot" in command
            or "hi roguebot" in command
        ):
            return "Hello Joshua."

        if "how are you" in command:
            return "All systems are functioning normally."

        # -------------------------
        # UNKNOWN COMMAND
        # -------------------------

        return (
            "I don't know how to perform that command yet."
        )
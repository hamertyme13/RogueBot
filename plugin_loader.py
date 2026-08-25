"""
Plugin skill auto-discovery for RogueBot.

Any .py file in the skills/ directory can become a plugin by defining:

    TRIGGERS: list[str]
        Strings or prefixes that activate this skill.
        A trigger ending with a space (" ") is matched as a prefix.
        A trigger without a trailing space is matched as a substring.

    def handle(command: str) -> str:
        The function called with the full normalised command string.
        Must return a spoken response string.

    PRIORITY: int  (optional, default 50)
        Lower numbers run first. Built-in routing in CommandProcessor
        uses priority 0–10 for memory/identity/etc., and 100 for
        the AI fallback.

Example skill file (skills/my_skill.py):

    TRIGGERS = ["say hello", "greet me"]
    PRIORITY = 50

    def handle(command: str) -> str:
        return "Hello there!"
"""

import importlib
import importlib.util
from pathlib import Path


_SKILLS_DIR = Path(__file__).parent / "skills"


def _load_plugin(path: Path):
    """Import a skill file and return the module if it looks like a plugin."""

    spec = importlib.util.spec_from_file_location(
        f"skills.{path.stem}", path
    )

    if spec is None or spec.loader is None:
        return None

    module = importlib.util.module_from_spec(spec)

    try:
        spec.loader.exec_module(module)
    except Exception as error:
        print(f"Plugin load error ({path.name}): {error}")
        return None

    # Must define TRIGGERS and handle()
    if not hasattr(module, "TRIGGERS") or not callable(
        getattr(module, "handle", None)
    ):
        return None

    return module


def load_plugins() -> list:
    """
    Discover and return all plugin skill modules, sorted by PRIORITY.
    """

    plugins = []

    for path in sorted(_SKILLS_DIR.glob("*.py")):
        if path.name.startswith("_"):
            continue

        module = _load_plugin(path)

        if module is not None:
            plugins.append(module)
            print(
                f"Plugin loaded: {path.stem} "
                f"(triggers: {module.TRIGGERS}, "
                f"priority: {getattr(module, 'PRIORITY', 50)})"
            )

    plugins.sort(key=lambda m: getattr(m, "PRIORITY", 50))

    return plugins


def dispatch_plugins(plugins: list, command: str) -> str | None:
    """
    Try each plugin in priority order.
    Returns the first non-None response, or None if no plugin matched.
    """

    for module in plugins:
        for trigger in module.TRIGGERS:
            matched = False

            if trigger.endswith(" "):
                # Prefix match
                if command.startswith(trigger):
                    matched = True
            else:
                # Substring match
                if trigger in command:
                    matched = True

            if matched:
                try:
                    return module.handle(command)
                except Exception as error:
                    print(
                        f"Plugin error ({module.__name__}): {error}"
                    )
                    return "I encountered an error in that skill."

    return None

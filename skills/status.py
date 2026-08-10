import platform

import psutil


def get_system_status() -> str:
    """Return a basic RogueBot system status report."""

    cpu_usage = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()

    memory_usage = round(memory.percent)

    system_name = platform.system()

    if system_name == "Darwin":
        system_name = "macOS"

    return (
        f"All core systems are online. "
        f"CPU usage is {cpu_usage:.0f} percent. "
        f"Memory usage is {memory_usage} percent. "
        f"I am currently running on {system_name}."
    )
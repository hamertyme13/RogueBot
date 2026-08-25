import subprocess


def _osascript(script: str) -> bool:
    """Run an AppleScript snippet. Returns True on success."""

    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
    )

    return result.returncode == 0


def set_volume(command: str) -> str:
    """
    Handle commands such as:
    'set volume to 50'
    'volume up' / 'turn it up'
    'volume down' / 'turn it down'
    'mute' / 'unmute'
    """

    command = command.lower().strip()

    if "mute" in command and "unmute" not in command:
        _osascript("set volume output muted true")
        return "Muted."

    if "unmute" in command:
        _osascript("set volume output muted false")
        return "Unmuted."

    if any(w in command for w in ("up", "louder", "increase", "raise")):
        _osascript(
            "set volume output volume "
            "(output volume of (get volume settings) + 10)"
        )
        return "Volume increased."

    if any(w in command for w in ("down", "lower", "quieter", "decrease", "reduce")):
        _osascript(
            "set volume output volume "
            "(output volume of (get volume settings) - 10)"
        )
        return "Volume decreased."

    # "set volume to N" or "volume N"
    import re
    match = re.search(r"(\d+)", command)
    if match:
        level = max(0, min(100, int(match.group(1))))
        _osascript(f"set volume output volume {level}")
        return f"Volume set to {level}."

    return (
        "Say 'volume up', 'volume down', 'mute', 'unmute', "
        "or 'set volume to 50'."
    )


def media_control(command: str) -> str:
    """
    Handle commands such as:
    'pause' / 'play' / 'next track' / 'previous track'
    """

    command = command.lower().strip()

    if any(w in command for w in ("pause", "stop the music")):
        _osascript('tell application "Music" to pause')
        return "Paused."

    if any(w in command for w in ("play", "resume")):
        _osascript('tell application "Music" to play')
        return "Playing."

    if any(w in command for w in ("next", "skip")):
        _osascript('tell application "Music" to next track')
        return "Next track."

    if any(w in command for w in ("previous", "back", "last track")):
        _osascript('tell application "Music" to previous track')
        return "Previous track."

    return "I didn't understand that media command."

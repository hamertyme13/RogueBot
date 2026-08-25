import subprocess
import webbrowser


# Common app aliases → macOS app names / bundle IDs
_APP_ALIASES: dict[str, str] = {
    "spotify": "Spotify",
    "chrome": "Google Chrome",
    "google chrome": "Google Chrome",
    "firefox": "Firefox",
    "safari": "Safari",
    "terminal": "Terminal",
    "finder": "Finder",
    "calculator": "Calculator",
    "calendar": "Calendar",
    "mail": "Mail",
    "messages": "Messages",
    "notes": "Notes",
    "reminders": "Reminders",
    "photos": "Photos",
    "music": "Music",
    "podcasts": "Podcasts",
    "facetime": "FaceTime",
    "system preferences": "System Preferences",
    "system settings": "System Settings",
    "activity monitor": "Activity Monitor",
    "vs code": "Visual Studio Code",
    "vscode": "Visual Studio Code",
    "slack": "Slack",
    "discord": "Discord",
    "zoom": "Zoom",
    "xcode": "Xcode",
}

# URL shortcuts
_URL_ALIASES: dict[str, str] = {
    "github": "https://github.com",
    "youtube": "https://youtube.com",
    "google": "https://google.com",
    "gmail": "https://mail.google.com",
    "reddit": "https://reddit.com",
    "twitter": "https://twitter.com",
    "x": "https://x.com",
}


def open_app_or_url(command: str) -> str:
    """
    Handle commands such as:
    'open spotify'
    'open github'
    'open chrome'
    """

    command = command.lower().strip()

    # Strip leading trigger words
    for prefix in ("open ", "launch ", "start "):
        if command.startswith(prefix):
            target = command[len(prefix):].strip()
            break
    else:
        target = command

    # Check URL aliases first
    if target in _URL_ALIASES:
        webbrowser.open(_URL_ALIASES[target])
        return f"Opening {target}."

    # Check app aliases
    app_name = _APP_ALIASES.get(target, target.title())

    result = subprocess.run(
        ["open", "-a", app_name],
        capture_output=True,
    )

    if result.returncode == 0:
        return f"Opening {app_name}."

    return f"I couldn't find an app called {target}."

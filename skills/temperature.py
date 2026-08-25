import subprocess


def get_temperature() -> str:
    """Return CPU temperature on macOS using the 'osx-cpu-temp' tool."""

    try:
        result = subprocess.run(
            ["osx-cpu-temp"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            temp_str = result.stdout.strip()
            return f"CPU temperature is {temp_str}."

    except FileNotFoundError:
        pass

    except subprocess.TimeoutExpired:
        pass

    # Fallback: try iStats gem
    try:
        result = subprocess.run(
            ["istats", "cpu", "--no-graphs"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if "cpu" in line.lower() and "°" in line:
                    temp_str = line.strip()
                    return f"CPU temperature: {temp_str}."

    except FileNotFoundError:
        pass

    except subprocess.TimeoutExpired:
        pass

    return (
        "Temperature sensors are not available. "
        "Install osx-cpu-temp with Homebrew to enable this feature."
    )

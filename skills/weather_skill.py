import json
import re
import urllib.error
import urllib.parse
import urllib.request


# Open-Meteo geocoding + forecast — no API key required.
_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

_DEFAULT_CITY = "New York"


def _fetch_json(url: str) -> dict | None:
    """Fetch a URL and return parsed JSON, or None on error."""

    try:
        with urllib.request.urlopen(url, timeout=8) as response:
            return json.loads(response.read().decode("utf-8"))

    except (urllib.error.URLError, json.JSONDecodeError) as error:
        print(f"Weather fetch error: {error}")
        return None


def _geocode(city: str) -> tuple[float, float] | None:
    """Return (latitude, longitude) for a city name."""

    params = urllib.parse.urlencode({
        "name": city,
        "count": 1,
        "language": "en",
        "format": "json",
    })

    data = _fetch_json(f"{_GEOCODE_URL}?{params}")

    if not data or not data.get("results"):
        return None

    result = data["results"][0]

    return result["latitude"], result["longitude"]


def _get_city() -> str:
    """
    Return the city to use for weather.

    Checks memory first (key 'my city'), then falls back to the
    IP geolocation API, then the hardcoded default.
    """

    # Check stored memory
    try:
        from memory import MemoryManager
        memory = MemoryManager()
        stored = memory.recall("my city")
        if stored:
            return stored
    except Exception:
        pass

    # Try IP geolocation (free, no key)
    try:
        data = _fetch_json("http://ip-api.com/json/?fields=city")
        if data and data.get("city"):
            return data["city"]
    except Exception:
        pass

    return _DEFAULT_CITY


def _extract_city_from_command(command: str) -> str | None:
    """
    Try to pull an explicit city from commands like
    'what's the weather in Tokyo' or 'weather for Paris'.
    """
    for pattern in (
        r"weather (?:in|for|at) (.+)",
        r"forecast (?:in|for|at) (.+)",
    ):
        m = re.search(pattern, command.lower())
        if m:
            return m.group(1).strip().title()
    return None


def get_weather(city: str | None = None, command: str | None = None) -> str:
    """Return a spoken current-conditions weather report."""

    if city is None:
        if command:
            city = _extract_city_from_command(command) or _get_city()
        else:
            city = _get_city()

    coords = _geocode(city)

    if coords is None:
        return f"I couldn't find weather data for {city}."

    lat, lon = coords

    params = urllib.parse.urlencode({
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,weathercode,windspeed_10m",
        "temperature_unit": "fahrenheit",
        "windspeed_unit": "mph",
        "timezone": "auto",
    })

    data = _fetch_json(f"{_FORECAST_URL}?{params}")

    if not data or "current" not in data:
        return "I wasn't able to retrieve weather data right now."

    current = data["current"]

    temp = round(current.get("temperature_2m", 0))
    wind = round(current.get("windspeed_10m", 0))
    code = current.get("weathercode", 0)

    condition = _weathercode_to_description(code)

    return (
        f"Current conditions in {city}: "
        f"{condition}, {temp} degrees Fahrenheit, "
        f"wind speed {wind} miles per hour."
    )


def _weathercode_to_description(code: int) -> str:
    """Convert a WMO weather code to a human-readable description."""

    if code == 0:
        return "clear sky"
    if code == 1:
        return "mainly clear"
    if code == 2:
        return "partly cloudy"
    if code == 3:
        return "overcast"
    if code in (45, 48):
        return "foggy"
    if code in (51, 53, 55):
        return "drizzle"
    if code in (61, 63, 65):
        return "rain"
    if code in (71, 73, 75):
        return "snow"
    if code in (80, 81, 82):
        return "rain showers"
    if code in (95, 96, 99):
        return "thunderstorm"

    return "mixed conditions"

import psutil


def get_temperature() -> str:
    """Return available system temperature information."""

    try:
        temperatures = psutil.sensors_temperatures()

    except AttributeError:
        return (
            "Temperature sensors are not currently available "
            "on this system."
        )

    if not temperatures:
        return (
            "I cannot currently read system temperature sensors."
        )

    readings = []

    for sensor_name, entries in temperatures.items():

        for entry in entries:

            if entry.current is not None:
                readings.append(
                    f"{sensor_name} is {entry.current:.1f} degrees Celsius"
                )

    if not readings:
        return "I could not find any temperature readings."

    return ". ".join(readings) + "."
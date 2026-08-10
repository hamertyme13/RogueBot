import psutil


def get_battery_status() -> str:
    """Return the computer's current battery status."""

    battery = psutil.sensors_battery()

    if battery is None:
        return "I cannot detect a battery on this system."

    percent = round(battery.percent)

    if battery.power_plugged:
        charging_status = "and I am connected to power"
    else:
        charging_status = "and I am running on battery power"

    return (
        f"Battery level is {percent} percent, "
        f"{charging_status}."
    )
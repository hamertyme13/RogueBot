"""
Calculator and unit-conversion skill.

Handles:
  - Arithmetic:  "what is 15% of 340"  "what is 12 times 8"
  - Conversions: "convert 72 fahrenheit to celsius"
                 "how many feet in a mile"
                 "convert 5 kilometres to miles"
"""

import re


# ---------------------------------------------------------------------------
# Safe expression evaluator — no eval(), no builtins
# ---------------------------------------------------------------------------

_WORD_OPS = {
    " plus ": "+",
    " minus ": "-",
    " times ": "*",
    " multiplied by ": "*",
    " divided by ": "/",
    " over ": "/",
    " squared": "**2",
    " cubed": "**3",
}


def _safe_eval(expr: str) -> float | None:
    """
    Evaluate a simple arithmetic expression using only +, -, *, /, **, ().
    Returns None if the expression is unsafe or fails to parse.
    """
    # Allow only digits, operators, parentheses, decimal points, whitespace
    if not re.fullmatch(r"[\d\s\+\-\*/\(\)\.\%\^]+", expr):
        return None
    try:
        # Replace ^ with ** for power
        expr = expr.replace("^", "**")
        result = eval(  # noqa: S307 — guarded by regex above
            expr,
            {"__builtins__": {}},
            {},
        )
        return float(result)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Percentage helper  "X% of Y"
# ---------------------------------------------------------------------------

def _try_percentage(command: str) -> str | None:
    m = re.search(r"(\d+(?:\.\d+)?)\s*%\s*of\s+(\d+(?:\.\d+)?)", command)
    if m:
        pct = float(m.group(1))
        whole = float(m.group(2))
        result = pct / 100 * whole
        return f"{pct}% of {whole:g} is {result:g}."
    return None


# ---------------------------------------------------------------------------
# Unit conversion tables
# ---------------------------------------------------------------------------

_CONVERSIONS: list[tuple[set, set, float]] = [
    # (from_aliases, to_aliases, factor_from→to)
    ({"fahrenheit", "f"}, {"celsius", "c", "centigrade"}, None),   # special
    ({"celsius", "c", "centigrade"}, {"fahrenheit", "f"}, None),   # special
    ({"kilometre", "kilometres", "kilometer", "kilometers", "km"}, {"mile", "miles", "mi"}, 0.621371),
    ({"mile", "miles", "mi"}, {"kilometre", "kilometres", "kilometer", "kilometers", "km"}, 1.60934),
    ({"metre", "metres", "meter", "meters", "m"}, {"foot", "feet", "ft"}, 3.28084),
    ({"foot", "feet", "ft"}, {"metre", "metres", "meter", "meters", "m"}, 0.3048),
    ({"kilogram", "kilograms", "kg", "kilo", "kilos"}, {"pound", "pounds", "lb", "lbs"}, 2.20462),
    ({"pound", "pounds", "lb", "lbs"}, {"kilogram", "kilograms", "kg", "kilo", "kilos"}, 0.453592),
    ({"litre", "litres", "liter", "liters", "l"}, {"gallon", "gallons", "gal"}, 0.264172),
    ({"gallon", "gallons", "gal"}, {"litre", "litres", "liter", "liters", "l"}, 3.78541),
    ({"inch", "inches", "in"}, {"centimetre", "centimetres", "centimeter", "centimeters", "cm"}, 2.54),
    ({"centimetre", "centimetres", "centimeter", "centimeters", "cm"}, {"inch", "inches", "in"}, 0.393701),
]


def _normalise_unit(unit: str) -> str:
    """
    Try to match a unit string against known aliases.
    Returns the unit lowercased and stripped; does NOT strip trailing 's'
    so that 'celsius', 'miles', etc. match correctly.
    """
    return unit.strip().lower()


def _find_unit_in_sets(unit: str) -> str:
    """
    Try the unit as-is, then with trailing 's' stripped (for plurals like
    'kilometres' -> 'kilometre'), but never strip from known non-plural
    endings that would break words like 'celsius'.
    """
    candidates = [unit]
    if unit.endswith("s") and len(unit) > 3:
        candidates.append(unit[:-1])   # kilometres -> kilometre
    return candidates


def _try_conversion(command: str) -> str | None:
    m = re.search(
        r"(\d+(?:\.\d+)?)\s+(\w[\w\s]*?)\s+(?:to|in|into)\s+(\w[\w\s]*)",
        command,
    )
    if not m:
        return None
    amount = float(m.group(1))
    from_raw = _normalise_unit(m.group(2))
    to_raw = _normalise_unit(m.group(3))
    from_candidates = _find_unit_in_sets(from_raw)
    to_candidates = _find_unit_in_sets(to_raw)

    from_unit = from_raw
    to_unit = to_raw

    for from_set, to_set, factor in _CONVERSIONS:
        matched_from = next((c for c in from_candidates if c in from_set), None)
        matched_to = next((c for c in to_candidates if c in to_set), None)
        if matched_from and matched_to:
            from_unit, to_unit = matched_from, matched_to
            if factor is None:
                # Temperature special cases
                if "fahrenheit" in from_set or from_unit == "f":
                    result = (amount - 32) * 5 / 9
                    return f"{amount:g}°F is {result:.1f}°C."
                else:
                    result = amount * 9 / 5 + 32
                    return f"{amount:g}°C is {result:.1f}°F."
            result = amount * factor
            to_label = next(iter(to_set))
            from_label = next(iter(from_set))
            return f"{amount:g} {from_label} is {result:.4g} {to_label}."
    return None


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def calculate(command: str) -> str:
    """Handle calculator and unit-conversion commands."""

    command = command.lower().strip()

    # Strip leading trigger phrases
    for prefix in ("what is ", "what's ", "calculate ", "compute ", "how much is "):
        if command.startswith(prefix):
            command = command[len(prefix):]
            break

    # Percentage
    result = _try_percentage(command)
    if result:
        return result

    # Unit conversion
    result = _try_conversion(command)
    if result:
        return result

    # Replace word operators
    expr = command
    for word, symbol in _WORD_OPS.items():
        expr = expr.replace(word, symbol)

    # Strip any remaining non-math text before evaluating
    expr = re.sub(r"[a-zA-Z]", "", expr).strip()

    value = _safe_eval(expr)
    if value is not None:
        # Tidy: no trailing .0 for whole numbers
        formatted = f"{value:g}"
        return f"The answer is {formatted}."

    return "I couldn't work that out. Try rephrasing it as a simple calculation."

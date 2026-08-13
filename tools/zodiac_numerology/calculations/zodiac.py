"""Western zodiac sign determination — pure date arithmetic, no I/O.

The sign is always computed here in Python, never guessed by the LLM.
The AI is only ever used later to narrate an interpretation of a sign
that has already been decided.
"""

# Canonical order, used by tests and anywhere a fixed listing is needed.
ZODIAC_SIGN_KEYS = (
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces",
)

# (sign_key, (start_month, start_day), (end_month, end_day)).
# Capricorn wraps across the new year (Dec 22 -> Jan 19).
_SIGN_RANGES = (
    ("capricorn", (12, 22), (1, 19)),
    ("aquarius", (1, 20), (2, 18)),
    ("pisces", (2, 19), (3, 20)),
    ("aries", (3, 21), (4, 19)),
    ("taurus", (4, 20), (5, 20)),
    ("gemini", (5, 21), (6, 20)),
    ("cancer", (6, 21), (7, 22)),
    ("leo", (7, 23), (8, 22)),
    ("virgo", (8, 23), (9, 22)),
    ("libra", (9, 23), (10, 22)),
    ("scorpio", (10, 23), (11, 21)),
    ("sagittarius", (11, 22), (12, 21)),
)


def get_zodiac_sign(birth_date):
    """Return the zodiac sign key ("aries", "taurus", ...) for a birth date."""
    month, day = birth_date.month, birth_date.day
    for key, (start_m, start_d), (end_m, end_d) in _SIGN_RANGES:
        if start_m <= end_m:
            in_range = (
                (month == start_m and day >= start_d)
                or (month == end_m and day <= end_d)
                or (start_m < month < end_m)
            )
        else:  # wraps around the new year, e.g. capricorn
            in_range = (month == start_m and day >= start_d) or (
                month == end_m and day <= end_d
            )
        if in_range:
            return key
    raise ValueError(f"Could not determine zodiac sign for {birth_date!r}")  # pragma: no cover

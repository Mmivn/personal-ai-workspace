"""Birth date parsing and validation.

Kept separate from models.py so all pure, I/O-free calculation logic
(zodiac, numerology, date parsing) lives together under calculations/,
independent of any terminal or GUI code.
"""
from datetime import date, datetime

# Supported input formats, tried in this order.
DATE_FORMATS = ("%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d")

MIN_BIRTH_YEAR = 1900


class InvalidDateError(ValueError):
    """A birth date string could not be parsed or is out of a sane range.

    `reason` is one of "unparseable", "future_date", "too_old" so the UI
    layer can pick the right localized message.
    """

    def __init__(self, reason):
        self.reason = reason
        super().__init__(reason)


def parse_birth_date(raw, today=None):
    """Parse a birth date from DD.MM.YYYY, DD/MM/YYYY or YYYY-MM-DD.

    Raises InvalidDateError if the string matches no supported format,
    describes an impossible calendar date (e.g. 30.02.2020), lies in the
    future, or is earlier than MIN_BIRTH_YEAR.
    """
    raw = raw.strip()
    today = today or date.today()

    parsed = None
    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(raw, fmt).date()
            break
        except ValueError:
            continue

    if parsed is None:
        raise InvalidDateError("unparseable")

    if parsed > today:
        raise InvalidDateError("future_date")

    if parsed.year < MIN_BIRTH_YEAR:
        raise InvalidDateError("too_old")

    return parsed

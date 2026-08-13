"""Structured, framework-independent data for the app.

The CLI today (and a future GUI) and the AI service all read from these
plain dataclasses instead of re-deriving facts themselves. Nothing here
touches input()/print() or the network — it only holds and builds data.
"""
from dataclasses import dataclass
from datetime import date

from calculations.numerology import life_path_number
from calculations.zodiac import get_zodiac_sign


@dataclass
class UserProfile:
    """The primary user's saved data, including derived facts."""

    name: str
    birth_date: date
    language: str
    zodiac_sign: str
    life_path_number: int


@dataclass
class CompanionProfile:
    """A second person's data, used only for compatibility checks."""

    name: str
    birth_date: date
    zodiac_sign: str
    life_path_number: int


def build_user_profile(name, birth_date, language):
    """Create a UserProfile, computing zodiac sign and life path number."""
    return UserProfile(
        name=name,
        birth_date=birth_date,
        language=language,
        zodiac_sign=get_zodiac_sign(birth_date),
        life_path_number=life_path_number(birth_date),
    )


def build_companion_profile(name, birth_date):
    """Create a CompanionProfile for compatibility checks."""
    return CompanionProfile(
        name=name,
        birth_date=birth_date,
        zodiac_sign=get_zodiac_sign(birth_date),
        life_path_number=life_path_number(birth_date),
    )

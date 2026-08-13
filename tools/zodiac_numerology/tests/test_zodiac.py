from datetime import date

import pytest

from calculations.zodiac import ZODIAC_SIGN_KEYS, get_zodiac_sign

# One representative date safely inside each sign's range.
MID_RANGE_DATES = {
    "capricorn": (1, 5),
    "aquarius": (2, 1),
    "pisces": (3, 5),
    "aries": (4, 1),
    "taurus": (5, 5),
    "gemini": (6, 5),
    "cancer": (7, 5),
    "leo": (8, 5),
    "virgo": (9, 5),
    "libra": (10, 5),
    "scorpio": (11, 5),
    "sagittarius": (12, 5),
}

# (sign, start (month, day), end (month, day)) — independent copy of the
# accepted Western zodiac boundaries, used to check the implementation.
BOUNDARIES = [
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
]


def test_all_twelve_signs_are_defined():
    assert len(ZODIAC_SIGN_KEYS) == 12
    assert len(set(ZODIAC_SIGN_KEYS)) == 12


@pytest.mark.parametrize("sign,month_day", MID_RANGE_DATES.items())
def test_mid_range_date_resolves_to_expected_sign(sign, month_day):
    month, day = month_day
    assert get_zodiac_sign(date(2023, month, day)) == sign


@pytest.mark.parametrize("sign,start,end", BOUNDARIES)
def test_boundary_dates_resolve_to_expected_sign(sign, start, end):
    start_month, start_day = start
    end_month, end_day = end
    assert get_zodiac_sign(date(2023, start_month, start_day)) == sign
    assert get_zodiac_sign(date(2023, end_month, end_day)) == sign


def test_day_before_range_start_belongs_to_previous_sign():
    # April 19 is the last day of Aries; April 20 is the first day of Taurus.
    assert get_zodiac_sign(date(2023, 4, 19)) == "aries"
    assert get_zodiac_sign(date(2023, 4, 20)) == "taurus"


def test_leap_day_is_pisces():
    assert get_zodiac_sign(date(2024, 2, 29)) == "pisces"


def test_new_year_wraparound_is_capricorn():
    assert get_zodiac_sign(date(2023, 12, 31)) == "capricorn"
    assert get_zodiac_sign(date(2023, 1, 1)) == "capricorn"

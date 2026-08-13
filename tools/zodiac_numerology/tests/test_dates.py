from datetime import date

import pytest

from calculations.dates import InvalidDateError, parse_birth_date


def test_parses_dot_format():
    assert parse_birth_date("15.03.1990") == date(1990, 3, 15)


def test_parses_slash_format():
    assert parse_birth_date("15/03/1990") == date(1990, 3, 15)


def test_parses_iso_format():
    assert parse_birth_date("1990-03-15") == date(1990, 3, 15)


def test_parses_leap_day():
    assert parse_birth_date("29.02.2000") == date(2000, 2, 29)


def test_rejects_impossible_calendar_date():
    with pytest.raises(InvalidDateError) as excinfo:
        parse_birth_date("30.02.2020")
    assert excinfo.value.reason == "unparseable"


def test_rejects_non_leap_year_feb_29():
    with pytest.raises(InvalidDateError) as excinfo:
        parse_birth_date("29.02.2001")
    assert excinfo.value.reason == "unparseable"


def test_rejects_garbage_input():
    with pytest.raises(InvalidDateError) as excinfo:
        parse_birth_date("not a date")
    assert excinfo.value.reason == "unparseable"


def test_rejects_future_date():
    with pytest.raises(InvalidDateError) as excinfo:
        parse_birth_date("01.01.2999", today=date(2026, 1, 1))
    assert excinfo.value.reason == "future_date"


def test_rejects_too_old_date():
    with pytest.raises(InvalidDateError) as excinfo:
        parse_birth_date("01.01.1500")
    assert excinfo.value.reason == "too_old"


def test_today_itself_is_accepted():
    today = date(2026, 8, 12)
    assert parse_birth_date("12.08.2026", today=today) == today

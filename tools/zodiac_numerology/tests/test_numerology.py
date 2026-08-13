from datetime import date

from calculations.numerology import (
    life_path_number,
    personal_day_number,
    personal_month_number,
    personal_year_number,
    reduce_fully,
    reduce_keep_master,
)


def test_reduce_keep_master_basic_reduction():
    assert reduce_keep_master(7) == 7
    assert reduce_keep_master(49) == 4  # 4+9=13 -> 1+3=4


def test_reduce_keep_master_stops_on_master_number():
    assert reduce_keep_master(29) == 11  # 2+9=11, a master number
    assert reduce_keep_master(38) == 11  # 3+8=11, a master number


def test_reduce_fully_ignores_master_numbers():
    assert reduce_fully(29) == 2  # 2+9=11 -> 1+1=2
    assert reduce_fully(11) == 2


def test_life_path_number_regular_case():
    # 1990-01-15: day 15->6, month 1->1, year 1990->1, total 8.
    assert life_path_number(date(1990, 1, 15)) == 8


def test_life_path_number_master_11():
    # 1971-01-01: day 1, month 1, year 1971->9, total 11 (master).
    assert life_path_number(date(1971, 1, 1)) == 11


def test_life_path_number_master_22():
    # 1903-09-09: day 9, month 9, year 1903->4, total 22 (master).
    assert life_path_number(date(1903, 9, 9)) == 22


def test_life_path_number_master_33():
    # 1901-11-29: day 29->11, month 11 (already master), year 1901->11,
    # total 33 (master).
    assert life_path_number(date(1901, 11, 29)) == 33


def test_personal_numbers_for_a_fixed_reference_date():
    birth_date = date(1990, 5, 20)
    today = date(2026, 8, 12)
    assert personal_year_number(birth_date, today) == 8
    assert personal_month_number(birth_date, today) == 7
    assert personal_day_number(birth_date, today) == 1


def test_personal_numbers_can_land_on_master_numbers():
    birth_date = date(1990, 9, 9)
    today = date(2020, 1, 6)
    assert personal_year_number(birth_date, today) == 22
    assert personal_month_number(birth_date, today) == 5
    assert personal_day_number(birth_date, today) == 11


def test_personal_year_defaults_to_real_today_when_not_given():
    birth_date = date(1990, 5, 20)
    assert personal_year_number(birth_date) == personal_year_number(birth_date, date.today())

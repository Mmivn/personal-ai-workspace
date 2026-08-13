"""Numerology calculations — pure arithmetic, no I/O.

All numbers here are computed in Python; the AI is only used to narrate
numbers that are already final by the time they reach it — it never does
the arithmetic itself.

Numerology has several competing traditions; this module documents the
one this app uses so results stay reproducible:

- Master numbers 11, 22 and 33 are preserved whenever a digit-reduction
  step lands exactly on one of them.
- Life Path Number: the birth day, month and year are each reduced
  separately (keeping master numbers), then the three results are summed
  and reduced once more.
- Personal Year / Month / Day: each component is fully reduced to a
  single digit first (master numbers are not kept mid-calculation) and
  only the final sum may end up as a master number.
"""
from datetime import date

MASTER_NUMBERS = (11, 22, 33)


def reduce_keep_master(n):
    """Sum digits repeatedly until a single digit or a master number remains."""
    while n > 9 and n not in MASTER_NUMBERS:
        n = sum(int(d) for d in str(n))
    return n


def reduce_fully(n):
    """Sum digits repeatedly until a single digit remains, ignoring master numbers."""
    while n > 9:
        n = sum(int(d) for d in str(n))
    return n


def life_path_number(birth_date):
    day = reduce_keep_master(birth_date.day)
    month = reduce_keep_master(birth_date.month)
    year = reduce_keep_master(birth_date.year)
    return reduce_keep_master(day + month + year)


def personal_year_number(birth_date, today=None):
    today = today or date.today()
    month = reduce_fully(birth_date.month)
    day = reduce_fully(birth_date.day)
    year = reduce_fully(today.year)
    return reduce_keep_master(month + day + year)


def personal_month_number(birth_date, today=None):
    today = today or date.today()
    personal_year = reduce_fully(personal_year_number(birth_date, today))
    return reduce_keep_master(personal_year + today.month)


def personal_day_number(birth_date, today=None):
    today = today or date.today()
    personal_month = reduce_fully(personal_month_number(birth_date, today))
    return reduce_keep_master(personal_month + today.day)

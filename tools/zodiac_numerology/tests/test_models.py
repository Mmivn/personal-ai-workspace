from datetime import date

from models import build_companion_profile, build_user_profile


def test_build_user_profile_computes_zodiac_and_life_path():
    profile = build_user_profile("Anna", date(1990, 1, 15), "en")
    assert profile.name == "Anna"
    assert profile.language == "en"
    assert profile.zodiac_sign == "capricorn"
    assert profile.life_path_number == 8


def test_build_companion_profile_has_no_language_field():
    companion = build_companion_profile("Bob", date(1990, 5, 20))
    assert companion.name == "Bob"
    assert companion.zodiac_sign == "taurus"
    assert not hasattr(companion, "language")

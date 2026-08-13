from calculations.zodiac import ZODIAC_SIGN_KEYS
from locales import LANGUAGE_CHOICES, LOCALES, resolve_language_choice


def _collect_key_paths(d, prefix=""):
    """Flatten a nested locale dict into a set of dotted key paths.

    Lists (e.g. menu "items") are treated as opaque leaves here; their
    item keys are checked separately in test_menu_item_keys_match.
    """
    paths = set()
    for key, value in d.items():
        path = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            paths |= _collect_key_paths(value, path)
        else:
            paths.add(path)
    return paths


def test_three_languages_are_registered():
    assert set(LOCALES.keys()) == {"ru", "en", "vi"}
    assert [code for _, code in LANGUAGE_CHOICES] == ["ru", "en", "vi"]


def test_all_languages_have_identical_key_structure():
    reference = _collect_key_paths(LOCALES["ru"])
    for lang_code in ("en", "vi"):
        assert _collect_key_paths(LOCALES[lang_code]) == reference, lang_code


def test_menu_item_keys_match_across_languages():
    for menu_name in ("main_menu", "zodiac_menu", "numerology_menu"):
        reference_keys = [key for key, _label in LOCALES["ru"][menu_name]["items"]]
        for lang_code in ("en", "vi"):
            keys = [key for key, _label in LOCALES[lang_code][menu_name]["items"]]
            assert keys == reference_keys, (menu_name, lang_code)


def test_all_languages_have_all_twelve_zodiac_sign_names():
    for lang_code, locale in LOCALES.items():
        assert set(locale["zodiac"]["sign_names"].keys()) == set(ZODIAC_SIGN_KEYS), lang_code


def test_resolve_language_choice_by_menu_number():
    assert resolve_language_choice("1") == "ru"
    assert resolve_language_choice("2") == "en"
    assert resolve_language_choice("3") == "vi"


def test_resolve_language_choice_by_language_code_case_insensitive():
    assert resolve_language_choice("ru") == "ru"
    assert resolve_language_choice("EN") == "en"
    assert resolve_language_choice(" vi ") == "vi"


def test_resolve_language_choice_invalid_returns_none():
    assert resolve_language_choice("9") is None
    assert resolve_language_choice("xx") is None
    assert resolve_language_choice("") is None

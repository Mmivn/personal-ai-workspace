"""End-to-end interaction tests for streamlit_app.py via Streamlit's

AppTest — simulates real widget interactions (clicks, form submits,
selectbox changes) without a browser. ai_service.ask_ai is monkeypatched
for every test here, so nothing in this file ever touches the network
or needs OPENAI_API_KEY, regardless of what's in .env.
"""
import pytest
from streamlit.testing.v1 import AppTest

import ai_service

# AppTest.from_file resolves relative paths against *this* file's
# directory (tests/), not the pytest working directory.
APP_PATH = "../streamlit_app.py"

FAKE_REPLY = (
    "Intro sentence about the reading.\n\n"
    "## Характер\n"
    "Body text about character.\n\n"
    "## Сильные стороны\n"
    "Body text about strengths.\n\n"
    "**Совет:**\n"
    "Body text with the advice.\n"
)


@pytest.fixture(autouse=True)
def mock_ai(monkeypatch):
    """Default mock: every ask_ai call succeeds with a canned, structured

    reply, and every translate_text call succeeds with a recognizably
    "translated" derivative of its input — this exercises the real
    card→panel→CTA→cache→reading-card pipeline, and the two-level
    canonical/translation cache, without ever calling OpenAI. Individual
    tests may still monkeypatch ai_service.ask_ai/translate_text again to
    cover error paths; that override just replaces this one for the rest
    of that test.

    Returns a {"ask_ai": n, "translate_text": n} call counter dict — used
    by tests that need to prove a language switch didn't re-invoke the
    main (expensive) assistant, only (at most) the cheap translator.
    """
    calls = {"ask_ai": 0, "translate_text": 0}

    def fake_ask_ai(instructions, message, previous_response_id=None):
        calls["ask_ai"] += 1
        return FAKE_REPLY, "resp_fake"

    def fake_translate_text(text, language):
        calls["translate_text"] += 1
        return f"[{language}] {text}"

    monkeypatch.setattr(ai_service, "ask_ai", fake_ask_ai)
    monkeypatch.setattr(ai_service, "translate_text", fake_translate_text)
    return calls


def _assert_clean(at):
    assert not at.exception, [str(e) for e in at.exception]


def _fresh_app_with_profile(name="Anna", birth_date="20.05.1990"):
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    at.text_input(key="profile_name_input").set_value(name)
    at.text_input(key="profile_birthdate_input").set_value(birth_date)
    # Tests expect AI features to be available; opt-in consent is required
    # in the UI now — simulate the user checking the consent checkbox and
    # let Streamlit process the widget changes before submitting the form.
    at.checkbox(key="profile_form_consent").check()
    at.run()
    at.button(key="cta_profile_form").click().run()
    # Sanity-check: the user's explicit consent should be recorded.
    assert at.session_state["consent_given"] is True
    return at


def test_initial_load_shows_profile_form_without_error():
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    _assert_clean(at)
    assert at.session_state["profile"] is None


def test_profile_form_computes_correct_zodiac_and_life_path():
    at = _fresh_app_with_profile()
    _assert_clean(at)
    profile = at.session_state["profile"]
    assert profile is not None
    assert profile.zodiac_sign == "taurus"
    assert profile.life_path_number == 8


def test_profile_form_rejects_invalid_date_without_crashing():
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    at.text_input(key="profile_name_input").set_value("Anna")
    at.text_input(key="profile_birthdate_input").set_value("31.02.2020")
    at.button(key="cta_profile_form").click().run()
    _assert_clean(at)
    assert at.session_state["profile"] is None
    assert len(at.error) >= 1


def test_profile_form_rejects_empty_name_without_crashing():
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    at.text_input(key="profile_name_input").set_value("")
    at.text_input(key="profile_birthdate_input").set_value("20.05.1990")
    at.button(key="cta_profile_form").click().run()
    _assert_clean(at)
    assert at.session_state["profile"] is None


@pytest.mark.parametrize(
    "action_key", ["my_sign", "today", "month", "year", "compatibility", "ask_ai"]
)
def test_all_zodiac_cards_select_without_error(action_key):
    at = _fresh_app_with_profile()
    at.button(key=f"card_zodiac_action_{action_key}_btn").click().run()
    _assert_clean(at)
    assert at.session_state["zodiac_action"] == action_key


@pytest.mark.parametrize(
    "action_key",
    ["life_path", "today", "month", "year", "full_reading", "compatibility", "ask_ai"],
)
def test_all_numerology_cards_select_without_error(action_key):
    at = _fresh_app_with_profile()
    at.button(key=f"card_numerology_action_{action_key}_btn").click().run()
    _assert_clean(at)
    assert at.session_state["numerology_action"] == action_key


def test_zodiac_my_sign_cta_renders_structured_reading():
    at = _fresh_app_with_profile()
    at.button(key="card_zodiac_action_my_sign_btn").click().run()
    at.button(key="cta_zodiac_my_sign_btn").click().run()
    _assert_clean(at)

    text = "\n".join(md.value for md in at.markdown)
    assert "Характер" in text
    assert "Совет" in text

    # Clicking again should reuse the cache (still no exception, cached
    # note visible) rather than erroring or duplicating content oddly.
    at.button(key="cta_zodiac_my_sign_btn").click().run()
    _assert_clean(at)


def test_numerology_full_reading_cta_works():
    at = _fresh_app_with_profile()
    at.button(key="card_numerology_action_full_reading_btn").click().run()
    at.button(key="cta_numerology_full_reading_btn").click().run()
    _assert_clean(at)
    text = "\n".join(md.value for md in at.markdown)
    assert "Характер" in text


def test_zodiac_compatibility_form_end_to_end():
    at = _fresh_app_with_profile()
    at.button(key="card_zodiac_action_compatibility_btn").click().run()
    at.text_input(key="zodiac_companion_form_name").set_value("Ivan")
    at.text_input(key="zodiac_companion_form_date").set_value("10/10/1998")
    at.button(key="cta_zodiac_companion_form").click().run()
    _assert_clean(at)


def test_numerology_compatibility_form_end_to_end():
    at = _fresh_app_with_profile()
    at.button(key="card_numerology_action_compatibility_btn").click().run()
    at.text_input(key="numerology_companion_form_name").set_value("Ivan")
    at.text_input(key="numerology_companion_form_date").set_value("10/10/1998")
    at.button(key="cta_numerology_companion_form").click().run()
    _assert_clean(at)


def test_compatibility_form_rejects_invalid_date_without_crashing():
    at = _fresh_app_with_profile()
    at.button(key="card_zodiac_action_compatibility_btn").click().run()
    at.text_input(key="zodiac_companion_form_name").set_value("X")
    at.text_input(key="zodiac_companion_form_date").set_value("31.02.2020")
    at.button(key="cta_zodiac_companion_form").click().run()
    _assert_clean(at)
    assert len(at.error) >= 1


def test_ask_ai_form_zodiac_end_to_end():
    at = _fresh_app_with_profile()
    at.button(key="card_zodiac_action_ask_ai_btn").click().run()
    at.text_area(key="zodiac_ask_ai_form_question").set_value("What about love?")
    at.button(key="cta_zodiac_ask_ai_form").click().run()
    _assert_clean(at)


def test_ask_ai_form_rejects_empty_question():
    at = _fresh_app_with_profile()
    at.button(key="card_numerology_action_ask_ai_btn").click().run()
    at.text_area(key="numerology_ask_ai_form_question").set_value("   ")
    at.button(key="cta_numerology_ask_ai_form").click().run()
    _assert_clean(at)
    assert len(at.error) >= 1


@pytest.mark.parametrize(
    "label,code", [("English", "en"), ("Tiếng Việt", "vi"), ("Русский", "ru")]
)
def test_language_switch_updates_state_and_ui(label, code):
    at = _fresh_app_with_profile()
    at.selectbox(key="language_selectbox").set_value(label).run()
    _assert_clean(at)
    assert at.session_state["lang_code"] == code


def test_language_switch_translates_cached_reading_instead_of_regenerating(mock_ai):
    """The two-level cache's whole point: switching UI language must never

    re-run the main (expensive) astrology assistant for a reading already
    generated — only, at most, one cheap translation call per new
    language, cached from then on so revisiting an already-seen language
    is completely free.
    """
    at = _fresh_app_with_profile()
    at.button(key="card_zodiac_action_today_btn").click().run()
    at.button(key="cta_zodiac_today_btn").click().run()
    _assert_clean(at)
    assert mock_ai["ask_ai"] == 1
    assert mock_ai["translate_text"] == 0

    ru_text = "\n".join(md.value for md in at.markdown)
    assert "Intro sentence about the reading." in ru_text
    assert "[English]" not in ru_text and "[Vietnamese]" not in ru_text

    # RU -> EN: one translation call, zero new main-assistant calls.
    # translate_text is called with the English name of the target
    # language (see ui/common.py's _TRANSLATION_LANGUAGE_NAMES), not the
    # UI's own-language label shown in the selectbox ("Tiếng Việt" etc).
    at.selectbox(key="language_selectbox").set_value("English").run()
    _assert_clean(at)
    assert mock_ai["ask_ai"] == 1
    assert mock_ai["translate_text"] == 1
    en_text = "\n".join(md.value for md in at.markdown)
    assert "[English] Intro sentence about the reading." in en_text

    # EN -> VI: one more translation call, still zero new main calls.
    at.selectbox(key="language_selectbox").set_value("Tiếng Việt").run()
    _assert_clean(at)
    assert mock_ai["ask_ai"] == 1
    assert mock_ai["translate_text"] == 2
    vi_text = "\n".join(md.value for md in at.markdown)
    assert "[Vietnamese] Intro sentence about the reading." in vi_text

    # VI -> EN -> RU: every one of these was already cached above, so
    # revisiting them costs nothing further at all.
    at.selectbox(key="language_selectbox").set_value("English").run()
    _assert_clean(at)
    assert mock_ai["ask_ai"] == 1
    assert mock_ai["translate_text"] == 2

    at.selectbox(key="language_selectbox").set_value("Русский").run()
    _assert_clean(at)
    assert mock_ai["ask_ai"] == 1
    assert mock_ai["translate_text"] == 2
    ru_text_again = "\n".join(md.value for md in at.markdown)
    assert "Intro sentence about the reading." in ru_text_again
    assert "[Russian]" not in ru_text_again  # RU is the canonical source, never "translated"


def test_edit_profile_button_returns_to_the_form():
    at = _fresh_app_with_profile()
    at.button(key="edit_profile_button").click().run()
    _assert_clean(at)
    assert at.session_state["show_profile_form"] is True


def test_missing_api_key_shows_friendly_error_not_a_crash(monkeypatch):
    def raise_missing_key(instructions, message, previous_response_id=None):
        raise ai_service.MissingAPIKeyError("no key")

    # Overrides this test's own copy of the autouse mock_ai fixture.
    monkeypatch.setattr(ai_service, "ask_ai", raise_missing_key)

    at = _fresh_app_with_profile()
    at.button(key="card_zodiac_action_my_sign_btn").click().run()
    at.button(key="cta_zodiac_my_sign_btn").click().run()
    _assert_clean(at)
    assert len(at.error) >= 1

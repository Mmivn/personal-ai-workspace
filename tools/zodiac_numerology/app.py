"""Terminal UI for the zodiac/numerology assistant.

This module is the only place in the app that calls input()/print(). All
actual computation lives in calculations/ and models.py, and all AI
calls go through ai_service.py — so a future GUI can reuse everything
below the UI layer without touching it.
"""
import os
from datetime import date

from dotenv import load_dotenv

import ai_service
from calculations.dates import InvalidDateError, parse_birth_date
from calculations.numerology import (
    personal_day_number,
    personal_month_number,
    personal_year_number,
)
from locales import (
    LOCALES,
    invalid_choice_text,
    language_menu_text,
    resolve_language_choice,
)
from models import build_companion_profile, build_user_profile

load_dotenv()

DATE_REASON_TO_ONBOARDING_KEY = {
    "unparseable": "invalid_date",
    "future_date": "date_in_future",
    "too_old": "date_too_old",
}


# --------------------------------------------------------------------------
# Generic input helpers
# --------------------------------------------------------------------------

def prompt_menu(title, items, invalid_choice_message):
    """Print a numbered menu and return the key of the chosen item."""
    print(title)
    for index, (_key, label) in enumerate(items, start=1):
        print(f"{index}. {label}")
    while True:
        raw_choice = input("> ").strip()
        if raw_choice.isdigit():
            position = int(raw_choice)
            if 1 <= position <= len(items):
                return items[position - 1][0]
        print(invalid_choice_message)


def prompt_nonempty(prompt_text, empty_message):
    while True:
        value = input(prompt_text).strip()
        if value:
            return value
        print(empty_message)


def prompt_birth_date(prompt_text, t):
    while True:
        raw = input(prompt_text)
        try:
            return parse_birth_date(raw)
        except InvalidDateError as error:
            key = DATE_REASON_TO_ONBOARDING_KEY.get(error.reason, "invalid_date")
            print(t["onboarding"][key])


def choose_language():
    print(language_menu_text())
    while True:
        raw_choice = input("> ")
        lang_code = resolve_language_choice(raw_choice)
        if lang_code is not None:
            return lang_code
        print(invalid_choice_text())


# --------------------------------------------------------------------------
# Onboarding / profile
# --------------------------------------------------------------------------

def run_onboarding(t, language, is_edit=False):
    print(t["onboarding"]["edit_intro"] if is_edit else t["onboarding"]["intro"])
    name = prompt_nonempty(t["onboarding"]["ask_name"], t["onboarding"]["empty_name"])
    birth_date = prompt_birth_date(t["onboarding"]["ask_birth_date"], t)
    profile = build_user_profile(name, birth_date, language)
    sign_name = t["zodiac"]["sign_names"][profile.zodiac_sign]
    print(
        t["onboarding"]["profile_saved"].format(
            name=profile.name,
            birth_date=profile.birth_date.strftime("%d.%m.%Y"),
            sign=sign_name,
            life_path=profile.life_path_number,
        )
    )
    return profile


def prompt_companion(t):
    """Ask for a second person's name and birth date, return a CompanionProfile."""
    name = prompt_nonempty(
        t["compatibility"]["ask_companion_name"], t["onboarding"]["empty_name"]
    )
    birth_date = prompt_birth_date(t["compatibility"]["ask_companion_birth_date"], t)
    return build_companion_profile(name, birth_date)


# --------------------------------------------------------------------------
# AI call wrapper
# --------------------------------------------------------------------------

def format_facts(pairs):
    return "\n".join(f"{label}: {value}" for label, value in pairs)


def call_ai(t, instructions, message, session):
    """Call the AI and print an already-localized error on failure.

    Returns the response text, or None if something went wrong (the
    error has already been shown to the user).
    """
    print(t["common"]["ai_thinking"])
    try:
        text, response_id = ai_service.ask_ai(
            instructions,
            message,
            previous_response_id=session.get("previous_response_id"),
        )
    except ai_service.MissingAPIKeyError:
        print(t["errors"]["api_key_missing"])
        return None
    except ai_service.EmptyResponseError:
        print(t["errors"]["empty_ai_response"])
        return None
    except ai_service.AIServiceError as error:
        print(t["errors"]["api_error"].format(error=error))
        return None

    session["previous_response_id"] = response_id
    return text


# --------------------------------------------------------------------------
# Zodiac branch
# --------------------------------------------------------------------------

def handle_zodiac_my_sign(profile, t):
    sign_name = t["zodiac"]["sign_names"][profile.zodiac_sign]
    print(t["zodiac"]["my_sign_result"].format(sign=sign_name))


def handle_zodiac_period(profile, t, session, period):
    sign_name = t["zodiac"]["sign_names"][profile.zodiac_sign]
    facts = format_facts(
        [
            ("Name", profile.name),
            ("Birth date", profile.birth_date.isoformat()),
            ("Zodiac sign", sign_name),
            ("Today", date.today().isoformat()),
            ("Requested period", period),
        ]
    )
    message = facts + "\n\n" + t["zodiac"]["requests"][period]
    reply = call_ai(t, t["zodiac"]["instructions"], message, session)
    if reply:
        print(f"\n{reply}")


def handle_zodiac_compatibility(profile, t, session):
    companion = prompt_companion(t)
    sign_name = t["zodiac"]["sign_names"][profile.zodiac_sign]
    companion_sign_name = t["zodiac"]["sign_names"][companion.zodiac_sign]
    facts = format_facts(
        [
            ("Person A name", profile.name),
            ("Person A zodiac sign", sign_name),
            ("Person B name", companion.name),
            ("Person B zodiac sign", companion_sign_name),
        ]
    )
    message = facts + "\n\n" + t["zodiac"]["requests"]["compatibility"]
    reply = call_ai(t, t["zodiac"]["instructions"], message, session)
    if reply:
        print(f"\n{reply}")


def handle_zodiac_ask_ai(profile, t, session):
    question = input(t["zodiac"]["ask_ai_prompt"] + " ").strip()
    if not question:
        print(t["common"]["empty_input"])
        return
    sign_name = t["zodiac"]["sign_names"][profile.zodiac_sign]
    facts = format_facts(
        [
            ("Name", profile.name),
            ("Zodiac sign", sign_name),
        ]
    )
    message = facts + "\n\n" + question
    reply = call_ai(t, t["zodiac"]["instructions"], message, session)
    if reply:
        print(f"\n{reply}")


def zodiac_branch(profile, t, session):
    print(t["zodiac_menu"]["disclaimer"])
    while True:
        action = prompt_menu(
            t["zodiac_menu"]["title"],
            t["zodiac_menu"]["items"],
            t["common"]["invalid_menu_choice"],
        )
        if action == "back":
            return
        if action == "my_sign":
            handle_zodiac_my_sign(profile, t)
        elif action in ("today", "month", "year"):
            handle_zodiac_period(profile, t, session, action)
        elif action == "compatibility":
            handle_zodiac_compatibility(profile, t, session)
        elif action == "ask_ai":
            handle_zodiac_ask_ai(profile, t, session)


# --------------------------------------------------------------------------
# Numerology branch
# --------------------------------------------------------------------------

_PERIOD_FUNCTIONS = {
    "today": personal_day_number,
    "month": personal_month_number,
    "year": personal_year_number,
}


def handle_numerology_life_path(profile, t):
    print(t["numerology"]["life_path_result"].format(number=profile.life_path_number))


def handle_numerology_period(profile, t, session, period):
    number = _PERIOD_FUNCTIONS[period](profile.birth_date)
    print(t["numerology"][f"{period}_result"].format(number=number))

    facts = format_facts(
        [
            ("Name", profile.name),
            ("Birth date", profile.birth_date.isoformat()),
            ("Today", date.today().isoformat()),
            (f"Computed {period} number", number),
        ]
    )
    message = facts + "\n\n" + t["numerology"]["requests"][period]
    reply = call_ai(t, t["numerology"]["instructions"], message, session)
    if reply:
        print(f"\n{reply}")


def handle_numerology_full_reading(profile, t, session):
    today = date.today()
    life_path = profile.life_path_number
    personal_year = personal_year_number(profile.birth_date, today)
    personal_month = personal_month_number(profile.birth_date, today)
    personal_day = personal_day_number(profile.birth_date, today)

    print(t["numerology"]["life_path_result"].format(number=life_path))
    print(t["numerology"]["year_result"].format(number=personal_year))
    print(t["numerology"]["month_result"].format(number=personal_month))
    print(t["numerology"]["today_result"].format(number=personal_day))

    facts = format_facts(
        [
            ("Name", profile.name),
            ("Birth date", profile.birth_date.isoformat()),
            ("Today", today.isoformat()),
            ("Life Path Number", life_path),
            ("Personal Year Number", personal_year),
            ("Personal Month Number", personal_month),
            ("Personal Day Number", personal_day),
        ]
    )
    message = facts + "\n\n" + t["numerology"]["requests"]["full_reading"]
    reply = call_ai(t, t["numerology"]["instructions"], message, session)
    if reply:
        print(f"\n{reply}")


def handle_numerology_compatibility(profile, t, session):
    companion = prompt_companion(t)
    facts = format_facts(
        [
            ("Person A name", profile.name),
            ("Person A Life Path Number", profile.life_path_number),
            ("Person B name", companion.name),
            ("Person B Life Path Number", companion.life_path_number),
        ]
    )
    message = facts + "\n\n" + t["numerology"]["requests"]["compatibility"]
    reply = call_ai(t, t["numerology"]["instructions"], message, session)
    if reply:
        print(f"\n{reply}")


def handle_numerology_ask_ai(profile, t, session):
    question = input(t["numerology"]["ask_ai_prompt"] + " ").strip()
    if not question:
        print(t["common"]["empty_input"])
        return
    facts = format_facts(
        [
            ("Name", profile.name),
            ("Life Path Number", profile.life_path_number),
        ]
    )
    message = facts + "\n\n" + question
    reply = call_ai(t, t["numerology"]["instructions"], message, session)
    if reply:
        print(f"\n{reply}")


def numerology_branch(profile, t, session):
    print(t["numerology_menu"]["disclaimer"])
    while True:
        action = prompt_menu(
            t["numerology_menu"]["title"],
            t["numerology_menu"]["items"],
            t["common"]["invalid_menu_choice"],
        )
        if action == "back":
            return
        if action == "life_path":
            handle_numerology_life_path(profile, t)
        elif action in ("today", "month", "year"):
            handle_numerology_period(profile, t, session, action)
        elif action == "full_reading":
            handle_numerology_full_reading(profile, t, session)
        elif action == "compatibility":
            handle_numerology_compatibility(profile, t, session)
        elif action == "ask_ai":
            handle_numerology_ask_ai(profile, t, session)


# --------------------------------------------------------------------------
# Main loop
# --------------------------------------------------------------------------

def main():
    lang_code = choose_language()
    t = LOCALES[lang_code]
    session = {"previous_response_id": None}

    profile = run_onboarding(t, lang_code)

    while True:
        action = prompt_menu(
            t["main_menu"]["title"],
            t["main_menu"]["items"],
            t["common"]["invalid_menu_choice"],
        )
        if action == "zodiac":
            zodiac_branch(profile, t, session)
        elif action == "numerology":
            numerology_branch(profile, t, session)
        elif action == "change_language":
            lang_code = choose_language()
            t = LOCALES[lang_code]
            profile.language = lang_code
            # Conversation history was built with instructions in the old
            # language; start fresh so the AI doesn't mix languages.
            session["previous_response_id"] = None
        elif action == "edit_profile":
            profile = run_onboarding(t, lang_code, is_edit=True)
        elif action == "exit":
            print(t["common"]["goodbye"])
            return


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n\nBye! / Пока! / Tạm biệt!")
    except Exception as exc:  # last-resort guard against a raw traceback
        print(f"\nUnexpected error, exiting: {exc}")
        if os.getenv("DEBUG"):
            raise

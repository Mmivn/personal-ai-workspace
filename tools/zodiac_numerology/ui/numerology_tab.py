"""Numerology branch of the GUI: life path, forecasts, full reading,

compatibility, free-form AI Qs. Every number shown is computed by
calculations/numerology.py in Python — the AI only ever interprets an
already-final number, and every interpretation is button-gated and
signature-cached via ui.common (see zodiac_tab.py for the same pattern).
Signatures never include the UI language — see that module's docstring.
"""
from datetime import date

import streamlit as st

from calculations.numerology import (
    personal_day_number,
    personal_month_number,
    personal_year_number,
)
from ui import icons
from ui.common import (
    call_ai_cached,
    format_facts,
    get_canonical_entry,
    label_only,
    render_action_grid,
    render_ai_section,
    render_ask_ai_panel,
    render_companion_form,
    render_reading_card,
    serve_existing_reading,
    trigger_scroll_to,
)

_PERIOD_FUNCTIONS = {
    "today": personal_day_number,
    "month": personal_month_number,
    "year": personal_year_number,
}

# Pre-rendered once at import time. today/month/year (sun/moon/star)
# intentionally mirror the zodiac tab's icons, reinforcing the same
# "time cycle" idea in both branches.
_ICONS_20 = {
    "life_path": icons.gem(20),
    "today": icons.sun(20),
    "month": icons.moon(20),
    "year": icons.star(20),
    "full_reading": icons.scroll(20),
    "compatibility": icons.venn(20),
    "ask_ai": icons.chat(20),
}
_ICONS_26 = {
    "life_path": icons.gem(26),
    "today": icons.sun(26),
    "month": icons.moon(26),
    "year": icons.star(26),
    "full_reading": icons.scroll(26),
    "compatibility": icons.venn(26),
    "ask_ai": icons.chat(26),
}

_ANCHOR_ID = "action-panel-numerology"
_SCROLL_FLAG = "scroll_to_numerology_action"


def render_numerology_tab(t, lang_code):
    profile = st.session_state["profile"]
    menu = t["numerology_menu"]

    st.caption(menu["disclaimer"])

    action_items = [item for item in menu["items"] if item[0] != "back"]
    action = render_action_grid(
        "numerology_action", action_items, _ICONS_20, t["gui"]["numerology_card_descriptions"]
    )
    descriptions = t["gui"]["numerology_card_descriptions"]

    st.markdown(f'<div id="{_ANCHOR_ID}"></div>', unsafe_allow_html=True)

    if action == "life_path":
        _render_life_path(t, profile, descriptions)
    elif action in ("today", "month", "year"):
        _render_period(t, profile, action, descriptions)
    elif action == "full_reading":
        _render_full_reading(t, profile, descriptions)
    elif action == "compatibility":
        _render_compatibility(t, profile, descriptions)
    elif action == "ask_ai":
        _render_ask_ai(t, profile, descriptions)

    if st.session_state.pop(_SCROLL_FLAG, False):
        trigger_scroll_to(_ANCHOR_ID)


def _render_life_path(t, profile, descriptions):
    nt = t["numerology"]
    gui = t["gui"]

    title = nt["life_path_result"].format(number=profile.life_path_number)
    facts = format_facts([("Name", profile.name), ("Life Path Number", profile.life_path_number)])
    message = facts + "\n\n" + nt["requests"]["life_path"]
    signature = str(profile.life_path_number)
    render_ai_section(
        t,
        descriptions["life_path"],
        gui["get_interpretation_button"],
        "numerology_life_path_btn",
        "numerology_life_path",
        signature,
        nt["instructions"],
        message,
        icon=_ICONS_26["life_path"],
        title=title,
    )


def _render_period(t, profile, period, descriptions):
    nt = t["numerology"]
    gui = t["gui"]
    today = date.today()

    number = _PERIOD_FUNCTIONS[period](profile.birth_date, today)
    title = nt[f"{period}_result"].format(number=number)

    facts = format_facts(
        [
            ("Name", profile.name),
            ("Birth date", profile.birth_date.isoformat()),
            ("Today", today.isoformat()),
            (f"Computed {period} number", number),
        ]
    )
    message = facts + "\n\n" + nt["requests"][period]
    signature = f"{number}|{period}|{today.isoformat()}"
    render_ai_section(
        t,
        descriptions[period],
        gui["get_forecast_button"],
        f"numerology_{period}_btn",
        f"numerology_{period}",
        signature,
        nt["instructions"],
        message,
        icon=_ICONS_26[period],
        title=title,
        subtitle=f"{today:%d.%m.%Y}",
    )


def _render_full_reading(t, profile, descriptions):
    nt = t["numerology"]
    gui = t["gui"]
    today = date.today()

    life_path = profile.life_path_number
    personal_year = personal_year_number(profile.birth_date, today)
    personal_month = personal_month_number(profile.birth_date, today)
    personal_day = personal_day_number(profile.birth_date, today)

    cols = st.columns(4)
    cols[0].metric(label_only(nt["life_path_result"]), life_path)
    cols[1].metric(label_only(nt["year_result"]), personal_year)
    cols[2].metric(label_only(nt["month_result"]), personal_month)
    cols[3].metric(label_only(nt["today_result"]), personal_day)

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
    message = facts + "\n\n" + nt["requests"]["full_reading"]
    signature = (
        f"{life_path}|{personal_year}|{personal_month}|{personal_day}"
        f"|{today.isoformat()}"
    )
    render_ai_section(
        t,
        descriptions["full_reading"],
        gui["get_full_reading_button"],
        "numerology_full_reading_btn",
        "numerology_full_reading",
        signature,
        nt["instructions"],
        message,
        icon=_ICONS_26["full_reading"],
        title=dict(t["numerology_menu"]["items"])["full_reading"],
    )


def _render_compatibility(t, profile, descriptions):
    nt = t["numerology"]
    gui = t["gui"]
    lang_code = st.session_state["lang_code"]
    cache_key = "numerology_compatibility"
    title = dict(t["numerology_menu"]["items"])["compatibility"]

    # See zodiac_tab.py's _render_compatibility for why this is tracked
    # separately from the full signature, and why language isn't in it.
    primary_fingerprint = str(profile.life_path_number)
    last_signature_key = f"{cache_key}_last_signature"

    companion = render_companion_form(
        t,
        "numerology_companion_form",
        icon=_ICONS_26["compatibility"],
        description=descriptions["compatibility"],
    )
    if companion is None:
        last_signature = st.session_state.get(last_signature_key)
        entry = get_canonical_entry(cache_key, last_signature) if last_signature else None
        if entry and entry.get("primary_fingerprint") == primary_fingerprint:
            text = serve_existing_reading(t, cache_key, last_signature, lang_code)
            if text:
                render_reading_card(cache_key, _ICONS_26["compatibility"], title, text)
        return

    st.info(f"{gui['profile_labels']['life_path']}: {companion.life_path_number}")

    facts = format_facts(
        [
            ("Person A name", profile.name),
            ("Person A Life Path Number", profile.life_path_number),
            ("Person B name", companion.name),
            ("Person B Life Path Number", companion.life_path_number),
        ]
    )
    message = facts + "\n\n" + nt["requests"]["compatibility"]
    signature = f"{primary_fingerprint}|{companion.life_path_number}|{companion.name}"

    text = call_ai_cached(
        t, cache_key, signature, lang_code, nt["instructions"], message,
        extra={"primary_fingerprint": primary_fingerprint},
    )
    if text:
        st.session_state[last_signature_key] = signature
        render_reading_card(cache_key, _ICONS_26["compatibility"], title, text)


def _render_ask_ai(t, profile, descriptions):
    nt = t["numerology"]
    gui = t["gui"]
    title = dict(t["numerology_menu"]["items"])["ask_ai"]

    facts = format_facts([("Name", profile.name), ("Life Path Number", profile.life_path_number)])
    render_ask_ai_panel(
        t,
        _ICONS_26["ask_ai"],
        title,
        descriptions["ask_ai"],
        nt["ask_ai_prompt"],
        gui["ask_button"],
        nt["instructions"],
        facts,
        "numerology_ask_ai_form",
        signature_key=str(profile.life_path_number),
    )

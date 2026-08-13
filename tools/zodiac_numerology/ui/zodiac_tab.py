"""Zodiac branch of the GUI: sign, forecasts, compatibility, free-form AI Qs.

All AI calls go through ui.common.render_ai_section / call_ai_cached, so
every request here is button-gated and signature-cached — no automatic
API calls just from switching actions or Streamlit reruns. Signatures
never include the UI language: the main assistant runs once per
signature (whatever language happens to be active at that moment becomes
its source language), and every other language is a cheap *translation*
of that one canonical result — see ui/common.py's call_ai_cached.
"""
from datetime import date

import streamlit as st

from ui import icons
from ui.common import (
    call_ai_cached,
    format_facts,
    get_canonical_entry,
    render_action_grid,
    render_ai_section,
    render_ask_ai_panel,
    render_companion_form,
    render_reading_card,
    serve_existing_reading,
    trigger_scroll_to,
)

# Pre-rendered once at import time — cheap, and keeps call sites simple.
_ICONS_20 = {
    "my_sign": icons.gem(20),
    "today": icons.sun(20),
    "month": icons.moon(20),
    "year": icons.star(20),
    "compatibility": icons.venn(20),
    "ask_ai": icons.chat(20),
}
_ICONS_26 = {key: fn(26) for key, fn in (
    ("my_sign", icons.gem),
    ("today", icons.sun),
    ("month", icons.moon),
    ("year", icons.star),
    ("compatibility", icons.venn),
    ("ask_ai", icons.chat),
)}

_ANCHOR_ID = "action-panel-zodiac"
_SCROLL_FLAG = "scroll_to_zodiac_action"


def render_zodiac_tab(t, lang_code):
    profile = st.session_state["profile"]
    menu = t["zodiac_menu"]

    st.caption(menu["disclaimer"])

    action_items = [item for item in menu["items"] if item[0] != "back"]
    action = render_action_grid(
        "zodiac_action", action_items, _ICONS_20, t["gui"]["zodiac_card_descriptions"]
    )
    sign_name = t["zodiac"]["sign_names"][profile.zodiac_sign]
    descriptions = t["gui"]["zodiac_card_descriptions"]

    st.markdown(f'<div id="{_ANCHOR_ID}"></div>', unsafe_allow_html=True)

    if action == "my_sign":
        _render_my_sign(t, profile, sign_name, descriptions)
    elif action in ("today", "month", "year"):
        _render_period(t, profile, sign_name, action, descriptions)
    elif action == "compatibility":
        _render_compatibility(t, profile, sign_name, descriptions)
    elif action == "ask_ai":
        _render_ask_ai(t, profile, sign_name, descriptions)

    if st.session_state.pop(_SCROLL_FLAG, False):
        trigger_scroll_to(_ANCHOR_ID)


def _render_my_sign(t, profile, sign_name, descriptions):
    zt = t["zodiac"]

    title = zt["my_sign_result"].format(sign=sign_name)
    reading_title = zt["my_sign_reading_title"].format(sign=sign_name)

    facts = format_facts([("Name", profile.name), ("Zodiac sign", sign_name)])
    message = facts + "\n\n" + zt["requests"]["my_sign"]
    signature = profile.zodiac_sign
    render_ai_section(
        t,
        descriptions["my_sign"],
        zt["my_sign_cta"],
        "zodiac_my_sign_btn",
        "zodiac_my_sign",
        signature,
        zt["instructions"],
        message,
        icon=_ICONS_26["my_sign"],
        title=title,
        reading_title=reading_title,
    )


def _render_period(t, profile, sign_name, period, descriptions):
    zt = t["zodiac"]
    gui = t["gui"]
    today = date.today()

    period_label = dict(t["zodiac_menu"]["items"])[period]

    facts = format_facts(
        [
            ("Name", profile.name),
            ("Birth date", profile.birth_date.isoformat()),
            ("Zodiac sign", sign_name),
            ("Today", today.isoformat()),
            ("Requested period", period),
        ]
    )
    message = facts + "\n\n" + zt["requests"][period]
    signature = f"{profile.zodiac_sign}|{period}|{today.isoformat()}"
    render_ai_section(
        t,
        descriptions[period],
        gui["get_forecast_button"],
        f"zodiac_{period}_btn",
        f"zodiac_{period}",
        signature,
        zt["instructions"],
        message,
        icon=_ICONS_26[period],
        title=period_label,
        subtitle=f"{sign_name} · {today:%d.%m.%Y}",
    )


def _render_compatibility(t, profile, sign_name, descriptions):
    zt = t["zodiac"]
    gui = t["gui"]
    lang_code = st.session_state["lang_code"]
    cache_key = "zodiac_compatibility"
    title = dict(t["zodiac_menu"]["items"])["compatibility"]

    # Identifies the *primary* side (this profile) regardless of whether
    # the companion form was resubmitted this run — stored alongside the
    # cached result so a revisit that hasn't resubmitted the companion
    # can still tell whether it's safe to keep showing it (e.g. after
    # editing the profile to a different sign, this won't match, and the
    # stale reading correctly stays hidden instead of leaking). Language
    # is deliberately not part of this — see call_ai_cached's `extra`.
    primary_fingerprint = profile.zodiac_sign
    last_signature_key = f"{cache_key}_last_signature"

    companion = render_companion_form(
        t,
        "zodiac_companion_form",
        icon=_ICONS_26["compatibility"],
        description=descriptions["compatibility"],
    )
    if companion is None:
        # Not submitted this run — keep showing the last analysis, if any,
        # instead of silently discarding it. serve_existing_reading may
        # still translate it (never regenerate) if this is the first
        # visit to this signature in the current UI language.
        last_signature = st.session_state.get(last_signature_key)
        entry = get_canonical_entry(cache_key, last_signature) if last_signature else None
        if entry and entry.get("primary_fingerprint") == primary_fingerprint:
            text = serve_existing_reading(t, cache_key, last_signature, lang_code)
            if text:
                render_reading_card(cache_key, _ICONS_26["compatibility"], title, text)
        return

    companion_sign_name = zt["sign_names"][companion.zodiac_sign]
    st.info(f"{gui['profile_labels']['zodiac_sign']}: {companion_sign_name}")

    facts = format_facts(
        [
            ("Person A name", profile.name),
            ("Person A zodiac sign", sign_name),
            ("Person B name", companion.name),
            ("Person B zodiac sign", companion_sign_name),
        ]
    )
    message = facts + "\n\n" + zt["requests"]["compatibility"]
    signature = f"{primary_fingerprint}|{companion.zodiac_sign}|{companion.name}"

    text = call_ai_cached(
        t, cache_key, signature, lang_code, zt["instructions"], message,
        extra={"primary_fingerprint": primary_fingerprint},
    )
    if text:
        st.session_state[last_signature_key] = signature
        render_reading_card(cache_key, _ICONS_26["compatibility"], title, text)


def _render_ask_ai(t, profile, sign_name, descriptions):
    zt = t["zodiac"]
    gui = t["gui"]
    title = dict(t["zodiac_menu"]["items"])["ask_ai"]

    facts = format_facts([("Name", profile.name), ("Zodiac sign", sign_name)])
    render_ask_ai_panel(
        t,
        _ICONS_26["ask_ai"],
        title,
        descriptions["ask_ai"],
        zt["ask_ai_prompt"],
        gui["ask_button"],
        zt["instructions"],
        facts,
        "zodiac_ask_ai_form",
        signature_key=profile.zodiac_sign,
    )

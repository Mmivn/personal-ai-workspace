"""Streamlit GUI for the zodiac/numerology assistant.

Run with:
    streamlit run streamlit_app.py

This module only handles page layout and session flow. All computation
lives in calculations/ and models.py, and all AI calls go through
ai_service.py — exactly like the terminal app.py. The two front ends
share every layer below the UI, so nothing about the calculations or
the AI wrapper is duplicated here. Colors/fonts/widget theming live in
.streamlit/config.toml; ui/styles.py adds only what that can't do
(starfield, hero, card grid, reading card); ui/icons.py supplies every
icon as inline SVG (no Unicode-glyph font dependency).
"""
import streamlit as st
from dotenv import load_dotenv

from locales import LOCALES
from ui.common import (
    ensure_session_defaults,
    render_hero,
    render_language_switcher,
    render_onboarding_intro,
    render_profile_form,
)
from ui.numerology_tab import render_numerology_tab
from ui.styles import inject_css
from ui.zodiac_tab import render_zodiac_tab

load_dotenv()

st.set_page_config(
    page_title="Zodiac & Numerology AI Assistant",
    page_icon="✨",
    layout="centered",
)


def main():
    ensure_session_defaults()
    inject_css()

    title_col, lang_col = st.columns([3, 1])
    with lang_col:
        lang_code = render_language_switcher()
    t = LOCALES[lang_code]

    with title_col:
        st.markdown(
            f"<div class='app-title'>{t['gui']['app_title']}</div>", unsafe_allow_html=True
        )

    profile = st.session_state["profile"]
    show_form = st.session_state["show_profile_form"]

    if profile is None or show_form:
        # Full onboarding screen: value-prop copy (left) + compact form
        # (right) — not a small form floating alone in empty space.
        intro_col, form_col = st.columns([6, 5], gap="large")
        with intro_col:
            render_onboarding_intro(t)
        with form_col:
            render_profile_form(t)
        return

    render_hero(t)

    zodiac_label = dict(t["main_menu"]["items"])["zodiac"]
    numerology_label = dict(t["main_menu"]["items"])["numerology"]
    tab_zodiac, tab_numerology = st.tabs([zodiac_label, numerology_label])

    with tab_zodiac:
        render_zodiac_tab(t, lang_code)
    with tab_numerology:
        render_numerology_tab(t, lang_code)


main()

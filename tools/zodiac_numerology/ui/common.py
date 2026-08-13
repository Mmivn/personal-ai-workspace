"""Shared Streamlit UI helpers.

Session-state setup, the onboarding screen (value-prop copy + form),
the compact hero, the second-person ("companion") form, the feature-card
action grid, the AI "reading card", and a cached wrapper around
ai_service that also owns the spinner and localized error messages.
calculations/, models.py and ai_service.py stay exactly as the terminal
app.py uses them — this module only adapts them to Streamlit widgets
and visuals. All icons here are inline SVG from ui/icons.py, never
Unicode symbol glyphs — see that module's docstring for why.
"""
import html
import re
from datetime import date

import streamlit as st

import ai_service
from calculations.dates import InvalidDateError, parse_birth_date
from locales import LANGUAGE_CHOICES, LOCALES
from models import build_companion_profile, build_user_profile
from ui import icons
from ui.styles import active_card_glow_css, wide_card_css

DATE_REASON_TO_ONBOARDING_KEY = {
    "unparseable": "invalid_date",
    "future_date": "date_in_future",
    "too_old": "date_too_old",
}


# --------------------------------------------------------------------------
# Session state
# --------------------------------------------------------------------------

# Query-param keys used to survive a full page reload. st.session_state is
# per-websocket-session and a browser refresh (F5) opens a brand new one —
# without this, a reload silently threw away the saved profile and
# language and dropped the user back at onboarding. The URL is the only
# state Streamlit gives us that a reload doesn't reset.
_QP_NAME = "name"
_QP_BIRTH_DATE = "bdate"
_QP_LANG = "lang"


def _persist_profile_to_url(profile):
    # Do not persist PII (name / birth date) into the URL.
    # Persist only language to preserve language-on-reload behavior.
    _persist_lang_to_url(profile.language)


def _persist_lang_to_url(lang_code):
    st.query_params[_QP_LANG] = lang_code


def _restore_profile_from_url():
    """Rebuild (profile, lang_code) from the URL's query params.

    Returns (None, lang_code_or_None) if there's no usable saved profile
    in the URL — the lang code alone may still be present and honored
    even before a profile exists (e.g. mid-onboarding reload).
    """
    qp = st.query_params
    lang_code = qp.get(_QP_LANG)
    lang_code = lang_code if lang_code in LOCALES else None

    name = qp.get(_QP_NAME)
    birth_date_raw = qp.get(_QP_BIRTH_DATE)
    if not name or not birth_date_raw:
        return None, lang_code
    try:
        birth_date = date.fromisoformat(birth_date_raw)
    except ValueError:
        return None, lang_code

    profile = build_user_profile(name, birth_date, lang_code or "ru")
    return profile, (lang_code or "ru")


def ensure_session_defaults():
    st.session_state.setdefault("lang_code", "ru")
    st.session_state.setdefault("profile", None)
    st.session_state.setdefault("show_profile_form", True)
    st.session_state.setdefault("ai_previous_response_id", None)
    st.session_state.setdefault("ai_cache", {})
    # Consent for sending profile facts (name, birth date) to third-party AI.
    # Default to False (opt-in) to require explicit user consent. Use an
    # explicit existence check to avoid surprising behavior with widget-
    # backed keys in some test runtimes.
    if "consent_given" not in st.session_state:
        st.session_state["consent_given"] = False

    # Only relevant on the very first run of a session (fresh tab or
    # reload): once a profile exists in session_state, later reruns
    # within the same session leave it alone.
    if st.session_state["profile"] is None:
        restored_profile, restored_lang = _restore_profile_from_url()
        if restored_profile is not None:
            st.session_state["profile"] = restored_profile
            st.session_state["show_profile_form"] = False
        if restored_lang is not None:
            st.session_state["lang_code"] = restored_lang


def format_facts(pairs):
    return "\n".join(f"{label}: {value}" for label, value in pairs)


def label_only(template):
    """Pull the "Label" part out of a "Label: {number}" locale template."""
    return template.split(":")[0].strip()


# --------------------------------------------------------------------------
# Language switcher
# --------------------------------------------------------------------------

def _set_language(lang_code):
    if st.session_state.get("lang_code") == lang_code:
        return
    st.session_state["lang_code"] = lang_code
    # The multi-turn conversation thread (previous_response_id) was built
    # with instructions in the old language, so it's no longer valid —
    # but the *cache* is deliberately left alone: every cache signature
    # already includes lang_code (see zodiac_tab.py/numerology_tab.py),
    # so a switch to a language visited before will find its own matching
    # entry and show it instantly, and a switch to a new language simply
    # won't match anything yet (forcing one fresh generation) — without
    # throwing away results for languages the user isn't currently on.
    st.session_state["ai_previous_response_id"] = None
    if st.session_state.get("profile") is not None:
        st.session_state["profile"].language = lang_code
        _persist_profile_to_url(st.session_state["profile"])
    else:
        _persist_lang_to_url(lang_code)


def render_language_switcher():
    codes = [code for _, code in LANGUAGE_CHOICES]
    labels = [LOCALES[code]["language_name"] for code in codes]
    current = st.session_state.get("lang_code", "ru")
    index = codes.index(current) if current in codes else 0

    selected_label = st.selectbox(
        LOCALES[current]["gui"]["language_label"],
        labels,
        index=index,
        key="language_selectbox",
        label_visibility="collapsed",
    )
    selected_code = codes[labels.index(selected_label)]
    _set_language(selected_code)
    return selected_code


# --------------------------------------------------------------------------
# Onboarding: value-prop copy (left) + form (right) — see streamlit_app.py
# for how the two columns are laid out.
# --------------------------------------------------------------------------

def render_onboarding_intro(t):
    """The marketing/value-prop half of the onboarding screen."""
    gui = t["gui"]
    points = gui["onboarding_points"]
    point_icons = (icons.gem(18), icons.scroll(18), icons.spark(18))

    points_html = "".join(
        f'<div class="onboarding-point">{icon}<span>{html.escape(point)}</span></div>'
        for icon, point in zip(point_icons, points)
    )

    st.markdown(
        f"""
        <div class="onboarding-copy">
            <div class="onboarding-eyebrow">{html.escape(gui['app_title'])}</div>
            <div class="onboarding-title">{html.escape(gui['onboarding_title'])}</div>
            <div class="onboarding-lede">{html.escape(gui['hero_value_prop'])}</div>
            <div class="onboarding-points">{points_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_profile_form(t):
    """The compact onboarding form itself (name, birth date, CTA)."""
    gui = t["gui"]
    onboarding = t["onboarding"]

    existing = st.session_state.get("profile")
    if existing is not None and "profile_name_input" not in st.session_state:
        st.session_state["profile_name_input"] = existing.name
        st.session_state["profile_birthdate_input"] = existing.birth_date.strftime("%d.%m.%Y")

    with st.container(border=True, key="onboarding_form"):
        st.markdown(
            f'<div class="panel-icon">{icons.gem(26)}</div>'
            f'<div class="panel-title">{html.escape(gui["profile_section_title"])}</div>',
            unsafe_allow_html=True,
        )
        with st.form("profile_form"):
            name = st.text_input(onboarding["ask_name"], key="profile_name_input")
            birth_date_raw = st.text_input(
                onboarding["ask_birth_date"], key="profile_birthdate_input"
            )
            # Consent checkbox for sending profile facts to the AI.
            # Use a form-scoped widget key so we can persist the user's
            # explicit choice into the canonical `consent_given` session
            # key after the form is submitted without colliding with a
            # widget-backed key.
            consent = st.checkbox(
                gui.get("consent_label", ""),
                value=st.session_state.get("consent_given", False),
                key="profile_form_consent",
            )
            submitted = st.form_submit_button(
                gui["save_button"], key="cta_profile_form", use_container_width=True, type="primary"
            )
        st.caption(gui["onboarding_hint"])

    if not submitted:
        return

    name = name.strip()
    if not name:
        st.error(onboarding["empty_name"])
        return
    try:
        birth_date = parse_birth_date(birth_date_raw)
    except InvalidDateError as error:
        key = DATE_REASON_TO_ONBOARDING_KEY.get(error.reason, "invalid_date")
        st.error(onboarding[key])
        return

    lang_code = st.session_state.get("lang_code", "ru")

    # No manual cache wipe here, on purpose. Every AI cache signature
    # already includes the zodiac sign / life path number derived from
    # birth_date (see zodiac_tab.py / numerology_tab.py) — so an edit
    # that doesn't actually change birth_date (a name fix, re-saving
    # unchanged) leaves every existing signature matching, and readings
    # keep showing without a wasted API call; an edit that *does* change
    # birth_date changes the derived sign/number, so exactly (and only)
    # the readings that depend on it stop matching and regenerate on
    # next visit — nothing has to be cleared by hand either way. Only
    # the multi-turn conversation thread is reset, and only when the
    # birth date actually changed (a different person's chart shouldn't
    # continue the same AI conversation).
    birth_date_changed = existing is None or existing.birth_date != birth_date

    profile = build_user_profile(name, birth_date, lang_code)
    st.session_state["profile"] = profile
    # Persist the user's explicit consent choice into the canonical
    # `consent_given` session key so downstream AI calls reliably see
    # the user's decision. The checkbox widget uses the separate
    # `profile_form_consent` key to avoid widget-backed assignment
    # conflicts; here we copy that value into the shared key.
    st.session_state["consent_given"] = st.session_state.get(
        "profile_form_consent", False
    )
    st.session_state["show_profile_form"] = False
    if birth_date_changed:
        st.session_state["ai_previous_response_id"] = None
    _persist_profile_to_url(profile)
    st.rerun()


def render_hero(t):
    """Compact personal hero: a sign badge + greeting/value-prop/stats row.

    The badge shows the sign's *name* (plain text, gradient-filled) inside
    a thin ring — deliberately not a special Unicode astrology glyph,
    which can render as an empty box on systems whose fonts don't cover
    that block (that was the "empty square" the previous pass shipped).
    """
    profile = st.session_state.get("profile")
    if profile is None:
        return

    gui = t["gui"]
    sign_name = t["zodiac"]["sign_names"][profile.zodiac_sign]
    safe_name = html.escape(profile.name)

    st.markdown(
        f"""
        <div class="hero">
            <div class="hero-constellation-bg">{icons.hero_constellation(150)}</div>
            <div class="hero-main">
                <div class="hero-badge">
                    <div class="hero-badge-ring"></div>
                    <div class="hero-badge-fill"></div>
                    <div class="hero-badge-text">{html.escape(sign_name)}</div>
                </div>
                <div class="hero-text">
                    <div class="hero-greeting">{gui['hero_greeting'].format(name=safe_name)}</div>
                    <div class="hero-value-prop">{html.escape(gui['hero_value_prop'])}</div>
                    <div class="hero-stats-row">
                        <div class="hero-stat">
                            <span class="hero-stat-label">{html.escape(gui['profile_labels']['birth_date'])}</span>
                            <span class="hero-stat-value">{profile.birth_date.strftime('%d.%m.%Y')}</span>
                        </div>
                        <div class="hero-stat-sep"></div>
                        <div class="hero-stat">
                            <span class="hero-stat-label">{html.escape(gui['profile_labels']['life_path'])}</span>
                            <span class="hero-stat-value">{profile.life_path_number}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    edit_label = dict(t["main_menu"]["items"])["edit_profile"]
    if st.button(edit_label, key="edit_profile_button"):
        st.session_state["show_profile_form"] = True
        st.rerun()


# --------------------------------------------------------------------------
# Companion (second person) form, shared by both branches' compatibility
# --------------------------------------------------------------------------

def render_companion_form(t, form_key, icon=None, description=""):
    """Ask for a second person's name + birth date, in the same big

    premium-panel style as the other actions.

    Returns a CompanionProfile the run the form is submitted successfully,
    else None (validation errors are shown inline via st.error).
    """
    compat = t["compatibility"]
    onboarding = t["onboarding"]
    gui = t["gui"]
    icon = icon or icons.venn(26)

    with st.container(border=True, key=f"panel_{form_key}"):
        st.markdown(
            f'<div class="panel-icon">{icon}</div>'
            f'<div class="panel-title">{html.escape(gui["companion_section_title"])}</div>'
            f'<div class="panel-desc">{html.escape(description)}</div>',
            unsafe_allow_html=True,
        )
        with st.form(form_key):
            name = st.text_input(compat["ask_companion_name"], key=f"{form_key}_name")
            birth_date_raw = st.text_input(
                compat["ask_companion_birth_date"], key=f"{form_key}_date"
            )
            submitted = st.form_submit_button(
                gui["get_compatibility_button"],
                key=f"cta_{form_key}",
                use_container_width=True,
                type="primary",
            )

    if not submitted:
        return None

    name = name.strip()
    if not name:
        st.error(onboarding["empty_name"])
        return None
    try:
        birth_date = parse_birth_date(birth_date_raw)
    except InvalidDateError as error:
        key = DATE_REASON_TO_ONBOARDING_KEY.get(error.reason, "invalid_date")
        st.error(onboarding[key])
        return None

    return build_companion_profile(name, birth_date)


# --------------------------------------------------------------------------
# Feature-card action grid (replaces the old small radio-button selector)
# --------------------------------------------------------------------------

def render_action_grid(state_key, items, icon_svgs, descriptions, columns=3):
    """A responsive grid of compact selectable cards (icon, title, blurb).

    items: list of (action_key, label) tuples — same shape as the CLI's
    menu items, minus "back". icon_svgs: {action_key: svg_markup_string}
    (see ui/icons.py — pre-render at the desired size at the call site).
    Cards reflow via CSS Grid (3 columns on desktop, 2 on tablet, 1 on
    mobile — see ui/styles.py) instead of a fixed st.columns() row, so
    this one Python loop works at every screen size. If the item count
    doesn't divide evenly by `columns`, the trailing card spans the full
    row width instead of being left as an orphaned single square.

    Selection is kept in st.session_state[state_key] and persists
    across reruns; picking a card is a plain widget interaction, it
    never triggers an AI call by itself. Returns the currently selected
    action_key.

    Each card's click target is the whole card, not a small button
    inside it — see the CSS comment in ui/styles.py above
    "div[class*='st-key-card_']" for exactly how (a real, in-flow
    button stretched via flex-grow, with the decorative content layered
    on top via pointer-events:none so clicks always reach the button).
    """
    valid_keys = {key for key, _label in items}
    if st.session_state.get(state_key) not in valid_keys:
        st.session_state[state_key] = items[0][0]
    current = st.session_state[state_key]

    remainder = len(items) % columns
    wide_index = len(items) - 1 if remainder and len(items) > columns else None

    # Per-card override CSS (the active glow, the trailing wide card) is
    # collected here and emitted as ONE st.markdown call *before* the grid
    # container, not interleaved between cards inside it. Streamlit gives
    # every st.markdown/st.container call its own DOM node, and the grid
    # container is `display:grid` — so a style-only node emitted *inside*
    # it became a real (invisible) grid cell, shoved in front of whichever
    # card was active. That silently shifted every card *after* the active
    # one into the next grid slot, and which cards moved depended on which
    # one was selected — the previous card-position-jumping bug. Keeping
    # the grid's children to exactly the N card containers, always, makes
    # the layout independent of selection.
    overrides = []
    for index, (action_key, _label) in enumerate(items):
        card_key = f"card_{state_key}_{action_key}"
        if current == action_key:
            overrides.append(active_card_glow_css(card_key))
        if index == wide_index:
            overrides.append(wide_card_css(card_key))
    if overrides:
        st.markdown("".join(overrides), unsafe_allow_html=True)

    with st.container(key=f"grid_{state_key}"):
        for index, (action_key, label) in enumerate(items):
            card_key = f"card_{state_key}_{action_key}"
            is_active = current == action_key
            with st.container(border=True, key=card_key):
                # Rendered first: the real, in-flow button — CSS
                # stretches it to fill the whole card via flex-grow
                # and makes it invisible (opacity:0). This is the
                # actual click target for the entire card.
                clicked = st.button(
                    label,
                    key=f"{card_key}_btn",
                    use_container_width=True,
                    type="primary" if is_active else "secondary",
                )
                # Rendered second: purely decorative, absolutely
                # positioned on top with pointer-events:none, so
                # clicks always fall through to the button above.
                icon_svg = icon_svgs.get(action_key, icons.spark(20))
                st.markdown(
                    '<div class="feature-content">'
                    f'<div class="feature-icon">{icon_svg}</div>'
                    f'<div class="feature-title">{html.escape(label)}</div>'
                    f'<div class="feature-desc">{html.escape(descriptions.get(action_key, ""))}</div>'
                    "</div>",
                    unsafe_allow_html=True,
                )
                if clicked and not is_active:
                    st.session_state[state_key] = action_key
                    st.session_state[f"scroll_to_{state_key}"] = True
                    st.rerun()

    return st.session_state[state_key]


def trigger_scroll_to(anchor_id):
    """Best-effort smooth scroll to an anchor element after a card click.

    st.html(unsafe_allow_javascript=True) inserts this directly into the
    main page (not iframed), so a plain document.getElementById reaches
    the anchor with no window.parent trickery. Still inherently a small
    hack: if it ever does nothing, nothing else in the app depends on it.
    """
    st.html(
        f"""
        <script>
        setTimeout(function() {{
            try {{
                const el = document.getElementById("{anchor_id}");
                if (el) {{ el.scrollIntoView({{behavior: "smooth", block: "start"}}); }}
            }} catch (e) {{}}
        }}, 80);
        </script>
        """,
        unsafe_allow_javascript=True,
    )


# --------------------------------------------------------------------------
# AI calls: spinner, localized errors, cost-control caching, reading card
# --------------------------------------------------------------------------

_TRANSLATION_LANGUAGE_NAMES = {"ru": "Russian", "en": "English", "vi": "Vietnamese"}


def _cache_bucket(cache_key):
    """The dict of {signature: entry} for one action, created on first use.

    Keyed by (cache_key, signature) rather than by cache_key alone — a
    single-slot-per-cache_key design would let a fresh signature (a
    different companion, a new day) silently overwrite and lose the
    previous signature's already-generated result. Keeping one slot per
    signature means every distinct input combination the user has
    actually generated stays cached side by side for the rest of the
    session.

    Signatures never include the UI language — see call_ai_cached and
    serve_existing_reading for how one canonical result is generated
    once per signature and then only ever *translated*, never
    regenerated, for the other two languages.
    """
    return st.session_state["ai_cache"].setdefault(cache_key, {})


def has_canonical_reading(cache_key, signature):
    """True if the main AI assistant has ever run for this exact signature

    (in any language) — regardless of whether the *current* UI language
    has been translated yet. Callers use this to decide whether a plain
    page revisit (no fresh click) is allowed to proceed to
    call_ai_cached: it may translate an existing reading, but it must
    never trigger the first, expensive generation on its own.
    """
    return _cache_bucket(cache_key).get(signature) is not None


def get_canonical_entry(cache_key, signature):
    """The raw cache entry for (cache_key, signature), or None.

    For callers that need entry metadata beyond the reading text itself
    — e.g. compatibility panels checking a stored "primary_fingerprint"
    before trusting a revisit's last-used signature (see
    zodiac_tab.py/numerology_tab.py's _render_compatibility).
    """
    return _cache_bucket(cache_key).get(signature)


def _translate_and_store(t, entry, lang_code):
    """Turn an existing canonical entry into a reading in `lang_code`.

    Never calls the main AI assistant — only ai_service.translate_text,
    on the cheaper TRANSLATE_MODEL, over the text already stored under
    the entry's source language. The result is cached back onto the
    entry so this exact (signature, lang_code) pair is never translated
    twice in the same session.
    """
    source_text = entry["by_lang"][entry["source_lang"]]
    language_name = _TRANSLATION_LANGUAGE_NAMES.get(lang_code, lang_code)
    with st.spinner(t["common"].get("ai_translating", t["common"]["ai_thinking"])):
        try:
            translated = ai_service.translate_text(source_text, language_name)
        except ai_service.MissingAPIKeyError:
            st.error(t["errors"]["api_key_missing"])
            return None
        except ai_service.EmptyResponseError:
            st.error(t["errors"]["empty_ai_response"])
            return None
        except ai_service.AIServiceError as error:
            st.error(t["errors"]["api_error"].format(error=error))
            return None

    entry["by_lang"][lang_code] = translated
    return translated


def serve_existing_reading(t, cache_key, signature, lang_code):
    """Show a reading that has already been generated at least once —

    instantly if `lang_code` is already cached for it, otherwise by
    *translating* (never regenerating) the entry's original-language
    text. Returns None, without any API call, if nothing has ever been
    generated for this signature — callers must not invoke this from a
    plain revisit in that case (there'd be nothing to translate).
    """
    entry = _cache_bucket(cache_key).get(signature)
    if entry is None:
        return None
    if lang_code in entry["by_lang"]:
        st.caption(t["gui"]["cached_note"])
        return entry["by_lang"][lang_code]
    return _translate_and_store(t, entry, lang_code)


def call_ai_cached(t, cache_key, signature, lang_code, instructions, message, extra=None):
    """Return reading text for (cache_key, signature) in `lang_code`.

    Two-level cache, cost-control guard for both levels:
    - If a canonical result already exists for this signature (in *any*
      language), the main AI assistant is never called again for it —
      this call either returns the already-cached `lang_code` version,
      or produces one by translating the canonical text (see
      serve_existing_reading). Switching UI language therefore never
      re-runs the astrology/numerology assistant, only (at most) a
      cheap translation pass, done once per language and cached.
    - Only when *no* canonical result exists yet for this signature does
      this call reach the main, expensive `ai_service.ask_ai` — and
      whatever language is active at that moment becomes the entry's
      permanent source language for every future translation.

    `signature` must not encode the UI language — language lives only
    in the per-entry `by_lang` cache, never in the signature that
    identifies *which underlying reading* this is.

    `extra`, if given, is merged into the stored entry once, at creation
    — e.g. compatibility panels store a "primary_fingerprint" there so a
    revisit with the companion form not (yet) re-submitted can still
    tell whether the *primary* profile it was generated under is still
    current (see zodiac_tab.py/numerology_tab.py's _render_compatibility).
    """
    # Respect user consent: do not call the external AI service if the
    # user has explicitly declined consent to share profile facts.
    if not st.session_state.get("consent_given", False):
        st.error(t["errors"].get("consent_required", "Consent required to call the AI."))
        return None

    bucket = _cache_bucket(cache_key)
    if bucket.get(signature) is not None:
        return serve_existing_reading(t, cache_key, signature, lang_code)

    with st.spinner(t["common"]["ai_thinking"]):
        try:
            text, response_id = ai_service.ask_ai(
                instructions,
                message,
                previous_response_id=st.session_state.get("ai_previous_response_id"),
            )
        except ai_service.MissingAPIKeyError:
            st.error(t["errors"]["api_key_missing"])
            return None
        except ai_service.EmptyResponseError:
            st.error(t["errors"]["empty_ai_response"])
            return None
        except ai_service.AIServiceError as error:
            st.error(t["errors"]["api_error"].format(error=error))
            return None

    st.session_state["ai_previous_response_id"] = response_id
    bucket[signature] = {
        "source_lang": lang_code,
        "by_lang": {lang_code: text},
        **(extra or {}),
    }
    return text


_HEADING_RE = re.compile(r"^#{1,4}\s+(.+?)\s*$")
_BOLD_HEADING_RE = re.compile(r"^\*\*(.+?)\*\*:?\s*$")
_INLINE_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


def _inline_markdown_to_html(text):
    """Escape `text`, then turn any surviving `**bold**` runs into <strong>.

    Section headings (e.g. "## Something **9**") keep any inline bold the
    AI put inside the heading line itself — `_HEADING_RE` only strips the
    leading "## ", not inline "**...**" within it. Headings are rendered
    via a raw HTML <span> (not st.markdown), so without this the "**"
    markers show up literally instead of becoming bold. Escaping first
    means the regex only ever wraps already-safe text in a fixed <strong>
    tag, so this can't introduce any HTML injection.
    """
    return _INLINE_BOLD_RE.sub(r"<strong>\1</strong>", html.escape(text))

# Best-effort, purely presentational keyword → icon matching against the
# AI's own (already-generated) section headings, checked across all three
# UI languages since the heading text arrives in whichever one the user
# picked. Never changes what the AI is asked for or what it said — only
# picks a fitting symbol and, for the "advice" group, a bit more visual
# weight for that one section. Icons are pre-rendered once (module load).
_SECTION_ICON_RULES = (
    (("совет", "рекоменд", "advice", "tip", "khuyên"), icons.spark(16), True),
    (("работ", "career", "дела", "công việc", "sự nghiệp"), icons.scroll(16), False),
    (
        ("отношен", "любов", "relationship", "love", "mối quan hệ", "tình"),
        icons.venn(16),
        False,
    ),
    (
        ("настроен", "энерг", "mood", "energy", "tâm trạng", "năng lượng"),
        icons.moon(16),
        False,
    ),
    (
        ("сложност", "challenge", "growth", "рост", "thử thách", "phát triển"),
        icons.star(16),
        False,
    ),
    (("сильн", "strength", "điểm mạnh"), icons.gem(16), False),
    (("характер", "черт", "trait", "character", "tính cách"), icons.sun(16), False),
    (("фокус", "focus", "trọng tâm"), icons.chat(16), False),
)
_DEFAULT_SECTION_ICON = icons.spark(16)


def _icon_for_heading(heading):
    """Return (icon_svg, is_key_takeaway) for a heading, via keyword matching."""
    low = heading.lower()
    for keywords, icon_svg, is_key in _SECTION_ICON_RULES:
        if any(kw in low for kw in keywords):
            return icon_svg, is_key
    return _DEFAULT_SECTION_ICON, False


def parse_markdown_sections(text):
    """Split an AI markdown reply into an intro and (heading, body) sections.

    A "section" starts at a line that is either a Markdown heading
    ("## Something") or a standalone bold line ("**Something**") — both
    are patterns the app's own instructions ask the AI to use. Anything
    before the first such line is the intro. If no heading-like line is
    found at all, sections is empty and the caller should fall back to
    rendering the full text as-is (this never invents structure that
    isn't already in the reply).
    """
    intro_lines = []
    sections = []  # [[heading, [body_lines]], ...]

    for line in text.split("\n"):
        stripped = line.strip()
        match = _HEADING_RE.match(stripped) or _BOLD_HEADING_RE.match(stripped)
        if match:
            # A trailing colon can land either inside or outside the
            # "**...**" markers ("**Advice:**" vs "**Advice**:") —
            # strip it either way so it doesn't show up twice.
            heading_text = match.group(1).strip().rstrip(":").strip()
            sections.append([heading_text, []])
        elif sections:
            sections[-1][1].append(line)
        else:
            intro_lines.append(line)

    intro = "\n".join(intro_lines).strip()
    clean_sections = [
        (heading, body_text)
        for heading, body_lines in sections
        if (body_text := "\n".join(body_lines).strip())
    ]
    return intro, clean_sections


def render_reading_card(cache_key, icon, title, text, subtitle=None):
    """Render an AI reply as a structured "reading": header (+ optional

    subtitle), a lead intro, then one lightweight visual block per
    detected section, with the advice/key-takeaway section (if any)
    given real visual weight. Falls back to plain markdown in one card
    if the reply has no clear heading structure — the content itself is
    never altered, only how it's laid out.
    """
    intro, sections = parse_markdown_sections(text)

    with st.container(border=True, key=f"reading_{cache_key}"):
        header_html = (
            f'<span class="reading-icon">{icon}</span>'
            f'<span class="reading-title">{html.escape(title)}</span>'
        )
        if subtitle:
            header_html += f'<div class="reading-subtitle">{html.escape(subtitle)}</div>'
        st.markdown(header_html, unsafe_allow_html=True)

        if not sections:
            st.markdown(text)
            return

        if intro:
            st.markdown(intro)

        for index, (heading, body) in enumerate(sections):
            section_icon, is_key = _icon_for_heading(heading)
            st.markdown(
                '<div class="reading-section-header'
                f'{" is-key" if is_key else ""}">'
                f'<span class="reading-section-icon">{section_icon}</span>'
                f'<span class="reading-section-title">{_inline_markdown_to_html(heading)}</span>'
                "</div>",
                unsafe_allow_html=True,
            )
            if is_key:
                with st.container(border=True, key=f"advice_{cache_key}_{index}"):
                    st.markdown(body)
            else:
                st.markdown(body)


def render_action_panel(cache_key, icon, title, description, button_label, button_key):
    """The big premium panel shown for the currently selected action:

    icon, title, description, and one wide primary CTA button. This is
    the main visual block of the page once an action is picked — not a
    small button tucked under a subheader. Returns True the run the
    button is clicked.
    """
    with st.container(border=True, key=f"panel_{cache_key}"):
        st.markdown(
            f'<div class="panel-icon">{icon}</div>'
            f'<div class="panel-title">{html.escape(title)}</div>'
            f'<div class="panel-desc">{html.escape(description)}</div>',
            unsafe_allow_html=True,
        )
        clicked = st.button(
            button_label,
            key=f"cta_{button_key}",
            use_container_width=True,
            type="primary",
        )
    return clicked


def render_ai_section(
    t,
    panel_description,
    button_label,
    button_key,
    cache_key,
    signature,
    instructions,
    message,
    icon=None,
    title=None,
    reading_title=None,
    subtitle=None,
):
    """Big-panel, button-gated AI call: only reaches the network on an

    actual click (for the first-ever generation) — after that, a cached
    result keeps showing on later reruns (tab switches, language
    switches, other widgets) without a button press. A language switch
    with no click may still trigger one cheap *translation* call if this
    signature has never been seen in that language before; it never
    re-runs the main assistant (see call_ai_cached).

    `signature` must not encode the UI language (see call_ai_cached).

    `title` labels the panel shown before the click; `reading_title`
    (defaults to `title`) labels the result card afterwards — pass both
    when a feature wants different wording for "here's the fact" vs.
    "here's the AI's take on it". `subtitle` is an optional small line
    under the result card's title (e.g. sign + date).
    """
    icon = icon or icons.spark(26)
    lang_code = st.session_state.get("lang_code", "ru")

    panel_title = title or button_label
    clicked = render_action_panel(
        cache_key, icon, panel_title, panel_description, button_label, button_key
    )

    if not clicked and not has_canonical_reading(cache_key, signature):
        return

    text = call_ai_cached(t, cache_key, signature, lang_code, instructions, message)
    if text:
        render_reading_card(
            cache_key, icon, reading_title or panel_title, text, subtitle=subtitle
        )


def render_ask_ai_panel(
    t,
    icon,
    panel_title,
    description,
    question_label,
    ask_button_label,
    instructions,
    base_facts,
    form_key,
    signature_key,
):
    """A dedicated "ask anything" panel: icon/title/description, a big

    question field, and a prominent submit button — answers land in the
    same reading card as every other AI result.

    `signature_key` is a language-independent identifier for whichever
    chart this question is about (e.g. profile.zodiac_sign or
    str(profile.life_path_number)) — combined with the raw question
    text, it forms the cache signature. `base_facts` is the (localized,
    display-ready) facts text actually sent to the AI in the message;
    it's kept out of the signature on purpose, since it's built from
    localized display strings (e.g. the sign's name in the current UI
    language) that would otherwise make an identical question look like
    a different signature in every language. Re-asking the exact same
    question reuses the cached answer, in whatever language it's
    already been seen in; a language it hasn't been seen in yet gets a
    translation of the original answer, never a fresh call to the main
    assistant, and changing profile facts that change `signature_key`
    (a different sign or life path number) correctly starts a new
    canonical answer.
    """
    cache_key = f"{form_key}_last"
    lang_code = st.session_state.get("lang_code", "ru")

    with st.container(border=True, key=f"panel_{form_key}"):
        st.markdown(
            f'<div class="panel-icon">{icon}</div>'
            f'<div class="panel-title">{html.escape(panel_title)}</div>'
            f'<div class="panel-desc">{html.escape(description)}</div>',
            unsafe_allow_html=True,
        )
        with st.form(form_key):
            question = st.text_area(
                question_label,
                key=f"{form_key}_question",
                height=110,
                label_visibility="collapsed",
                placeholder=question_label,
            )
            submitted = st.form_submit_button(
                ask_button_label,
                key=f"cta_{form_key}",
                use_container_width=True,
                type="primary",
            )

    question = question.strip()
    signature = f"{signature_key}|{question}"

    if not submitted:
        text = serve_existing_reading(t, cache_key, signature, lang_code)
        if text:
            render_reading_card(cache_key, icon, panel_title, text)
        return

    if not question:
        st.error(t["common"]["empty_input"])
        return

    message = base_facts + "\n\n" + question
    text = call_ai_cached(t, cache_key, signature, lang_code, instructions, message)
    if text:
        render_reading_card(cache_key, icon, panel_title, text)

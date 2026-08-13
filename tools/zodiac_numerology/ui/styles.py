"""Custom CSS for the Streamlit GUI's cosmic premium look.

Colors, fonts and widget theming live in .streamlit/config.toml — that's
the mechanism Streamlit itself recommends, and every built-in widget
(buttons, inputs, forms, tabs, metrics) inherits it correctly. This
module only adds what config.toml cannot: the starfield/nebula
background, the compact hero, the action-card grid, the action panel,
and the AI "reading card". It never sets base widget colors.

Deliberately avoids relying on "fancy" Unicode glyphs for anything
visual — see ui/icons.py for why (font-coverage gaps render those as an
empty box on some systems). Every icon here is inline SVG, colored via
`currentColor`, so there's nothing here that can silently fail to
render depending on the viewer's installed fonts.

The starfield is generated once at import time with a fixed random seed
— not on every Streamlit rerun — so the stars never jitter between
clicks.
"""
import random

import streamlit as st

# Keep in sync with .streamlit/config.toml's palette.
_GOLD = "#F2C14E"
_VIOLET = "#8B7CF6"
_BLUE = "#22D3EE"


def _generate_star_shadows(count, seed, x_range, y_range, size, opacity_range):
    rng = random.Random(seed)
    parts = []
    for _ in range(count):
        x = rng.randint(*x_range)
        y = rng.randint(*y_range)
        opacity = rng.uniform(*opacity_range)
        parts.append(f"{x}px {y}px 0 {size}px rgba(237, 235, 247, {opacity:.2f})")
    return ", ".join(parts)


_STARS_SMALL = _generate_star_shadows(140, 1, (0, 2600), (0, 1600), 0, (0.25, 0.55))
_STARS_MEDIUM = _generate_star_shadows(50, 2, (0, 2600), (0, 1600), 1, (0.4, 0.75))
_STARS_BRIGHT = _generate_star_shadows(14, 3, (0, 2600), (0, 1600), 1, (0.75, 1.0))


_CSS = f"""
<style>
    /* ===============================================================
       Chrome removal
       =============================================================== */
    #MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"] {{
        visibility: hidden;
        height: 0;
    }}
    [data-testid="stHeader"] {{
        background: transparent;
        /* This bar spans the full page width at z-index ~999990 (a
           Streamlit internal). Its own controls are already hidden above,
           but without pointer-events:none it still sits on top of and
           steals clicks from anything else living in that top strip —
           in this app, the language selector next to the title. */
        pointer-events: none;
    }}

    /* ===============================================================
       Cosmic background: nebula glow (::before) + starfield (::after)
       =============================================================== */
    [data-testid="stApp"] {{
        position: relative;
        overflow-x: hidden;
    }}
    [data-testid="stApp"]::before {{
        content: "";
        position: fixed;
        inset: -10%;
        z-index: 0;
        pointer-events: none;
        background:
            radial-gradient(38% 30% at 15% 12%, rgba(139, 124, 246, 0.30), transparent 70%),
            radial-gradient(32% 26% at 88% 18%, rgba(34, 211, 238, 0.18), transparent 70%),
            radial-gradient(40% 34% at 50% 92%, rgba(242, 193, 78, 0.10), transparent 70%);
        animation: nebula-drift 40s ease-in-out infinite alternate;
    }}
    [data-testid="stApp"]::after {{
        content: "";
        position: fixed;
        inset: 0;
        z-index: 0;
        pointer-events: none;
        width: 2px;
        height: 2px;
        border-radius: 50%;
        box-shadow: {_STARS_SMALL}, {_STARS_MEDIUM}, {_STARS_BRIGHT};
        /* soften the starfield so it remains subtle behind content */
        opacity: 0.62;
        animation: twinkle 6s ease-in-out infinite alternate;
    }}
    @keyframes nebula-drift {{
        0%   {{ transform: translate3d(0, 0, 0) scale(1); }}
        100% {{ transform: translate3d(-1.5%, 1.5%, 0) scale(1.05); }}
    }}
    @keyframes twinkle {{
        0%   {{ opacity: 0.65; }}
        100% {{ opacity: 1; }}
    }}
    [data-testid="stAppViewContainer"], [data-testid="stMain"] {{
        position: relative;
        z-index: 1;
    }}
    html {{ scroll-behavior: smooth; }}

    /* Tight page rhythm — this is the single biggest lever against the
       "huge empty Streamlit demo" feeling: less vertical padding
       between every block, everywhere. */
    .block-container {{
        max-width: 960px;
        padding-top: 1.3rem;
        padding-bottom: 2.4rem;
    }}
    div[data-testid="stVerticalBlock"] {{
        gap: 0.6rem;
    }}

    /* ===============================================================
       Top bar: wordmark + language switcher
       =============================================================== */
    .app-title {{
        font-size: clamp(1.35rem, 2.6vw, 1.7rem);
        font-weight: 700;
        background: linear-gradient(90deg, {_GOLD}, {_VIOLET} 55%, {_BLUE});
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        letter-spacing: -0.01em;
        line-height: 1.3;
    }}

    /* ===============================================================
       Onboarding screen (no profile yet): two-column — value prop +
       compact form card. Stacks on mobile.
       =============================================================== */
    .onboarding-copy {{
        padding: 0.6rem 0 0;
    }}
    .onboarding-eyebrow {{
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-size: 0.72rem;
        opacity: 0.6;
        margin-bottom: 0.5rem;
    }}
    .onboarding-title {{
        font-size: clamp(1.4rem, 3.4vw, 1.9rem);
        font-weight: 700;
        line-height: 1.25;
        margin-bottom: 0.6rem;
    }}
    .onboarding-title .accent {{
        background: linear-gradient(120deg, {_GOLD}, {_VIOLET});
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }}
    .onboarding-lede {{
        font-size: 0.95rem;
        opacity: 0.68;
        line-height: 1.55;
        max-width: 42ch;
        margin-bottom: 1.1rem;
    }}
    .onboarding-points {{
        display: flex;
        flex-direction: column;
        gap: 0.55rem;
    }}
    .onboarding-point {{
        display: flex;
        align-items: flex-start;
        gap: 0.55rem;
        font-size: 0.86rem;
        opacity: 0.75;
    }}
    .onboarding-point svg {{ color: {_VIOLET}; flex: 0 0 auto; margin-top: 0.1rem; }}
    div[class*="st-key-onboarding_form"] {{
        background: linear-gradient(165deg, rgba(255,255,255,0.045), rgba(255,255,255,0.012));
        backdrop-filter: blur(10px);
        text-align: center;
    }}
    div[class*="st-key-onboarding_form"] .panel-icon {{ margin-bottom: 0.5rem; }}

    /* ===============================================================
       Hero (profile exists): compact horizontal row on desktop.
       =============================================================== */
    .hero {{
        position: relative;
        padding: 0.5rem 0 0.9rem;
    }}
    .hero-main {{
        display: flex;
        align-items: center;
        gap: 1.6rem;
    }}
    .hero-badge {{
        position: relative;
        flex: 0 0 auto;
        width: 108px;
        height: 108px;
    }}
    .hero-badge-ring {{
        position: absolute;
        inset: 0;
        border-radius: 50%;
        border: 1.5px solid rgba(139, 124, 246, 0.38);
        animation: spin 26s linear infinite;
    }}
    .hero-badge-ring::before {{
        content: "";
        position: absolute;
        top: -2.5px;
        left: 50%;
        width: 5px;
        height: 5px;
        margin-left: -2.5px;
        border-radius: 50%;
        background: {_GOLD};
        box-shadow: 0 0 8px 2px {_GOLD};
    }}
    @keyframes spin {{
        from {{ transform: rotate(0deg); }}
        to   {{ transform: rotate(360deg); }}
    }}
    .hero-badge-fill {{
        position: absolute;
        inset: 9px;
        border-radius: 50%;
        background: radial-gradient(circle at 32% 26%, rgba(139,124,246,0.20), rgba(242,193,78,0.05) 72%);
        border: 1px solid rgba(255, 255, 255, 0.07);
    }}
    .hero-badge-text {{
        position: absolute;
        inset: 9px;
        display: flex;
        align-items: center;
        justify-content: center;
        text-align: center;
        padding: 0 0.5rem;
        font-weight: 700;
        font-size: clamp(0.72rem, 1.5vw, 0.92rem);
        letter-spacing: 0.04em;
        text-transform: uppercase;
        line-height: 1.2;
        background: linear-gradient(160deg, {_GOLD}, {_VIOLET});
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
    }}
    .hero-constellation-bg {{
        position: absolute;
        top: -18px;
        right: -6px;
        color: {_VIOLET};
        opacity: 0.14;
        pointer-events: none;
        z-index: -1;
    }}
    .hero-text {{
        flex: 1 1 auto;
        min-width: 0;
    }}
    .hero-greeting {{
        font-size: clamp(1rem, 2vw, 1.2rem);
        font-weight: 600;
        opacity: 0.92;
        margin-bottom: 0.15rem;
    }}
    .hero-value-prop {{
        font-size: 0.86rem;
        opacity: 0.6;
        line-height: 1.45;
        max-width: 46ch;
        margin-bottom: 0.65rem;
    }}
    .hero-stats-row {{
        display: flex;
        align-items: center;
        gap: 1rem;
        flex-wrap: wrap;
    }}
    .hero-stat {{
        display: flex;
        flex-direction: column;
        gap: 0.05rem;
    }}
    .hero-stat-label {{
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        opacity: 0.5;
    }}
    .hero-stat-value {{
        font-size: 0.9rem;
        font-weight: 600;
    }}
    .hero-stat-sep {{
        width: 1px;
        height: 20px;
        background: rgba(255, 255, 255, 0.12);
    }}

    /* ===============================================================
       Section eyebrow + disclaimer
       =============================================================== */
    .eyebrow {{
        text-transform: uppercase;
        letter-spacing: 0.08em;
        font-size: 0.72rem;
        opacity: 0.55;
        margin: 0.2rem 0 0.1rem;
    }}
    div[data-testid="stCaptionContainer"] {{
        opacity: 0.6;
    }}

    /* ===============================================================
       Action-card grid — compact, fixed 3 columns on desktop, reflows
       to 2 then 1. st.container(key="grid_...") gets the .st-key-grid_*
       class from Streamlit; overriding its default flex-column layout
       with CSS Grid gives real reflow from a single Python loop.
       =============================================================== */
    div[class*="st-key-grid_"] {{
        display: grid !important;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 0.65rem;
        align-items: stretch;
        margin-top: 0.3rem;
    }}
    @media (max-width: 860px) {{
        div[class*="st-key-grid_"] {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
    }}
    @media (max-width: 560px) {{
        div[class*="st-key-grid_"] {{ grid-template-columns: 1fr; }}
    }}

    /* Feature cards. The whole card is clickable: (1) the real
       st.button, first element-container child, stretched to fill via
       flex-grow — a normal, reliably-sized in-flow element; (2) the
       decorative icon/title/subtitle, second child, layered on top via
       position:absolute + pointer-events:none, so clicks fall straight
       through it to the button. There's no visible "button inside the
       card" — the button is invisible (opacity:0), only its hit area
       remains, covering the whole card. This mechanism is unchanged
       from the previous pass; only the sizing/spacing below is new. */
    /* :not([class*="_btn"]) matters: the card's own st.button carries a
       key ending in "_btn", and Streamlit stamps that key onto the
       button's *wrapping* element-container div as a "st-key-..._btn"
       class — which also contains the substring "st-key-card_" and
       would otherwise match this same attribute selector. Without the
       exclusion, that inner wrapper gets its own copy of the card's
       background/blur, showing up as a second, empty "card" nested
       inside the real one. */
    div[class*="st-key-card_"]:not([class*="_btn"]) {{
        position: relative;
        display: flex;
        flex-direction: column;
        min-height: 8rem;
        background: linear-gradient(165deg, rgba(255,255,255,0.035), rgba(255,255,255,0.01));
        backdrop-filter: blur(6px);
        cursor: pointer;
        transition: transform 0.16s ease, border-color 0.16s ease, box-shadow 0.16s ease;
        /* keep a consistent transparent border so hover/active border-color
           changes don't cause any layout shift */
        border: 1px solid rgba(255,255,255,0.02);
        border-radius: 12px;
        overflow: hidden;
    }}
    div[class*="st-key-card_"]:not([class*="_btn"]):hover {{
        transform: translateY(-2px);
        border-color: rgba(139, 124, 246, 0.55) !important;
        box-shadow: 0 8px 22px -12px rgba(139, 124, 246, 0.5);
    }}
    div[class*="st-key-card_"]:not([class*="_btn"]):has(button:active) {{
        transform: translateY(-1px) scale(0.98);
    }}
    div[class*="st-key-card_"] > div[data-testid="stElementContainer"]:first-child {{
        flex: 1;
        display: flex;
    }}
    div[class*="st-key-card_"] div[data-testid="stButton"] {{
        flex: 1;
        display: flex;
        margin: 0;
    }}
    div[class*="st-key-card_"] div[data-testid="stButton"] button {{
        flex: 1;
        width: 100%;
        min-height: 100%;
        opacity: 0;
        cursor: pointer;
        border: none !important;
        box-shadow: none !important;
    }}
    div[class*="st-key-card_"] > div[data-testid="stElementContainer"]:last-child {{
        position: absolute;
        inset: 0;
        pointer-events: none;
        display: flex;
        align-items: flex-start;
    }}
    .feature-content {{
        width: 100%;
        padding: 1rem 0.9rem;
        text-align: left;
    }}
    .feature-icon {{
        display: inline-flex;
        color: {_VIOLET};
        opacity: 0.95;
        margin-bottom: 0.45rem;
    }}
    .feature-title {{
        font-weight: 700;
        font-size: 0.98rem;
        margin-bottom: 0.18rem;
        line-height: 1.22;
    }}
    .feature-desc {{
        font-size: 0.79rem;
        opacity: 0.66;
        line-height: 1.38;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }}

    /* ===============================================================
       Action panel — the big block shown below the grid for whatever
       action is selected. Same st-key mechanism, one clear focal point.
       =============================================================== */
    div[class*="st-key-panel_"] {{
        background: linear-gradient(165deg, rgba(139,124,246,0.07), rgba(34,211,238,0.02));
        backdrop-filter: blur(8px);
        border-top: 2px solid {_VIOLET} !important;
        text-align: center;
        padding: 1rem;
        border-radius: 12px;
    }}
    .panel-icon {{
        display: inline-flex;
        color: {_GOLD};
        margin-bottom: 0.3rem;
        filter: drop-shadow(0 0 8px rgba(242, 193, 78, 0.4));
    }}
    .panel-title {{
        font-weight: 700;
        font-size: 1.22rem;
        margin-bottom: 0.3rem;
    }}
    .panel-desc {{
        opacity: 0.72;
        font-size: 0.92rem;
        margin-bottom: 0.85rem;
        max-width: 46ch;
        margin-left: auto;
        margin-right: auto;
    }}
    .panel-preview {{
        font-size: 0.78rem;
        opacity: 0.55;
        margin-bottom: 0.9rem;
    }}
    div[class*="st-key-cta_"] button {{
        font-size: 1.02rem;
        font-weight: 700;
        padding-top: 0.62rem;
        padding-bottom: 0.62rem;
        letter-spacing: 0.01em;
        border-radius: 10px;
        box-shadow: 0 8px 18px -10px rgba(0,0,0,0.6);
    }}
    div[class*="st-key-panel_"] textarea {{
        font-size: 1rem;
    }}

    /* ===============================================================
       Reading card (AI output) — same st-key mechanism. Structured
       into: header (icon/title/subtitle), an emphasized lead intro,
       lightweight per-section headers, and one stronger box for the
       advice/key-takeaway section. Fades in gently on appearance.
       =============================================================== */
    div[class*="st-key-reading_"] {{
        background: linear-gradient(165deg, rgba(139,124,246,0.05), rgba(34,211,238,0.02));
        backdrop-filter: blur(6px);
        border-left: 3px solid {_GOLD} !important;
        animation: reading-fade-in 0.45s ease both;
        padding: 1rem;
        border-radius: 12px;
    }}
    @keyframes reading-fade-in {{
        from {{ opacity: 0; transform: translateY(6px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
    }}
    .reading-icon {{
        display: inline-flex;
        vertical-align: middle;
        color: {_GOLD};
        margin-right: 0.4rem;
    }}
    .reading-title {{
        display: inline-block;
        font-weight: 700;
        font-size: 1.1rem;
        vertical-align: middle;
    }}
    .reading-subtitle {{
        opacity: 0.55;
        font-size: 0.82rem;
        margin: 0.1rem 0 0 1.9rem;
        letter-spacing: 0.02em;
    }}
    div[class*="st-key-reading_"] h1,
    div[class*="st-key-reading_"] h2,
    div[class*="st-key-reading_"] h3 {{
        color: {_GOLD};
        font-size: 1.02rem;
        margin-top: 0.9rem;
    }}
    div[class*="st-key-reading_"] p,
    div[class*="st-key-reading_"] li {{
        line-height: 1.66;
        font-size: 0.98rem;
        color: rgba(255,255,255,0.95);
    }}
    div[class*="st-key-reading_"] > div[data-testid="stMarkdown"]:nth-of-type(2) p:first-child {{
        font-size: 1.02rem;
        font-weight: 500;
        color: {_GOLD};
        border-left: 2px solid {_VIOLET};
        padding-left: 0.65rem;
    }}
    div[class*="st-key-reading_"] ul {{ padding-left: 1.1rem; }}
    div[class*="st-key-reading_"] li::marker {{ color: {_VIOLET}; }}
    div[class*="st-key-reading_"] strong {{ color: {_GOLD}; }}
    .reading-section-header {{
        display: flex;
        align-items: center;
        gap: 0.4rem;
        margin-top: 1.15rem;
        margin-bottom: 0.25rem;
        padding-top: 0.7rem;
        border-top: 1px solid rgba(139, 124, 246, 0.16);
    }}
    .reading-section-header:first-of-type {{
        border-top: none;
        padding-top: 0;
        margin-top: 0.75rem;
    }}
    .reading-section-icon {{ display: inline-flex; color: {_VIOLET}; opacity: 0.9; }}
    .reading-section-title {{
        font-weight: 600;
        font-size: 0.94rem;
        opacity: 0.92;
    }}
    .reading-section-header.is-key .reading-section-icon,
    .reading-section-header.is-key .reading-section-title {{ color: {_GOLD}; }}
    div[class*="st-key-advice_"] {{
        background: linear-gradient(165deg, rgba(242,193,78,0.10), rgba(242,193,78,0.02));
        border-color: rgba(242, 193, 78, 0.4) !important;
        margin-top: 0.35rem;
    }}

    /* ===============================================================
       Responsive
       =============================================================== */
    @media (max-width: 640px) {{
        .block-container {{ padding-left: 1rem; padding-right: 1rem; }}
        .hero-main {{ flex-direction: column; text-align: center; }}
        .hero-stats-row {{ justify-content: center; }}
        .hero-value-prop {{ max-width: 100%; margin-left: auto; margin-right: auto; }}
        .panel-title {{ font-size: 1.08rem; }}
    }}

    /* ===============================================================
       Respect prefers-reduced-motion
       =============================================================== */
    @media (prefers-reduced-motion: reduce) {{
        *, *::before, *::after {{
            animation-duration: 0.001ms !important;
            animation-iteration-count: 1 !important;
            transition-duration: 0.001ms !important;
            scroll-behavior: auto !important;
        }}
    }}
</style>
"""


def inject_css():
    st.markdown(_CSS, unsafe_allow_html=True)


def active_card_glow_css(card_key):
    """A small extra stylesheet that highlights exactly one card by its

    st.container(key=...) value — injected right before that card is
    rendered, see ui/common.py:render_action_grid. Gold border with a
    soft violet halo, matching the app's two main accent colors.

    Explicitly repeats the rule under `:hover` (same declarations, same
    specificity as the generic `div[class*="st-key-card_"]:hover` rule in
    the base stylesheet) so the gold "selected" state doesn't flip to the
    generic violet hover border the moment the cursor sits over the card
    it just selected — which it does, right after a click.
    """
    # slightly more restrained glow: thinner halo and softer violet
    glow = (
        f"border-color: {_GOLD} !important; "
        f"box-shadow: 0 0 0 1px {_GOLD}55, 0 8px 22px -10px {_VIOLET}66, "
        f"0 0 14px -6px {_GOLD}44;"
    )
    return (
        f"<style>"
        f"div.st-key-{card_key} {{ {glow} }} "
        f"div.st-key-{card_key}:hover {{ {glow} }}"
        f"</style>"
    )


def wide_card_css(card_key):
    """Makes one specific card span the full grid width — used for a

    trailing "leftover" card when an action list doesn't divide evenly
    into the 3-column grid (e.g. 7 items), so it reads as an
    intentional wide entry rather than an orphaned single card.

    `grid-column` only has any effect on an actual grid *item* — a
    direct child of the `display:grid` container. But the element
    carrying `.st-key-{card_key}` (the card's own st.container) is
    nested one level *inside* the real grid item: Streamlit wraps every
    st.container(key=...) in its own extra `stLayoutWrapper` div, and
    that wrapper — not the keyed container — is what the grid actually
    lays out. Setting `grid-column` on `.st-key-{card_key}` directly was
    therefore silently a no-op; `:has()` reaches up to style the actual
    grid-item ancestor instead.
    """
    return (
        f'<style>div[data-testid="stLayoutWrapper"]:has(> .st-key-{card_key}) '
        f"{{ grid-column: 1 / -1; }}</style>"
    )

"""Tests for the AI-reply markdown sectioning used by the GUI's reading card.

Pure functions, no Streamlit runtime needed — ui.common can be imported
bare (it only touches st.session_state inside functions, not at import
time).
"""
from ui.common import _icon_for_heading, parse_markdown_sections


def test_plain_text_with_no_headings_has_no_sections():
    intro, sections = parse_markdown_sections("Just a plain paragraph, no structure at all.")
    assert sections == []
    assert "plain paragraph" in intro


def test_hash_headings_are_split_into_sections():
    text = (
        "Intro line.\n\n"
        "## Work\n"
        "Body about work.\n\n"
        "## Mood\n"
        "Body about mood.\n"
    )
    intro, sections = parse_markdown_sections(text)
    assert intro == "Intro line."
    assert [h for h, _ in sections] == ["Work", "Mood"]
    assert sections[0][1] == "Body about work."
    assert sections[1][1] == "Body about mood."


def test_standalone_bold_lines_are_also_headings():
    text = "**Advice**\nTake it easy today."
    intro, sections = parse_markdown_sections(text)
    assert intro == ""
    assert sections == [("Advice", "Take it easy today.")]


def test_bold_heading_with_trailing_colon_is_recognized():
    text = "**Advice:**\nBreathe.\n"
    _intro, sections = parse_markdown_sections(text)
    assert sections[0][0] == "Advice"


def test_inline_bold_within_a_sentence_is_not_treated_as_a_heading():
    text = "This is a **bold** word inside a normal sentence, not a heading."
    intro, sections = parse_markdown_sections(text)
    assert sections == []
    assert "bold" in intro


def test_sections_with_no_body_are_dropped():
    text = "## Empty\n## Work\nSomething here.\n"
    _intro, sections = parse_markdown_sections(text)
    assert [h for h, _ in sections] == ["Work"]


def test_icon_for_heading_matches_advice_keywords_across_languages():
    for heading in ("Совет дня", "Advice", "Lời khuyên"):
        icon, is_key = _icon_for_heading(heading)
        assert is_key is True
        assert icon


def test_icon_for_heading_falls_back_when_unmatched():
    icon, is_key = _icon_for_heading("Something completely unrelated 42")
    assert is_key is False
    assert icon

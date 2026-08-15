"""Regression coverage for the Family Secret reservation form
(tools/lead_qualifier/app.py) via Streamlit's AppTest.

Scope is deliberately narrow: these tests never submit the form and
never touch send_telegram/requests/Telegram, so they never depend on
st.secrets being configured (real or absent) and never make a network
call, regardless of what's in the local .streamlit/secrets.toml. The
actual Telegram delivery path was verified manually against the real
API during the 2026-08-xx notification audit (getMe + a marked
diagnostic sendMessage) — not something a routine pytest run should
repeat on every invocation.
"""
from pathlib import Path

from streamlit.testing.v1 import AppTest

# AppTest.from_file resolves relative paths against *this* file's
# directory (tests/lead_qualifier/), not the pytest working directory.
APP_PATH = str(Path(__file__).parent.parent.parent / "tools" / "lead_qualifier" / "app.py")


def _app() -> AppTest:
    at = AppTest.from_file(APP_PATH)
    at.run()
    return at


def test_app_loads_without_error():
    at = _app()
    assert not at.exception


def test_submit_button_shows_the_real_bilingual_label_not_the_debug_placeholder():
    """Regression test for the reported "HIDDEN SUBMIT (FS)" bug: the
    submit button's label was a leftover debug placeholder
    ("Hidden submit (fs)") instead of the real customer-facing,
    bilingual call-to-action text."""
    at = _app()
    submit_labels = [b.label for b in at.button if b.key == "fs_submit"]

    assert submit_labels, "expected a form_submit_button with key='fs_submit'"
    assert "Hidden submit (fs)" not in submit_labels
    assert any(
        "Request a reservation" in label and "Отправить заявку" in label for label in submit_labels
    )

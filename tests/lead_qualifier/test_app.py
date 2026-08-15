"""Regression coverage for the Family Secret reservation form
(tools/lead_qualifier/app.py) via Streamlit's AppTest.

Note: AppTest runs the script in a lightweight "bare mode" sandbox that
does *not* go through Streamlit's normal `streamlit run` bootstrap, so
it never loads a local .streamlit/secrets.toml — st.secrets is always
empty here regardless of what's configured locally or in Streamlit
Cloud. That's why test_submit_succeeds_... below configures credentials
via environment variables (through the app's os.environ fallback, see
_configured_secret in app.py) instead of secrets.toml, and why it uses
fake values + a mocked requests.post rather than the real Telegram API.
The real API was verified manually during the 2026-08 notification
audit (getMe + marked diagnostic sendMessage calls) — not something a
routine pytest run should repeat on every invocation.
"""
from pathlib import Path
from unittest.mock import Mock

import requests
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


def test_submit_succeeds_when_credentials_are_valid_and_never_raises_keyerror(monkeypatch):
    """Regression test for a real production bug: even with correctly
    configured TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID, send_telegram()
    used to unconditionally raise KeyError('label_requests') while
    building the notification text (a local `translations` dict inside
    send_telegram was missing that key) — caught by the same generic
    `except KeyError` as a *missing secret*, so it displayed the exact
    same "notifications unavailable" message even when the secrets
    were entirely correct. Uses fake, clearly-not-real credentials and
    a mocked requests.post — never the real Telegram API."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "000000:test-only-not-a-real-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "000000000")

    fake_response = Mock(status_code=200)
    fake_post = Mock(return_value=fake_response)
    monkeypatch.setattr(requests, "post", fake_post)

    at = _app()
    at.text_input(key="fs_name").set_value("Test Guest")
    at.text_input(key="fs_contact").set_value("+1 555 000 0000")
    at.button(key="fs_submit").click().run()

    assert not at.exception
    assert not at.error, f"expected no error message, got: {[e.value for e in at.error]}"
    assert at.success, "expected a success message after submit — send_telegram likely raised"
    fake_post.assert_called_once()

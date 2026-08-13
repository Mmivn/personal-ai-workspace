"""Unit tests for ai_service.py's ALL_API adapter layer.

These monkeypatch ai_service._gateway with a stub exposing the same
.generate()/.translate() surface as AIGateway, so they run without any
network access and without needing real provider keys. See
test_ai_service_fallback.py for tests that exercise the real
AIGateway/FallbackRouter (with mocked HTTP) through this same module.
"""
import pytest

import ai_service
from all_api.exceptions import AllProvidersFailedError, ConfigurationError
from all_api.models import GenerateResult


class _FakeGateway:
    """Stand-in for AIGateway exposing only what ai_service calls."""

    def __init__(self, text="", raise_error=None):
        self._text = text
        self._raise_error = raise_error
        self.last_generate_kwargs = None
        self.last_translate_kwargs = None

    def generate(self, prompt, system_prompt=None, **kwargs):
        self.last_generate_kwargs = {"prompt": prompt, "system_prompt": system_prompt, **kwargs}
        if self._raise_error:
            raise self._raise_error
        return GenerateResult(text=self._text, provider="gemini", model="mock-model", latency_ms=1.0)

    def translate(self, text, target_language=None, **kwargs):
        self.last_translate_kwargs = {"text": text, "target_language": target_language, **kwargs}
        if self._raise_error:
            raise self._raise_error
        return GenerateResult(text=self._text, provider="gemini", model="mock-model", latency_ms=1.0)


@pytest.fixture(autouse=True)
def _reset_gateway():
    ai_service.reset_client()
    yield
    ai_service.reset_client()


def test_no_provider_configured_raises_missing_api_key_error(monkeypatch):
    fake = _FakeGateway(raise_error=ConfigurationError("no provider is configured"))
    monkeypatch.setattr(ai_service, "_gateway", fake)

    with pytest.raises(ai_service.MissingAPIKeyError):
        ai_service.ask_ai("instructions", "hi")


def test_successful_call_returns_text_and_a_response_id_slot(monkeypatch):
    fake = _FakeGateway(text="Sunny days ahead.")
    monkeypatch.setattr(ai_service, "_gateway", fake)

    text, response_id = ai_service.ask_ai("instructions", "hi")

    assert text == "Sunny days ahead."
    assert response_id is None  # no cross-provider server-side thread — see module docstring
    assert fake.last_generate_kwargs["prompt"] == "hi"
    assert fake.last_generate_kwargs["system_prompt"] == "instructions"


def test_previous_response_id_is_accepted_but_not_forwarded(monkeypatch):
    """Kept for backward-compatible call signatures (app.py, ui/common.py
    both pass it) — see module docstring for why it's a no-op now."""
    fake = _FakeGateway(text="More.")
    monkeypatch.setattr(ai_service, "_gateway", fake)

    ai_service.ask_ai("instructions", "hi", previous_response_id="resp_0")

    assert "previous_response_id" not in fake.last_generate_kwargs


def test_empty_response_raises_empty_response_error(monkeypatch):
    fake = _FakeGateway(text="")
    monkeypatch.setattr(ai_service, "_gateway", fake)

    with pytest.raises(ai_service.EmptyResponseError):
        ai_service.ask_ai("instructions", "hi")


def test_whitespace_only_response_raises_empty_response_error(monkeypatch):
    fake = _FakeGateway(text="   \n  ")
    monkeypatch.setattr(ai_service, "_gateway", fake)

    with pytest.raises(ai_service.EmptyResponseError):
        ai_service.ask_ai("instructions", "hi")


def test_all_providers_failed_is_wrapped_as_ai_service_error(monkeypatch):
    fake = _FakeGateway(raise_error=AllProvidersFailedError("all providers failed"))
    monkeypatch.setattr(ai_service, "_gateway", fake)

    with pytest.raises(ai_service.AIServiceError):
        ai_service.ask_ai("instructions", "hi")


def test_unexpected_exception_is_wrapped_as_ai_service_error(monkeypatch):
    fake = _FakeGateway(raise_error=ConnectionError("network down"))
    monkeypatch.setattr(ai_service, "_gateway", fake)

    with pytest.raises(ai_service.AIServiceError):
        ai_service.ask_ai("instructions", "hi")


# --------------------------------------------------------------------------
# translate_text
# --------------------------------------------------------------------------

def test_translate_text_returns_translated_text(monkeypatch):
    fake = _FakeGateway(text="Bonjour le monde")
    monkeypatch.setattr(ai_service, "_gateway", fake)

    translated = ai_service.translate_text("Hello world", "French")

    assert translated == "Bonjour le monde"
    assert fake.last_translate_kwargs["text"] == "Hello world"
    assert fake.last_translate_kwargs["target_language"] == "French"


def test_translate_text_empty_response_raises_empty_response_error(monkeypatch):
    fake = _FakeGateway(text="   ")
    monkeypatch.setattr(ai_service, "_gateway", fake)

    with pytest.raises(ai_service.EmptyResponseError):
        ai_service.translate_text("hi", "Russian")


def test_translate_text_missing_api_key_raises(monkeypatch):
    fake = _FakeGateway(raise_error=ConfigurationError("no provider is configured"))
    monkeypatch.setattr(ai_service, "_gateway", fake)

    with pytest.raises(ai_service.MissingAPIKeyError):
        ai_service.translate_text("hi", "Russian")


def test_translate_text_provider_error_is_wrapped_as_ai_service_error(monkeypatch):
    fake = _FakeGateway(raise_error=AllProvidersFailedError("all providers failed"))
    monkeypatch.setattr(ai_service, "_gateway", fake)

    with pytest.raises(ai_service.AIServiceError):
        ai_service.translate_text("hi", "Russian")

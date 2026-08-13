"""Integration tests for ai_service.py's ALL_API-backed fallback chain.

These go through ai_service.ask_ai/translate_text (the actual call path
every UI/CLI handler uses) rather than calling AIGateway directly — the
point is to verify *this project's* integration, not re-test ALL_API in
isolation (that suite already covers the router exhaustively). All HTTP
is mocked via requests.post; no test makes a real network call or spends
real money.

Active chain under test: gemini -> groq -> mistral -> cloudflare -> openai
(paid, last resort). Cerebras/OpenRouter/DeepSeek must never be reached.
"""
import requests
import pytest

import ai_service
from all_api import AIGateway
from all_api.config import Config
from all_api.exceptions import AllProvidersFailedError


# --------------------------------------------------------------------------
# Fake HTTP layer (mirrors ALL_API's own tests/conftest.py fixtures, kept
# local so this suite has no test-time dependency on ALL_API's test package).
# --------------------------------------------------------------------------

class FakeResponse:
    def __init__(self, status_code=200, json_data=None, text=None, headers=None):
        self.status_code = status_code
        self._json_data = {} if json_data is None else json_data
        self.text = text if text is not None else str(self._json_data)
        self.headers = headers or {}

    def json(self):
        return self._json_data


def openai_style_success(text="mocked response", model="mock-model"):
    """Shared wire format: OpenAI, Groq, and Mistral all speak this."""
    return FakeResponse(
        200,
        {
            "choices": [{"message": {"content": text}}],
            "model": model,
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        },
    )


def gemini_style_success(text="mocked response"):
    return FakeResponse(
        200,
        {
            "candidates": [{"content": {"parts": [{"text": text}]}}],
            "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 5},
        },
    )


def cloudflare_style_success(text="mocked response"):
    return FakeResponse(
        200,
        {"result": {"response": text}, "success": True, "errors": [], "messages": []},
    )


def error_response(status_code, message="mocked error", headers=None):
    return FakeResponse(
        status_code, {"error": {"message": message}}, text=f'{{"error": "{message}"}}', headers=headers
    )


class RoutedFakePost:
    """Replaces requests.post. Each test queues canned responses per host
    substring; each matching call pops the next one."""

    def __init__(self):
        self._queues = {}
        self.calls = []

    def add(self, host_substring, item):
        self._queues.setdefault(host_substring, []).append(item)
        return self

    def __call__(self, url, headers=None, json=None, timeout=None, **kwargs):
        self.calls.append(url)
        for host, queue in self._queues.items():
            if host in url:
                if not queue:
                    raise AssertionError(f"no more mocked responses queued for host {host!r} (url={url})")
                item = queue.pop(0)
                if isinstance(item, Exception):
                    raise item
                return item
        raise AssertionError(f"no mocked response registered for url {url}")


PROVIDER_HOSTS = {
    "gemini": "generativelanguage.googleapis.com",
    "groq": "api.groq.com",
    "mistral": "api.mistral.ai",
    "cloudflare": "api.cloudflare.com",
    "openai": "api.openai.com",
}

_API_KEY_ENV_VARS = {
    "gemini": "GEMINI_API_KEY",
    "groq": "GROQ_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "openai": "OPENAI_API_KEY",
}
_CLOUDFLARE_ENV_VARS = ("CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID")
_ALL_KEY_ENV_VARS = (
    "GEMINI_API_KEY",
    "GROQ_API_KEY",
    "MISTRAL_API_KEY",
    "OPENAI_API_KEY",
    "CEREBRAS_API_KEY",
    "OPENROUTER_API_KEY",
    "DEEPSEEK_API_KEY",
    "CLOUDFLARE_API_TOKEN",
    "CLOUDFLARE_ACCOUNT_ID",
)


def set_keys(monkeypatch, *provider_names):
    for name in provider_names:
        if name == "cloudflare":
            monkeypatch.setenv("CLOUDFLARE_API_TOKEN", "test-cloudflare-token-not-real")
            monkeypatch.setenv("CLOUDFLARE_ACCOUNT_ID", "test-cloudflare-account-not-real")
        else:
            monkeypatch.setenv(_API_KEY_ENV_VARS[name], f"test-{name}-key-not-real")


@pytest.fixture
def clean_env(monkeypatch, tmp_path):
    """Strip every provider env var and move cwd away from this project's
    real .env, so no test can accidentally pick up a real key or make a
    real call. Also resets ai_service's cached gateway before and after."""
    for env_var in _ALL_KEY_ENV_VARS:
        monkeypatch.delenv(env_var, raising=False)
    for env_var in ("PAID_FALLBACK_ENABLED", "DAILY_PAID_BUDGET_USD", "PROVIDER_ORDER", "TRANSLATION_PROVIDER_ORDER"):
        monkeypatch.delenv(env_var, raising=False)
    monkeypatch.chdir(tmp_path)
    ai_service.reset_client()
    yield monkeypatch
    ai_service.reset_client()


@pytest.fixture
def fake_post(monkeypatch):
    router = RoutedFakePost()
    monkeypatch.setattr(requests, "post", router)
    return router


def _install_gateway(monkeypatch):
    """Build a real AIGateway from the current env and wire it into
    ai_service, exactly as ai_service._get_gateway() would — this is what
    makes these tests exercise the actual application call path
    (ai_service.ask_ai/translate_text) instead of AIGateway directly."""
    gateway = AIGateway(config=Config.from_env())
    monkeypatch.setattr(ai_service, "_gateway", gateway)
    return gateway


# --------------------------------------------------------------------------
# Fallback chain, driven through ai_service.ask_ai
# --------------------------------------------------------------------------

def test_gemini_success_no_later_provider_called(clean_env, fake_post):
    set_keys(clean_env, "gemini", "groq", "mistral")
    fake_post.add(PROVIDER_HOSTS["gemini"], gemini_style_success("hi from gemini"))
    _install_gateway(clean_env)

    text, response_id = ai_service.ask_ai("instructions", "hi")

    assert text == "hi from gemini"
    assert len(fake_post.calls) == 1
    assert PROVIDER_HOSTS["gemini"] in fake_post.calls[0]


def test_gemini_failure_falls_through_to_groq(clean_env, fake_post):
    set_keys(clean_env, "gemini", "groq")
    fake_post.add(PROVIDER_HOSTS["gemini"], error_response(500, "server error"))
    fake_post.add(PROVIDER_HOSTS["groq"], openai_style_success("hi from groq"))
    _install_gateway(clean_env)

    text, _ = ai_service.ask_ai("instructions", "hi")

    assert text == "hi from groq"
    assert len(fake_post.calls) == 2


def test_full_free_chain_falls_through_to_cloudflare(clean_env, fake_post):
    set_keys(clean_env, "gemini", "groq", "mistral", "cloudflare")
    fake_post.add(PROVIDER_HOSTS["gemini"], error_response(500))
    fake_post.add(PROVIDER_HOSTS["groq"], error_response(500))
    fake_post.add(PROVIDER_HOSTS["mistral"], error_response(500))
    fake_post.add(PROVIDER_HOSTS["cloudflare"], cloudflare_style_success("hi from cloudflare"))
    _install_gateway(clean_env)

    text, _ = ai_service.ask_ai("instructions", "hi")

    assert text == "hi from cloudflare"
    assert len(fake_post.calls) == 4


def test_openai_reached_only_after_all_four_free_providers_fail(clean_env, fake_post):
    set_keys(clean_env, "gemini", "groq", "mistral", "cloudflare", "openai")
    for name in ("gemini", "groq", "mistral", "cloudflare"):
        fake_post.add(PROVIDER_HOSTS[name], error_response(500))
    fake_post.add(PROVIDER_HOSTS["openai"], openai_style_success("hi from openai"))
    clean_env.setenv("PAID_FALLBACK_ENABLED", "true")
    _install_gateway(clean_env)

    text, _ = ai_service.ask_ai("instructions", "hi")

    assert text == "hi from openai"
    called_hosts = [PROVIDER_HOSTS[n] for n in ("gemini", "groq", "mistral", "cloudflare") if any(PROVIDER_HOSTS[n] in u for u in fake_post.calls)]
    assert called_hosts == [PROVIDER_HOSTS[n] for n in ("gemini", "groq", "mistral", "cloudflare")]


def test_successful_earlier_provider_prevents_openai_call(clean_env, fake_post):
    """A working free provider must stop the chain — OpenAI's endpoint must
    never even be hit."""
    set_keys(clean_env, "gemini", "openai")
    fake_post.add(PROVIDER_HOSTS["gemini"], gemini_style_success("hi from gemini"))
    _install_gateway(clean_env)

    text, _ = ai_service.ask_ai("instructions", "hi")

    assert text == "hi from gemini"
    assert not any(PROVIDER_HOSTS["openai"] in u for u in fake_post.calls)


def test_rate_limited_and_timing_out_providers_fall_through_gracefully(clean_env, fake_post):
    """Rate limits/timeouts must not crash the app — they fall through like
    any other failure, same as a plain 5xx."""
    set_keys(clean_env, "gemini", "groq", "mistral")
    fake_post.add(PROVIDER_HOSTS["gemini"], error_response(429, "rate limited", headers={"Retry-After": "1"}))
    fake_post.add(PROVIDER_HOSTS["groq"], requests.exceptions.Timeout("request timed out"))
    fake_post.add(PROVIDER_HOSTS["mistral"], openai_style_success("hi from mistral"))
    _install_gateway(clean_env)

    text, _ = ai_service.ask_ai("instructions", "hi")

    assert text == "hi from mistral"


def test_all_providers_failing_raises_ai_service_error_not_a_crash(clean_env, fake_post):
    set_keys(clean_env, "gemini", "groq")
    fake_post.add(PROVIDER_HOSTS["gemini"], error_response(500))
    fake_post.add(PROVIDER_HOSTS["groq"], error_response(500))
    _install_gateway(clean_env)

    with pytest.raises(ai_service.AIServiceError):
        ai_service.ask_ai("instructions", "hi")


def test_no_provider_configured_raises_missing_api_key_error(clean_env, fake_post):
    _install_gateway(clean_env)

    with pytest.raises(ai_service.MissingAPIKeyError):
        ai_service.ask_ai("instructions", "hi")


def test_disabled_providers_are_never_reached_even_when_only_key_present(clean_env, fake_post):
    """Cerebras/OpenRouter/DeepSeek keys may still be set (per policy, kept
    but out of automatic routing) — even so, with only a disabled
    provider's key present, generation must fail rather than silently
    calling a disabled provider."""
    clean_env.setenv("OPENROUTER_API_KEY", "test-openrouter-key-not-real")
    clean_env.setenv("DEEPSEEK_API_KEY", "test-deepseek-key-not-real")
    clean_env.setenv("CEREBRAS_API_KEY", "test-cerebras-key-not-real")
    _install_gateway(clean_env)

    with pytest.raises(ai_service.MissingAPIKeyError):
        ai_service.ask_ai("instructions", "hi")

    assert fake_post.calls == []


# --------------------------------------------------------------------------
# translate_text — same gateway, translation-preference routing
# --------------------------------------------------------------------------

def test_translate_text_uses_free_provider_first(clean_env, fake_post):
    set_keys(clean_env, "gemini", "openai")
    fake_post.add(PROVIDER_HOSTS["gemini"], gemini_style_success("Bonjour le monde"))
    _install_gateway(clean_env)

    translated = ai_service.translate_text("Hello world", "French")

    assert translated == "Bonjour le monde"
    assert not any(PROVIDER_HOSTS["openai"] in u for u in fake_post.calls)


def test_translate_text_falls_back_like_ask_ai(clean_env, fake_post):
    set_keys(clean_env, "gemini", "groq")
    fake_post.add(PROVIDER_HOSTS["gemini"], error_response(500))
    fake_post.add(PROVIDER_HOSTS["groq"], openai_style_success("Hallo Welt"))
    _install_gateway(clean_env)

    translated = ai_service.translate_text("hi", "German")

    assert translated == "Hallo Welt"


# --------------------------------------------------------------------------
# Caching — a repeated identical call must not re-hit any provider.
# --------------------------------------------------------------------------

def test_repeated_identical_call_is_served_from_gateway_cache(clean_env, fake_post):
    set_keys(clean_env, "gemini")
    fake_post.add(PROVIDER_HOSTS["gemini"], gemini_style_success("hi from gemini"))
    _install_gateway(clean_env)

    first, _ = ai_service.ask_ai("instructions", "hi")
    second, _ = ai_service.ask_ai("instructions", "hi")

    assert first == second == "hi from gemini"
    # only one real HTTP call — the second call was served from cache
    assert len(fake_post.calls) == 1

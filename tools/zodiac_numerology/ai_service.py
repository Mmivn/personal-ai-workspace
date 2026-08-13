"""Thin adapter around ALL_API's AIGateway.

This module's only job is turning zodiac/numerology instructions + a
message into a normalized (text, response_id) pair or a translated
string, via ALL_API's multi-provider gateway instead of talking to any
single provider directly. It knows nothing about zodiac signs,
numerology, or which language the user picked — the caller builds the
instructions/message text.

Provider selection, ordering, and fallback are entirely ALL_API's job
(see ALL_API/README.md and ALL_API/all_api/config.py):

    Gemini -> Groq -> Mistral -> Cloudflare Workers AI -> OpenAI (last resort)

Cerebras, OpenRouter, and DeepSeek are excluded from automatic routing.
OpenAI is only ever reached once every free provider ahead of it has
failed, rate-limited, or timed out. All credentials come from this
project's own .env, read by ALL_API's Config.from_env() (never
hardcoded, never printed).

Multi-turn continuation note: the previous OpenAI-only implementation
threaded conversations server-side via `previous_response_id` (the
Responses API's own feature). ALL_API's `generate()` is stateless and
provider-agnostic — a thread ID from one provider would be meaningless
to another after a fallback — so that server-side threading is not
carried over. `ask_ai` keeps the `previous_response_id` parameter for
backward compatibility with its callers (app.py, ui/common.py) and
still returns a response id slot, but no longer forwards it anywhere;
every call already sends the full set of facts/context it needs in
`user_input`, so no reading loses information as a result.
"""
import logging

from all_api import AIGateway
from all_api.exceptions import AllAPIError, ConfigurationError

_gateway = None
_logger = logging.getLogger(__name__)


class AIServiceError(Exception):
    """Base class for anything that went wrong talking to the AI."""


class MissingAPIKeyError(AIServiceError):
    """No AI provider is configured (no *_API_KEY set in the environment/.env)."""


class EmptyResponseError(AIServiceError):
    """The API call succeeded but returned no usable text."""


def _get_gateway():
    global _gateway
    if _gateway is None:
        _gateway = AIGateway()
    return _gateway


def reset_client():
    """Drop the cached gateway so a fresh one is built next call. Used by tests."""
    global _gateway
    _gateway = None


def ask_ai(instructions, user_input, previous_response_id=None):
    """Send one request through the AI gateway (Gemini -> Groq -> Mistral ->
    Cloudflare -> OpenAI last resort).

    Returns (text, response_id). Raises MissingAPIKeyError,
    EmptyResponseError, or AIServiceError (covers provider errors, an
    exhausted fallback chain, and network failures) on failure — never
    lets a raw provider/network exception or an API key leak to the
    caller. `previous_response_id` is accepted for signature
    compatibility but not forwarded — see module docstring.
    """
    gateway = _get_gateway()
    _logger.debug("[AI-CALL-LOG] MAIN GENERATION input_len=%d", len(user_input))

    try:
        result = gateway.generate(user_input, system_prompt=instructions)
    except ConfigurationError as error:
        raise MissingAPIKeyError(str(error)) from error
    except AllAPIError as error:
        raise AIServiceError(str(error)) from error
    except Exception as error:  # network/timeout/etc. — anything else the gateway can raise
        raise AIServiceError(str(error)) from error

    text = result.text
    if not text or not text.strip():
        raise EmptyResponseError("The AI returned an empty response")

    _logger.info(
        "[AI-CALL-LOG] MAIN GENERATION answered by provider=%s model=%s "
        "fallback_count=%d cached=%s used_paid_provider=%s",
        result.provider, result.model, result.fallback_count, result.cached, result.used_paid_provider,
    )
    return text, None


def translate_text(text, language):
    """Faithfully translate `text` into `language` (e.g. "Vietnamese").

    Uses the gateway's free-first translation routing (see
    AIGateway.translate), which prefers the same free providers before
    OpenAI. This is a mechanical translation of a reading already
    produced, not a new generation, and is deliberately stateless.
    Returns the translated text; raises the same exceptions as ask_ai.
    """
    gateway = _get_gateway()
    _logger.debug("[AI-CALL-LOG] TRANSLATE language=%s text_len=%d", language, len(text))

    try:
        result = gateway.translate(text, target_language=language)
    except ConfigurationError as error:
        raise MissingAPIKeyError(str(error)) from error
    except AllAPIError as error:
        raise AIServiceError(str(error)) from error
    except Exception as error:  # network/timeout/etc.
        raise AIServiceError(str(error)) from error

    translated = result.text
    if not translated or not translated.strip():
        raise EmptyResponseError("The AI returned an empty translation")

    _logger.info(
        "[AI-CALL-LOG] TRANSLATE answered by provider=%s model=%s "
        "fallback_count=%d cached=%s used_paid_provider=%s",
        result.provider, result.model, result.fallback_count, result.cached, result.used_paid_provider,
    )
    return translated

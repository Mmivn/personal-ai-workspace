# Zodiac & Numerology AI Assistant

A Python-computed **zodiac sign** and **numerology** engine paired with an
AI assistant that turns those facts into a friendly, personal read — in
Russian, English, or Vietnamese. Streamlit GUI (`streamlit_app.py`) and a
terminal app (`app.py`), both built on the same business logic.

> **Entertainment disclaimer.** Astrology and numerology are offered here
> as entertainment and a prompt for self-reflection, not as scientifically
> validated ways to predict the future.

## AI provider chain

AI calls go through [ALL_API](https://github.com/Mmivn/ALL_API), a
reusable multi-provider gateway with automatic fallback:

```
Gemini → Groq → Mistral → Cloudflare Workers AI → OpenAI (paid, last resort)
```

A free provider being down or rate-limited never breaks a reading — the
gateway silently moves to the next one; OpenAI is only ever reached once
every free provider ahead of it has failed. See `ai_service.py` (this
tool's only integration point with ALL_API) and that project's own README
for the full provider/config reference.

## Structure

```
streamlit_app.py     # Streamlit entry point (this tool's "main file" on Streamlit Cloud)
app.py                # Terminal front end — same engine, no browser needed
ai_service.py          # Adapter over ALL_API's AIGateway
models.py                # UserProfile / CompanionProfile
locales.py                 # ru/en/vi text
calculations/                # zodiac sign + numerology — pure functions, no AI
ui/                            # Streamlit widgets/screens (streamlit_app.py only)
tests/                           # pytest suite (AI calls mocked, no network/cost)
requirements.txt                   # extra deps beyond the workspace root's streamlit/python-dotenv
.streamlit/config.toml               # this app's own theme (script-scoped — see note below)
```

`calculations/`, `models.py`, `ai_service.py`, and `locales.py` have no
dependency on either front end.

This tool is intentionally self-contained (flat imports like `import
ai_service`, not `tools.zodiac_numerology.ai_service`) rather than a
`tools.*`-qualified package like `text_summarizer` — Streamlit adds a
script's own directory to `sys.path` when it runs it, so this works
unmodified both locally and on Streamlit Community Cloud without any
import rewrite of already-verified working code.

## Local setup

```bash
cd tools/zodiac_numerology
python3 -m venv .venv && source .venv/bin/activate   # or reuse the workspace's own .venv
pip install -r requirements.txt
# Provider keys: create a `.env` at the *workspace repo root* (not here) —
# ALL_API's Config.from_env() reads .env from the process's current working
# directory, which is the repo root when Streamlit runs this app from there.
streamlit run tools/zodiac_numerology/streamlit_app.py   # run from the repo root
```

## Tests

Kept self-contained under this tool's own `tests/`, not the workspace's
top-level `tests/`, so pytest's package-root sys.path insertion (via
`tests/__init__.py`) keeps resolving the flat imports above correctly.
Run explicitly (an explicit path bypasses the root `pyproject.toml`'s
`testpaths = ["tests"]`, which only points at the top-level tests dir):

```bash
python -m pytest tools/zodiac_numerology/tests
```

All AI calls are mocked — no network access, no real provider keys
needed, no cost.

## Deploying / updating on Streamlit Community Cloud

- **Main file path:** `tools/zodiac_numerology/streamlit_app.py`
- **Requirements file:** auto-discovered — `tools/zodiac_numerology/requirements.txt`
  (colocated with the main file)
- **Python version:** select 3.12 in this app's own Advanced settings —
  there is deliberately no repo-root `runtime.txt`, so this doesn't affect
  `lead_qualifier`/`text_summarizer`'s deployments.
- **Secrets** (Streamlit Cloud → this app → Settings → Secrets):
  `GEMINI_API_KEY`, `GROQ_API_KEY`, `MISTRAL_API_KEY`,
  `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `OPENAI_API_KEY` — see
  the repo-root `.env.example` for the full annotated list (placeholders
  only, never real values, never committed).
- Do **not** add `CEREBRAS_API_KEY`, `OPENROUTER_API_KEY`, or
  `DEEPSEEK_API_KEY` as secrets — ALL_API's `Config` only reads keys for
  providers actually listed in `PROVIDER_ORDER` (gemini, groq, mistral,
  cloudflare, openai), so those three stay excluded from automatic
  routing by construction.

To pick up a newer ALL_API version later, bump the pinned commit SHA in
`requirements.txt` — no other change needed.

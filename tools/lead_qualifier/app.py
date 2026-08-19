import logging
import os
import sys
from datetime import date
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv
from qdrant_client import QdrantClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.lead_qualifier.knowledge_base import load_knowledge_chunks  # noqa: E402
from tools.lead_qualifier.rag_assistant import (  # noqa: E402
    GeminiGenerationClient,
    GroqGenerationClient,
    answer_from_results,
    direct_answer_for_common_question,
)
from tools.lead_qualifier.semantic_search import GeminiEmbeddingClient  # noqa: E402
from tools.lead_qualifier.vector_store import index_chunks, search_vector_store  # noqa: E402

load_dotenv(PROJECT_ROOT / ".env")

# Diagnostic logging for the Telegram notification pipeline — never logs
# the bot token or chat ID themselves (see send_telegram below), only
# exception types/HTTP status codes/missing-key *names*/booleans, so
# these lines are safe to leave in Streamlit Cloud's app logs.
logger = logging.getLogger(__name__)


RESTAURANT_NAME = "FAMILY SECRET"
RESTAURANT_TAGLINE = "Table Reservations & Private Events"
HOT_GUEST_THRESHOLD = 10

TELEGRAM_SECRET_KEYS = ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")


def _configured_secret(key: str) -> str | None:
    """Read a config value by name — prefers Streamlit Cloud's
    st.secrets (the documented, primary way to configure this app;
    accessing a missing key always raises KeyError, never any other
    exception type, per Streamlit's own Secrets.__getitem__), falling
    back to a plain environment variable if st.secrets doesn't have it.
    The env var fallback covers the same value being set as a Streamlit
    Cloud *environment variable* instead of (or in addition to) a
    Secret, or running this app somewhere other than Streamlit Cloud.
    Returns None — never raises — if neither has a non-empty value."""
    try:
        value = st.secrets[key]
    except KeyError:
        value = None
    if not value:
        value = os.environ.get(key)
    return str(value) if value else None


def telegram_config_status() -> dict[str, bool]:
    """{"TELEGRAM_BOT_TOKEN": bool, "TELEGRAM_CHAT_ID": bool,
    "notifications_enabled": bool} — never the values themselves, only
    whether each is present. Safe to log or display."""
    status = {key: _configured_secret(key) is not None for key in TELEGRAM_SECRET_KEYS}
    status["notifications_enabled"] = all(status.values())
    return status


@st.cache_resource
def family_secret_assistant_services(
) -> tuple[GeminiEmbeddingClient, GeminiGenerationClient, QdrantClient]:
    """Build and cache the in-memory vector database used by the website assistant."""
    api_key = _configured_secret("GEMINI_API_KEY") or ""
    embedding_client = GeminiEmbeddingClient(api_key)
    generation_client = GeminiGenerationClient(api_key)
    qdrant = QdrantClient(":memory:")
    index_chunks(load_knowledge_chunks(), embedding_client, qdrant)
    return embedding_client, generation_client, qdrant


st.set_page_config(
    page_title=f"{RESTAURANT_NAME} | Reservations",
    page_icon="🍽️",
    layout="centered",
    initial_sidebar_state="collapsed",
)


st.markdown(
    """
<style>
:root {
    --ink: #0b0c0c;
    --panel: #111211;
    --panel-soft: #151614;
    --champagne: #cbb486;
    --champagne-light: #e4d5b6;
    --ivory: #f4f0e7;
    --muted: #97958f;
    --line: rgba(203, 180, 134, .24);
}

html, body, [data-testid="stAppViewContainer"], .stApp {
    background:
        radial-gradient(circle at 50% -18%, rgba(117, 98, 61, .20), transparent 38%),
        var(--ink);
    color: var(--ivory);
}

header[data-testid="stHeader"] {
    background: transparent;
}

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

.block-container {
    max-width: 760px;
    padding-top: 1rem;
    padding-bottom: 3rem;
}

.fs-hero {
    text-align: center;
    padding: 54px 20px 32px;
}

.fs-mark {
    color: var(--champagne);
    font-size: 14px;
    letter-spacing: 8px;
    margin-bottom: 18px;
}

.fs-name {
    color: var(--ivory);
    font-family: Georgia, "Times New Roman", serif;
    font-size: clamp(46px, 8vw, 68px);
    font-weight: 400;
    line-height: .90;
    letter-spacing: .13em;
}

.fs-type {
    color: var(--champagne);
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 2.8px;
    margin-top: 25px;
}

.fs-copy {
    color: #aaa79f;
    font-family: Georgia, "Times New Roman", serif;
    font-size: 17px;
    font-style: italic;
    line-height: 1.55;
    margin: 22px auto 0;
    max-width: 520px;
}

.fs-line {
    width: 42px;
    height: 1px;
    background: var(--champagne);
    margin: 30px auto 0;
}

.fs-reservation {
    text-align: center;
    margin: 18px 0 22px;
}

.fs-reservation-title {
    color: var(--ivory);
    font-family: Georgia, "Times New Roman", serif;
    font-size: 28px;
    font-weight: 400;
    letter-spacing: .5px;
}

.fs-reservation-copy {
    color: var(--muted);
    font-size: 12px;
    line-height: 1.6;
    max-width: 500px;
    margin: 8px auto 0;
}

div[data-testid="stForm"] {
    background: linear-gradient(145deg, rgba(21,22,20,.98), rgba(14,15,14,.98));
    border: 1px solid var(--line);
    border-radius: 2px;
    padding: 28px 30px 24px;
    box-shadow: 0 28px 80px rgba(0,0,0,.28);
}

div[data-testid="stForm"] p strong {
    color: #bcb49f;
    font-size: 9px;
    font-weight: 600;
    letter-spacing: 1.7px;
    text-transform: uppercase;
}

div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div {
    border-radius: 1px !important;
}

div[data-testid="stForm"] input,
div[data-testid="stForm"] textarea {
    background-color: #eeebe4 !important;
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
    caret-color: #111111 !important;
    border-color: transparent !important;
    font-weight: 500 !important;
}

div[data-testid="stForm"] input::placeholder,
div[data-testid="stForm"] textarea::placeholder {
    color: #77746e !important;
    -webkit-text-fill-color: #77746e !important;
}

div[data-testid="stForm"] input:focus,
div[data-testid="stForm"] textarea:focus {
    box-shadow: 0 0 0 1px var(--champagne) !important;
}

div[data-testid="stFormSubmitButton"] button {
    background: var(--champagne) !important;
    color: #10110f !important;
    border: 1px solid var(--champagne) !important;
    border-radius: 1px !important;
    min-height: 48px;
    font-size: 10px !important;
    font-weight: 700 !important;
    letter-spacing: 2px;
    text-transform: uppercase;
}

div[data-testid="stFormSubmitButton"] button:hover {
    background: var(--champagne-light) !important;
    border-color: var(--champagne-light) !important;
}

div[data-testid="stAlert"] {
    border-radius: 2px;
}

div[data-testid="stChatMessage"] {
    background: rgba(203, 180, 134, .07);
    border: 1px solid var(--line);
    border-radius: 2px;
    color: var(--ivory) !important;
    padding: 18px 20px;
}

div[data-testid="stChatMessage"] p,
div[data-testid="stChatMessage"] li,
div[data-testid="stChatMessage"] span {
    color: var(--ivory) !important;
}

hr {
    border-color: var(--line) !important;
    margin: 48px 0 34px !important;
}

.fs-concierge-kicker {
    color: var(--champagne);
    font-size: 9px;
    letter-spacing: 2.4px;
    margin-bottom: 9px;
}

.fs-footer {
    text-align: center;
    padding: 48px 15px 14px;
}

.fs-footer-name {
    color: var(--champagne);
    font-family: Georgia, "Times New Roman", serif;
    font-size: 16px;
    letter-spacing: 4px;
}

.fs-footer-type {
    color: #777169;
    font-size: 10px;
    letter-spacing: 1.6px;
    margin-top: 12px;
}

.fs-footer-note {
    color: #625e59;
    font-size: 11px;
    margin-top: 20px;
}

@media (max-width: 700px) {
    .block-container {
        padding-left: 16px;
        padding-right: 16px;
        padding-top: 0.5rem;
    }

    .fs-hero {
        padding-top: 38px;
        padding-bottom: 24px;
    }

    .fs-name {
        font-size: 44px;
        letter-spacing: 4px;
    }

    .fs-type {
        font-size: 9px;
        letter-spacing: 1.4px;
    }

    .fs-copy {
        font-size: 16px;
    }

    .fs-reservation-title {
        font-size: 27px;
    }

    div[data-testid="stForm"] {
        padding: 22px 18px 18px;
    }
}
</style>
    """,
    unsafe_allow_html=True,
)


def qualify_request(message: str, guests: int) -> str:
    text = message.lower()

    hot_words = [
        "urgent",
        "asap",
        "today",
        "tonight",
        "private",
        "private room",
        "event",
        "birthday",
        "wedding",
        "corporate",
        "anniversary",
        "celebration",
        "party",
        "срочно",
        "сегодня",
        "вечером",
        "банкет",
        "день рождения",
        "свадьба",
        "мероприятие",
        "корпоратив",
        "юбилей",
        "праздник",
    ]

    if guests >= HOT_GUEST_THRESHOLD:
        return "HOT"

    if any(word in text for word in hot_words):
        return "HOT"

    if guests >= 5:
        return "WARM"

    return "NORMAL"


def send_telegram(
    name: str,
    contact: str,
    reservation_date: str,
    reservation_time: str,
    guests: int,
    request_text: str,
    priority: str,
) -> None:
    status = telegram_config_status()
    # Booleans only, never the values — this is the line to check in
    # Streamlit Cloud's app logs (Manage app -> ... -> logs) to see
    # whether a just-saved Secret actually took effect, independent of
    # whatever the UI is showing.
    logger.info(
        "Telegram notification config check: TELEGRAM_BOT_TOKEN configured=%s, "
        "TELEGRAM_CHAT_ID configured=%s, notifications enabled=%s",
        status["TELEGRAM_BOT_TOKEN"],
        status["TELEGRAM_CHAT_ID"],
        status["notifications_enabled"],
    )
    if not status["notifications_enabled"]:
        missing = [key for key in TELEGRAM_SECRET_KEYS if not status[key]]
        # `missing` is a list of *key names* (e.g. ["TELEGRAM_CHAT_ID"]),
        # never a secret value — safe to log. Raised as KeyError so the
        # caller's existing `except KeyError` -> "notifications
        # unavailable" handling is unchanged.
        logger.error("Telegram notification config missing: %s", ", ".join(missing))
        raise KeyError(", ".join(missing))

    token = _configured_secret("TELEGRAM_BOT_TOKEN")
    chat_id = _configured_secret("TELEGRAM_CHAT_ID")

    # Use st.context.locale to choose language for the notification text
    locale = (getattr(st, "context", None) and getattr(st.context, "locale", "")) or ""
    lang = "ru" if locale.startswith("ru") else "en"

    translations = {
        "en": {
            "priority_hot": "🔥 HIGH PRIORITY",
            "priority_warm": "🟠 MEDIUM PRIORITY",
            "priority_normal": "🔔 NORMAL REQUEST",
            "action_hot": "Contact this guest as soon as possible.",
            "action_warm": "Follow up with this guest.",
            "action_normal": "Confirm availability with the guest.",
            "new_request": "NEW RESERVATION REQUEST",
            "special_none": "None",
            "guest_label": "Guest",
            "phone_label": "Phone / WhatsApp",
            "date_label": "Date",
            "time_label": "Time",
            "guests_label": "Guests",
            "recommended": "Recommended action",
            "branding": "FAMILY SECRET",
            "label_requests": "Special requests",
        },
        "ru": {
            "priority_hot": "🔥 ВЫСОКИЙ ПРИОРИТЕТ",
            "priority_warm": "🟠 СРЕДНИЙ ПРИОРИТЕТ",
            "priority_normal": "🔔 ОБЫЧНАЯ ЗАЯВКА",
            "action_hot": "Связаться с гостем как можно скорее.",
            "action_warm": "Связаться с гостем в ближайшее время.",
            "action_normal": "Подтвердить наличие мест.",
            "new_request": "НОВАЯ ЗАЯВКА",
            "special_none": "Нет",
            "guest_label": "Гость",
            "phone_label": "Телефон",
            "date_label": "Дата",
            "time_label": "Время",
            "guests_label": "Гостей",
            "recommended": "Рекомендация",
            "branding": "FAMILY SECRET",
            "label_requests": "Особые пожелания",
        },
    }

    # Build a bilingual (EN | RU) telegram message so recipients see both languages.
    tr_en = translations["en"]
    tr_ru = translations["ru"]

    if priority == "HOT":
        priority_en = tr_en["priority_hot"]
        priority_ru = tr_ru["priority_hot"]
        action_en = tr_en["action_hot"]
        action_ru = tr_ru["action_hot"]

    elif priority == "WARM":
        priority_en = tr_en["priority_warm"]
        priority_ru = tr_ru["priority_warm"]
        action_en = tr_en["action_warm"]
        action_ru = tr_ru["action_warm"]

    else:
        priority_en = tr_en["priority_normal"]
        priority_ru = tr_ru["priority_normal"]
        action_en = tr_en["action_normal"]
        action_ru = tr_ru["action_normal"]

    special_text = request_text or f"{tr_en['special_none']} | {tr_ru['special_none']}"

    message = (
        f"🍽️ {RESTAURANT_NAME}\n"
        f"{tr_en['new_request']} | {tr_ru['new_request']}\n\n"
        f"{priority_en} | {priority_ru}\n\n"
        f"👤 {tr_en['guest_label']} | {tr_ru['guest_label']}: {name}\n"
        f"📱 {tr_en['phone_label']} | {tr_ru['phone_label']}: {contact}\n\n"
        f"📅 {tr_en['date_label']} | {tr_ru['date_label']}: {reservation_date}\n"
        f"🕐 {tr_en['time_label']} | {tr_ru['time_label']}: {reservation_time}\n"
        f"👥 {tr_en['guests_label']} | {tr_ru['guests_label']}: {guests}\n\n"
        f"💬 {tr_en['label_requests'].capitalize()} | {tr_ru['label_requests']}:\n"
        f"{special_text}\n\n"
        f"📌 {tr_en['recommended']} | {tr_ru['recommended']}:\n"
        f"{action_en} | {action_ru}"
    )

    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={
            "chat_id": chat_id,
            "text": message,
        },
        timeout=10,
    )

    response.raise_for_status()

    logger.info("Telegram reservation notification sent (status=%s)", response.status_code)


# Determine user's locale (use browser/Streamlit context if available)
_locale = (getattr(st, "context", None) and getattr(st.context, "locale", "")) or ""
_lang = "ru" if _locale.startswith("ru") else "en"

_translations_ui = {
    "en": {
        "mark": "✦",
        "name_lines": "FAMILY<br>SECRET",
        "type": "RESTAURANT • PRIVATE DINING • EVENTS",
        "copy": "Intimate dining. Memorable evenings.",
        "reservation_title": "Reserve Your Table",
        "reservation_copy": "Leave your details. We will personally confirm your table.",
        "label_name": "Your name",
        "placeholder_name": "John Smith",
        "label_contact": "Phone or WhatsApp",
        "placeholder_contact": "+1 555 123 4567",
        "label_date": "Reservation date",
        "label_time": "Preferred time",
        "label_guests": "Number of guests",
        "label_requests": "Special requests",
        "placeholder_requests": "Birthday, private dining, dietary requirements...",
        "submit": "Request a reservation",
        "warning_missing": "Please enter your name and phone or WhatsApp number.",
        "success_received": "✓ Your reservation request has been received.",
        "info_followup": f"The {RESTAURANT_NAME} team will contact you shortly to confirm your reservation.",
        "error_send": "We couldn't send your request right now. Please try again in a moment.",
        "error_unavailable": "Reservation notifications are temporarily unavailable.",
        "footer_name": RESTAURANT_NAME,
        "footer_type": "RESERVATIONS • PRIVATE DINING • SPECIAL EVENTS",
        "footer_note": "Reservations are confirmed after our team contacts you.",
    },
    "ru": {
        "mark": "✦",
        "name_lines": "FAMILY<br>SECRET",
        "type": "РЕСТОРАН • ЧАСТНЫЕ УЖИНЫ • МЕРОПРИЯТИЯ",
        "copy": "Камерные ужины. Незабываемые вечера.",
        "reservation_title": "Забронировать столик",
        "reservation_copy": "Оставьте контакты — мы лично подтвердим ваш столик.",
        "label_name": "Ваше имя",
        "placeholder_name": "Иван Иванов",
        "label_contact": "Телефон или WhatsApp",
        "placeholder_contact": "+7 900 000 0000",
        "label_date": "Дата бронирования",
        "label_time": "Желаемое время",
        "label_guests": "Количество гостей",
        "label_requests": "Особые пожелания",
        "placeholder_requests": "День рождения, отдельный зал, питание, особый повод...",
        "submit": "Отправить заявку",
        "warning_missing": "Укажите имя и номер телефона или WhatsApp.",
        "success_received": "✓ Ваша заявка на бронирование получена.",
        "info_followup": f"Команда {RESTAURANT_NAME} скоро свяжется с вами для подтверждения.",
        "error_send": "Не удалось отправить заявку. Попробуйте ещё раз через минуту.",
        "error_unavailable": "Уведомления временно недоступны.",
        "footer_name": RESTAURANT_NAME,
        "footer_type": "БРОНИРОВАНИЕ • ЧАСТНЫЕ УЖИНЫ • МЕРОПРИЯТИЯ",
        "footer_note": "Бронирование считается подтверждённым после связи с нашей командой.",
    },
}

_tr_en = _translations_ui["en"]
_tr_ru = _translations_ui["ru"]

def bi(key: str) -> str:
    """Return bilingual string: English | Русский for the given translation key."""
    return f"{_tr_en[key]} | {_tr_ru[key]}"

hero_html = (
    '<section class="fs-hero">'
    f'<div class="fs-mark">{_tr_en["mark"]}</div>'
    f'<div class="fs-name">{_tr_en["name_lines"]}</div>'
    '<div class="fs-type">'
    'PRIVATE DINING · NHA TRANG'
    '</div>'
    '<div class="fs-copy">'
    f'{_tr_en["copy"]}<br>{_tr_ru["copy"]}'
    '</div>'
    '<div class="fs-line"></div>'
    '</section>'
)

st.markdown(hero_html, unsafe_allow_html=True)

reservation_intro = (
    '<section class="fs-reservation">'
    '<div class="fs-reservation-title">'
    f'{_tr_en["reservation_title"]} · {_tr_ru["reservation_title"]}'
    '</div>'
    '<div class="fs-reservation-copy">'
    f'{_tr_en["reservation_copy"]}<br>{_tr_ru["reservation_copy"]}'
    '</div>'
    '</section>'
)

st.markdown(reservation_intro, unsafe_allow_html=True)


with st.form("family_secret_reservation"):
    # Visible bilingual labels above the actual Streamlit widgets. Native widgets
    # have unique keys and are used as authoritative inputs (hidden labels via
    # `label_visibility="collapsed"`) so Streamlit state and backend logic remain.
    st.markdown("**NAME · ИМЯ**")
    name = st.text_input("Hidden name (fs)", placeholder="John Smith | Иван Иванов", key="fs_name", label_visibility="collapsed")

    st.markdown("**PHONE / WHATSAPP · ТЕЛЕФОН**")
    contact = st.text_input("Hidden contact (fs)", placeholder="+1 555 123 4567 | +7 900 000 0000", key="fs_contact", label_visibility="collapsed")

    date_col, time_col = st.columns(2)
    with date_col:
        st.markdown("**DATE · ДАТА**")
        reservation_date = st.date_input("Hidden date (fs)", min_value=date.today(), key="fs_date", label_visibility="collapsed")
    with time_col:
        st.markdown("**TIME · ВРЕМЯ**")
        reservation_time = st.time_input("Hidden time (fs)", key="fs_time", label_visibility="collapsed")

    st.markdown("**GUESTS · ГОСТИ**")
    guests = st.number_input("Hidden guests (fs)", min_value=1, max_value=200, value=2, step=1, key="fs_guests", label_visibility="collapsed")

    st.markdown("**OCCASION / REQUESTS · ПОЖЕЛАНИЯ**")
    request_text = st.text_area("Hidden request (fs)", placeholder="Birthday, private dining, dietary requirements... | День рождения, отдельный зал, питание, особый повод...", height=130, key="fs_request", label_visibility="collapsed")

    submitted = st.form_submit_button(bi("submit"), use_container_width=True, key="fs_submit")


if submitted:
    if not name.strip() or not contact.strip():
        st.warning(bi("warning_missing"))

    else:
        priority = qualify_request(
            request_text,
            int(guests),
        )

        try:
            send_telegram(
                name=name,
                contact=contact,
                reservation_date=reservation_date.strftime("%d %B %Y"),
                reservation_time=reservation_time.strftime("%H:%M"),
                guests=int(guests),
                request_text=request_text,
                priority=priority,
            )

            st.success(bi("success_received"))

            st.info(bi("info_followup")) 

        except requests.RequestException as exc:
            # Deliberately never logs str(exc)/repr(exc): the request
            # URL contains the bot token
            # (api.telegram.org/bot<TOKEN>/sendMessage), and requests'
            # own exception messages typically include the URL they
            # failed on. Only the exception's class name and (if the
            # failure was an HTTP error response) its status code are
            # logged — enough to diagnose "network down" vs "Telegram
            # rejected the request" without ever risking the token.
            status = getattr(getattr(exc, "response", None), "status_code", None)
            logger.error(
                "Telegram sendMessage request failed: %s (status=%s)", type(exc).__name__, status
            )
            st.error(bi("error_send"))

        except KeyError:
            # Already logged (with the missing key *name*, never a
            # secret value) inside send_telegram before this re-raised.
            st.error(bi("error_unavailable"))


st.markdown("---")
st.markdown(
    """
    <section class="fs-reservation">
      <div class="fs-concierge-kicker">PRIVATE CONCIERGE · ЛИЧНЫЙ КОНСЬЕРЖ</div>
      <div class="fs-reservation-title">Ask Family Secret</div>
      <div class="fs-reservation-copy">
        Hours, menu, children or a private occasion.<br>
        Часы работы, меню, дети или частное мероприятие.
      </div>
    </section>
    """,
    unsafe_allow_html=True,
)

with st.form("family_secret_assistant"):
    assistant_question = st.text_input(
        "QUESTION · ВОПРОС",
        placeholder="When does the kitchen close? | Во сколько закрывается кухня?",
        key="fs_assistant_question",
    )
    assistant_submitted = st.form_submit_button(
        "ASK CONCIERGE · СПРОСИТЬ",
        use_container_width=True,
        key="fs_assistant_submit",
    )

if assistant_submitted:
    if not assistant_question.strip():
        st.warning("Please enter a question. | Пожалуйста, задайте вопрос.")
    else:
        with st.spinner("Searching Family Secret knowledge…"):
            try:
                direct_answer = direct_answer_for_common_question(assistant_question)
                if direct_answer:
                    assistant_text = direct_answer
                else:
                    try:
                        embedding_client, generation_client, qdrant = (
                            family_secret_assistant_services()
                        )
                        search_results = search_vector_store(
                            assistant_question,
                            embedding_client,
                            qdrant,
                            limit=3,
                        )
                        assistant_answer = answer_from_results(
                            assistant_question,
                            search_results,
                            generation_client,
                        )
                        assistant_text = assistant_answer.text
                    except (requests.RequestException, ValueError, KeyError):
                        logger.warning(
                            "Primary Family Secret assistant unavailable; using Groq fallback",
                            exc_info=True,
                        )
                        fallback_context = "\n\n".join(
                            f"{chunk.heading}\n{chunk.content}"
                            for chunk in load_knowledge_chunks()
                        )
                        assistant_text = GroqGenerationClient(
                            _configured_secret("GROQ_API_KEY") or ""
                        ).generate(assistant_question, fallback_context)
                with st.chat_message("assistant"):
                    st.markdown(assistant_text)
            except (requests.RequestException, ValueError, KeyError):
                logger.exception("Family Secret assistant request failed")
                st.error(
                    "The assistant is temporarily unavailable. | "
                    "Ассистент временно недоступен."
                )


footer_html = (
    '<footer class="fs-footer">'
    f'<div class="fs-footer-name">{RESTAURANT_NAME}</div>'
    '<div class="fs-footer-type">'
    f'{bi("footer_type")}'
    '</div>'
    '<div class="fs-footer-note">'
    f'{bi("footer_note")}'
    '</div>'
    '</footer>'
)

st.markdown(footer_html, unsafe_allow_html=True)

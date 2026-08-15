import logging
from datetime import date

import requests
import streamlit as st

# Diagnostic logging for the Telegram notification pipeline — never logs
# the bot token or chat ID themselves (see send_telegram below), only
# exception types/HTTP status codes/missing-key *names*, so these lines
# are safe to leave in Streamlit Cloud's app logs.
logger = logging.getLogger(__name__)


RESTAURANT_NAME = "FAMILY SECRET"
RESTAURANT_TAGLINE = "Table Reservations & Private Events"
HOT_GUEST_THRESHOLD = 10


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
    --bg: #090909;
    --card: #121211;
    --gold: #c5a263;
    --gold-light: #dfc083;
    --text: #f4efe7;
    --muted: #aaa399;
    --border: #343028;
}

html, body, [data-testid="stAppViewContainer"], .stApp {
    background:
        radial-gradient(circle at 50% -10%, #312a20 0%, #151310 28%, #090909 65%);
    color: var(--text);
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
    max-width: 880px;
    padding-top: 2rem;
    padding-bottom: 5rem;
}

.fs-hero {
    text-align: center;
    padding: 75px 20px 55px 20px;
}

.fs-mark {
    color: var(--gold);
    font-size: 24px;
    letter-spacing: 12px;
    margin-bottom: 20px;
}

.fs-name {
    color: var(--text);
    font-family: Georgia, "Times New Roman", serif;
    font-size: 64px;
    font-weight: 400;
    line-height: 1.02;
    letter-spacing: 10px;
}

.fs-type {
    color: var(--gold);
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 3px;
    margin-top: 24px;
}

.fs-copy {
    color: #c4bdb3;
    font-family: Georgia, "Times New Roman", serif;
    font-size: 18px;
    font-style: italic;
    line-height: 1.7;
    margin: 34px auto 0 auto;
    max-width: 620px;
}

.fs-line {
    width: 72px;
    height: 1px;
    background: var(--gold);
    margin: 44px auto 0 auto;
}

.fs-reservation {
    text-align: center;
    margin: 30px 0 30px 0;
}

.fs-reservation-title {
    color: var(--text);
    font-family: Georgia, "Times New Roman", serif;
    font-size: 33px;
    letter-spacing: 1px;
}

.fs-reservation-copy {
    color: var(--muted);
    font-size: 14px;
    line-height: 1.7;
    max-width: 620px;
    margin: 12px auto 0 auto;
}

div[data-testid="stForm"] {
    background:
        linear-gradient(180deg, rgba(24,23,20,.98), rgba(16,16,15,.98));
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 36px;
    box-shadow: 0 24px 70px rgba(0,0,0,.30);
}

div[data-testid="stTextInput"] label,
div[data-testid="stTextArea"] label,
div[data-testid="stDateInput"] label,
div[data-testid="stTimeInput"] label,
div[data-testid="stNumberInput"] label {
    color: #d6c7ae !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    letter-spacing: 1.4px;
    text-transform: uppercase;
}

div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div {
    border-radius: 5px !important;
}

/* Textarea & input colors that adapt to user's color scheme */
@media (prefers-color-scheme: dark) {
    div[data-baseweb="input"] input,
    div[data-baseweb="textarea"] textarea,
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stDateInput"] input,
    div[data-testid="stTimeInput"] input {
        background-color: #f4f1eb !important;
        color: #111111 !important;
        -webkit-text-fill-color: #111111 !important;
        caret-color: #111111 !important;
        opacity: 1 !important;
        font-weight: 500 !important;
    }

    div[data-baseweb="input"] input::placeholder,
    div[data-baseweb="textarea"] textarea::placeholder {
        color: #777777 !important;
        -webkit-text-fill-color: #777777 !important;
        opacity: 1 !important;
    }

    /* autofill styling */
    input:-webkit-autofill,
    textarea:-webkit-autofill {
        -webkit-text-fill-color: #111111 !important;
        caret-color: #111111 !important;
        box-shadow: 0 0 0px 1000px #f4f1eb inset !important;
    }
}

@media (prefers-color-scheme: light) {
    div[data-baseweb="input"] input,
    div[data-baseweb="textarea"] textarea,
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input,
    div[data-testid="stDateInput"] input,
    div[data-testid="stTimeInput"] input {
        background-color: #ffffff !important;
        color: #111111 !important;
        -webkit-text-fill-color: #111111 !important;
        caret-color: #c5a263 !important;
        opacity: 1 !important;
        font-weight: 500 !important;
    }

    div[data-baseweb="input"] input::placeholder,
    div[data-baseweb="textarea"] textarea::placeholder {
        color: #666666 !important;
        -webkit-text-fill-color: #666666 !important;
        opacity: 1 !important;
    }

    input:-webkit-autofill,
    textarea:-webkit-autofill {
        -webkit-text-fill-color: #111111 !important;
        caret-color: #c5a263 !important;
        box-shadow: 0 0 0px 1000px #ffffff inset !important;
    }
}

/* Ensure the Special Requests textarea always shows typed text and caret
   in both dark and light modes. Selectors verified against the live DOM:
   textarea[aria-label="Особые пожелания"] (Russian) and
   textarea[aria-label="Special requests"] (English). */
textarea[aria-label="Особые пожелания"],
textarea[aria-label="Special requests"],
div[data-testid="stTextArea"] textarea {
    background-color: #f4f1eb !important;
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
    caret-color: #111111 !important;
    border: 1px solid #b8aa92 !important;
    border-radius: 6px !important;
    padding: 10px !important;
    box-shadow: none !important;
}

@media (prefers-color-scheme: light) {
    textarea[aria-label="Особые пожелания"],
    textarea[aria-label="Special requests"],
    div[data-testid="stTextArea"] textarea {
        background-color: #ffffff !important;
        color: #111111 !important;
        -webkit-text-fill-color: #111111 !important;
        caret-color: #c5a263 !important;
    }
}

@media (prefers-color-scheme: dark) {
    textarea[aria-label="Особые пожелания"],
    textarea[aria-label="Special requests"],
    div[data-testid="stTextArea"] textarea {
        background-color: #f4f1eb !important;
        color: #111111 !important;
        -webkit-text-fill-color: #111111 !important;
        caret-color: #111111 !important;
    }
}

textarea::selection {
    background: rgba(197, 162, 99, 0.2) !important;
    color: #111111 !important;
}

textarea:focus {
    outline: 2px solid rgba(197,162,99,0.18) !important;
}

/* Strong override for the textarea instance observed in the DOM during testing.
   This targets the emotion-generated classes present at runtime and ensures
   visible text/caret/background. Verified selector: class="st-emotion-cache-i9mjlf e1wz7dbj2" */
textarea.st-emotion-cache-i9mjlf.e1wz7dbj2 {
    background-color: #f4f1eb !important;
    color: #111111 !important;
    -webkit-text-fill-color: #111111 !important;
    caret-color: #111111 !important;
}

div[data-testid="stFormSubmitButton"] button {
    background: linear-gradient(90deg, #ad8b53, #c9a867) !important;
    color: #0b0b0b !important;
    border: 1px solid #d2b477 !important;
    border-radius: 4px !important;
    min-height: 54px;
    font-size: 12px !important;
    font-weight: 800 !important;
    letter-spacing: 1.8px;
    text-transform: uppercase;
}

div[data-testid="stFormSubmitButton"] button:hover {
    background: linear-gradient(90deg, #c3a061, #dfbf7f) !important;
    border-color: #ecd18f !important;
}

div[data-testid="stAlert"] {
    border-radius: 6px;
}

.fs-footer {
    text-align: center;
    padding: 58px 15px 20px 15px;
}

.fs-footer-name {
    color: var(--gold);
    font-family: Georgia, "Times New Roman", serif;
    font-size: 19px;
    letter-spacing: 5px;
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
        padding-top: 52px;
        padding-bottom: 38px;
    }

    .fs-name {
        font-size: 39px;
        letter-spacing: 5px;
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
        padding: 22px;
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
    try:
        token = st.secrets["TELEGRAM_BOT_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]
    except KeyError as exc:
        # exc here is just the missing dict *key name* (e.g.
        # "TELEGRAM_BOT_TOKEN") — never a secret value — so it's safe to
        # log. This is what tells you *which* secret is missing from
        # Streamlit Cloud's app secrets instead of just "something's
        # wrong".
        logger.error("Telegram notification config missing from st.secrets: %s", exc)
        raise

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


hero_html = (
    '<section class="fs-hero">'
    '<div class="fs-mark">✦</div>'
    '<div class="fs-name">FAMILY<br>SECRET</div>'
    '<div class="fs-type">'
    'RESTAURANT • PRIVATE DINING • EVENTS | РЕСТОРАН • ЧАСТНЫЕ УЖИНЫ • МЕРОПРИЯТИЯ'
    '</div>'
    '<div class="fs-copy">'
    'Good food brings people together. | Хорошая еда объединяет людей.<br>'
    'Great evenings become family secrets. | Лучшие вечера становятся семейными секретами.'
    '</div>'
    '<div class="fs-line"></div>'
    '</section>'
)

# Determine user's locale (use browser/Streamlit context if available)
_locale = (getattr(st, "context", None) and getattr(st.context, "locale", "")) or ""
_lang = "ru" if _locale.startswith("ru") else "en"

_translations_ui = {
    "en": {
        "mark": "✦",
        "name_lines": "FAMILY<br>SECRET",
        "type": "RESTAURANT • PRIVATE DINING • EVENTS",
        "copy": "Good food brings people together.<br>Great evenings become family secrets.",
        "reservation_title": "Reserve Your Table",
        "reservation_copy": "Choose your preferred date and time and send us your request. Our team will contact you to confirm availability.",
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
        "copy": "Хорошая еда объединяет людей.<br>Лучшие вечера становятся семейными секретами.",
        "reservation_title": "Забронировать столик",
        "reservation_copy": "Выберите дату и время и отправьте заявку. Наша команда свяжется с вами для подтверждения.",
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
    f'{_tr_en["type"]} | {_tr_ru["type"]}'
    '</div>'
    '<div class="fs-copy">'
    f'{_tr_en["copy"]} | {_tr_ru["copy"]}'
    '</div>'
    '<div class="fs-line"></div>'
    '</section>'
)

st.markdown(hero_html, unsafe_allow_html=True)

reservation_intro = (
    '<section class="fs-reservation">'
    '<div class="fs-reservation-title">'
    f'{bi("reservation_title")}'
    '</div>'
    '<div class="fs-reservation-copy">'
    f'{bi("reservation_copy")}'
    '</div>'
    '</section>'
)

st.markdown(reservation_intro, unsafe_allow_html=True)


with st.form("family_secret_reservation"):
    # Visible bilingual labels above the actual Streamlit widgets. Native widgets
    # have unique keys and are used as authoritative inputs (hidden labels via
    # `label_visibility="collapsed"`) so Streamlit state and backend logic remain.
    st.markdown("**YOUR NAME | ВАШЕ ИМЯ**")
    name = st.text_input("Hidden name (fs)", placeholder="John Smith | Иван Иванов", key="fs_name", label_visibility="collapsed")

    st.markdown("**PHONE OR WHATSAPP | ТЕЛЕФОН ИЛИ WHATSAPP**")
    contact = st.text_input("Hidden contact (fs)", placeholder="+1 555 123 4567 | +7 900 000 0000", key="fs_contact", label_visibility="collapsed")

    date_col, time_col = st.columns(2)
    with date_col:
        st.markdown("**RESERVATION DATE | ДАТА БРОНИРОВАНИЯ**")
        reservation_date = st.date_input("Hidden date (fs)", min_value=date.today(), key="fs_date", label_visibility="collapsed")
    with time_col:
        st.markdown("**PREFERRED TIME | ЖЕЛАЕМОЕ ВРЕМЯ**")
        reservation_time = st.time_input("Hidden time (fs)", key="fs_time", label_visibility="collapsed")

    st.markdown("**NUMBER OF GUESTS | КОЛИЧЕСТВО ГОСТЕЙ**")
    guests = st.number_input("Hidden guests (fs)", min_value=1, max_value=200, value=2, step=1, key="fs_guests", label_visibility="collapsed")

    st.markdown("**SPECIAL REQUESTS | ОСОБЫЕ ПОЖЕЛАНИЯ**")
    request_text = st.text_area("Hidden request (fs)", placeholder="Birthday, private dining, dietary requirements... | День рождения, отдельный зал, питание, особый повод...", height=130, key="fs_request", label_visibility="collapsed")

    st.markdown("**REQUEST RESERVATION | ОТПРАВИТЬ ЗАЯВКУ**")
    # Was a leftover debug placeholder ("Hidden submit (fs)") instead of
    # the real bilingual call-to-action — bi("submit") is the same
    # translation dict every other customer-facing string on this page
    # already goes through.
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
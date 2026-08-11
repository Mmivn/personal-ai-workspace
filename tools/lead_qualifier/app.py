from datetime import date

import requests
import streamlit as st


RESTAURANT_NAME = "FAMILY SECRET"
HOT_GUEST_THRESHOLD = 10


st.set_page_config(
    page_title="FAMILY SECRET | Reservations",
    page_icon="✦",
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
    background-color: #f4f1eb !important;
    border: 1px solid #b8aa92 !important;
    border-radius: 5px !important;
}

div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea,
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input,
div[data-testid="stDateInput"] input,
div[data-testid="stTimeInput"] input {
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
    token = st.secrets["TELEGRAM_BOT_TOKEN"]
    chat_id = st.secrets["TELEGRAM_CHAT_ID"]

    if priority == "HOT":
        priority_label = "🔥 HIGH PRIORITY | ВЫСОКИЙ ПРИОРИТЕТ"
        action = "Contact this guest as soon as possible. | Связаться с гостем как можно скорее."

    elif priority == "WARM":
        priority_label = "🟠 MEDIUM PRIORITY | СРЕДНИЙ ПРИОРИТЕТ"
        action = "Follow up with this guest soon. | Связаться с гостем в ближайшее время."

    else:
        priority_label = "🔔 NORMAL REQUEST | ОБЫЧНАЯ ЗАЯВКА"
        action = "Confirm availability with this guest. | Подтвердить наличие мест."

    message = (
        "✦ FAMILY SECRET ✦\n"
        "NEW RESERVATION REQUEST | НОВАЯ ЗАЯВКА\n\n"
        f"{priority_label}\n\n"
        f"👤 Guest | Гость: {name}\n"
        f"📱 Phone / WhatsApp | Телефон: {contact}\n\n"
        f"📅 Date | Дата: {reservation_date}\n"
        f"🕐 Time | Время: {reservation_time}\n"
        f"👥 Guests | Гостей: {guests}\n\n"
        "💬 Special requests | Пожелания:\n"
        f"{request_text or 'None | Нет'}\n\n"
        "📌 Recommended action | Рекомендация:\n"
        f"{action}"
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

st.markdown(hero_html, unsafe_allow_html=True)


reservation_intro = (
    '<section class="fs-reservation">'
    '<div class="fs-reservation-title">'
    'Reserve Your Table | Забронировать столик'
    '</div>'
    '<div class="fs-reservation-copy">'
    'Choose your preferred date and time and send us your request. '
    '| Выберите дату и время и отправьте заявку. '
    'Our team will contact you to confirm availability. '
    '| Наша команда свяжется с вами для подтверждения.'
    '</div>'
    '</section>'
)

st.markdown(reservation_intro, unsafe_allow_html=True)


with st.form("family_secret_reservation"):
    name = st.text_input(
        "Your name | Ваше имя",
        placeholder="John Smith | Иван Иванов",
    )

    contact = st.text_input(
        "Phone or WhatsApp | Телефон или WhatsApp",
        placeholder="+1 555 123 4567",
    )

    date_col, time_col = st.columns(2)

    with date_col:
        reservation_date = st.date_input(
            "Reservation date | Дата бронирования",
            min_value=date.today(),
        )

    with time_col:
        reservation_time = st.time_input(
            "Preferred time | Желаемое время",
        )

    guests = st.number_input(
        "Number of guests | Количество гостей",
        min_value=1,
        max_value=200,
        value=2,
        step=1,
    )

    request_text = st.text_area(
        "Special requests | Особые пожелания",
        placeholder=(
            "Birthday, private dining, dietary requirements... "
            "| День рождения, отдельный зал, питание, особый повод..."
        ),
        height=130,
    )

    submitted = st.form_submit_button(
        "Request Reservation | Отправить заявку",
        use_container_width=True,
    )


if submitted:
    if not name.strip() or not contact.strip():
        st.warning(
            "Please enter your name and phone or WhatsApp number. "
            "| Укажите имя и номер телефона или WhatsApp."
        )

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

            st.success(
                "✓ Your reservation request has been received. "
                "| Ваша заявка на бронирование получена."
            )

            st.info(
                "The FAMILY SECRET team will contact you shortly to confirm your reservation. "
                "| Команда FAMILY SECRET скоро свяжется с вами для подтверждения."
            )

        except requests.RequestException:
            st.error(
                "We couldn't send your request right now. Please try again in a moment. "
                "| Не удалось отправить заявку. Попробуйте ещё раз через минуту."
            )

        except KeyError:
            st.error(
                "Reservation notifications are temporarily unavailable. "
                "| Уведомления временно недоступны."
            )


footer_html = (
    '<footer class="fs-footer">'
    '<div class="fs-footer-name">FAMILY SECRET</div>'
    '<div class="fs-footer-type">'
    'RESERVATIONS • PRIVATE DINING • SPECIAL EVENTS '
    '| БРОНИРОВАНИЕ • ЧАСТНЫЕ УЖИНЫ • МЕРОПРИЯТИЯ'
    '</div>'
    '<div class="fs-footer-note">'
    'Reservations are confirmed after our team contacts you. '
    '| Бронирование считается подтверждённым после связи с нашей командой.'
    '</div>'
    '</footer>'
)

st.markdown(footer_html, unsafe_allow_html=True)
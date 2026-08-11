import streamlit as st
import requests
from datetime import date

st.set_page_config(
    page_title="Restaurant Reservations",
    page_icon="🍽️",
    layout="centered",
)

st.title("🍽️ Restaurant Reservations")
st.subheader("Reservation & Private Event Request")
st.write(
    "Planning a dinner, celebration, or private event? "
    "Send us your request and our team will contact you shortly."
)

with st.form("restaurant_request", clear_on_submit=False):
    name = st.text_input("Your name *", placeholder="John Smith")
    phone = st.text_input(
        "Phone or WhatsApp *",
        placeholder="+1 555 123 4567",
    )

    col1, col2 = st.columns(2)
    with col1:
        visit_date = st.date_input(
            "Preferred date",
            value=date.today(),
        )
    with col2:
        guests = st.number_input(
            "Number of guests",
            min_value=1,
            max_value=500,
            value=2,
            step=1,
        )

    request_text = st.text_area(
        "Tell us about your request *",
        placeholder=(
            "Example: We would like a private dinner for 25 people "
            "this Friday evening."
        ),
        height=140,
    )

    submitted = st.form_submit_button(
        "Send request",
        use_container_width=True,
    )


def classify_lead(text, guest_count):
    text = text.lower()

    hot_words = [
        "urgent",
        "asap",
        "today",
        "tonight",
        "private",
        "event",
        "wedding",
        "birthday",
        "corporate",
        "celebration",
    ]

    if guest_count >= 10 or any(word in text for word in hot_words):
        return "HOT"

    if guest_count >= 5:
        return "WARM"

    return "COLD"


def send_telegram(message):
    try:
        token = st.secrets["TELEGRAM_BOT_TOKEN"]
        chat_id = st.secrets["TELEGRAM_CHAT_ID"]

        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={
                "chat_id": chat_id,
                "text": message,
            },
            timeout=10,
        )

        return response.ok
    except Exception:
        return False


if submitted:
    if not name.strip() or not phone.strip() or not request_text.strip():
        st.error("Please complete your name, contact details, and request.")
    else:
        priority = classify_lead(request_text, guests)

        icons = {
            "HOT": "🔥",
            "WARM": "🟠",
            "COLD": "❄️",
        }

        manager_message = f"""
{icons[priority]} NEW RESTAURANT REQUEST — {priority}

Customer: {name}
Phone / WhatsApp: {phone}
Date: {visit_date.strftime("%d %B %Y")}
Guests: {guests}

Request:
{request_text}

Priority: {priority}
"""

        notified = send_telegram(manager_message)

        st.divider()
        st.success("Thank you! Your request has been received.")
        st.write(
            "The restaurant team will review your request "
            "and contact you shortly."
        )

        if not notified:
            st.warning(
                "Your request was received, but the manager notification "
                "could not be delivered."
            )

st.divider()
st.caption(
    "For urgent same-day requests, please include your preferred time "
    "and contact number."
)

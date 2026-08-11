import streamlit as st
import requests

st.set_page_config(
    page_title="Restaurant Reservations",
    page_icon="🍽️",
    layout="centered",
)

def qualify_lead(text):
    text = text.lower()

    hot_words = [
        "urgent", "as soon as possible", "asap",
        "today", "tonight", "tomorrow",
        "large group", "private dinner",
        "birthday", "wedding", "event",
        "20 people", "25 people", "30 people",
        "50 people", "100 people",
    ]

    if any(word in text for word in hot_words):
        return "HOT"

    return "NORMAL"


def send_telegram(name, contact, request_text, priority):
    token = st.secrets["TELEGRAM_BOT_TOKEN"]
    chat_id = st.secrets["TELEGRAM_CHAT_ID"]

    icon = "🔥" if priority == "HOT" else "🔔"

    message = f"""
{icon} NEW RESTAURANT INQUIRY

Priority: {priority}

👤 Customer: {name}
📞 Contact: {contact}

📝 Request:
{request_text}

Please contact the customer as soon as possible.
"""

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": chat_id,
            "text": message,
        },
        timeout=10,
    )

    response.raise_for_status()


st.title("🍽️ Restaurant Reservations")
st.subheader("Planning a dinner, celebration or group event?")

st.write(
    "Send us your request and the restaurant team will contact you directly."
)

with st.form("reservation_form"):

    name = st.text_input(
        "Your name",
        placeholder="John Smith"
    )

    contact = st.text_input(
        "Phone or WhatsApp",
        placeholder="+1 555 123 4567"
    )

    request_text = st.text_area(
        "Tell us what you need",
        placeholder=(
            "Example: We need a private dinner for 25 people "
            "this Friday at 7 PM."
        ),
        height=150,
    )

    submitted = st.form_submit_button(
        "Send request",
        use_container_width=True
    )

if submitted:

    if not name or not contact or not request_text:
        st.warning("Please complete all fields.")

    else:
        priority = qualify_lead(request_text)

        try:
            send_telegram(
                name,
                contact,
                request_text,
                priority
            )

            st.success(
                "✅ Thank you! Your request has been sent to the restaurant."
            )

            st.info(
                "The restaurant team will contact you using the phone "
                "or WhatsApp number you provided."
            )

        except Exception:
            st.error(
                "We couldn't send your request right now. "
                "Please try again in a moment."
            )

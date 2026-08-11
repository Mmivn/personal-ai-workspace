import streamlit as st
import requests
from datetime import date

st.set_page_config(
    page_title="Restaurant Reservations",
    page_icon="🍽️",
    layout="centered",
)

def qualify_lead(message, guests):
    text = message.lower()

    urgent_words = [
        "urgent", "asap", "today", "tonight",
        "private", "event", "birthday",
        "wedding", "corporate",
    ]

    if guests >= 10 or any(word in text for word in urgent_words):
        return "HOT"

    return "NORMAL"


def send_telegram(
    name,
    contact,
    reservation_date,
    reservation_time,
    guests,
    request_text,
    priority,
):
    token = st.secrets["TELEGRAM_BOT_TOKEN"]
    chat_id = st.secrets["TELEGRAM_CHAT_ID"]

    priority_line = (
        "🔥 HIGH PRIORITY"
        if priority == "HOT"
        else "🔔 NEW REQUEST"
    )

    message = f"""🍽️ NEW RESTAURANT RESERVATION

{priority_line}

👤 Guest: {name}
📱 Phone / WhatsApp: {contact}

📅 Date: {reservation_date}
🕐 Time: {reservation_time}
👥 Guests: {guests}

💬 Customer request:
{request_text or "No additional request"}

➡️ Please contact the guest to confirm the reservation.
"""

    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={
            "chat_id": chat_id,
            "text": message,
        },
        timeout=10,
    )

    response.raise_for_status()


st.title("🍽️ Restaurant Reservations")

st.subheader("Reserve your table")

st.write(
    "Send your reservation request and our restaurant team "
    "will contact you to confirm availability."
)

with st.form("reservation_form"):

    name = st.text_input(
        "Your name",
        placeholder="John Smith",
    )

    contact = st.text_input(
        "Phone or WhatsApp",
        placeholder="+1 555 123 4567",
    )

    col1, col2 = st.columns(2)

    with col1:
        reservation_date = st.date_input(
            "Date",
            min_value=date.today(),
        )

    with col2:
        reservation_time = st.time_input(
            "Time",
        )

    guests = st.number_input(
        "Number of guests",
        min_value=1,
        max_value=200,
        value=2,
        step=1,
    )

    request_text = st.text_area(
        "Special requests",
        placeholder=(
            "Birthday, private room, dietary requirements, "
            "children, special occasion..."
        ),
        height=120,
    )

    submitted = st.form_submit_button(
        "Request a reservation",
        use_container_width=True,
    )


if submitted:

    if not name.strip() or not contact.strip():

        st.warning(
            "Please enter your name and phone or WhatsApp number."
        )

    else:

        priority = qualify_lead(
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
                "✅ Reservation request received!"
            )

            st.info(
                "The restaurant will contact you shortly "
                "to confirm your reservation."
            )

        except Exception:

            st.error(
                "We couldn't send your reservation request. "
                "Please try again."
            )


st.divider()

st.caption(
    "Reservations are confirmed only after the restaurant "
    "contacts you."
)

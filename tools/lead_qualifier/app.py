import requests
import streamlit as st
from datetime import date


# =========================================================
# RESTAURANT SETTINGS
# For another restaurant, change these values.
# =========================================================

RESTAURANT_NAME = "FAMILY SECRET"
RESTAURANT_TAGLINE = "Table Reservations & Private Events"

HOT_GUEST_THRESHOLD = 10


# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title=f"{RESTAURANT_NAME} | Reservations",
    page_icon="🍽️",
    layout="centered",
)


# =========================================================
# LEAD PRIORITY
# =========================================================

def qualify_request(message, guests):
    text = message.lower()

    high_value_words = [
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
    ]

    if guests >= HOT_GUEST_THRESHOLD:
        return "HOT"

    if any(word in text for word in high_value_words):
        return "HOT"

    if guests >= 5:
        return "WARM"

    return "NORMAL"


# =========================================================
# TELEGRAM
# =========================================================

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

    if priority == "HOT":
        priority_text = "🔥 HIGH PRIORITY"
        action = "Contact this guest as soon as possible."

    elif priority == "WARM":
        priority_text = "🟠 MEDIUM PRIORITY"
        action = "Follow up with this guest."

    else:
        priority_text = "🔔 NORMAL REQUEST"
        action = "Confirm availability with the guest."

    message = f"""🍽️ {RESTAURANT_NAME}
NEW RESERVATION REQUEST

{priority_text}

👤 Guest: {name}
📱 Phone / WhatsApp: {contact}

📅 Date: {reservation_date}
🕐 Time: {reservation_time}
👥 Guests: {guests}

💬 Special requests:
{request_text or "None"}

📌 Recommended action:
{action}
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


# =========================================================
# CUSTOMER INTERFACE
# =========================================================

st.title(f"🍽️ {RESTAURANT_NAME}")

st.subheader(RESTAURANT_TAGLINE)

st.write(
    "Reserve your table or send us a request for a celebration, "
    "group dinner or private event."
)

st.divider()

with st.form("reservation_form"):

    name = st.text_input(
        "Your name *",
        placeholder="John Smith",
    )

    contact = st.text_input(
        "Phone or WhatsApp *",
        placeholder="+1 555 123 4567",
    )

    col1, col2 = st.columns(2)

    with col1:
        reservation_date = st.date_input(
            "Reservation date *",
            min_value=date.today(),
        )

    with col2:
        reservation_time = st.time_input(
            "Preferred time *",
        )

    guests = st.number_input(
        "Number of guests *",
        min_value=1,
        max_value=200,
        value=2,
        step=1,
    )

    request_text = st.text_area(
        "Special requests",
        placeholder=(
            "Birthday, private event, dietary requirements, "
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

        priority = qualify_request(
            request_text,
            int(guests),
        )

        try:

            send_telegram(
                name=name,
                contact=contact,
                reservation_date=reservation_date.strftime(
                    "%d %B %Y"
                ),
                reservation_time=reservation_time.strftime(
                    "%H:%M"
                ),
                guests=int(guests),
                request_text=request_text,
                priority=priority,
            )

            st.success(
                "✅ Thank you! Your reservation request has been received."
            )

            st.write(
                f"The {RESTAURANT_NAME} team will contact you "
                "shortly to confirm availability."
            )

            st.info(
                "Your reservation is confirmed only after "
                "our team contacts you."
            )

        except requests.RequestException:

            st.error(
                "We couldn't send your request right now. "
                "Please try again in a moment."
            )

        except KeyError:

            st.error(
                "Reservation notifications are temporarily unavailable."
            )


st.divider()

st.caption(
    f"© {RESTAURANT_NAME} • Reservations & Private Events"
)

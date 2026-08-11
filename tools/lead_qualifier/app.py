import requests
import streamlit as st
from datetime import date


# =========================================================
# FAMILY SECRET — SETTINGS
# =========================================================

RESTAURANT_NAME = "FAMILY SECRET"
TAGLINE = "RESTAURANT • PRIVATE DINING • EVENTS"
HOT_GUEST_THRESHOLD = 10


# =========================================================
# PAGE SETTINGS
# =========================================================

st.set_page_config(
    page_title="FAMILY SECRET | Reservations",
    page_icon="✦",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# =========================================================
# PREMIUM DESIGN
# =========================================================

st.markdown(
    """
    <style>

    /* Main background */
    .stApp {
        background:
            radial-gradient(
                circle at 50% -10%,
                #29251f 0%,
                #151412 35%,
                #090909 75%
            );
        color: #f4efe6;
    }

    /* Hide Streamlit decoration */
    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    /* Main content width */
    .block-container {
        max-width: 900px;
        padding-top: 2rem;
        padding-bottom: 5rem;
    }

    /* HERO */
    .hero {
        text-align: center;
        padding: 75px 20px 55px 20px;
    }

    .hero-symbol {
        color: #c8a96b;
        font-size: 25px;
        letter-spacing: 8px;
        margin-bottom: 22px;
    }

    .hero-title {
        color: #f7f0e5;
        font-family: Georgia, "Times New Roman", serif;
        font-size: 64px;
        font-weight: 400;
        letter-spacing: 10px;
        line-height: 1.05;
        margin-bottom: 22px;
    }

    .hero-tagline {
        color: #c8a96b;
        font-size: 12px;
        letter-spacing: 5px;
        font-weight: 600;
        margin-bottom: 35px;
    }

    .hero-description {
        color: #bcb6ad;
        max-width: 570px;
        margin: auto;
        font-family: Georgia, "Times New Roman", serif;
        font-size: 19px;
        line-height: 1.7;
        font-style: italic;
    }

    .gold-line {
        width: 70px;
        height: 1px;
        background: #c8a96b;
        margin: 45px auto 0 auto;
    }

    /* Reservation card */
    .reservation-header {
        text-align: center;
        margin-top: 45px;
        margin-bottom: 30px;
    }

    .reservation-title {
        color: #f7f0e5;
        font-family: Georgia, "Times New Roman", serif;
        font-size: 34px;
        letter-spacing: 2px;
    }

    .reservation-subtitle {
        color: #a9a197 !important;
        font-size: 15px !important;
        line-height: 1.7 !important;
        margin: 12px auto 0 auto !important;
        max-width: 560px;
    }

    /* Labels */
    label,
    .stMarkdown,
    p {
        color: #d9d3c9;
    }

    div[data-testid="stTextInput"] label,
    div[data-testid="stTextArea"] label,
    div[data-testid="stDateInput"] label,
    div[data-testid="stTimeInput"] label,
    div[data-testid="stNumberInput"] label {
        color: #c8a96b !important;
        font-size: 12px !important;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }

    /* Inputs */
    div[data-baseweb="input"] > div,
    div[data-baseweb="textarea"] > div {
        background-color: #151515 !important;
        border: 1px solid #39352f !important;
        border-radius: 4px !important;
    }

    input,
    textarea {
        color: #f4efe6 !important;
    }

    input::placeholder,
    textarea::placeholder {
        color: #716d67 !important;
    }

    /* Form */
    div[data-testid="stForm"] {
        background: rgba(20, 20, 19, 0.92);
        border: 1px solid #302d28;
        border-radius: 8px;
        padding: 35px;
        box-shadow: 0 25px 80px rgba(0, 0, 0, 0.25);
    }

    /* Gold button */
    div[data-testid="stFormSubmitButton"] button {
        background: #b8965d !important;
        color: #0d0d0d !important;
        border: 1px solid #c8a96b !important;
        border-radius: 3px !important;
        min-height: 52px;
        font-size: 13px !important;
        font-weight: 700 !important;
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    div[data-testid="stFormSubmitButton"] button:hover {
        background: #d0b274 !important;
        border-color: #d0b274 !important;
        color: #000000 !important;
    }

    /* Divider */
    hr {
        border-color: #302d28 !important;
    }

    /* Footer */
    .custom-footer {
        text-align: center;
        color: #777169;
        padding-top: 50px;
        font-size: 11px;
        letter-spacing: 2px;
    }

    .footer-brand {
        color: #b8965d;
        font-family: Georgia, "Times New Roman", serif;
        font-size: 18px;
        letter-spacing: 4px;
        margin-bottom: 8px;
    }

    /* Mobile */
    @media (max-width: 700px) {

        .block-container {
            padding-left: 18px;
            padding-right: 18px;
            padding-top: 0.5rem;
        }

        .hero {
            padding-top: 55px;
            padding-bottom: 35px;
        }

        .hero-title {
            font-size: 39px;
            letter-spacing: 5px;
        }

        .hero-tagline {
            font-size: 9px;
            letter-spacing: 2px;
        }

        .hero-description {
            font-size: 16px;
        }

        div[data-testid="stForm"] {
            padding: 22px;
        }
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# PRIORITY ENGINE
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

    message = f"""✦ FAMILY SECRET ✦
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
# HERO
# =========================================================

st.markdown(
    """
    <div class="hero">

        <div class="hero-symbol">
            ✦
        </div>

        <div class="hero-title">
            FAMILY<br>SECRET
        </div>

        <div class="hero-tagline">
            RESTAURANT • PRIVATE DINING • EVENTS
        </div>

        <div class="hero-description">
            Good food brings people together.<br>
            Great evenings become family secrets.
        </div>

        <div class="gold-line"></div>

    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# RESERVATION
# =========================================================

st.markdown(
    """
    <div class="reservation-header">
        <div class="reservation-title">Reserve Your Table</div>
        <p class="reservation-subtitle">
            Send us your request and our team will contact you
            to confirm your reservation.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
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
            "Reservation date",
            min_value=date.today(),
        )

    with col2:
        reservation_time = st.time_input(
            "Preferred time",
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
            "Birthday, private dining, dietary requirements, "
            "children or a special occasion..."
        ),
        height=120,
    )

    submitted = st.form_submit_button(
        "Request Reservation",
        use_container_width=True,
    )


# =========================================================
# FORM RESULT
# =========================================================

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
                "Your reservation request has been received."
            )

            st.write(
                "The FAMILY SECRET team will contact you shortly "
                "to confirm availability."
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


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div class="custom-footer">

        <div class="footer-brand">
            FAMILY SECRET
        </div>

        RESERVATIONS • PRIVATE DINING • SPECIAL EVENTS

        <br><br>

        Reservations are confirmed after our team contacts you.

    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# END
# =========================================================

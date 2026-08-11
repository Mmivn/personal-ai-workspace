import requests
import streamlit as st

from main import qualify_lead


st.set_page_config(
    page_title="Restaurant Lead Manager",
    page_icon="🍽️",
    layout="centered",
)


def send_telegram_notification(name, phone, request_text, status):
    bot_token = st.secrets["TELEGRAM_BOT_TOKEN"]
    chat_id = st.secrets["TELEGRAM_CHAT_ID"]

    if status == "HOT":
        priority = "🔥 HIGH PRIORITY"
        action = "Contact this customer immediately."
    elif status == "WARM":
        priority = "🟡 MEDIUM PRIORITY"
        action = "Follow up with this customer."
    else:
        priority = "❄️ LOW PRIORITY"
        action = "Keep this lead for future follow-up."

    message = (
        "🍽️ NEW RESTAURANT LEAD\n\n"
        f"{priority}\n\n"
        f"Customer: {name or 'Not provided'}\n"
        f"Phone / WhatsApp: {phone or 'Not provided'}\n\n"
        f"Request:\n{request_text}\n\n"
        f"Lead status: {status}\n"
        f"Recommended action: {action}"
    )

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    response = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": message,
        },
        timeout=10,
    )

    response.raise_for_status()


st.title("🍽️ Restaurant Lead Manager")

st.subheader(
    "Turn website inquiries into prioritized sales leads"
)

st.write(
    "When a customer submits an inquiry, the system analyzes "
    "the request and immediately notifies the restaurant manager."
)

with st.form("lead_form"):
    name = st.text_input(
        "Customer name",
        placeholder="John Smith",
    )

    phone = st.text_input(
        "Phone or WhatsApp",
        placeholder="+1 555 123 4567",
    )

    request_text = st.text_area(
        "Customer request",
        placeholder=(
            "Example: We need a private dinner for 25 people "
            "this Friday. Please call me ASAP."
        ),
        height=160,
    )

    submitted = st.form_submit_button(
        "Send inquiry"
    )

if submitted:
    if not request_text.strip():
        st.warning(
            "Please enter the customer's request."
        )

    else:
        status = qualify_lead(request_text)

        st.divider()
        st.subheader("Request received")

        if status == "HOT":
            st.error("🔥 High-priority customer")
            st.write(
                "The restaurant manager should contact "
                "this customer immediately."
            )

        elif status == "WARM":
            st.warning("🟡 Medium-priority customer")
            st.write(
                "The restaurant should follow up with "
                "this customer."
            )

        else:
            st.info("❄️ Low-priority customer")
            st.write(
                "The request can be handled as a normal "
                "follow-up."
            )

        try:
            send_telegram_notification(
                name,
                phone,
                request_text,
                status,
            )

            st.success(
                "✅ The restaurant manager has been notified."
            )

        except requests.RequestException as error:
            st.error(
                "The request was analyzed, but the manager "
                "notification could not be sent."
            )

            st.caption(str(error))

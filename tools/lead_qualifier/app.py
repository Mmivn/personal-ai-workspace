import streamlit as st
from main import qualify_lead

st.set_page_config(
    page_title="Restaurant Lead Manager",
    page_icon="🍽️",
    layout="centered",
)

st.title("🍽️ Restaurant Lead Manager")
st.subheader("Turn website inquiries into prioritized sales leads")

st.write(
    "This demo analyzes incoming customer requests and helps "
    "your team decide who should be contacted first."
)

with st.form("lead_form"):
    name = st.text_input(
        "Customer name",
        placeholder="John Smith"
    )

    phone = st.text_input(
        "Phone or WhatsApp",
        placeholder="+1 555 123 4567"
    )

    request = st.text_area(
        "Customer request",
        placeholder="Example: I need a table for 20 people this Friday. Please call me ASAP.",
        height=150,
    )

    submitted = st.form_submit_button(
        "Analyze customer"
    )

if submitted:
    if not request.strip():
        st.warning("Please enter the customer's request.")
    else:
        status = qualify_lead(request)

        st.divider()
        st.subheader("Lead Analysis")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Customer**")
            st.write(name if name else "Not provided")

        with col2:
            st.write("**Contact**")
            st.write(phone if phone else "Not provided")

        if status == "HOT":
            st.error("🔥 HOT LEAD")
            st.write(
                "**High buying intent or urgency detected.**"
            )
            st.write(
                "Recommended action: Contact this customer immediately."
            )

        elif status == "WARM":
            st.warning("🟡 WARM LEAD")
            st.write(
                "**Customer shows interest but may need follow-up.**"
            )
            st.write(
                "Recommended action: Contact the customer and qualify the opportunity."
            )

        else:
            st.info("❄️ COLD LEAD")
            st.write(
                "**No immediate buying intent detected.**"
            )
            st.write(
                "Recommended action: Keep this lead for future follow-up."
            )

        st.divider()
        st.caption(
            "In a real restaurant website, this analysis can run "
            "automatically when a visitor submits a contact form."
        )

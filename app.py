import streamlit as st
import requests
import uuid
from datetime import datetime
import json

API_URL = "https://script.google.com/macros/s/AKfycbyhSbiNnsZv3Y3K_kJL4gF87tt5dl4We38p72-LOp2zdLnEG_2mnSXmyuwuC3kW_5qi/exec"

st.set_page_config(page_title="AI Client Intake Assistant")
st.title("💬 Talk to Our Assistant")

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "lead_saved" not in st.session_state:
    st.session_state.lead_saved = False

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
user_input = st.chat_input("How can we help you today?")

if user_input:
    # Save user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    # Simple assistant reply (placeholder for AI)
    assistant_reply = (
        "Thanks for sharing. Can you tell me a bit more about "
        "what you're looking for and your timeline?"
    )

    st.session_state.messages.append({
        "role": "assistant",
        "content": assistant_reply
    })

    with st.chat_message("assistant"):
        st.markdown(assistant_reply)

# Save lead button (TEMP – will become automatic)
if st.session_state.messages and not st.session_state.lead_saved:
    if st.button("Finish & Send to Team"):
        payload = {
            "created_at": datetime.utcnow().isoformat(),
            "lead_id": str(uuid.uuid4()),
            "source": "streamlit-chat",
            "intent": "unknown",
            "service_interest": "unknown",
            "budget_range": "unknown",
            "timeline": "unknown",
            "urgency_level": "unknown",
            "lead_score": 0,
            "lead_temperature": "cold",
            "suggested_action": "Review conversation",
            "ai_summary": "Conversation captured via chatbot.",
            "conversation_log": st.session_state.messages
        }

        response = requests.post(
            f"{API_URL}?action=saveLead",
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            st.success("Thanks! Our team will get back to you.")
            st.session_state.lead_saved = True
        else:
            st.error("Something went wrong. Please try again.")

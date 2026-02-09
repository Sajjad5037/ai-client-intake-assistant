import streamlit as st
import requests
import uuid
from datetime import datetime
import os
import json
from openai import OpenAI


# ================= CONFIG =================
API_URL = "https://script.google.com/macros/s/AKfycbyhSbiNnsZv3Y3K_kJL4gF87tt5dl4We38p72-LOp2zdLnEG_2mnSXmyuwuC3kW_5qi/exec"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="AI Client Intake Assistant")
st.title("💬 Talk to Our Assistant")


# ================= SESSION STATE =================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "lead_saved" not in st.session_state:
    st.session_state.lead_saved = False


# ================= JSON UTILS =================
def extract_json_from_text(text: str) -> dict:
    if not text:
        raise ValueError("Empty AI response")

    cleaned = text.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start != -1 and end != -1:
            return json.loads(cleaned[start:end + 1])

    raise ValueError("Could not extract valid JSON")


# ================= AI CHAT =================
def generate_ai_reply(messages):
    system_prompt = (
        "You are a friendly AI assistant for a digital agency. "
        "Ask concise follow-up questions to understand the visitor’s needs, "
        "timeline, and budget. Keep responses professional and conversational."
    )

    chat = [{"role": "system", "content": system_prompt}] + messages

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=chat,
        temperature=0.4
    )

    return response.choices[0].message.content


# ================= AI EXTRACTION =================
def extract_lead_data(messages):
    prompt = (
        "From the following conversation, extract structured lead information.\n\n"
        "Return ONLY valid JSON with the following fields:\n"
        "- intent (sales/support/other)\n"
        "- service_interest\n"
        "- budget_range (low/medium/high/unknown)\n"
        "- timeline (urgent/soon/flexible/unknown)\n"
        "- urgency_level (low/medium/high)\n"
        "- lead_score (0-100)\n"
        "- lead_temperature (hot/warm/cold)\n"
        "- ai_summary (1-2 sentences)\n"
        "- suggested_action\n\n"
        f"{json.dumps(messages, indent=2)}"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You output strict JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0
    )

    try:
        return extract_json_from_text(response.choices[0].message.content)
    except Exception:
        return {
            "intent": "sales",
            "service_interest": "Website redesign",
            "budget_range": "unknown",
            "timeline": "unknown",
            "urgency_level": "medium",
            "lead_score": 50,
            "lead_temperature": "warm",
            "ai_summary": "Lead captured via chatbot, but details are incomplete.",
            "suggested_action": "Review conversation manually"
        }


# ================= AUTO SAVE =================
def auto_save_lead(messages):
    if st.session_state.lead_saved:
        return

    extracted = extract_lead_data(messages)

    if (
        extracted["intent"] == "sales"
        and extracted["service_interest"]
        and extracted["lead_score"] >= 60
        and (
            extracted["budget_range"] != "unknown"
            or extracted["timeline"] != "unknown"
        )
    ):

        payload = {
            "created_at": datetime.utcnow().isoformat(),
            "lead_id": str(uuid.uuid4()),
            "source": "streamlit-chat",
            **extracted,
            "conversation_log": messages,
        }

        response = requests.post(
            f"{API_URL}?action=saveLead",
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            st.session_state.lead_saved = True

        # Show confirmation in chat (TEMP – for dev/demo)
        st.session_state.messages.append({
            "role": "assistant",
            "content": "✅ Thanks! Your request has been saved and our team will be in touch shortly."
        })


# ================= UI =================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("How can we help you today?")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    ai_reply = generate_ai_reply(st.session_state.messages)
    st.session_state.messages.append({"role": "assistant", "content": ai_reply})
    with st.chat_message("assistant"):
        st.markdown(ai_reply)

    # Silent auto-save check
    auto_save_lead(st.session_state.messages)

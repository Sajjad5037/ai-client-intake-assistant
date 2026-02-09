import streamlit as st
import requests
import uuid
from datetime import datetime
import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# --- CONFIG ---
API_URL = "https://script.google.com/macros/s/AKfycbyhSbiNnsZv3Y3K_kJL4gF87tt5dl4We38p72-LOp2zdLnEG_2mnSXmyuwuC3kW_5qi/exec"

st.set_page_config(page_title="AI Client Intake Assistant")
st.title("💬 Talk to Our Assistant")

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "lead_saved" not in st.session_state:
    st.session_state.lead_saved = False

def extract_lead_data(messages):
    extraction_prompt = (
        "From the following conversation, extract structured lead information.\n\n"
        "Return ONLY valid JSON. Do not include explanations, markdown, or extra text.\n\n"
        "Required JSON fields:\n"
        "- intent (sales/support/other)\n"
        "- service_interest\n"
        "- budget_range (low/medium/high/unknown)\n"
        "- timeline (urgent/soon/flexible/unknown)\n"
        "- urgency_level (low/medium/high)\n"
        "- lead_score (0-100 integer)\n"
        "- lead_temperature (hot/warm/cold)\n"
        "- ai_summary (1-2 sentences)\n"
        "- suggested_action\n\n"
        "Conversation:\n"
        f"{json.dumps(messages, indent=2)}"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a strict JSON generator. Output ONLY valid JSON."
            },
            {
                "role": "user",
                "content": extraction_prompt
            }
        ],
        temperature=0
    )

    raw = response.choices[0].message.content.strip()

    # Remove markdown fences if present
    if raw.startswith("```"):
        raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Fallback: return safe defaults instead of crashing
        return {
            "intent": "sales",
            "service_interest": "Website redesign",
            "budget_range": "unknown",
            "timeline": "unknown",
            "urgency_level": "medium",
            "lead_score": 50,
            "lead_temperature": "warm",
            "ai_summary": "Lead captured via chatbot, but some details could not be confidently extracted.",
            "suggested_action": "Review conversation manually"
        }
# --- AI CHAT REPLY ---
def generate_ai_reply(messages):
    system_prompt = (
        "You are a friendly AI assistant for a digital agency. "
        "Your job is to understand what the visitor needs, ask concise follow-up questions, "
        "and gently gather information about their project, timeline, and budget. "
        "Be professional, warm, and conversational."
    )

    chat = [{"role": "system", "content": system_prompt}]
    chat.extend(messages)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=chat,
        temperature=0.4
    )
    
    return response.choices[0].message.content


    

# --- AI EXTRACTION ---
def extract_lead_data(messages):
    extraction_prompt = (
        "From the following conversation, extract structured lead information.\n\n"
        "Return ONLY valid JSON. Do not include explanations, markdown, or extra text.\n\n"
        "Required JSON fields:\n"
        "- intent (sales/support/other)\n"
        "- service_interest\n"
        "- budget_range (low/medium/high/unknown)\n"
        "- timeline (urgent/soon/flexible/unknown)\n"
        "- urgency_level (low/medium/high)\n"
        "- lead_score (0-100 integer)\n"
        "- lead_temperature (hot/warm/cold)\n"
        "- ai_summary (1-2 sentences)\n"
        "- suggested_action\n\n"
        "Conversation:\n"
        f"{json.dumps(messages, indent=2)}"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a strict JSON generator. Output ONLY valid JSON."
            },
            {
                "role": "user",
                "content": extraction_prompt
            }
        ],
        temperature=0
    )

    raw = response.choices[0].message.content

    try:
        return extract_json_from_text(raw)
    except ValueError:
        # Graceful fallback (never crash UX)
        return {
            "intent": "sales",
            "service_interest": "Website redesign",
            "budget_range": "unknown",
            "timeline": "unknown",
            "urgency_level": "medium",
            "lead_score": 50,
            "lead_temperature": "warm",
            "ai_summary": "Lead captured, but some details could not be confidently extracted.",
            "suggested_action": "Review conversation manually"
        }


# --- DISPLAY CHAT HISTORY ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# --- USER INPUT ---
user_input = st.chat_input("How can we help you today?")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    ai_reply = generate_ai_reply(st.session_state.messages)

    st.session_state.messages.append({"role": "assistant", "content": ai_reply})

    with st.chat_message("assistant"):
        st.markdown(ai_reply)


# --- SAVE LEAD ---
if st.session_state.messages and not st.session_state.lead_saved:
    if st.button("Finish & Send to Team"):
        with st.spinner("Analyzing your request..."):
            extracted = extract_lead_data(st.session_state.messages)

            payload = {
                "created_at": datetime.utcnow().isoformat(),
                "lead_id": str(uuid.uuid4()),
                "source": "streamlit-chat",
                "intent": extracted["intent"],
                "service_interest": extracted["service_interest"],
                "budget_range": extracted["budget_range"],
                "timeline": extracted["timeline"],
                "urgency_level": extracted["urgency_level"],
                "lead_score": extracted["lead_score"],
                "lead_temperature": extracted["lead_temperature"],
                "suggested_action": extracted["suggested_action"],
                "ai_summary": extracted["ai_summary"],
                "conversation_log": st.session_state.messages,
            }

            response = requests.post(
                f"{API_URL}?action=saveLead",
                json=payload,
                timeout=10,
            )

        if response.status_code == 200:
            st.success("Thanks! Our team will get back to you shortly.")
            st.session_state.lead_saved = True
        else:
            st.error("Something went wrong while saving your request.")

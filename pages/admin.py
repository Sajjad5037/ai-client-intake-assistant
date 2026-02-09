import streamlit as st
import requests
import json
from datetime import datetime

# ---------------- CONFIG ----------------
API_URL = "https://script.google.com/macros/s/AKfycbyhSbiNnsZv3Y3K_kJL4gF87tt5dl4We38p72-LOp2zdLnEG_2mnSXmyuwuC3kW_5qi/exec"

st.set_page_config(page_title="Admin – Leads Dashboard")
st.title("🧠 AI Leads Dashboard")

# ---------------- SIMPLE AUTH (DEMO ONLY) ----------------
password = st.text_input("Admin password", type="password")

if password != "demo123":
    st.info("Enter demo123 as password to view leads.")
    st.stop()

# ---------------- FETCH LEADS ----------------
with st.spinner("Loading leads..."):
    response = requests.get(f"{API_URL}?action=getLeads", timeout=10)

if response.status_code != 200:
    st.error("Failed to load leads.")
    st.stop()

leads = response.json()

if not leads:
    st.info("No leads yet.")
    st.stop()

# ---------------- FILTERS ----------------
st.subheader("📊 Lead Filters")

col1, col2 = st.columns(2)

with col1:
    filter_temp = st.selectbox(
        "Lead temperature",
        ["All", "hot", "warm", "cold"]
    )

with col2:
    min_score = st.slider(
        "Minimum lead score",
        min_value=0,
        max_value=100,
        value=0
    )

def passes_filters(lead):
    if filter_temp != "All" and lead.get("lead_temperature") != filter_temp:
        return False
    if int(lead.get("lead_score", 0)) < min_score:
        return False
    return True

filtered_leads = [l for l in leads if passes_filters(l)]

st.markdown(f"**Showing {len(filtered_leads)} lead(s)**")

# ---------------- LEADS LIST ----------------
st.divider()

for lead in reversed(filtered_leads):
    title = (
        f"{lead.get('service_interest', 'Unknown').title()} | "
        f"{lead.get('lead_temperature', '').upper()} | "
        f"Score: {lead.get('lead_score', 0)}"
    )

    with st.expander(title):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📝 AI Summary")
            st.write(lead.get("ai_summary", ""))

            st.markdown("### 🎯 Suggested Action")
            st.write(lead.get("suggested_action", ""))

        with col2:
            st.markdown("### 📌 Lead Details")
            st.write("**Intent:**", lead.get("intent"))
            st.write("**Budget:**", lead.get("budget_range"))
            st.write("**Timeline:**", lead.get("timeline"))
            st.write("**Urgency:**", lead.get("urgency_level"))
            st.write("**Created At:**", lead.get("created_at"))

        st.markdown("### 💬 Conversation")

        try:
            conversation = json.loads(lead.get("conversation_log", "[]"))
            for msg in conversation:
                st.chat_message(msg["role"]).write(msg["content"])
        except Exception:
            st.write("Could not load conversation.")

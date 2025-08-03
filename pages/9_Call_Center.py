import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import io
import json

st.set_page_config(page_title="Call Analysis CRM", layout="wide")
st.title("📞 Call CRM Dashboard")

GSHEET_URL = "https://docs.google.com/spreadsheets/d/1LFfNwb9lRQpIosSEvV3O6zIwymUIWeG9L_k7cxw1jQs/edit?gid=0"

EXPECTED_COLUMNS = [
    "call_id", "customer_name", "email", "phone number", "Booking Status", "voice_agent_name",
    "call_date", "call_start_time", "call_end_time", "call_duration_seconds", "call_duration_hms",
    "cost", "call_success", "appointment_scheduled", "intent_detected", "sentiment_score",
    "confidence_score", "keyword_tags", "summary_word_count", "transcript", "summary",
    "action_items", "call_recording_url", "customer_satisfaction", "resolution_time_seconds",
    "escalation_required", "language_detected", "emotion_detected", "speech_rate_wpm",
    "silence_percentage", "interruption_count", "ai_accuracy_score", "follow_up_required",
    "customer_tier", "call_complexity", "agent_performance_score", "call_outcome",
    "revenue_impact", "lead_quality_score", "conversion_probability", "next_best_action",
    "customer_lifetime_value", "call_category", "Upload_Timestamp"
]

# -------- Sidebar: Service Account Upload ---------
with st.sidebar:
    st.subheader("🔑 Google Service Account")
    uploaded_json = st.file_uploader(
        "Upload your Google Service Account JSON file",
        type="json",
        key="service_account_json"
    )
    st.markdown("*Required for live Google Sheets connection*")

# -------- Data Loading Function ---------
@st.cache_data(show_spinner=True)
def load_data(uploaded_json):
    if uploaded_json is None:
        st.info("Please upload your Google Service Account JSON file in the sidebar to load live data.")
        return pd.DataFrame(columns=EXPECTED_COLUMNS)
    try:
        json_dict = json.load(uploaded_json)
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(json_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(GSHEET_URL).sheet1
        df = get_as_dataframe(sheet, evaluate_formulas=True).dropna(how="all")
        df.columns = [col.strip() for col in df.columns]
        return df
    except Exception as e:
        st.warning(f"⚠️ Could not load live data. Using demo data instead. Error: {e}")
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

df = load_data(uploaded_json)

for col in EXPECTED_COLUMNS:
    if col not in df.columns:
        df[col] = ""
df = df[EXPECTED_COLUMNS]

# --------- SIDEBAR: SEARCH FILTERS ----------
with st.sidebar:
    st.header("🔍 Search Filters")
    customer_name = st.text_input("Customer Name")
    agent_name = st.text_input("Voice Agent Name")
    call_success = st.selectbox("Call Success", ["", "Yes", "No"])
    sentiment_range = st.slider("Sentiment Score", -1.0, 1.0, (-1.0, 1.0))

# --------- FILTERS ----------
filtered_df = df.copy()
if customer_name:
    filtered_df = filtered_df[filtered_df["customer_name"].str.contains(customer_name, case=False, na=False)]
if agent_name:
    filtered_df = filtered_df[filtered_df["voice_agent_name"].str.contains(agent_name, case=False, na=False)]
if call_success:
    filtered_df = filtered_df[filtered_df["call_success"].astype(str).str.lower() == call_success.lower()]
filtered_df = filtered_df[
    (filtered_df["sentiment_score"].astype(str).replace("None", "0").astype(float) >= sentiment_range[0]) &
    (filtered_df["sentiment_score"].astype(str).replace("None", "0").astype(float) <= sentiment_range[1])
]

# --------- TABS ---------
tab1, tab2, tab3, tab4 = st.tabs(["📋 All Calls", "📈 Analytics", "🧠 AI Summary", "🔊 Recordings"])

with tab1:
    st.subheader("📋 Call Log Table")
    st.dataframe(filtered_df, use_container_width=True)

with tab2:
    st.subheader("📈 Analytics Overview")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Calls", len(df))
    with col2:
        st.metric("Successful Calls", df["call_success"].str.lower().eq("yes").sum())
    with col3:
        st.metric("Avg Sentiment", round(pd.to_numeric(df["sentiment_score"], errors='coerce').mean(), 2))
    st.bar_chart(df["voice_agent_name"].value_counts())

with tab3:
    st.subheader("🧠 Summaries and Action Items")
    for idx, row in filtered_df.iterrows():
        with st.expander(f"{row['call_id']} - {row['customer_name']}"):
            st.write("**Summary:**", row["summary"])
            st.write("**Action Items:**", row["action_items"])
            st.write("**Transcript Preview:**")
            st.text(row["transcript"][:1000] + "..." if row["transcript"] else "No transcript")

with tab4:
    st.subheader("🔊 Audio Recordings")
    for idx, row in filtered_df.iterrows():
        if row["call_recording_url"]:
            st.markdown(f"**{row['call_id']}** - [{row['customer_name']}]({row['call_recording_url']}) 🔗")

st.success("✅ CRM dashboard loaded with all matching columns.")

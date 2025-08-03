import streamlit as st
import pandas as pd
import gspread
from gspread_dataframe import get_as_dataframe
from oauth2client.service_account import ServiceAccountCredentials
import json

st.set_page_config(page_title="Call Analysis CRM", layout="wide")
st.title("📞 Call CRM Dashboard")
st.caption("Live Google Sheets CRM with call analysis, intelligent filtering and direct audio recording playback.")

GSHEET_URL = "https://docs.google.com/spreadsheets/d/1LFfNwb9lRQpIosSEvV3O6zIwymUIWeG9L_k7cxw1jQs/edit?gid=0"

# --------------- COLUMN DEFINITIONS ---------------
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

# --------- SIDEBAR: AUTH & FILTERS ----------
with st.sidebar:
    st.subheader("🔑 Google Service Account")
    uploaded_json = st.file_uploader(
        "Upload your Google Service Account JSON file",
        type="json",
        key="service_account_json"
    )
    st.markdown(
        "*Required for live Google Sheets connection.*\n"
        "<sup>Get this from your GCP service credentials. JSON file is never stored on the server.</sup>",
        unsafe_allow_html=True
    )

    st.divider()

    st.header("🔍 Search & Filters")
    customer_name = st.text_input("Customer Name")
    agent_name = st.text_input("Voice Agent Name")
    call_success = st.selectbox("Call Success", ["", "Yes", "No"])
    sentiment_range = st.slider("Sentiment Score", -1.0, 1.0, (-1.0, 1.0))

    st.divider()
    st.markdown(
        "💡 <sup>You can combine filters for fast drill-down. Sentiment is -1 (very negative) to 1 (very positive).</sup>",
        unsafe_allow_html=True
    )

# --------- LOAD DATA ---------
@st.cache_data(show_spinner=True)
def load_data(uploaded_json):
    """Authenticate and load data from google sheets into pandas DataFrame."""
    if uploaded_json is None:
        st.info("Please upload your Google Service Account JSON file in the sidebar to enable live data.")
        return pd.DataFrame(columns=EXPECTED_COLUMNS)
    try:
        json_dict = json.load(uploaded_json)
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(json_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(GSHEET_URL).sheet1
        df = get_as_dataframe(sheet, evaluate_formulas=True).dropna(how="all")
        df.columns = [col.strip() for col in df.columns]
        return df
    except Exception as e:
        st.warning(f"⚠️ Could not load live data. Using placeholder columns for demo. Error: {e}")
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

df = load_data(uploaded_json)

# Ensure all expected columns exist
for col in EXPECTED_COLUMNS:
    if col not in df.columns:
        df[col] = ""
df = df[EXPECTED_COLUMNS]

# ------- FILTER LOGIC ----------
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

# ----- MAIN CONTENT -----
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 All Calls", "📈 Analytics", "🧠 AI Summary", "🔊 Recordings"
])

with tab1:
    st.subheader("📋 Call Log Table")
    st.dataframe(filtered_df, use_container_width=True)
    st.caption(f"Showing {len(filtered_df)} calls out of {len(df)} total records.")

with tab2:
    st.subheader("📈 Analytics Overview")
    col1, col2, col3, col4 = st.columns([1,1,1,2])
    with col1:
        st.metric("Total Calls", len(df))
    with col2:
        st.metric("Successful", df["call_success"].str.lower().eq("yes").sum())
    with col3:
        st.metric("Avg Sentiment", round(pd.to_numeric(df["sentiment_score"], errors='coerce').mean(), 2))
    with col4:
        st.metric("Distinct Agents", df["voice_agent_name"].nunique())
    st.markdown("#### Calls by Agent")
    st.bar_chart(df["voice_agent_name"].value_counts())
    st.markdown("#### Conversion Probability Distribution")
    st.bar_chart(pd.to_numeric(df["conversion_probability"], errors="coerce"))

with tab3:
    st.subheader("🧠 Summaries and Action Items")
    st.caption("Dive into AI-generated summaries, action steps, and transcript previews for each call.")
    if filtered_df.empty:
        st.info("No matching calls for these filters.")
    for idx, row in filtered_df.iterrows():
        with st.expander(f"📞 {row['call_id']} - {row['customer_name']} ({row['call_date']})"):
            st.markdown(f"**Agent:** {row['voice_agent_name']}  \n**Sentiment:** {row['sentiment_score']}  \n**Outcome:** {row['call_outcome']}")
            st.markdown(f"**Summary:**\n{row['summary']}")
            st.markdown(f"**Action Items:**\n{row['action_items']}")
            st.markdown("**Transcript Preview:**")
            st.text((row["transcript"][:1200] + "...") if row["transcript"] else "No transcript")

with tab4:
    st.subheader("🔊 Audio Recordings")
    st.caption("Directly play call recordings below. For best results, recordings must be accessible URLs (mp3, wav, etc).")
    if filtered_df.empty:
        st.info("No calls with recordings for these filters.")
    found = False
    for idx, row in filtered_df.iterrows():
        audio_url = row["call_recording_url"]
        if audio_url:
            found = True
            st.markdown(f"#### 📞 {row['call_id']} - {row['customer_name']}")
            # Attempt filename extraction for nicer labeling, fallback to raw URL
            filename = audio_url.split("/")[-1] if "/" in audio_url else audio_url
            st.markdown(f"**File:** `{filename}`")
            # Playback
            st.audio(audio_url)
            with st.expander("📝 Transcript Preview"):
                st.text((row["transcript"][:1000] + "...") if row["transcript"] else "No transcript available.")
            st.divider()
    if not found:
        st.warning("No recordings found in the current filtered data.")

st.success("✅ CRM dashboard loaded. Use the tabs above for logs, analysis, summaries, and direct audio playback.")

# ------------- TIPS FOR USERS -------------
st.markdown(
    """
    <hr>
    <h6>ℹ️ Tips & Notes:</h6>
    <ul>
      <li>For secure, live Google Sheets access, your audio file URLs must be open/public or accessible to the server.</li>
      <li><b>Audio streaming works with direct .mp3, .wav links. Google Drive links may require file permissions and might not stream directly.</b></li>
      <li>You can combine filters in the sidebar to drill down—try filtering for a specific agent and positive sentiment score.</li>
    </ul>
    """,
    unsafe_allow_html=True
)

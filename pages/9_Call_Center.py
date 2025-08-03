import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

st.set_page_config(page_title="📞 Call Intelligence Dashboard", layout="wide")

# Load sample or actual data
@st.cache_data
def load_data():
    # Replace this with actual live data loading logic (e.g., from Google Sheets or a database)
    df = pd.read_csv("call_insights.csv")  # Replace with actual path
    return df

df = load_data()

# Ensure all expected columns exist
expected_columns = [
    "call_id", "customer_name", "email", "phone number", "Booking Status",
    "voice_agent_name", "call_date", "call_start_time", "call_end_time",
    "call_duration_seconds", "call_duration_hms", "cost", "call_success",
    "appointment_scheduled", "intent_detected", "sentiment_score", "confidence_score",
    "keyword_tags", "summary_word_count", "transcript", "summary", "action_items",
    "call_recording_url", "customer_satisfaction", "resolution_time_seconds",
    "escalation_required", "language_detected", "emotion_detected", "speech_rate_wpm",
    "silence_percentage", "interruption_count", "ai_accuracy_score", "follow_up_required",
    "customer_tier", "call_complexity", "agent_performance_score", "call_outcome",
    "revenue_impact", "lead_quality_score", "conversion_probability", "next_best_action",
    "customer_lifetime_value", "call_category", "Upload_Timestamp"
]

# Add missing columns if necessary
for col in expected_columns:
    if col not in df.columns:
        df[col] = None

# Sidebar filter
st.sidebar.header("🔍 Filter")
selected_agent = st.sidebar.selectbox("Select Agent", options=["All"] + sorted(df["voice_agent_name"].dropna().unique().tolist()))
selected_date = st.sidebar.date_input("Select Date", value=datetime.date.today())

if selected_agent != "All":
    df = df[df["voice_agent_name"] == selected_agent]

df = df[df["call_date"] == str(selected_date)]

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📋 Call Log", "📊 Agent Performance", "🧠 AI Summary", "📈 Metrics",
    "🧭 Intent & Actions", "🗣️ Sentiment & Emotion", "📤 Upload Logs"
])

with tab1:
    st.subheader("📋 Complete Call Log")
    st.dataframe(df[expected_columns], use_container_width=True)

with tab2:
    st.subheader("📊 Agent Performance Overview")
    performance_df = df.groupby("voice_agent_name")["agent_performance_score"].mean().reset_index()
    fig = px.bar(performance_df, x="voice_agent_name", y="agent_performance_score", title="Agent Performance Score")
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("🧠 AI Summary & Keywords")
    st.write("Summaries of recent calls and key extracted insights.")
    st.dataframe(df[["call_id", "summary", "keyword_tags", "action_items"]].dropna(), use_container_width=True)

with tab4:
    st.subheader("📈 Call Metrics")
    st.metric("Total Calls", len(df))
    st.metric("Avg Call Duration (s)", round(df["call_duration_seconds"].mean(), 2))
    st.metric("Total Revenue Impact", df["revenue_impact"].sum())

    chart = px.histogram(df, x="call_duration_seconds", nbins=20, title="Call Duration Distribution")
    st.plotly_chart(chart, use_container_width=True)

with tab5:
    st.subheader("🧭 Intent Detection and Actions")
    st.dataframe(df[["intent_detected", "action_items", "next_best_action", "follow_up_required"]].dropna(), use_container_width=True)

with tab6:
    st.subheader("🗣️ Sentiment & Emotion Analytics")
    st.dataframe(df[["call_id", "sentiment_score", "emotion_detected", "speech_rate_wpm", "silence_percentage", "interruption_count"]].dropna(), use_container_width=True)

with tab7:
    st.subheader("📤 Upload & Call Logs")
    st.dataframe(df[["call_id", "Upload_Timestamp", "call_recording_url", "language_detected", "call_category"]].dropna(), use_container_width=True)

# Export option
st.sidebar.download_button("Download Full CSV", df.to_csv(index=False), file_name="call_insights_export.csv")

# Footer
st.markdown("---")
st.caption("📞 Built for better agent insights and smarter AI call tracking.")
x

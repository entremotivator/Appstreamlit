import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from io import StringIO
import datetime
import pytz

st.set_page_config(page_title="📞 Live Call Center Dashboard", layout="wide")

# Required columns list
REQUIRED_COLUMNS = [
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

# Sidebar - Upload Google Service Account JSON file
st.sidebar.header("🔐 Google Sheets Authentication")
uploaded_json = st.sidebar.file_uploader("Upload Google Service Account JSON", type="json")

# Input: Google Sheets URL (public or shared with service account)
default_sheet_url = "https://docs.google.com/spreadsheets/d/1LFfNwb9lRQpIosSEvV3O6zIwymUIWeG9L_k7cxw1jQs/edit#gid=0"
sheet_url = st.sidebar.text_input("Google Sheets URL", value=default_sheet_url)

# Function to extract sheet ID from URL
def extract_sheet_id(url):
    try:
        return url.split("/d/")[1].split("/")[0]
    except Exception:
        return None

# Load data from Google Sheets live
@st.cache_data(ttl=300)
def load_gsheets_data(json_credentials, sheet_id):
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = Credentials.from_service_account_info(json_credentials, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheet_id)
        worksheet = sheet.sheet1
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)

        # Add missing required columns with empty values
        for col in REQUIRED_COLUMNS:
            if col not in df.columns:
                df[col] = ""

        # Reorder columns
        df = df[REQUIRED_COLUMNS]

        # Format call_duration_hms if empty but seconds exist
        if df["call_duration_hms"].isnull().all() or df["call_duration_hms"].eq("").all():
            def seconds_to_hms(x):
                try:
                    s = int(float(x))
                    return str(datetime.timedelta(seconds=s))
                except:
                    return ""
            df["call_duration_hms"] = df["call_duration_seconds"].apply(seconds_to_hms)

        # Add/refresh Upload_Timestamp
        df["Upload_Timestamp"] = datetime.datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        return df

    except Exception as e:
        st.error(f"Error loading Google Sheets data: {e}")
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

# Main app logic
if uploaded_json:
    try:
        import json
        json_creds = json.load(uploaded_json)
        sheet_id = extract_sheet_id(sheet_url)

        if not sheet_id:
            st.error("Invalid Google Sheets URL. Please check and try again.")
        else:
            with st.spinner("Loading live data from Google Sheets..."):
                df = load_gsheets_data(json_creds, sheet_id)

            if df.empty:
                st.warning("No data found in the sheet or sheet is empty.")
            else:
                # Filters
                st.sidebar.header("📅 Filters")
                unique_agents = ["All"] + sorted(df["voice_agent_name"].dropna().unique().tolist())
                selected_agent = st.sidebar.selectbox("Filter by Agent", unique_agents)
                selected_date = st.sidebar.date_input("Filter by Call Date", datetime.datetime.utcnow().date())

                filtered_df = df.copy()
                if selected_agent != "All":
                    filtered_df = filtered_df[filtered_df["voice_agent_name"] == selected_agent]
                filtered_df = filtered_df[filtered_df["call_date"] == selected_date.strftime("%Y-%m-%d")]

                # Tabs
                tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                    "📋 Call Log",
                    "📊 Agent Performance",
                    "🧠 AI Summary",
                    "📈 Metrics",
                    "🧭 Intent & Actions",
                    "🗣️ Sentiment & Emotion",
                    "📤 Upload Logs"
                ])

                with tab1:
                    st.subheader("📋 Complete Call Log")
                    st.dataframe(filtered_df, use_container_width=True)

                with tab2:
                    st.subheader("📊 Agent Performance Overview")
                    if not filtered_df.empty:
                        perf_df = filtered_df.groupby("voice_agent_name")["agent_performance_score"].mean().reset_index()
                        perf_df = perf_df.dropna()
                        if not perf_df.empty:
                            st.bar_chart(perf_df.rename(columns={"voice_agent_name":"Agent", "agent_performance_score":"Performance Score"}).set_index("Agent"))
                        else:
                            st.info("No performance data available.")
                    else:
                        st.info("No data to show for selected filters.")

                with tab3:
                    st.subheader("🧠 AI Summaries & Keywords")
                    ai_cols = ["call_id", "summary", "keyword_tags", "action_items"]
                    st.dataframe(filtered_df[ai_cols].dropna(how="all"), use_container_width=True)

                with tab4:
                    st.subheader("📈 Call Metrics")
                    st.metric("Total Calls", len(filtered_df))
                    avg_duration = filtered_df["call_duration_seconds"].dropna().astype(float).mean()
                    st.metric("Avg Call Duration (s)", f"{avg_duration:.2f}" if avg_duration else "N/A")
                    revenue_sum = filtered_df["revenue_impact"].dropna().astype(float).sum()
                    st.metric("Total Revenue Impact", f"${revenue_sum:.2f}" if revenue_sum else "N/A")

                    if not filtered_df.empty:
                        fig = px.histogram(filtered_df, x="call_duration_seconds", nbins=30, title="Call Duration Distribution")
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No data to visualize.")

                with tab5:
                    st.subheader("🧭 Intent Detection & Next Actions")
                    intent_cols = ["intent_detected", "action_items", "next_best_action", "follow_up_required"]
                    st.dataframe(filtered_df[intent_cols].dropna(how="all"), use_container_width=True)

                with tab6:
                    st.subheader("🗣️ Sentiment & Emotion Analytics")
                    sent_cols = [
                        "call_id", "sentiment_score", "emotion_detected",
                        "speech_rate_wpm", "silence_percentage", "interruption_count"
                    ]
                    st.dataframe(filtered_df[sent_cols].dropna(how="all"), use_container_width=True)

                with tab7:
                    st.subheader("📤 Upload & Metadata Logs")
                    meta_cols = ["call_id", "Upload_Timestamp", "call_recording_url", "language_detected", "call_category"]
                    st.dataframe(filtered_df[meta_cols].dropna(how="all"), use_container_width=True)

                # Download CSV button
                csv_data = filtered_df.to_csv(index=False).encode("utf-8")
                st.sidebar.download_button("📥 Download Filtered Data as CSV", data=csv_data, file_name="call_center_data.csv", mime="text/csv")

    except Exception as ex:
        st.error(f"Failed to process uploaded credentials or load data: {ex}")

else:
    st.info("Upload your Google Service Account JSON file via the sidebar to start loading live data.")


import streamlit as st
import pandas as pd
import json
import requests
from datetime import datetime, timezone
from io import StringIO
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Call CRM", layout="wide")
st.title("📞 Call CRM – Multi-Entry Management")

# --- Session-state storage for multiple call records ---
if "call_records" not in st.session_state:
    st.session_state.call_records = []

# --- Load data from Google Sheets ---
@st.cache_data(ttl=300)
def load_google_sheets_data(sheet_url):
    try:
        if "/spreadsheets/d/" in sheet_url:
            sheet_id = sheet_url.split("/spreadsheets/d/")[1].split("/")[0]
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        else:
            csv_url = sheet_url + "/export?format=csv"
        response = requests.get(csv_url)
        response.raise_for_status()
        return pd.read_csv(StringIO(response.text))
    except Exception as e:
        st.error(f"Error loading Google Sheets data: {str(e)}")
        return None

def convert_sheets_to_records(df):
    records = []
    for _, row in df.iterrows():
        record = {
            "transcript": str(row.get("transcript", row.get("call_summary", ""))),
            "recording_url": str(row.get("recording_url", "")),
            "call_summary": str(row.get("call_summary", "")),
            "cost": float(row.get("cost", row.get("call_cost", 0.0))) if pd.notna(row.get("cost", row.get("call_cost"))) else 0.0,
            "customer_number": str(row.get("customer_number", row.get("phone number", ""))),
            "started_at": str(row.get("started_at", row.get("call_start_time", ""))),
            "ended_at": str(row.get("ended_at", row.get("call_end_time", ""))),
            "call_id": str(row.get("call_id", f"SHEET{len(records) + 1:04d}")),
            "added_at": datetime.now().isoformat(),
            "source": "google_sheets"
        }
        records.append(record)
    return records

# ----- Sidebar: Manual Entry + JSON Upload + Google Sheets -----
with st.sidebar:
    st.header("➕ Add Call Record")

    with st.form("add_call_form", clear_on_submit=True):
        transcript = st.text_area("Transcript", height=100)
        recording_url = st.text_input("Recording URL", placeholder="https://...")
        call_summary = st.text_area("Summary", height=60)
        cost = st.number_input("Cost (USD)", min_value=0.0, format="%.2f")
        customer_number = st.text_input("Customer Number", placeholder="+1...")
        started_at = st.text_input("Started At (ISO)", placeholder="YYYY-MM-DDTHH:MM:SSZ")
        ended_at = st.text_input("Ended At (ISO)", placeholder="YYYY-MM-DDTHH:MM:SSZ")
        call_id = st.text_input("Call ID")
        submitted = st.form_submit_button("Add Call")
        if submitted:
            st.session_state.call_records.append({
                "transcript": transcript,
                "recording_url": recording_url,
                "call_summary": call_summary,
                "cost": cost,
                "customer_number": customer_number,
                "started_at": started_at,
                "ended_at": ended_at,
                "call_id": call_id if call_id else f"ID{len(st.session_state.call_records)+1:04d}",
                "added_at": datetime.now().isoformat(),
                "source": "manual"
            })
            st.success("✔️ Call record added!")

    st.divider()
    st.header("📁 Upload JSON Data")
    uploaded_file = st.file_uploader("Choose a JSON file", type=["json"])
    if uploaded_file is not None:
        try:
            json_data = json.load(uploaded_file)
            if isinstance(json_data, list):
                records_to_add = json_data
            elif isinstance(json_data, dict) and "records" in json_data:
                records_to_add = json_data["records"]
            elif isinstance(json_data, dict):
                records_to_add = [json_data]
            else:
                st.error("Invalid JSON format")
                records_to_add = []
            if st.button("Import JSON Records"):
                imported_count = 0
                for record in records_to_add:
                    formatted = {
                        "transcript": record.get("transcript", ""),
                        "recording_url": record.get("recording_url", ""),
                        "call_summary": record.get("call_summary", ""),
                        "cost": float(record.get("cost", 0.0)),
                        "customer_number": record.get("customer_number", ""),
                        "started_at": record.get("started_at", ""),
                        "ended_at": record.get("ended_at", ""),
                        "call_id": record.get("call_id", f"JSON{len(st.session_state.call_records)+imported_count+1:04d}"),
                        "added_at": datetime.now().isoformat(),
                        "source": "json_upload"
                    }
                    st.session_state.call_records.append(formatted)
                    imported_count += 1
                st.success(f"✔️ Imported {imported_count} records!")
        except json.JSONDecodeError:
            st.error("Invalid JSON file format.")
        except Exception as e:
            st.error(f"Error processing JSON file: {str(e)}")

    st.divider()
    st.header("📊 Google Sheets Integration")
    sheets_url = st.text_input(
        "Google Sheets URL",
        value="https://docs.google.com/spreadsheets/d/1LFfNwb9lRQpIosSEvV3O6zIwymUIWeG9L_k7cxw1jQs/",
        help="Paste the public Google Sheets link here"
    )

    st.markdown("### 🔄 Auto-Refresh Settings")
    enable_autorefresh = st.checkbox("Enable auto-refresh from Google Sheets")
    refresh_minutes = st.selectbox("Refresh every:", [1, 2, 5, 10, 15], index=2)
    if enable_autorefresh:
        st_autorefresh(interval=refresh_minutes * 60 * 1000, key="autorefresh")

    manual_load = st.button("📥 Load from Google Sheets")
    if manual_load or enable_autorefresh:
        with st.spinner("Fetching data from Google Sheets..."):
            df = load_google_sheets_data(sheets_url)
            if df is not None and not df.empty:
                new_records = convert_sheets_to_records(df)
                st.session_state.call_records = [
                    r for r in st.session_state.call_records if r.get("source") != "google_sheets"
                ]
                st.session_state.call_records.extend(new_records)
                st.success(f"✅ Loaded {len(new_records)} records from Google Sheets.")
            elif df is not None:
                st.warning("⚠️ Sheet is accessible but contains no data.")
            else:
                st.error("❌ Failed to load Google Sheets data.")

    if manual_load or enable_autorefresh:
        st.caption(f"🕒 Last synced at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S %Z')}")

# ---- Main Display: All Records ----
st.header("📋 All Calls Overview")
if st.session_state.call_records:
    df = pd.DataFrame(st.session_state.call_records)
    df["transcript_short"] = df["transcript"].str.slice(0, 30) + "..."
    show_cols = ["call_id", "customer_number", "started_at", "cost", "transcript_short", "call_summary", "source"]
    st.dataframe(df[show_cols], use_container_width=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Calls", len(df))
    col2.metric("Total Cost", f"${df['cost'].sum():.2f}")
    col3.metric("Manual Entries", len(df[df["source"] == "manual"]))
    col4.metric("Imported Records", len(df[df["source"].isin(["json_upload", "google_sheets"])]))

    call_ids = df["call_id"].tolist()
    selected_id = st.selectbox("🔎 Select Call", call_ids)
    selected = df[df["call_id"] == selected_id].iloc[0].to_dict()

    tabs = st.tabs(["Transcript", "Summary", "Customer Info", "Recording", "Cost & Timing"])
    with tabs[0]:
        st.subheader("Transcript")
        st.text_area("Transcript", value=selected["transcript"], height=200, key=f"t_{selected_id}")
    with tabs[1]:
        st.subheader("Summary")
        st.write(selected["call_summary"])
    with tabs[2]:
        st.subheader("Customer Info")
        st.text_input("Number", value=selected["customer_number"], disabled=True)
        st.text_input("Call ID", value=selected["call_id"], disabled=True)
        st.text_input("Source", value=selected.get("source", "unknown"), disabled=True)
    with tabs[3]:
        st.subheader("Call Recording")
        if selected["recording_url"]:
            st.audio(selected["recording_url"], format="audio/wav")
        else:
            st.info("No recording URL available.")
    with tabs[4]:
        st.subheader("Cost & Timing")
        st.metric("Cost", f"${selected['cost']:.2f}")
        st.write(f"Start: {selected['started_at']}")
        st.write(f"End: {selected['ended_at']}")
        st.write(f"Added: {selected['added_at']}")

    st.divider()
    if st.button("🗑️ Clear All Records"):
        st.session_state.call_records = []
        st.success("All records cleared!")

else:
    st.info("No records yet. Use the sidebar to add or load data.")

# ---- Instructions ----
with st.expander("ℹ️ How to Use This CRM"):
    st.write("""
    **Features:**
    - Add call records manually
    - Upload JSON files with records
    - Sync from Google Sheets (public URL only)
    - Auto-refresh every few minutes (optional)

    **Sheet columns:** `transcript`, `recording_url`, `call_summary`, `cost`, `customer_number`, `started_at`, `ended_at`, `call_id`

    **Note:** Data is session-based only. You can export or save via backend later.
    """)

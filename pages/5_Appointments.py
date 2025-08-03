import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# ---------- Configuration ----------
STATIC_SHEET_URL = "https://docs.google.com/spreadsheets/d/1mgToY7I10uwPrdPnjAO9gosgoaEKJCf7nv-E0-1UfVQ/edit#gid=0"
SHEET_SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# ---------- Streamlit Page Settings ----------
st.set_page_config(
    page_title="🚀 Advanced CRM System", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .confirmed { background-color: #28a745; color: white; }
    .pending { background-color: #ffc107; color: black; }
    .cancelled { background-color: #dc3545; color: white; }
    .completed { background-color: #6c757d; color: white; }
</style>
""", unsafe_allow_html=True)

st.title("🚀 Advanced CRM System")

# ---------- Helper Functions ----------
@st.cache_data
def load_data_from_sheets(json_credentials, sheet_url):
    """Load data from Google Sheets with error handling"""
    try:
        # Parse JSON credentials
        if isinstance(json_credentials, str):
            creds_dict = json.loads(json_credentials)
        else:
            creds_dict = json.load(json_credentials)
        
        # Authenticate and connect
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SHEET_SCOPE)
        client = gspread.authorize(creds)
        
        # Extract sheet ID from URL
        sheet_id = sheet_url.split('/d/')[1].split('/')[0]
        spreadsheet = client.open_by_key(sheet_id)
        
        # Load all worksheets
        worksheets = {}
        for worksheet in spreadsheet.worksheets():
            try:
                data = worksheet.get_all_records()
                if data:  # Only add non-empty worksheets
                    worksheets[worksheet.title] = pd.DataFrame(data)
            except Exception as e:
                st.warning(f"Could not load worksheet '{worksheet.title}': {str(e)}")
        
        return worksheets, None
    
    except Exception as e:
        return None, str(e)

def create_sample_data():
    """Create sample data if no Google Sheets connection"""
    return {
        'Contacts': pd.DataFrame({
            'Name': ['John Doe', 'Jane Smith', 'Bob Johnson'],
            'Email': ['john@email.com', 'jane@email.com', 'bob@email.com'],
            'Phone': ['123-456-7890', '098-765-4321', '555-123-4567'],
            'Status': ['Active', 'Active', 'Inactive']
        }),
        'Appointments': pd.DataFrame({
            'Date': ['2024-01-15', '2024-01-16', '2024-01-17'],
            'Client': ['John Doe', 'Jane Smith', 'Bob Johnson'],
            'Status': ['Confirmed', 'Pending', 'Cancelled'],
            'Time': ['10:00 AM', '2:00 PM', '11:00 AM']
        }),
        'Leads': pd.DataFrame({
            'Name': ['Alice Brown', 'Charlie Wilson', 'Diana Lee'],
            'Source': ['Website', 'Referral', 'Social Media'],
            'Status': ['New', 'Qualified', 'Converted'],
            'Value': [1000, 2500, 5000]
        })
    }

# ---------- Sidebar Navigation ----------
def sidebar_navigation():
    st.sidebar.header("🔐 Google Sheets Access")
    json_file = st.sidebar.file_uploader("Upload your `service_account.json`", type="json")
    
    # Initialize session state for data
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
        st.session_state.worksheets = create_sample_data()
        st.session_state.error_message = None
    
    # Handle file upload
    if json_file is not None:
        try:
            # Read the uploaded file
            json_content = json_file.read()
            
            with st.sidebar.spinner("Loading data from Google Sheets..."):
                worksheets, error = load_data_from_sheets(json_content, STATIC_SHEET_URL)
            
            if error:
                st.sidebar.error(f"Error loading data: {error}")
                st.session_state.worksheets = create_sample_data()
                st.session_state.data_loaded = False
                st.session_state.error_message = error
            else:
                st.sidebar.success("✅ Data loaded successfully!")
                st.session_state.worksheets = worksheets
                st.session_state.data_loaded = True
                st.session_state.error_message = None
                
        except Exception as e:
            st.sidebar.error(f"Error processing file: {str(e)}")
            st.session_state.worksheets = create_sample_data()
            st.session_state.data_loaded = False
    
    st.sidebar.markdown("---")
    st.sidebar.header("📊 Navigation")
    page = st.sidebar.selectbox(
        "Select Page",
        ["📋 Dashboard", "📅 Appointments", "👥 Contacts", "🎯 Leads", "📈 Analytics", "⚙️ Settings"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("✅ **Data Source:**")
    if st.session_state.data_loaded:
        st.sidebar.success("Google Sheets Connected")
    else:
        st.sidebar.info("Using Sample Data")
    
    return page

# ---------- Dashboard Functions ----------
def show_dashboard():
    st.header("📋 Dashboard Overview")
    
    # Get data
    worksheets = st.session_state.worksheets
    
    # Create metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        contacts_count = len(worksheets.get('Contacts', pd.DataFrame()))
        st.metric("👥 Total Contacts", contacts_count)
    
    with col2:
        appointments_count = len(worksheets.get('Appointments', pd.DataFrame()))
        st.metric("📅 Appointments", appointments_count)
    
    with col3:
        leads_count = len(worksheets.get('Leads', pd.DataFrame()))
        st.metric("🎯 Leads", leads_count)
    
    with col4:
        if 'Leads' in worksheets and 'Value' in worksheets['Leads'].columns:
            total_value = worksheets['Leads']['Value'].sum()
            st.metric("💰 Total Lead Value", f"${total_value:,}")
        else:
            st.metric("💰 Total Lead Value", "$0")
    
    # Recent activities
    st.subheader("📊 Recent Activities")
    
    if 'Appointments' in worksheets:
        appointments_df = worksheets['Appointments']
        if not appointments_df.empty:
            st.dataframe(appointments_df.head(5), use_container_width=True)
        else:
            st.info("No appointments data available")
    else:
        st.info("No appointments data available")

def show_contacts():
    st.header("👥 Contacts Management")
    
    if 'Contacts' in st.session_state.worksheets:
        contacts_df = st.session_state.worksheets['Contacts']
        if not contacts_df.empty:
            st.dataframe(contacts_df, use_container_width=True)
        else:
            st.info("No contacts data available")
    else:
        st.info("No contacts data available")

def show_appointments():
    st.header("📅 Appointments")
    
    if 'Appointments' in st.session_state.worksheets:
        appointments_df = st.session_state.worksheets['Appointments']
        if not appointments_df.empty:
            st.dataframe(appointments_df, use_container_width=True)
        else:
            st.info("No appointments data available")
    else:
        st.info("No appointments data available")

def show_leads():
    st.header("🎯 Leads Management")
    
    if 'Leads' in st.session_state.worksheets:
        leads_df = st.session_state.worksheets['Leads']
        if not leads_df.empty:
            st.dataframe(leads_df, use_container_width=True)
        else:
            st.info("No leads data available")
    else:
        st.info("No leads data available")

def show_analytics():
    st.header("📈 Analytics")
    
    worksheets = st.session_state.worksheets
    
    if 'Leads' in worksheets and 'Status' in worksheets['Leads'].columns:
        leads_df = worksheets['Leads']
        
        # Lead status distribution
        status_counts = leads_df['Status'].value_counts()
        fig = px.pie(values=status_counts.values, names=status_counts.index, 
                    title="Lead Status Distribution")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No analytics data available")

def show_settings():
    st.header("⚙️ Settings")
    st.info("Settings page - Configuration options would go here")

# ---------- Main Application ----------
def main():
    # Get current page from sidebar
    current_page = sidebar_navigation()
    
    # Show error message if there was an authentication issue
    if st.session_state.error_message:
        st.error(f"Authentication Error: {st.session_state.error_message}")
        st.info("Please check your service account JSON file and try again. Using sample data for now.")
    
    # Route to appropriate page
    if current_page == "📋 Dashboard":
        show_dashboard()
    elif current_page == "👥 Contacts":
        show_contacts()
    elif current_page == "📅 Appointments":
        show_appointments()
    elif current_page == "🎯 Leads":
        show_leads()
    elif current_page == "📈 Analytics":
        show_analytics()
    elif current_page == "⚙️ Settings":
        show_settings()

# ---------- Run Application ----------
if __name__ == "__main__":
    main()

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
def append_to_sheet(worksheet_name, data_dict):
    """Append new data to Google Sheet"""
    try:
        if st.session_state.get('spreadsheet') is None:
            return False, "No Google Sheets connection available"
        
        worksheet = st.session_state.spreadsheet.worksheet(worksheet_name)
        
        # Convert dict to list in the order of existing columns
        headers = worksheet.row_values(1)
        row_data = [data_dict.get(header, '') for header in headers]
        
        # Append the row
        worksheet.append_row(row_data)
        return True, "Data added successfully!"
        
    except Exception as e:
        return False, str(e)

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
        st.session_state.client = None
        st.session_state.spreadsheet = None
    
    # Handle file upload
    if json_file is not None:
        try:
            # Read the uploaded file
            json_content = json_file.read()
            
            with st.spinner("Loading data from Google Sheets..."):
                worksheets, error = load_data_from_sheets(json_content, STATIC_SHEET_URL)
            
            if error:
                st.sidebar.error(f"Error loading data: {error}")
                st.session_state.worksheets = create_sample_data()
                st.session_state.data_loaded = False
                st.session_state.error_message = error
                st.session_state.client = None
                st.session_state.spreadsheet = None
            else:
                st.sidebar.success("✅ Data loaded successfully!")
                st.session_state.worksheets = worksheets
                st.session_state.data_loaded = True
                st.session_state.error_message = None
                
                # Store client and spreadsheet for appending data
                creds_dict = json.loads(json_content) if isinstance(json_content, bytes) else json.load(json_content)
                creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SHEET_SCOPE)
                client = gspread.authorize(creds)
                sheet_id = STATIC_SHEET_URL.split('/d/')[1].split('/')[0]
                st.session_state.client = client
                st.session_state.spreadsheet = client.open_by_key(sheet_id)
                
        except Exception as e:
            st.sidebar.error(f"Error processing file: {str(e)}")
            st.session_state.worksheets = create_sample_data()
            st.session_state.data_loaded = False
            st.session_state.client = None
            st.session_state.spreadsheet = None
    
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
    
    # Add new contact form
    with st.expander("➕ Add New Contact"):
        with st.form("add_contact_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Name*")
                email = st.text_input("Email*")
            with col2:
                phone = st.text_input("Phone")
                status = st.selectbox("Status", ["Active", "Inactive"])
            
            submitted = st.form_submit_button("Add Contact")
            
            if submitted:
                if name and email:
                    new_contact = {
                        'Name': name,
                        'Email': email,
                        'Phone': phone,
                        'Status': status
                    }
                    
                    if st.session_state.data_loaded:
                        success, message = append_to_sheet('Contacts', new_contact)
                        if success:
                            st.success(message)
                            # Refresh data
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"Error adding contact: {message}")
                    else:
                        st.warning("Google Sheets not connected. Contact added to local data only.")
                        # Add to local data
                        if 'Contacts' in st.session_state.worksheets:
                            new_row = pd.DataFrame([new_contact])
                            st.session_state.worksheets['Contacts'] = pd.concat([st.session_state.worksheets['Contacts'], new_row], ignore_index=True)
                        st.success("Contact added to local data!")
                        st.rerun()
                else:
                    st.error("Please fill in required fields (Name and Email)")
    
    # Display contacts
    if 'Contacts' in st.session_state.worksheets:
        contacts_df = st.session_state.worksheets['Contacts']
        if not contacts_df.empty:
            st.subheader("📋 Current Contacts")
            st.dataframe(contacts_df, use_container_width=True)
        else:
            st.info("No contacts data available")
    else:
        st.info("No contacts data available")

def show_appointments():
    st.header("📅 Appointments")
    
    # Add new appointment form
    with st.expander("➕ Add New Appointment"):
        with st.form("add_appointment_form"):
            col1, col2 = st.columns(2)
            with col1:
                date = st.date_input("Date*")
                client = st.text_input("Client Name*")
            with col2:
                time = st.time_input("Time*")
                status = st.selectbox("Status", ["Confirmed", "Pending", "Cancelled", "Completed"])
            
            notes = st.text_area("Notes (optional)")
            submitted = st.form_submit_button("Add Appointment")
            
            if submitted:
                if date and client and time:
                    new_appointment = {
                        'Date': date.strftime('%Y-%m-%d'),
                        'Client': client,
                        'Time': time.strftime('%I:%M %p'),
                        'Status': status,
                        'Notes': notes
                    }
                    
                    if st.session_state.data_loaded:
                        success, message = append_to_sheet('Appointments', new_appointment)
                        if success:
                            st.success(message)
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"Error adding appointment: {message}")
                    else:
                        st.warning("Google Sheets not connected. Appointment added to local data only.")
                        if 'Appointments' in st.session_state.worksheets:
                            new_row = pd.DataFrame([new_appointment])
                            st.session_state.worksheets['Appointments'] = pd.concat([st.session_state.worksheets['Appointments'], new_row], ignore_index=True)
                        st.success("Appointment added to local data!")
                        st.rerun()
                else:
                    st.error("Please fill in required fields (Date, Client, and Time)")
    
    # Display appointments
    if 'Appointments' in st.session_state.worksheets:
        appointments_df = st.session_state.worksheets['Appointments']
        if not appointments_df.empty:
            st.subheader("📋 Current Appointments")
            
            # Filter appointments
            col1, col2 = st.columns(2)
            with col1:
                status_filter = st.multiselect("Filter by Status", 
                                             options=appointments_df['Status'].unique() if 'Status' in appointments_df.columns else [],
                                             default=appointments_df['Status'].unique() if 'Status' in appointments_df.columns else [])
            with col2:
                date_filter = st.date_input("Filter by Date (optional)")
            
            # Apply filters
            filtered_df = appointments_df.copy()
            if status_filter:
                filtered_df = filtered_df[filtered_df['Status'].isin(status_filter)]
            if date_filter:
                filtered_df = filtered_df[filtered_df['Date'] == date_filter.strftime('%Y-%m-%d')]
            
            st.dataframe(filtered_df, use_container_width=True)
        else:
            st.info("No appointments data available")
    else:
        st.info("No appointments data available")

def show_leads():
    st.header("🎯 Leads Management")
    
    # Add new lead form
    with st.expander("➕ Add New Lead"):
        with st.form("add_lead_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Lead Name*")
                source = st.selectbox("Source", ["Website", "Referral", "Social Media", "Cold Call", "Email Campaign", "Other"])
            with col2:
                status = st.selectbox("Status", ["New", "Contacted", "Qualified", "Proposal", "Converted", "Lost"])
                value = st.number_input("Estimated Value ($)", min_value=0, value=0)
            
            notes = st.text_area("Notes (optional)")
            submitted = st.form_submit_button("Add Lead")
            
            if submitted:
                if name:
                    new_lead = {
                        'Name': name,
                        'Source': source,
                        'Status': status,
                        'Value': value,
                        'Notes': notes,
                        'Date Added': datetime.now().strftime('%Y-%m-%d')
                    }
                    
                    if st.session_state.data_loaded:
                        success, message = append_to_sheet('Leads', new_lead)
                        if success:
                            st.success(message)
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"Error adding lead: {message}")
                    else:
                        st.warning("Google Sheets not connected. Lead added to local data only.")
                        if 'Leads' in st.session_state.worksheets:
                            new_row = pd.DataFrame([new_lead])
                            st.session_state.worksheets['Leads'] = pd.concat([st.session_state.worksheets['Leads'], new_row], ignore_index=True)
                        st.success("Lead added to local data!")
                        st.rerun()
                else:
                    st.error("Please enter a lead name")
    
    # Display leads
    if 'Leads' in st.session_state.worksheets:
        leads_df = st.session_state.worksheets['Leads']
        if not leads_df.empty:
            st.subheader("📋 Current Leads")
            
            # Lead metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                total_leads = len(leads_df)
                st.metric("Total Leads", total_leads)
            with col2:
                if 'Value' in leads_df.columns:
                    total_value = leads_df['Value'].sum()
                    st.metric("Total Pipeline Value", f"${total_value:,.2f}")
            with col3:
                if 'Status' in leads_df.columns:
                    converted = len(leads_df[leads_df['Status'] == 'Converted'])
                    conversion_rate = (converted / total_leads * 100) if total_leads > 0 else 0
                    st.metric("Conversion Rate", f"{conversion_rate:.1f}%")
            
            # Filter leads
            col1, col2 = st.columns(2)
            with col1:
                if 'Status' in leads_df.columns:
                    status_filter = st.multiselect("Filter by Status", 
                                                 options=leads_df['Status'].unique(),
                                                 default=leads_df['Status'].unique())
            with col2:
                if 'Source' in leads_df.columns:
                    source_filter = st.multiselect("Filter by Source", 
                                                  options=leads_df['Source'].unique(),
                                                  default=leads_df['Source'].unique())
            
            # Apply filters
            filtered_df = leads_df.copy()
            if 'Status' in leads_df.columns and status_filter:
                filtered_df = filtered_df[filtered_df['Status'].isin(status_filter)]
            if 'Source' in leads_df.columns and source_filter:
                filtered_df = filtered_df[filtered_df['Source'].isin(source_filter)]
            
            st.dataframe(filtered_df, use_container_width=True)
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

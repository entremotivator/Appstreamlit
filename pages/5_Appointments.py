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
STATIC_SHEET_URL = "https://docs.google.com/spreadsheets/d/1LFfNwb9lRQpIosSEvV3O6zIwymUIWeG9L_k7cxw1jQs/edit#gid=0"
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

# ---------- Sidebar Navigation ----------
def sidebar_navigation():
    st.sidebar.header("🔐 Google Sheets Access")
    json_file = st.sidebar.file_uploader("Upload your `service_account.json`", type="json")
    
    st.sidebar.markdown("---")
    st.sidebar.header("📊 Navigation")
    page = st.sidebar.selectbox(
        "Select Page",
        ["📋 Dashboard", "📅 Appointments", "👥 Contacts", "🎯 Leads", "📈 Analytics", "⚙️ Settings"]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("✅ **Data Source:**")
    st.sidebar.code(STATIC_SHEET_URL, language="text")
    
    return json_file, page

# ---------- Load Google Sheets Data ----------
@st.cache_data(show_spinner=True)
def load_gsheet_data(credentials_dict):
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, SHEET_SCOPE)
        client = gspread.authorize(creds)
        sheet = client.open_by_url(STATIC_SHEET_URL).sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error loading Google Sheets data: {e}")
        return None

# ---------- Enhanced Demo Data ----------
def get_demo_data():
    # Appointments data
    appointments = pd.DataFrame([
        {
            "Email": "customallstars@gmail.com",
            "Guest Email": "client1@company.com",
            "Name": "Vietnamese Services",
            "Status": "confirmed",
            "Event ID": "7e62f941-c6f8-42c8-bf2b-fac739b2ded7",
            "Start Time (12hr)": "7/24/2025 1:00pm",
            "Start Time (24hr)": "7/24/2025 13:00",
            "Google Meet Link": "https://meet.google.com/kkp-htju-itz",
            "Duration": "60 min",
            "Type": "Consultation"
        },
        {
            "Email": "customallstars@gmail.com",
            "Guest Email": "don.hudson@email.com",
            "Name": "Don Hudson",
            "Status": "confirmed",
            "Event ID": "d1b7ff1b-f4a1-4337-9416-928bb3f3b2ab",
            "Start Time (12hr)": "7/24/2025 2:00pm",
            "Start Time (24hr)": "7/24/2025 14:00",
            "Google Meet Link": "https://meet.google.com/ebj-ctqh-dxf",
            "Duration": "45 min",
            "Type": "Follow-up"
        },
        {
            "Email": "customallstars@gmail.com",
            "Guest Email": "sarah.johnson@corp.com",
            "Name": "Sarah Johnson",
            "Status": "pending",
            "Event ID": "abc123",
            "Start Time (12hr)": "7/25/2025 10:00am",
            "Start Time (24hr)": "7/25/2025 10:00",
            "Google Meet Link": "https://meet.google.com/xyz-abc-def",
            "Duration": "30 min",
            "Type": "Sales Call"
        }
    ])
    
    # Contacts data
    contacts = pd.DataFrame([
        {
            "Name": "Vietnamese Services",
            "Email": "client1@company.com",
            "Phone": "+1-555-0101",
            "Company": "VN Corp",
            "Position": "Manager",
            "Lead Source": "Website",
            "Tags": "VIP, Enterprise",
            "Last Contact": "2025-07-20",
            "Status": "Active Customer"
        },
        {
            "Name": "Don Hudson",
            "Email": "don.hudson@email.com",
            "Phone": "+1-555-0102",
            "Company": "Hudson LLC",
            "Position": "CEO",
            "Lead Source": "Referral",
            "Tags": "High Value",
            "Last Contact": "2025-07-22",
            "Status": "Prospect"
        },
        {
            "Name": "Sarah Johnson",
            "Email": "sarah.johnson@corp.com",
            "Phone": "+1-555-0103",
            "Company": "Johnson Corp",
            "Position": "Director",
            "Lead Source": "LinkedIn",
            "Tags": "Tech, SaaS",
            "Last Contact": "2025-07-23",
            "Status": "Lead"
        }
    ])
    
    # Leads data
    leads = pd.DataFrame([
        {
            "Lead ID": "L001",
            "Name": "Tech Startup Inc",
            "Email": "contact@techstartup.com",
            "Lead Score": 85,
            "Stage": "Qualified",
            "Source": "Google Ads",
            "Value": "$50,000",
            "Probability": "75%",
            "Expected Close": "2025-08-15",
            "Assigned To": "Sales Rep 1"
        },
        {
            "Lead ID": "L002",
            "Name": "Enterprise Solutions",
            "Email": "info@enterprise.com",
            "Lead Score": 92,
            "Stage": "Proposal",
            "Source": "Trade Show",
            "Value": "$125,000",
            "Probability": "60%",
            "Expected Close": "2025-09-01",
            "Assigned To": "Sales Rep 2"
        },
        {
            "Lead ID": "L003",
            "Name": "Small Business Co",
            "Email": "hello@smallbiz.com",
            "Lead Score": 45,
            "Stage": "New",
            "Source": "Website",
            "Value": "$10,000",
            "Probability": "25%",
            "Expected Close": "2025-08-30",
            "Assigned To": "Sales Rep 1"
        }
    ])
    
    return appointments, contacts, leads

# ---------- Dashboard Page ----------
def dashboard_page(appointments_df, contacts_df, leads_df):
    st.header("📋 CRM Dashboard")
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_appointments = len(appointments_df)
        st.metric("📅 Total Appointments", total_appointments)
    
    with col2:
        total_contacts = len(contacts_df)
        st.metric("👥 Total Contacts", total_contacts)
    
    with col3:
        total_leads = len(leads_df)
        st.metric("🎯 Active Leads", total_leads)
    
    with col4:
        if 'Value' in leads_df.columns:
            pipeline_value = leads_df['Value'].str.replace('$', '').str.replace(',', '').astype(float).sum()
            st.metric("💰 Pipeline Value", f"${pipeline_value:,.0f}")
    
    st.markdown("---")
    
    # Charts Row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Appointment Status Distribution")
        if 'Status' in appointments_df.columns:
            status_counts = appointments_df['Status'].value_counts()
            fig = px.pie(values=status_counts.values, names=status_counts.index, 
                        color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Lead Pipeline Stages")
        if 'Stage' in leads_df.columns:
            stage_counts = leads_df['Stage'].value_counts()
            fig = px.bar(x=stage_counts.index, y=stage_counts.values,
                        color=stage_counts.values, color_continuous_scale='Blues')
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
    
    # Recent Activity
    st.subheader("🕐 Recent Activity")
    recent_appointments = appointments_df.head(5)
    st.dataframe(recent_appointments[['Name', 'Status', 'Start Time (12hr)', 'Type']], 
                use_container_width=True)

# ---------- Appointments Page ----------
def appointments_page(df):
    st.header("📅 Appointment Manager")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.multiselect(
            "Filter by Status",
            options=df['Status'].unique() if 'Status' in df.columns else [],
            default=df['Status'].unique() if 'Status' in df.columns else []
        )
    
    with col2:
        if 'Type' in df.columns:
            type_filter = st.multiselect(
                "Filter by Type",
                options=df['Type'].unique(),
                default=df['Type'].unique()
            )
        else:
            type_filter = []
    
    with col3:
        search_term = st.text_input("🔍 Search by Name or Email")
    
    # Apply filters
    filtered_df = df.copy()
    if status_filter and 'Status' in df.columns:
        filtered_df = filtered_df[filtered_df['Status'].isin(status_filter)]
    if type_filter and 'Type' in df.columns:
        filtered_df = filtered_df[filtered_df['Type'].isin(type_filter)]
    if search_term:
        filtered_df = filtered_df[
            filtered_df['Name'].str.contains(search_term, case=False, na=False) |
            filtered_df['Email'].str.contains(search_term, case=False, na=False)
        ]
    
    # Display appointments
    st.subheader(f"📋 Appointments ({len(filtered_df)} results)")
    
    # Enhanced display with status badges
    for idx, row in filtered_df.iterrows():
        with st.expander(f"📅 {row['Name']} - {row['Start Time (12hr)']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Email:** {row['Email']}")
                st.write(f"**Guest Email:** {row['Guest Email']}")
                if 'Duration' in row:
                    st.write(f"**Duration:** {row['Duration']}")
                if 'Type' in row:
                    st.write(f"**Type:** {row['Type']}")
            with col2:
                status = row['Status']
                st.markdown(f'<span class="status-badge {status}">{status.upper()}</span>', 
                           unsafe_allow_html=True)
                if 'Google Meet Link' in row and row['Google Meet Link']:
                    st.markdown(f"[🎥 Join Meeting]({row['Google Meet Link']})")
    
    # Bulk actions
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="⬇️ Download Filtered Data",
            data=filtered_df.to_csv(index=False),
            file_name=f"appointments_filtered_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    with col2:
        if st.button("📧 Send Reminder Emails"):
            st.success(f"Reminder emails would be sent to {len(filtered_df)} contacts")

# ---------- Contacts Page ----------
def contacts_page(contacts_df):
    st.header("👥 Contact Management")
    
    # Add new contact form
    with st.expander("➕ Add New Contact"):
        col1, col2 = st.columns(2)
        with col1:
            new_name = st.text_input("Name")
            new_email = st.text_input("Email")
            new_phone = st.text_input("Phone")
        with col2:
            new_company = st.text_input("Company")
            new_position = st.text_input("Position")
            new_source = st.selectbox("Lead Source", ["Website", "Referral", "LinkedIn", "Google Ads", "Trade Show"])
        
        new_tags = st.text_input("Tags (comma-separated)")
        
        if st.button("➕ Add Contact"):
            st.success(f"Contact '{new_name}' would be added to the system")
    
    st.markdown("---")
    
    # Contact filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.multiselect(
            "Filter by Status",
            options=contacts_df['Status'].unique() if 'Status' in contacts_df.columns else [],
            default=contacts_df['Status'].unique() if 'Status' in contacts_df.columns else []
        )
    
    with col2:
        source_filter = st.multiselect(
            "Filter by Lead Source",
            options=contacts_df['Lead Source'].unique() if 'Lead Source' in contacts_df.columns else [],
            default=contacts_df['Lead Source'].unique() if 'Lead Source' in contacts_df.columns else []
        )
    
    with col3:
        search_contacts = st.text_input("🔍 Search Contacts")
    
    # Apply filters
    filtered_contacts = contacts_df.copy()
    if status_filter and 'Status' in contacts_df.columns:
        filtered_contacts = filtered_contacts[filtered_contacts['Status'].isin(status_filter)]
    if source_filter and 'Lead Source' in contacts_df.columns:
        filtered_contacts = filtered_contacts[filtered_contacts['Lead Source'].isin(source_filter)]
    if search_contacts:
        filtered_contacts = filtered_contacts[
            filtered_contacts['Name'].str.contains(search_contacts, case=False, na=False) |
            filtered_contacts['Company'].str.contains(search_contacts, case=False, na=False)
        ]
    
    # Display contacts
    st.subheader(f"👥 Contacts ({len(filtered_contacts)} results)")
    st.dataframe(filtered_contacts, use_container_width=True)
    
    # Contact actions
    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button(
            "⬇️ Export Contacts",
            data=filtered_contacts.to_csv(index=False),
            file_name=f"contacts_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    with col2:
        if st.button("📧 Email Campaign"):
            st.success(f"Email campaign would be sent to {len(filtered_contacts)} contacts")
    
    with col3:
        if st.button("🏷️ Bulk Tag"):
            bulk_tag = st.text_input("Enter tag to apply")
            if bulk_tag:
                st.success(f"Tag '{bulk_tag}' would be applied to selected contacts")

# ---------- Leads Page ----------
def leads_page(leads_df):
    st.header("🎯 Lead Management")
    
    # Lead pipeline overview
    col1, col2, col3, col4 = st.columns(4)
    
    stage_counts = leads_df['Stage'].value_counts() if 'Stage' in leads_df.columns else {}
    
    with col1:
        new_leads = stage_counts.get('New', 0)
        st.metric("🆕 New Leads", new_leads)
    
    with col2:
        qualified = stage_counts.get('Qualified', 0)
        st.metric("✅ Qualified", qualified)
    
    with col3:
        proposals = stage_counts.get('Proposal', 0)
        st.metric("📋 Proposals", proposals)
    
    with col4:
        if 'Lead Score' in leads_df.columns:
            avg_score = leads_df['Lead Score'].mean()
            st.metric("📊 Avg Lead Score", f"{avg_score:.0f}")
    
    # Lead pipeline visualization
    st.subheader("🔄 Sales Pipeline")
    if 'Stage' in leads_df.columns and 'Value' in leads_df.columns:
        pipeline_data = leads_df.groupby('Stage')['Value'].apply(
            lambda x: x.str.replace('$', '').str.replace(',', '').astype(float).sum()
        ).reset_index()
        
        fig = px.funnel(pipeline_data, x='Value', y='Stage', 
                       title="Sales Pipeline by Stage")
        st.plotly_chart(fig, use_container_width=True)
    
    # Lead details
    st.subheader("📋 Lead Details")
    
    # Lead filters
    col1, col2 = st.columns(2)
    with col1:
        stage_filter = st.selectbox(
            "Filter by Stage",
            options=['All'] + list(leads_df['Stage'].unique()) if 'Stage' in leads_df.columns else ['All']
        )
    
    with col2:
        score_range = st.slider("Minimum Lead Score", 0, 100, 0)
    
    # Apply filters
    filtered_leads = leads_df.copy()
    if stage_filter != 'All' and 'Stage' in leads_df.columns:
        filtered_leads = filtered_leads[filtered_leads['Stage'] == stage_filter]
    if 'Lead Score' in leads_df.columns:
        filtered_leads = filtered_leads[filtered_leads['Lead Score'] >= score_range]
    
    # Display leads with enhanced formatting
    for idx, row in filtered_leads.iterrows():
        with st.expander(f"🎯 {row['Name']} - Score: {row.get('Lead Score', 'N/A')}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Email:** {row['Email']}")
                st.write(f"**Source:** {row.get('Source', 'N/A')}")
                st.write(f"**Assigned To:** {row.get('Assigned To', 'N/A')}")
            
            with col2:
                st.write(f"**Stage:** {row.get('Stage', 'N/A')}")
                st.write(f"**Value:** {row.get('Value', 'N/A')}")
                st.write(f"**Probability:** {row.get('Probability', 'N/A')}")
            
            with col3:
                st.write(f"**Expected Close:** {row.get('Expected Close', 'N/A')}")
                if st.button(f"📞 Contact {row['Name']}", key=f"contact_{idx}"):
                    st.success(f"Contact action initiated for {row['Name']}")

# ---------- Analytics Page ----------
def analytics_page(appointments_df, contacts_df, leads_df):
    st.header("📈 Analytics Dashboard")
    
    # Time-based analytics
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 Appointments Over Time")
        # Mock time series data
        dates = pd.date_range(start='2025-07-01', end='2025-07-31', freq='D')
        appointment_counts = np.random.randint(0, 5, len(dates))
        time_series_df = pd.DataFrame({'Date': dates, 'Appointments': appointment_counts})
        
        fig = px.line(time_series_df, x='Date', y='Appointments',
                     title="Daily Appointment Bookings")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Lead Conversion Funnel")
        funnel_data = {
            'Stage': ['Leads', 'Qualified', 'Proposals', 'Closed'],
            'Count': [100, 60, 30, 15]
        }
        fig = px.funnel(funnel_data, x='Count', y='Stage')
        st.plotly_chart(fig, use_container_width=True)
    
    # Performance metrics
    st.subheader("🏆 Performance Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 Conversion Rate", "15%", delta="2.1%")
        st.metric("⏱️ Avg. Response Time", "2.3 hours", delta="-0.5 hours")
    
    with col2:
        st.metric("💰 Revenue This Month", "$45,000", delta="$12,000")
        st.metric("📞 Calls Made", "127", delta="23")
    
    with col3:
        st.metric("✉️ Email Open Rate", "34%", delta="4.2%")
        st.metric("🎯 Lead Quality Score", "78", delta="5")
    
    # Advanced analytics
    st.subheader("🔍 Advanced Analytics")
    
    tab1, tab2, tab3 = st.tabs(["Lead Sources", "Revenue Forecast", "Activity Heatmap"])
    
    with tab1:
        if 'Lead Source' in contacts_df.columns:
            source_data = contacts_df['Lead Source'].value_counts()
            fig = px.bar(x=source_data.index, y=source_data.values,
                        title="Contacts by Lead Source")
            st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Mock revenue forecast
        forecast_dates = pd.date_range(start='2025-08-01', end='2025-12-31', freq='M')
        forecast_revenue = [50000, 55000, 60000, 58000, 65000]
        forecast_df = pd.DataFrame({'Month': forecast_dates, 'Projected Revenue': forecast_revenue})
        
        fig = px.line(forecast_df, x='Month', y='Projected Revenue',
                     title="Revenue Forecast")
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        # Mock activity heatmap data
        activities = ['Calls', 'Emails', 'Meetings', 'Proposals']
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']
        activity_data = np.random.randint(1, 10, (len(activities), len(days)))
        
        fig = px.imshow(activity_data, 
                       x=days, y=activities,
                       title="Weekly Activity Heatmap",
                       color_continuous_scale="Blues")
        st.plotly_chart(fig, use_container_width=True)

# ---------- Settings Page ----------
def settings_page():
    st.header("⚙️ CRM Settings")
    
    tab1, tab2, tab3 = st.tabs(["General", "Notifications", "Integrations"])
    
    with tab1:
        st.subheader("🔧 General Settings")
        
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Company Name", value="Your Company")
            st.selectbox("Time Zone", ["UTC", "EST", "PST", "CST"])
            st.selectbox("Date Format", ["MM/DD/YYYY", "DD/MM/YYYY", "YYYY-MM-DD"])
        
        with col2:
            st.selectbox("Currency", ["USD", "EUR", "GBP", "CAD"])
            st.number_input("Default Meeting Duration (minutes)", value=30)
            st.selectbox("Business Hours", ["9 AM - 5 PM", "8 AM - 6 PM", "24/7"])
    
    with tab2:
        st.subheader("🔔 Notification Settings")
        
        st.checkbox("Email notifications for new leads", value=True)
        st.checkbox("SMS alerts for urgent appointments", value=False)
        st.checkbox("Daily activity digest", value=True)
        st.checkbox("Weekly performance report", value=True)
        
        st.selectbox("Reminder frequency", ["15 minutes", "30 minutes", "1 hour", "2 hours"])
    
    with tab3:
        st.subheader("🔗 Integrations")
        
        integrations = [
            {"name": "Google Calendar", "status": "Connected", "color": "green"},
            {"name": "Outlook", "status": "Not Connected", "color": "red"},
            {"name": "Slack", "status": "Connected", "color": "green"},
            {"name": "Zoom", "status": "Not Connected", "color": "red"},
            {"name": "Mailchimp", "status": "Connected", "color": "green"}
        ]
        
        for integration in integrations:
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(f"**{integration['name']}**")
            with col2:
                st.markdown(f"<span style='color: {integration['color']}'>{integration['status']}</span>", 
                           unsafe_allow_html=True)
            with col3:
                action = "Disconnect" if integration['status'] == "Connected" else "Connect"
                st.button(action, key=f"{integration['name']}_action")

# ---------- Main Application Logic ----------
def main():
    json_file, selected_page = sidebar_navigation()
    
    # Load data
    if json_file:
        try:
            credentials = json_file.read()
            credentials_dict = json.loads(credentials)
            gsheet_data = load_gsheet_data(credentials_dict)
            
            if gsheet_data is not None:
                st.success("✅ Live data loaded from Google Sheets.")
                appointments_df = gsheet_data
                # For demo purposes, create mock contacts and leads from appointments
                contacts_df = pd.DataFrame({
                    'Name': appointments_df['Name'],
                    'Email': appointments_df['Guest Email'],
                    'Status': 'Active'
                })
                leads_df = pd.DataFrame()  # Empty for now
            else:
                st.warning("⚠️ Failed to load live data. Using demo data.")
                appointments_df, contacts_df, leads_df = get_demo_data()
        except Exception as e:
            st.error(f"❌ Error processing credentials: {e}")
            appointments_df, contacts_df, leads_df = get_demo_data()
    else:
        st.info("📄 Upload credentials to view live data. Using demo data.")
        appointments_df, contacts_df, leads_df = get_demo_data()
    
    # Route to selected page
    if selected_page == "📋 Dashboard":
        dashboard_page(appointments_df, contacts_df, leads_df)
    elif selected_page == "📅 Appointments":
        appointments_page(appointments_df)
    elif selected_page == "👥 Contacts":
        contacts_page(contacts_df)
    elif selected_page == "🎯 Leads":
        leads_page(leads_df)
    elif selected_page == "📈 Analytics":
        analytics_page(appointments_df, contacts_df, leads_df)
    elif selected_page == "⚙️ Settings":
        settings_page()
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col2:
        st.markdown("🚀 **Advanced CRM System** | Built with Streamlit")

if __name__ == "__main__":
    main()

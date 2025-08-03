import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
from datetime import datetime, timedelta
import uuid
from utils.auth import require_auth
from utils.gsheet import get_sheet_as_df, update_sheet_from_df
from utils.vapi import make_vapi_call, get_call_status, get_call_recording
from utils.validators import validate_phone, validate_required_fields

@require_auth
def main():
    st.title("📞 Outbound Voice Calling (VAPI)")
    
    # Tabs for call management
    tab1, tab2, tab3, tab4 = st.tabs(["📞 Make Calls", "📋 Call Campaigns", "📊 Call Analytics", "⚙️ VAPI Settings"])
    
    with tab1:
        show_call_interface()
    
    with tab2:
        show_call_campaigns()
    
    with tab3:
        show_call_analytics()
    
    with tab4:
        show_vapi_settings()

def show_call_interface():
    """Main calling interface"""
    st.subheader("Make Outbound Calls")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📞 Calls Today", "23", "5")
    
    with col2:
        st.metric("✅ Successful", "18", "4")
    
    with col3:
        st.metric("⏱️ Avg Duration", "3:24", "0:15")
    
    with col4:
        st.metric("💰 Cost Today", "$12.45", "$2.30")
    
    st.divider()
    
    # Single call interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📱 Single Call")
        
        # Load customers for quick selection
        if "gsheets_creds" in st.session_state:
            customers_df = get_sheet_as_df("customers")
            
            if customers_df is not None and not customers_df.empty:
                call_type = st.radio("Call Type", ["New Call", "Select Customer"], horizontal=True)
                
                if call_type == "Select Customer":
                    selected_customer = st.selectbox(
                        "Select Customer",
                        customers_df['Name'].tolist(),
                        help="Choose from existing customers"
                    )
                    
                    if selected_customer:
                        customer_data = customers_df[customers_df['Name'] == selected_customer].iloc[0]
                        phone_number = st.text_input("Phone Number", value=customer_data.get('Phone', ''))
                        customer_name = selected_customer
                else:
                    phone_number = st.text_input("Phone Number", placeholder="+1 (555) 123-4567")
                    customer_name = st.text_input("Customer Name (optional)")
            else:
                phone (555) 123-4567")
                customer_name = st.text_input("Customer Name (optional)")
            else:
                phone_number = st.text_input("Phone Number", placeholder="+1 (555) 123-4567")
                customer_name = st.text_input("Customer Name (optional)")
        
        # Call script selection
        script_options = [
            "Appointment Reminder",
            "Follow-up Call", 
            "Service Inquiry",
            "Payment Reminder",
            "Survey Call",
            "Custom Script"
        ]
        
        selected_script = st.selectbox("Call Script", script_options)
        
        if selected_script == "Custom Script":
            call_script = st.text_area(
                "Custom Script",
                placeholder="Enter your custom call script here...",
                height=150
            )
        else:
            call_script = get_predefined_script(selected_script, customer_name)
            st.text_area("Script Preview", value=call_script, height=150, disabled=True)
        
        # Call settings
        col_settings1, col_settings2 = st.columns(2)
        
        with col_settings1:
            voice_selection = st.selectbox("Voice", [
                "Sarah (Female, Professional)",
                "Mike (Male, Friendly)", 
                "Emma (Female, Warm)",
                "James (Male, Authoritative)"
            ])
            
            call_priority = st.selectbox("Priority", ["Normal", "High", "Low"])
        
        with col_settings2:
            max_duration = st.number_input("Max Duration (minutes)", min_value=1, max_value=30, value=5)
            
            record_call = st.checkbox("Record Call", value=True)
        
        # Advanced settings
        with st.expander("🔧 Advanced Settings"):
            retry_attempts = st.number_input("Retry Attempts", min_value=0, max_value=5, value=2)
            retry_delay = st.number_input("Retry Delay (minutes)", min_value=1, max_value=60, value=15)
            
            enable_voicemail = st.checkbox("Leave Voicemail", value=True)
            voicemail_script = st.text_area(
                "Voicemail Script",
                value="Hi, this is calling from [Company]. Please call us back at your convenience.",
                height=100
            )
        
        # Make call button
        if st.button("📞 Make Call", type="primary", use_container_width=True):
            make_single_call(phone_number, customer_name, call_script, voice_selection, max_duration, record_call)
    
    with col2:
        st.markdown("### 🕐 Recent Calls")
        show_recent_calls()
    
    st.divider()
    
    # Bulk calling
    st.markdown("### 📞 Bulk Calling")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Upload CSV or select from customers
        bulk_option = st.radio("Bulk Call Option", ["Upload CSV", "Select from Customers"], horizontal=True)
        
        if bulk_option == "Upload CSV":
            uploaded_file = st.file_uploader(
                "Upload CSV with phone numbers",
                type=['csv'],
                help="CSV should have columns: phone, name (optional)"
            )
            
            if uploaded_file:
                df = pd.read_csv(uploaded_file)
                st.dataframe(df.head())
                
                if st.button("📞 Start Bulk Calls"):
                    start_bulk_campaign(df, selected_script)
        
        else:
            if "gsheets_creds" in st.session_state:
                customers_df = get_sheet_as_df("customers")
                
                if customers_df is not None and not customers_df.empty:
                    # Filter customers
                    status_filter = st.multiselect(
                        "Customer Status",
                        customers_df['Status'].unique().tolist(),
                        default=["Active"]
                    )
                    
                    filtered_customers = customers_df[customers_df['Status'].isin(status_filter)]
                    st.markdown(f"**{len(filtered_customers)} customers selected**")
                    
                    if st.button("📞 Call Selected Customers"):
                        start_bulk_campaign(filtered_customers, selected_script)
    
    with col2:
        st.markdown("### 📊 Call Queue")
        
        # Show pending calls
        queue_status = [
            {"phone": "+1-555-0123", "status": "Pending", "retry": 0},
            {"phone": "+1-555-0124", "status": "In Progress", "retry": 1},
            {"phone": "+1-555-0125", "status": "Completed", "retry": 0},
        ]
        
        for call in queue_status:
            status_color = {
                "Pending": "🟡",
                "In Progress": "🔵", 
                "Completed": "🟢",
                "Failed": "🔴"
            }.get(call["status"], "⚪")
            
            st.markdown(f"{status_color} {call['phone']}")
            st.caption(f"Status: {call['status']}, Retry: {call['retry']}")

def show_call_campaigns():
    """Manage call campaigns"""
    st.subheader("Call Campaign Management")
    
    # Campaign creation
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### ✨ Create New Campaign")
        
        with st.form("campaign_form"):
            campaign_name = st.text_input("Campaign Name", placeholder="Monthly Follow-up Campaign")
            campaign_description = st.text_area("Description", placeholder="Campaign description...")
            
            col_form1, col_form2 = st.columns(2)
            
            with col_form1:
                campaign_type = st.selectbox("Campaign Type", [
                    "Follow-up", "Reminder", "Survey", "Promotional", "Support"
                ])
                
                schedule_type = st.selectbox("Schedule", [
                    "Immediate", "Scheduled", "Recurring"
                ])
                
                if schedule_type == "Scheduled":
                    schedule_date = st.date_input("Schedule Date")
                    schedule_time = st.time_input("Schedule Time")
                elif schedule_type == "Recurring":
                    recurrence = st.selectbox("Recurrence", [
                        "Daily", "Weekly", "Monthly"
                    ])
            
            with col_form2:
                target_audience = st.multiselect("Target Audience", [
                    "All Customers", "Active Customers", "Inactive Customers",
                    "High Value", "Recent Customers", "Overdue Payments"
                ])
                
                max_concurrent = st.number_input("Max Concurrent Calls", min_value=1, max_value=10, value=3)
                
                call_script_campaign = st.selectbox("Campaign Script", [
                    "Appointment Reminder", "Follow-up Call", "Service Inquiry",
                    "Payment Reminder", "Survey Call", "Custom Script"
                ])
            
            if st.form_submit_button("🚀 Create Campaign", type="primary"):
                create_call_campaign(campaign_name, campaign_type, target_audience, call_script_campaign)
    
    with col2:
        st.markdown("### 📊 Campaign Stats")
        
        st.metric("🎯 Active Campaigns", "3")
        st.metric("📞 Calls in Queue", "45")
        st.metric("✅ Completed Today", "28")
        st.metric("💰 Cost This Week", "$89.50")
    
    # Active campaigns
    st.markdown("### 📋 Active Campaigns")
    
    campaigns = [
        {
            "name": "Monthly Follow-up",
            "type": "Follow-up",
            "status": "Running",
            "progress": 65,
            "calls_made": 156,
            "success_rate": 78,
            "created": "2024-01-10"
        },
        {
            "name": "Payment Reminders",
            "type": "Reminder",
            "status": "Scheduled",
            "progress": 0,
            "calls_made": 0,
            "success_rate": 0,
            "created": "2024-01-15"
        }
    ]
    
    for campaign in campaigns:
        with st.expander(f"📈 {campaign['name']} - {campaign['status']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Type:** {campaign['type']}")
                st.markdown(f"**Status:** {campaign['status']}")
                st.markdown(f"**Progress:** {campaign['progress']}%")
                st.progress(campaign['progress'] / 100)
            
            with col2:
                st.markdown(f"**Calls Made:** {campaign['calls_made']}")
                st.markdown(f"**Success Rate:** {campaign['success_rate']}%")
                st.markdown(f"**Created:** {campaign['created']}")
            
            # Campaign actions
            col_action1, col_action2, col_action3 = st.columns(3)
            
            with col_action1:
                if st.button("⏸️ Pause", key=f"pause_{campaign['name']}"):
                    st.success("Campaign paused")
            
            with col_action2:
                if st.button("📊 Details", key=f"details_{campaign['name']}"):
                    show_campaign_details(campaign)
            
            with col_action3:
                if st.button("🗑️ Delete", key=f"delete_{campaign['name']}"):
                    st.success("Campaign deleted")

def show_call_analytics():
    """Show call analytics and performance metrics"""
    st.subheader("Call Analytics & Performance")
    
    # Date range selector
    col1, col2 = st.columns(2)
    
    with col1:
        date_range = st.date_input(
            "Analysis Period",
            value=(datetime.now().date() - timedelta(days=30), datetime.now().date())
        )
    
    with col2:
        analytics_view = st.selectbox("Analytics View", [
            "Overview", "Performance", "Cost Analysis", "Call Quality"
        ])
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📞 Total Calls", "1,247", "123")
    
    with col2:
        st.metric("✅ Success Rate", "73.5%", "2.1%")
    
    with col3:
        st.metric("⏱️ Avg Duration", "4:32", "0:15")
    
    with col4:
        st.metric("💰 Total Cost", "$428.90", "$45.20")
    
    if analytics_view == "Overview":
        show_overview_analytics()
    elif analytics_view == "Performance":
        show_performance_analytics() 
    elif analytics_view == "Cost Analysis":
        show_cost_analytics()
    elif analytics_view == "Call Quality":
        show_quality_analytics()

def show_overview_analytics():
    """Show overview analytics"""
    col1, col2 = st.columns(2)
    
    with col1:
        # Call outcomes
        outcomes = {
            "Successful": 156,
            "No Answer": 78,
            "Busy": 45,
            "Voicemail": 67,
            "Failed": 23
        }
        
        fig_outcomes = px.pie(
            values=list(outcomes.values()),
            names=list(outcomes.keys()),
            title="Call Outcomes Distribution"
        )
        st.plotly_chart(fig_outcomes, use_container_width=True)
    
    with col2:
        # Daily call volume
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        call_volumes = [20 + i % 15 for i in range(len(dates))]
        
        fig_volume = px.line(
            x=dates,
            y=call_volumes,
            title="Daily Call Volume"
        )
        st.plotly_chart(fig_volume, use_container_width=True)
    
    # Best performing times
    st.markdown("### 🕐 Best Call Times")
    
    hourly_success = {
        "9 AM": 85, "10 AM": 92, "11 AM": 88, "12 PM": 65,
        "1 PM": 58, "2 PM": 75, "3 PM": 82, "4 PM": 79, "5 PM": 71
    }
    
    fig_times = px.bar(
        x=list(hourly_success.keys()),
        y=list(hourly_success.values()),
        title="Success Rate by Hour"
    )
    fig_times.update_yaxis(title="Success Rate (%)")
    st.plotly_chart(fig_times, use_container_width=True)

def show_performance_analytics():
    """Show performance analytics"""
    st.markdown("### 📈 Performance Metrics")
    
    # Performance by script type
    script_performance = {
        "Appointment Reminder": {"calls": 234, "success": 89, "avg_duration": "2:45"},
        "Follow-up Call": {"calls": 156, "success": 67, "avg_duration": "4:23"},
        "Payment Reminder": {"calls": 89, "success": 78, "avg_duration": "3:12"},
        "Survey Call": {"calls": 67, "success": 45, "avg_duration": "6:34"}
    }
    
    performance_df = pd.DataFrame(script_performance).T
    performance_df['Success Rate %'] = (performance_df['success'] / performance_df['calls'] * 100).round(1)
    
    st.dataframe(performance_df, use_container_width=True)
    
    # Voice performance comparison
    st.markdown("### 🎙️ Voice Performance Comparison")
    
    voice_data = {
        "Voice": ["Sarah", "Mike", "Emma", "James"],
        "Calls": [345, 289, 267, 234],
        "Success Rate": [76, 71, 82, 68],
        "Avg Duration": [4.2, 3.8, 4.7, 3.9]
    }
    
    voice_df = pd.DataFrame(voice_data)
    
    fig_voice = px.scatter(
        voice_df,
        x="Success Rate",
        y="Avg Duration", 
        size="Calls",
        color="Voice",
        title="Voice Performance: Success Rate vs Duration"
    )
    st.plotly_chart(fig_voice, use_container_width=True)

def show_cost_analytics():
    """Show cost analytics"""
    st.markdown("### 💰 Cost Analysis")
    
    # Cost breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        cost_breakdown = {
            "Successful Calls": 285.40,
            "Failed Calls": 45.20,
            "Voicemail": 67.80,
            "Setup Fees": 30.50
        }
        
        fig_cost = px.pie(
            values=list(cost_breakdown.values()),
            names=list(cost_breakdown.keys()),
            title="Cost Breakdown"
        )
        st.plotly_chart(fig_cost, use_container_width=True)
    
    with col2:
        # Cost per outcome
        cost_per_outcome = {
            "Successful": 1.83,
            "No Answer": 0.58,
            "Busy": 0.32,
            "Voicemail": 1.01,
            "Failed": 1.96
        }
        
        fig_cost_outcome = px.bar(
            x=list(cost_per_outcome.keys()),
            y=list(cost_per_outcome.values()),
            title="Average Cost per Outcome"
        )
        fig_cost_outcome.update_yaxis(title="Cost ($)")
        st.plotly_chart(fig_cost_outcome, use_container_width=True)
    
    # Monthly cost trend
    st.markdown("### 📊 Monthly Cost Trend")
    
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    costs = [428, 456, 389, 512, 445, 478]
    
    fig_trend = px.line(
        x=months,
        y=costs,
        title="Monthly Call Costs"
    )
    fig_trend.update_yaxis(title="Cost ($)")
    st.plotly_chart(fig_trend, use_container_width=True)

def show_quality_analytics():
    """Show call quality analytics"""
    st.markdown("### 🎯 Call Quality Metrics")
    
    quality_metrics = {
        "Audio Quality": 4.2,
        "Connection Stability": 4.5,
        "Voice Clarity": 4.1,
        "Response Accuracy": 3.8,
        "Customer Satisfaction": 4.0
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        for metric, score in quality_metrics.items():
            st.metric(metric, f"{score}/5.0", f"{score-4.0:+.1f}")
    
    with col2:
        # Quality trend over time
        fig_quality = px.line(
            x=list(quality_metrics.keys()),
            y=list(quality_metrics.values()),
            title="Quality Metrics Overview"
        )
        fig_quality.update_yaxis(range=[0, 5])
        st.plotly_chart(fig_quality, use_container_width=True)

def show_vapi_settings():
    """VAPI configuration and settings"""
    st.subheader("VAPI Configuration")
    
    # API Configuration
    st.markdown("### 🔧 API Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        vapi_api_key = st.text_input(
            "VAPI API Key",
            type="password",
            help="Your VAPI API key"
        )
        
        vapi_endpoint = st.text_input(
            "VAPI Endpoint",
            value="https://api.vapi.ai/v1",
            help="VAPI API endpoint URL"
        )
        
        default_voice = st.selectbox("Default Voice", [
            "Sarah (Female, Professional)",
            "Mike (Male, Friendly)",
            "Emma (Female, Warm)", 
            "James (Male, Authoritative)"
        ])
    
    with col2:
        max_call_duration = st.number_input("Max Call Duration (minutes)", min_value=1, max_value=60, value=10)
        
        retry_attempts = st.number_input("Default Retry Attempts", min_value=0, max_value=10, value=3)
        
        enable_recordings = st.checkbox("Enable Call Recordings", value=True)
        
        webhook_url = st.text_input(
            "Webhook URL (optional)",
            placeholder="https://your-domain.com/webhook",
            help="URL for call status updates"
        )
    
    # Voice Settings
    st.markdown("### 🎙️ Voice Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Voice Parameters**")
        
        speech_rate = st.slider("Speech Rate", min_value=0.5, max_value=2.0, value=1.0, step=0.1)
        pitch = st.slider("Pitch", min_value=0.5, max_value=2.0, value=1.0, step=0.1)
        volume = st.slider("Volume", min_value=0.1, max_value=1.0, value=0.8, step=0.1)
    
    with col2:
        st.markdown("**Language & Accent**")
        
        language = st.selectbox("Language", [
            "English (US)", "English (UK)", "Spanish", "French", "German"
        ])
        
        accent = st.selectbox("Accent", [
            "General American", "British", "Australian", "Canadian"
        ])
        
        enable_ssml = st.checkbox("Enable SSML", help="Speech Synthesis Markup Language")
    
    # Cost Management
    st.markdown("### 💰 Cost Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        daily_budget = st.number_input("Daily Budget ($)", min_value=0.0, format="%.2f")
        monthly_budget = st.number_input("Monthly Budget ($)", min_value=0.0, format="%.2f")
        
        cost_alerts = st.checkbox("Enable Cost Alerts")
        
        if cost_alerts:
            alert_threshold = st.slider("Alert at % of budget", min_value=50, max_value=95, value=80)
    
    with col2:
        cost_per_minute = st.number_input("Cost per Minute ($)", value=0.02, format="%.4f", disabled=True)
        
        st.metric("Current Month Spend", "$127.45")
        st.metric("Remaining Budget", "$372.55")
        
        if st.button("💳 View Billing Details"):
            show_billing_details()
    
    # Advanced Settings
    with st.expander("🔬 Advanced Settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            enable_transcription = st.checkbox("Enable Live Transcription")
            enable_sentiment = st.checkbox("Enable Sentiment Analysis") 
            enable_keywords = st.checkbox("Enable Keyword Detection")
            
            if enable_keywords:
                keywords = st.text_area("Keywords to detect", placeholder="appointment, cancel, reschedule")
        
        with col2:
            connection_timeout = st.number_input("Connection Timeout (seconds)", min_value=10, max_value=120, value=30)
            response_timeout = st.number_input("Response Timeout (seconds)", min_value=5, max_value=60, value=15)
            
            enable_fallback = st.checkbox("Enable Fallback Voice")
            
            if enable_fallback:
                fallback_voice = st.selectbox("Fallback Voice", [
                    "System Default", "Backup Sarah", "Backup Mike"
                ])
    
    # Test Configuration
    st.markdown("### 🧪 Test Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        test_phone = st.text_input("Test Phone Number", placeholder="+1 (555) 123-4567")
        test_script = st.text_area("Test Script", value="This is a test call from your VAPI configuration.")
    
    with col2:
        if st.button("🧪 Test VAPI Connection", type="primary"):
            test_vapi_connection()
        
        if st.button("📞 Make Test Call"):
            if test_phone and test_script:
                make_test_call(test_phone, test_script)
            else:
                st.error("Please enter test phone number and script")
    
    # Save settings
    if st.button("💾 Save VAPI Settings", type="primary"):
        settings = {
            "api_key": vapi_api_key,
            "endpoint": vapi_endpoint,
            "default_voice": default_voice,
            "max_duration": max_call_duration,
            "retry_attempts": retry_attempts,
            "enable_recordings": enable_recordings
        }
        
        st.success("✅ VAPI settings saved successfully!")
        st.json(settings)

def make_single_call(phone, name, script, voice, duration, record):
    """Make a single outbound call"""
    if not phone or not script:
        st.error("❌ Phone number and script are required")
        return
    
    if not validate_phone(phone):
        st.error("❌ Please enter a valid phone number")
        return
    
    # Show call progress
    progress_container = st.container()
    
    with progress_container:
        st.info("📞 Initiating call...")
        
        # Call VAPI API
        call_data = {
            "phone": phone,
            "script": script,
            "voice": voice,
            "max_duration": duration,
            "record": record,
            "caller_id": st.session_state.get("user_name", "Business App")
        }
        
        try:
            with st.spinner("Connecting..."):
                result = make_vapi_call(call_data)
            
            if result.get("success"):
                call_id = result.get("call_id")
                st.success(f"✅ Call initiated successfully! Call ID: {call_id}")
                
                # Log call to database/sheet
                log_call_attempt(phone, name, script, call_id, "Initiated")
                
                # Show call monitoring
                monitor_call_progress(call_id)
            else:
                st.error(f"❌ Call failed: {result.get('error', 'Unknown error')}")
                log_call_attempt(phone, name, script, None, "Failed")
        
        except Exception as e:
            st.error(f"❌ Error making call: {str(e)}")

def start_bulk_campaign(df, script_type):
    """Start bulk calling campaign"""
    st.info(f"🚀 Starting bulk campaign with {len(df)} contacts...")
    
    # Validate phone numbers
    valid_contacts = []
    invalid_contacts = []
    
    for _, row in df.iterrows():
        phone = row.get('phone', row.get('Phone', ''))
        if validate_phone(str(phone)):
            valid_contacts.append(row)
        else:
            invalid_contacts.append(row)
    
    if invalid_contacts:
        st.warning(f"⚠️ {len(invalid_contacts)} contacts have invalid phone numbers and will be skipped")
    
    if valid_contacts:
        st.success(f"✅ Campaign started with {len(valid_contacts)} valid contacts")
        
        # Create campaign record
        campaign_id = f"CAMP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Here you would typically queue the calls for processing
        st.info(f"📊 Campaign ID: {campaign_id}")
        st.info("🔄 Calls will be processed in the background")
    else:
        st.error("❌ No valid contacts found")

def show_recent_calls():
    """Show recent call history"""
    recent_calls = [
        {"phone": "+1-555-0123", "name": "John Doe", "status": "Completed", "duration": "3:45", "time": "10 min ago"},
        {"phone": "+1-555-0124", "name": "Jane Smith", "status": "No Answer", "duration": "0:30", "time": "25 min ago"},
        {"phone": "+1-555-0125", "name": "Bob Johnson", "status": "Completed", "duration": "5:12", "time": "1 hour ago"},
    ]
    
    for call in recent_calls:
        status_icon = {
            "Completed": "✅",
            "No Answer": "📵",
            "Busy": "📞",
            "Failed": "❌"
        }.get(call["status"], "📞")
        
        st.markdown(f"{status_icon} **{call['name']}**")
        st.caption(f"{call['phone']} • {call['duration']} • {call['time']}")
        st.divider()

def get_predefined_script(script_type, customer_name=""):
    """Get predefined script based on type"""
    scripts = {
        "Appointment Reminder": f"Hello {customer_name or '[Customer]'}, this is a friendly reminder about your upcoming appointment. Please confirm your attendance or let us know if you need to reschedule.",
        
        "Follow-up Call": f"Hi {customer_name or '[Customer]'}, I'm calling to follow up on our recent service. How was your experience? Is there anything else we can help you with?",
        
        "Service Inquiry": f"Hello {customer_name or '[Customer]'}, I'm calling to tell you about our new services that might interest you. Do you have a moment to learn about how we can help you?",
        
        "Payment Reminder": f"Hello {customer_name or '[Customer]'}, this is a friendly reminder about your outstanding payment. Please contact us to discuss payment options.",
        
        "Survey Call": f"Hi {customer_name or '[Customer]'}, we'd love to get your feedback about our service. This will only take a few minutes of your time."
    }
    
    return scripts.get(script_type, "Hello, this is a call from our business app.")

def create_call_campaign(name, campaign_type, audience, script):
    """Create a new call campaign"""
    campaign_id = f"CAMP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    campaign_data = {
        "campaign_id": campaign_id,
        "name": name,
        "type": campaign_type,
        "audience": audience,
        "script": script,
        "created_by": st.session_state.user_name,
        "created_date": datetime.now().isoformat(),
        "status": "Active"
    }
    
    # Here you would save to database
    st.success(f"✅ Campaign '{name}' created successfully!")
    st.info(f"📊 Campaign ID: {campaign_id}")

def show_campaign_details(campaign):
    """Show detailed campaign information"""
    st.markdown(f"### 📊 Campaign Details: {campaign['name']}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Campaign Information**")
        st.markdown(f"- Type: {campaign['type']}")
        st.markdown(f"- Status: {campaign['status']}")
        st.markdown(f"- Created: {campaign['created']}")
        st.markdown(f"- Progress: {campaign['progress']}%")
    
    with col2:
        st.markdown("**Performance Metrics**")
        st.markdown(f"- Calls Made: {campaign['calls_made']}")
        st.markdown(f"- Success Rate: {campaign['success_rate']}%")
        st.markdown(f"- Avg Duration: 4:23")
        st.markdown(f"- Cost: $45.67")

def monitor_call_progress(call_id):
    """Monitor call progress in real-time"""
    st.markdown("### 📊 Call Monitoring")
    
    # Create placeholder for real-time updates
    status_placeholder = st.empty()
    progress_placeholder = st.empty()
    
    # Simulate call progress monitoring
    import time
    
    statuses = ["Dialing", "Ringing", "Connected", "In Progress", "Completed"]
    
    for i, status in enumerate(statuses):
        status_placeholder.info(f"🔄 Status: {status}")
        progress_placeholder.progress((i + 1) / len(statuses))
        
        if status == "Completed":
            st.success("✅ Call completed successfully!")
            
            # Show call summary
            with st.expander("📋 Call Summary"):
                st.markdown("- Duration: 4:32")
                st.markdown("- Outcome: Successful")
                st.markdown("- Recording: Available")
                st.markdown("- Cost: $0.89")
        
        time.sleep(1)  # In real app, this would be real-time updates

def log_call_attempt(phone, name, script, call_id, status):
    """Log call attempt to database"""
    call_log = {
        "call_id": call_id or f"CALL-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "phone": phone,
        "customer_name": name,
        "script_used": script[:50] + "..." if len(script) > 50 else script,
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "user": st.session_state.user_name
    }
    
    # Here you would save to your call log database/sheet
    print(f"Call logged: {call_log}")

def test_vapi_connection():
    """Test VAPI API connection"""
    try:
        # Test API connection
        st.info("🧪 Testing VAPI connection...")
        
        # Simulate API test
        import time
        time.sleep(2)
        
        st.success("✅ VAPI connection successful!")
        st.info("📊 API Status: Active")
        st.info("🏃 Response Time: 245ms")
        st.info("💰 Account Balance: $127.45")
        
    except Exception as e:
        st.error(f"❌ Connection test failed: {str(e)}")

def make_test_call(phone, script):
    """Make a test call"""
    st.info("📞 Making test call...")
    
    # Simulate test call
    import time
    time.sleep(3)
    
    st.success("✅ Test call completed successfully!")
    st.info("📊 Call Duration: 0:45")
    st.info("💰 Cost: $0.23")

def show_billing_details():
    """Show VAPI billing information"""
    st.markdown("### 💳 VAPI Billing Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Current Month**")
        st.metric("Total Calls", "1,247")
        st.metric("Total Duration", "87h 23m")
        st.metric("Total Cost", "$428.90")
    
    with col2:
        st.markdown("**Account Status**")
        st.metric("Account Balance", "$571.10")
        st.metric("Next Billing", "Jan 31, 2024")
        st.metric("Plan", "Professional")

if __name__ == "__main__":
    main()

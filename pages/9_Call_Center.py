import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import uuid
from utils.auth import require_auth
from utils.gsheet import get_sheet_as_df, update_sheet_from_df
from utils.validators import validate_required_fields

@require_auth
def main():
    st.title("🎧 Call Center Management")
    
    # Tabs for call center operations
    tab1, tab2, tab3, tab4 = st.tabs(["📞 Live Dashboard", "📋 Call Management", "👥 Agent Management", "📊 Performance Analytics"])
    
    with tab1:
        show_live_dashboard()
    
    with tab2:
        show_call_management()
    
    with tab3:
        show_agent_management()
    
    with tab4:
        show_performance_analytics()

def show_live_dashboard():
    """Real-time call center dashboard"""
    st.subheader("Live Call Center Dashboard")
    
    # Real-time metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🟢 Active Calls", "12", "2")
    
    with col2:
        st.metric("⏳ Calls in Queue", "8", "-1")
    
    with col3:
        st.metric("👥 Available Agents", "15/20", "1")
    
    with col4:
        st.metric("⏱️ Avg Wait Time", "2:34", "-0:15")
    
    st.divider()
    
    # Live call queue
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📞 Live Call Queue")
        
        # Sample queue data (would be real-time in production)
        queue_data = [
            {"position": 1, "caller": "+1-555-0123", "wait_time": "1:23", "priority": "High", "reason": "Billing Issue"},
            {"position": 2, "caller": "+1-555-0124", "wait_time": "0:45", "priority": "Normal", "reason": "General Inquiry"},
            {"position": 3, "caller": "+1-555-0125", "wait_time": "0:32", "priority": "Low", "reason": "Information Request"},
            {"position": 4, "caller": "+1-555-0126", "wait_time": "0:18", "priority": "High", "reason": "Technical Support"},
        ]
        
        for call in queue_data:
            priority_color = {
                "High": "🔴",
                "Normal": "🟡", 
                "Low": "🟢"
            }.get(call["priority"], "⚪")
            
            with st.container():
                col_pos, col_caller, col_wait, col_reason = st.columns([1, 2, 1, 2])
                
                with col_pos:
                    st.markdown(f"**#{call['position']}**")
                
                with col_caller:
                    st.markdown(f"{call['caller']}")
                
                with col_wait:
                    st.markdown(f"⏱️ {call['wait_time']}")
                
                with col_reason:
                    st.markdown(f"{priority_color} {call['reason']}")
        
        # Queue management controls
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            if st.button("⏸️ Pause Queue"):
                st.info("Queue paused")
        
        with col_btn2:
            if st.button("🔄 Refresh Queue"):
                st.rerun()
        
        with col_btn3:
            if st.button("📊 Queue Analytics"):
                show_queue_analytics()
    
    with col2:
        st.markdown("### 👥 Agent Status")
        
        # Agent status overview
        agents = [
            {"name": "Sarah Johnson", "status": "Available", "calls": 8, "duration": "4:23"},
            {"name": "Mike Wilson", "status": "On Call", "calls": 12, "duration": "6:45"},
            {"name": "Emma Davis", "status": "Break", "calls": 6, "duration": "2:18"},
            {"name": "James Brown", "status": "Available", "calls": 9, "duration": "5:12"},
            {"name": "Lisa Garcia", "status": "On Call", "calls": 11, "duration": "7:34"},
        ]
        
        for agent in agents:
            status_icon = {
                "Available": "🟢",
                "On Call": "🔵",
                "Break": "🟡",
                "Offline": "🔴"
            }.get(agent["status"], "⚪")
            
            with st.expander(f"{status_icon} {agent['name']} - {agent['status']}"):
                st.markdown(f"**Calls Today:** {agent['calls']}")
                st.markdown(f"**Total Duration:** {agent['duration']}")
                
                col_agent1, col_agent2 = st.columns(2)
                
                with col_agent1:
                    if st.button("📞 Assign Call", key=f"assign_{agent['name']}"):
                        st.success(f"Call assigned to {agent['name']}")
                
                with col_agent2:
                    if st.button("💬 Message", key=f"message_{agent['name']}"):
                        show_agent_message_modal(agent['name'])
    
    # Real-time performance charts
    st.markdown("### 📊 Real-time Performance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Call volume by hour (today)
        hours = list(range(9, 18))  # 9 AM to 5 PM
        call_volumes = [15, 23, 28, 31, 25, 18, 22, 26, 19]  # Sample data
        
        fig_volume = px.bar(
            x=hours,
            y=call_volumes,
            title="Hourly Call Volume (Today)",
            labels={'x': 'Hour', 'y': 'Calls'}
        )
        st.plotly_chart(fig_volume, use_container_width=True)
    
    with col2:
        # Average wait time trend
        time_points = ["9 AM", "10 AM", "11 AM", "12 PM", "1 PM", "2 PM", "3 PM", "4 PM", "5 PM"]
        wait_times = [1.2, 2.1, 3.4, 4.8, 3.2, 2.7, 2.1, 1.8, 1.5]  # In minutes
        
        fig_wait = px.line(
            x=time_points,
            y=wait_times,
            title="Average Wait Time Trend",
            labels={'x': 'Time', 'y': 'Wait Time (minutes)'}
        )
        st.plotly_chart(fig_wait, use_container_width=True)

def show_call_management():
    """Call management and routing"""
    st.subheader("Call Management & Routing")
    
    # Call routing configuration
    st.markdown("### 🔀 Call Routing Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Routing Rules**")
        
        routing_strategy = st.selectbox("Routing Strategy", [
            "Round Robin", "Least Busy", "Skills Based", "Priority Based"
        ])
        
        max_queue_size = st.number_input("Max Queue Size", min_value=1, max_value=100, value=50)
        
        max_wait_time = st.number_input("Max Wait Time (minutes)", min_value=1, max_value=60, value=10)
        
        enable_callbacks = st.checkbox("Enable Callback Option", value=True)
        
        if enable_callbacks:
            callback_threshold = st.number_input("Callback Threshold (wait time in minutes)", min_value=1, max_value=30, value=5)
    
    with col2:
        st.markdown("**Business Hours**")
        
        col_days1, col_days2 = st.columns(2)
        
        with col_days1:
            st.checkbox("Monday", value=True)
            st.checkbox("Tuesday", value=True)
            st.checkbox("Wednesday", value=True)
            st.checkbox("Thursday", value=True)
        
        with col_days2:
            st.checkbox("Friday", value=True)
            st.checkbox("Saturday", value=False)
            st.checkbox("Sunday", value=False)
        
        start_time = st.time_input("Start Time", value=datetime.strptime("09:00", "%H:%M").time())
        end_time = st.time_input("End Time", value=datetime.strptime("17:00", "%H:%M").time())
    
    # Call categories and skills
    st.markdown("### 🎯 Call Categories & Skills")
    
    categories = [
        {"name": "Technical Support", "priority": "High", "skills": ["Technical", "Problem Solving"], "agents": 5},
        {"name": "Billing Inquiries", "priority": "Normal", "skills": ["Finance", "Customer Service"], "agents": 3},
        {"name": "General Information", "priority": "Low", "skills": ["Customer Service"], "agents": 8},
        {"name": "Sales Inquiries", "priority": "High", "skills": ["Sales", "Product Knowledge"], "agents": 4},
    ]
    
    category_df = pd.DataFrame(categories)
    
    edited_categories = st.data_editor(
        category_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "priority": st.column_config.SelectboxColumn(
                "Priority",
                options=["Low", "Normal", "High", "Critical"]
            ),
            "agents": st.column_config.NumberColumn("Available Agents", min_value=0)
        }
    )
    
    # Interactive Voice Response (IVR) Settings
    st.markdown("### 📱 IVR Configuration")
    
    with st.expander("🔧 IVR Menu Setup"):
        st.markdown("**Main Menu Options:**")
        
        ivr_options = [
            {"option": "1", "description": "Technical Support", "route_to": "Tech Queue"},
            {"option": "2", "description": "Billing Questions", "route_to": "Billing Queue"},
            {"option": "3", "description": "General Information", "route_to": "General Queue"},
            {"option": "0", "description": "Speak to Operator", "route_to": "Main Queue"},
        ]
        
        ivr_df = pd.DataFrame(ivr_options)
        
        edited_ivr = st.data_editor(
            ivr_df,
            use_container_width=True,
            num_rows="dynamic"
        )
        
        # IVR Messages
        welcome_message = st.text_area(
            "Welcome Message",
            value="Thank you for calling. Please listen carefully as our menu options have changed.",
            height=100
        )
        
        hold_music = st.selectbox("Hold Music", [
            "Classical", "Jazz", "Corporate", "Ambient", "Custom Upload"
        ])
    
    # Call escalation rules
    st.markdown("### ⬆️ Escalation Rules")
    
    col1, col2 = st.columns(2)
    
    with col1:
        escalation_rules = [
            {"trigger": "Wait Time > 5 minutes", "action": "Offer Callback", "enabled": True},
            {"trigger": "Agent Unavailable", "action": "Route to Supervisor", "enabled": True},
            {"trigger": "Customer Request", "action": "Transfer to Manager", "enabled": True},
            {"trigger": "Technical Issue", "action": "Route to L2 Support", "enabled": False},
        ]
        
        for i, rule in enumerate(escalation_rules):
            col_check, col_trigger, col_action = st.columns([1, 3, 3])
            
            with col_check:
                enabled = st.checkbox("", value=rule["enabled"], key=f"rule_{i}")
            
            with col_trigger:
                st.markdown(rule["trigger"])
            
            with col_action:
                st.markdown(f"→ {rule['action']}")
    
    with col2:
        st.markdown("**Escalation Contacts**")
        
        supervisor_email = st.text_input("Supervisor Email", value="supervisor@company.com")
        manager_phone = st.text_input("Manager Phone", value="+1-555-0100")
        
        enable_email_alerts = st.checkbox("Email Alerts for Escalations", value=True)
        enable_sms_alerts = st.checkbox("SMS Alerts for Critical Issues", value=True)
    
    # Save configuration
    if st.button("💾 Save Call Management Settings", type="primary"):
        settings = {
            "routing_strategy": routing_strategy,
            "max_queue_size": max_queue_size,
            "max_wait_time": max_wait_time,
            "business_hours": f"{start_time} - {end_time}",
            "categories": edited_categories.to_dict('records'),
            "ivr_options": edited_ivr.to_dict('records')
        }
        
        st.success("✅ Call management settings saved!")
        st.json(settings)

def show_agent_management():
    """Agent management and performance"""
    st.subheader("Agent Management")
    
    # Agent overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 Total Agents", "20")
    
    with col2:
        st.metric("🟢 Available", "15")
    
    with col3:
        st.metric("📞 On Calls", "4")
    
    with col4:
        st.metric("⏸️ On Break", "1")
    
    # Agent list and management
    st.markdown("### 👥 Agent Directory")
    
    # Sample agent data
    agents_data = [
        {
            "name": "Sarah Johnson",
            "id": "AGT001",
            "status": "Available",
            "skills": "Technical, Customer Service",
            "calls_today": 12,
            "avg_handle_time": "6:45",
            "satisfaction": 4.8,
            "shift": "9 AM - 5 PM"
        },
        {
            "name": "Mike Wilson", 
            "id": "AGT002",
            "status": "On Call",
            "skills": "Sales, Product Knowledge",
            "calls_today": 8,
            "avg_handle_time": "8:12",
            "satisfaction": 4.6,
            "shift": "10 AM - 6 PM"
        },
        {
            "name": "Emma Davis",
            "id": "AGT003", 
            "status": "Break",
            "skills": "Billing, Customer Service",
            "calls_today": 15,
            "avg_handle_time": "4:23",
            "satisfaction": 4.9,
            "shift": "8 AM - 4 PM"
        }
    ]
    
    agents_df = pd.DataFrame(agents_data)
    
    # Agent filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox("Filter by Status", ["All", "Available", "On Call", "Break", "Offline"])
    
    with col2:
        skill_filter = st.selectbox("Filter by Skill", ["All", "Technical", "Sales", "Billing", "Customer Service"])
    
    with col3:
        shift_filter = st.selectbox("Filter by Shift", ["All", "Morning", "Afternoon", "Evening"])
    
    # Display agents
    for _, agent in agents_df.iterrows():
        with st.expander(f"👤 {agent['name']} ({agent['id']}) - {agent['status']}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Performance Today**")
                st.markdown(f"📞 Calls: {agent['calls_today']}")
                st.markdown(f"⏱️ Avg Handle Time: {agent['avg_handle_time']}")
                st.markdown(f"😊 Satisfaction: {agent['satisfaction']}/5.0")
            
            with col2:
                st.markdown("**Skills & Schedule**")
                st.markdown(f"🎯 Skills: {agent['skills']}")
                st.markdown(f"🕒 Shift: {agent['shift']}")
                st.markdown(f"📊 Status: {agent['status']}")
            
            with col3:
                st.markdown("**Quick Actions**")
                
                col_action1, col_action2 = st.columns(2)
                
                with col_action1:
                    if st.button("📞 Assign Call", key=f"assign_call_{agent['id']}"):
                        st.success(f"Call assigned to {agent['name']}")
                    
                    if st.button("⏸️ Set Break", key=f"break_{agent['id']}"):
                        st.info(f"{agent['name']} is now on break")
                
                with col_action2:
                    if st.button("📊 View Details", key=f"details_{agent['id']}"):
                        show_agent_details(agent)
                    
                    if st.button("💬 Send Message", key=f"msg_{agent['id']}"):
                        show_agent_message_modal(agent['name'])
    
    # Add new agent
    st.markdown("### ➕ Add New Agent")
    
    with st.expander("Add Agent"):
        with st.form("add_agent_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_agent_name = st.text_input("Full Name")
                new_agent_email = st.text_input("Email")
                new_agent_phone = st.text_input("Phone")
                new_agent_id = st.text_input("Agent ID", placeholder="AGT004")
            
            with col2:
                new_agent_skills = st.multiselect("Skills", [
                    "Technical", "Sales", "Billing", "Customer Service", 
                    "Problem Solving", "Product Knowledge"
                ])
                
                new_agent_shift = st.selectbox("Shift", [
                    "9 AM - 5 PM", "10 AM - 6 PM", "8 AM - 4 PM", "1 PM - 9 PM"
                ])
                
                new_agent_team = st.selectbox("Team", [
                    "Support", "Sales", "Billing", "Technical"
                ])
            
            if st.form_submit_button("➕ Add Agent"):
                if new_agent_name and new_agent_email and new_agent_id:
                    st.success(f"✅ Agent {new_agent_name} added successfully!")
                else:
                    st.error("❌ Please fill in required fields")

def show_performance_analytics():
    """Call center performance analytics"""
    st.subheader("Performance Analytics")
    
    # Date range selector
    col1, col2 = st.columns(2)
    
    with col1:
        date_range = st.date_input(
            "Analysis Period",
            value=(datetime.now().date() - timedelta(days=30), datetime.now().date())
        )
    
    with col2:
        analytics_view = st.selectbox("Analytics View", [
            "Overview", "Agent Performance", "Queue Analysis", "Customer Satisfaction"
        ])
    
    if analytics_view == "Overview":
        show_overview_analytics_cc()
    elif analytics_view == "Agent Performance":
        show_agent_performance_analytics()
    elif analytics_view == "Queue Analysis":
        show_queue_analytics_detailed()
    elif analytics_view == "Customer Satisfaction":
        show_satisfaction_analytics()

def show_overview_analytics_cc():
    """Show call center overview analytics"""
    # Key performance indicators
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📞 Total Calls", "3,247", "234")
    
    with col2:
        st.metric("⏱️ Avg Wait Time", "2:34", "-0:15")
    
    with col3:
        st.metric("✅ Service Level", "87.5%", "2.1%")
    
    with col4:
        st.metric("😊 CSAT Score", "4.3/5", "0.1")
    
    # Performance trends
    col1, col2 = st.columns(2)
    
    with col1:
        # Daily call volume
        dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='D')
        volumes = [150 + (i % 10) * 20 for i in range(len(dates))]
        
        fig_volume = px.line(
            x=dates,
            y=volumes,
            title="Daily Call Volume Trend"
        )
        st.plotly_chart(fig_volume, use_container_width=True)
    
    with col2:
        # Service level by hour
        hours = list(range(9, 18))
        service_levels = [92, 89, 85, 78, 82, 87, 91, 88, 94]
        
        fig_service = px.bar(
            x=hours,
            y=service_levels,
            title="Service Level by Hour"
        )
        fig_service.update_yaxis(title="Service Level (%)")
        st.plotly_chart(fig_service, use_container_width=True)
    
    # Call outcome distribution
    st.markdown("### 📊 Call Outcomes")
    
    outcomes = {
        "Resolved": 2834,
        "Transferred": 287,
        "Escalated": 89,
        "Abandoned": 37
    }
    
    fig_outcomes = px.pie(
        values=list(outcomes.values()),
        names=list(outcomes.keys()),
        title="Call Outcome Distribution"
    )
    st.plotly_chart(fig_outcomes, use_container_width=True)

def show_agent_performance_analytics():
    """Show agent performance analytics"""
    st.markdown("### 👥 Agent Performance Analysis")
    
    # Agent performance summary
    agent_performance = [
        {"agent": "Sarah Johnson", "calls": 156, "aht": "5:23", "csat": 4.8, "fcr": 89},
        {"agent": "Mike Wilson", "calls": 134, "aht": "6:45", "csat": 4.6, "fcr": 85},
        {"agent": "Emma Davis", "calls": 178, "aht": "4:12", "csat": 4.9, "fcr": 92},
        {"agent": "James Brown", "calls": 145, "aht": "5:56", "csat": 4.5, "fcr": 87},
        {"agent": "Lisa Garcia", "calls": 167, "aht": "5:34", "csat": 4.7, "fcr": 90}
    ]
    
    perf_df = pd.DataFrame(agent_performance)
    
    # Performance metrics comparison
    col1, col2 = st.columns(2)
    
    with col1:
        # Calls handled
        fig_calls = px.bar(
            perf_df,
            x="agent",
            y="calls",
            title="Calls Handled by Agent"
        )
        st.plotly_chart(fig_calls, use_container_width=True)
    
    with col2:
        # Customer satisfaction
        fig_csat = px.bar(
            perf_df,
            x="agent", 
            y="csat",
            title="Customer Satisfaction by Agent"
        )
        fig_csat.update_yaxis(range=[4.0, 5.0])
        st.plotly_chart(fig_csat, use_container_width=True)
    
    # Detailed performance table
    st.markdown("### 📋 Detailed Performance Metrics")
    
    st.dataframe(
        perf_df,
        column_config={
            "agent": "Agent Name",
            "calls": st.column_config.NumberColumn("Calls Handled"),
            "aht": "Avg Handle Time",
            "csat": st.column_config.NumberColumn("CSAT Score", format="%.1f"),
            "fcr": st.column_config.NumberColumn("First Call Resolution (%)")
        },
        use_container_width=True,
        hide_index=True
    )

def show_queue_analytics_detailed():
    """Show detailed queue analytics"""
    st.markdown("### 📊 Queue Performance Analysis")
    
    # Queue metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📞 Total Queued Calls", "1,456")
        st.metric("⏱️ Avg Queue Time", "3:24")
        st.metric("📈 Peak Queue Size", "23")
    
    with col2:
        st.metric("🚪 Abandonment Rate", "4.2%")
        st.metric("⚡ Service Level (20s)", "82%")
        st.metric("🎯 Service Level (60s)", "94%")
    
    with col3:
        st.metric("🔄 Queue Efficiency", "87%")
        st.metric("📞 Callback Success", "76%")
        st.metric("⏰ Longest Wait", "12:45")
    
    # Queue performance by time
    st.markdown("### 🕐 Queue Performance by Time")
    
    # Sample data for hourly queue metrics
    hours = list(range(9, 18))
    queue_sizes = [5, 8, 12, 18, 15, 10, 7, 9, 6]
    wait_times = [1.2, 2.1, 3.4, 5.2, 4.1, 2.8, 1.9, 2.3, 1.5]
    
    fig_queue = go.Figure()
    
    fig_queue.add_trace(go.Scatter(
        x=hours,
        y=queue_sizes,
        mode='lines+markers',
        name='Queue Size',
        yaxis='y'
    ))
    
    fig_queue.add_trace(go.Scatter(
        x=hours,
        y=wait_times,
        mode='lines+markers',
        name='Wait Time (min)',
        yaxis='y2'
    ))
    
    fig_queue.update_layout(
        title="Queue Size and Wait Time by Hour",
        xaxis_title="Hour",
        yaxis=dict(title="Queue Size", side="left"),
        yaxis2=dict(title="Wait Time (minutes)", side="right", overlaying="y")
    )
    
    st.plotly_chart(fig_queue, use_container_width=True)

def show_satisfaction_analytics():
    """Show customer satisfaction analytics"""
    st.markdown("### 😊 Customer Satisfaction Analysis")
    
    # CSAT metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Overall CSAT", "4.3/5.0", "0.1")
    
    with col2:
        st.metric("📈 Response Rate", "76%", "3%")
    
    with col3:
        st.metric("😊 Promoters (9-10)", "67%", "2%")
    
    with col4:
        st.metric("😐 Detractors (0-6)", "8%", "-1%")
    
    # Satisfaction trends
    col1, col2 = st.columns(2)
    
    with col1:
        # CSAT by category
        categories = ["Technical", "Billing", "General", "Sales"]
        csat_scores = [4.1, 4.5, 4.3, 4.2]
        
        fig_csat_cat = px.bar(
            x=categories,
            y=csat_scores,
            title="CSAT by Category"
        )
        fig_csat_cat.update_yaxis(range=[3.5, 5.0])
        st.plotly_chart(fig_csat_cat, use_container_width

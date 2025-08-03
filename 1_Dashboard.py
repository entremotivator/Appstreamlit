import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from utils.auth import require_auth
from utils.gsheet import get_sheet_as_df, get_cached_data

@require_auth
def main():
    st.title("📊 Business Dashboard")
    
    # Dashboard header with key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Sample metrics (replace with real data)
    with col1:
        st.metric(
            label="💰 Monthly Revenue",
            value="$45,230",
            delta="12.5%",
            help="Revenue for current month"
        )
    
    with col2:
        st.metric(
            label="👥 Active Customers",
            value="1,234",
            delta="8.2%",
            help="Number of active customers"
        )
    
    with col3:
        st.metric(
            label="📞 Calls Made",
            value="856",
            delta="-2.1%",
            help="Outbound calls this month"
        )
    
    with col4:
        st.metric(
            label="📅 Appointments",
            value="142",
            delta="15.3%",
            help="Scheduled appointments"
        )
    
    st.divider()
    
    # Charts section
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Revenue Trend")
        
        # Generate sample revenue data
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='M')
        revenue = np.random.normal(40000, 5000, len(dates))
        revenue = np.maximum(revenue, 20000)  # Ensure positive values
        
        df_revenue = pd.DataFrame({
            'Date': dates,
            'Revenue': revenue
        })
        
        fig_revenue = px.line(
            df_revenue, 
            x='Date', 
            y='Revenue',
            title="Monthly Revenue Trend",
            color_discrete_sequence=['#1f77b4']
        )
        fig_revenue.update_layout(
            xaxis_title="Month",
            yaxis_title="Revenue ($)",
            showlegend=False
        )
        st.plotly_chart(fig_revenue, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Service Distribution")
        
        # Sample service data
        services = ['Consulting', 'Development', 'Support', 'Training', 'Other']
        values = [35, 25, 20, 15, 5]
        
        fig_pie = px.pie(
            values=values,
            names=services,
            title="Revenue by Service Type",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    # Recent activity section
    st.subheader("🕐 Recent Activity")
    
    # Sample recent activity data
    recent_activities = [
        {"time": "2 minutes ago", "activity": "New customer registered", "type": "success"},
        {"time": "15 minutes ago", "activity": "Invoice #1234 paid", "type": "success"},
        {"time": "1 hour ago", "activity": "Appointment scheduled", "type": "info"},
        {"time": "2 hours ago", "activity": "Call completed successfully", "type": "success"},
        {"time": "3 hours ago", "activity": "System backup completed", "type": "info"},
    ]
    
    for activity in recent_activities:
        icon = "✅" if activity["type"] == "success" else "ℹ️"
        st.markdown(f"{icon} **{activity['time']}** - {activity['activity']}")
    
    st.divider()
    
    # Quick actions
    st.subheader("⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📄 Create Invoice", use_container_width=True):
            st.session_state.current_page = "Invoices"
            st.rerun()
    
    with col2:
        if st.button("👥 Add Customer", use_container_width=True):
            st.session_state.current_page = "Customers"
            st.rerun()
    
    with col3:
        if st.button("📅 Schedule Meeting", use_container_width=True):
            st.session_state.current_page = "Appointments"
            st.rerun()
    
    with col4:
        if st.button("📞 Make Call", use_container_width=True):
            st.session_state.current_page = "Voice Calls"
            st.rerun()
    
    # System status
    with st.expander("🔧 System Status", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Services Status:**")
            st.markdown("🟢 Google Sheets API")
            st.markdown("🟢 Voice API (VAPI)")
            st.markdown("🟢 AI Chat Service")
            st.markdown("🟢 Database Connection")
        
        with col2:
            st.markdown("**Performance Metrics:**")
            st.markdown("⚡ Response Time: 120ms")
            st.markdown("💾 Memory Usage: 45%")
            st.markdown("🔄 Uptime: 99.9%")
            st.markdown("📊 API Calls: 1,247/10,000")

if __name__ == "__main__":
    main()

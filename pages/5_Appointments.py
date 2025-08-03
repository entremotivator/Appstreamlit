import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, time
import uuid
from utils.auth import require_auth
from utils.gsheet import get_sheet_as_df, update_sheet_from_df
from utils.validators import validate_required_fields

@require_auth
def main():
    st.title("🕐 Appointment Booking System")
    
    # Tabs for appointment management
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Booking Management", "⚙️ Availability Settings", "📊 Booking Analytics", "🔔 Notifications"])
    
    with tab1:
        show_booking_management()
    
    with tab2:
        show_availability_settings()
    
    with tab3:
        show_booking_analytics()
    
    with tab4:
        show_notifications()

def show_booking_management():
    """Main booking management interface"""
    st.subheader("Appointment Booking Management")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    if "gsheets_creds" in st.session_state:
        df = get_sheet_as_df("appointments")
        
        if df is not None and not df.empty:
            today = datetime.now().date()
            today_appointments = df[pd.to_datetime(df['Date']).dt.date == today]
            
            with col1:
                st.metric("📅 Today's Appointments", len(today_appointments))
            
            with col2:
                pending_count = len(df[df['Status'] == 'Scheduled'])
                st.metric("⏳ Pending", pending_count)
            
            with col3:
                completed_today = len(today_appointments[today_appointments['Status'] == 'Completed'])
                st.metric("✅ Completed Today", completed_today)
            
            with col4:
                no_shows = len(df[df['Status'] == 'No-show'])
                st.metric("❌ No-shows", no_shows)
        else:
            for col in [col1, col2, col3, col4]:
                with col:
                    st.metric("📊 Data", "No data")
    
    st.divider()
    
    # Booking interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📅 Quick Book Appointment")
        
        with st.form("quick_book_form"):
            col_form1, col_form2 = st.columns(2)
            
            with col_form1:
                customer_name = st.text_input("Customer Name *")
                phone = st.text_input("Phone Number")
                email = st.text_input("Email")
            
            with col_form2:
                appointment_date = st.date_input("Date *", min_value=datetime.now().date())
                appointment_time = st.time_input("Time *")
                service = st.selectbox("Service *", [
                    "Consultation", "Follow-up", "Treatment", "Assessment",
                    "Meeting", "Training", "Support", "Other"
                ])
            
            duration = st.selectbox("Duration", [15, 30, 45, 60, 90, 120], index=2)
            notes = st.text_area("Notes")
            
            if st.form_submit_button("📅 Book Appointment", type="primary"):
                book_appointment(customer_name, phone, email, appointment_date, appointment_time, service, duration, notes)
    
    with col2:
        st.markdown("### 🕐 Today's Schedule")
        show_todays_schedule()
    
    st.divider()
    
    # Recent bookings
    st.markdown("### 📋 Recent Bookings")
    show_recent_bookings()

def show_availability_settings():
    """Configure availability and booking settings"""
    st.subheader("Availability & Booking Settings")
    
    # Business hours configuration
    st.markdown("### 🕒 Business Hours")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Weekdays (Monday - Friday)**")
        weekday_start = st.time_input("Start Time", value=time(9, 0), key="weekday_start")
        weekday_end = st.time_input("End Time", value=time(17, 0), key="weekday_end")
        weekday_break_start = st.time_input("Lunch Break Start", value=time(12, 0), key="weekday_break_start")
        weekday_break_end = st.time_input("Lunch Break End", value=time(13, 0), key="weekday_break_end")
    
    with col2:
        st.markdown("**Weekends (Saturday - Sunday)**")
        weekend_enabled = st.checkbox("Weekend Appointments Available")
        
        if weekend_enabled:
            weekend_start = st.time_input("Start Time", value=time(10, 0), key="weekend_start")
            weekend_end = st.time_input("End Time", value=time(15, 0), key="weekend_end")
        else:
            st.info("Weekend appointments are disabled")
    
    # Service configuration
    st.markdown("### 🛠️ Service Configuration")
    
    services_config = [
        {"name": "Consultation", "duration": 60, "buffer": 15, "enabled": True},
        {"name": "Follow-up", "duration": 30, "buffer": 10, "enabled": True},
        {"name": "Treatment", "duration": 90, "buffer": 15, "enabled": True},
        {"name": "Assessment", "duration": 45, "buffer": 15, "enabled": True},
    ]
    
    for i, service in enumerate(services_config):
        with st.expander(f"⚙️ {service['name']} Settings"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                duration = st.number_input(
                    "Duration (minutes)", 
                    value=service['duration'], 
                    min_value=15, 
                    max_value=240,
                    step=15,
                    key=f"duration_{i}"
                )
            
            with col2:
                buffer_time = st.number_input(
                    "Buffer Time (minutes)", 
                    value=service['buffer'], 
                    min_value=0, 
                    max_value=60,
                    step=5,
                    key=f"buffer_{i}"
                )
            
            with col3:
                enabled = st.checkbox("Service Enabled", value=service['enabled'], key=f"enabled_{i}")
    
    # Booking rules
    st.markdown("### 📏 Booking Rules")
    
    col1, col2 = st.columns(2)
    
    with col1:
        advance_booking_days = st.number_input("Maximum days in advance", value=30, min_value=1, max_value=365)
        min_notice_hours = st.number_input("Minimum notice hours", value=24, min_value=1, max_value=168)
        max_daily_appointments = st.number_input("Max appointments per day", value=8, min_value=1, max_value=20)
    
    with col2:
        allow_same_day = st.checkbox("Allow same-day booking", value=False)
        require_confirmation = st.checkbox("Require email confirmation", value=True)
        send_reminders = st.checkbox("Send appointment reminders", value=True)
        
        if send_reminders:
            reminder_hours = st.selectbox("Reminder timing", [1, 2, 4, 24, 48], index=3)
    
    # Save settings
    if st.button("💾 Save Settings", type="primary"):
        settings = {
            "weekday_hours": f"{weekday_start} - {weekday_end}",
            "weekend_enabled": weekend_enabled,
            "advance_booking_days": advance_booking_days,
            "min_notice_hours": min_notice_hours,
            "max_daily_appointments": max_daily_appointments,
            "allow_same_day": allow_same_day,
            "require_confirmation": require_confirmation,
            "send_reminders": send_reminders
        }
        
        st.success("✅ Settings saved successfully!")
        st.json(settings)

def show_booking_analytics():
    """Show booking analytics and insights"""
    st.subheader("Booking Analytics & Insights")
    
    if "gsheets_creds" in st.session_state:
        df = get_sheet_as_df("appointments")
        
        if df is not None and not df.empty:
            df['Date'] = pd.to_datetime(df['Date'])
            df['Hour'] = pd.to_datetime(df['Time'], format='%H:%M').dt.hour
            
            # Time period selector
            col1, col2 = st.columns(2)
            
            with col1:
                date_range = st.date_input(
                    "Analysis Period",
                    value=(datetime.now().date() - timedelta(days=30), datetime.now().date()),
                    help="Select date range for analysis"
                )
            
            with col2:
                if isinstance(date_range, tuple) and len(date_range) == 2:
                    filtered_df = df[
                        (df['Date'].dt.date >= date_range[0]) & 
                        (df['Date'].dt.date <= date_range[1])
                    ]
                else:
                    filtered_df = df
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_bookings = len(filtered_df)
                st.metric("📅 Total Bookings", total_bookings)
            
            with col2:
                completion_rate = len(filtered_df[filtered_df['Status'] == 'Completed']) / total_bookings * 100 if total_bookings > 0 else 0
                st.metric("✅ Completion Rate", f"{completion_rate:.1f}%")
            
            with col3:
                no_show_rate = len(filtered_df[filtered_df['Status'] == 'No-show']) / total_bookings * 100 if total_bookings > 0 else 0
                st.metric("❌ No-show Rate", f"{no_show_rate:.1f}%")
            
            with col4:
                avg_duration = filtered_df['Duration'].astype(int).mean() if not filtered_df.empty else 0
                st.metric("⏱️ Avg Duration", f"{avg_duration:.0f} min")
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Bookings by day of week
                filtered_df['DayOfWeek'] = filtered_df['Date'].dt.day_name()
                day_counts = filtered_df['DayOfWeek'].value_counts()
                
                # Order days properly
                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                day_counts = day_counts.reindex([day for day in day_order if day in day_counts.index])
                
                fig_days = px.bar(
                    x=day_counts.index,
                    y=day_counts.values,
                    title="Bookings by Day of Week"
                )
                st.plotly_chart(fig_days, use_container_width=True)
            
            with col2:
                # Bookings by hour
                hour_counts = filtered_df['Hour'].value_counts().sort_index()
                
                fig_hours = px.bar(
                    x=hour_counts.index,
                    y=hour_counts.values,
                    title="Bookings by Hour of Day"
                )
                fig_hours.update_xaxis(title="Hour")
                fig_hours.update_yaxis(title="Number of Bookings")
                st.plotly_chart(fig_hours, use_container_width=True)
            
            # Service popularity
            st.subheader("📊 Service Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                service_counts = filtered_df['Service'].value_counts()
                fig_services = px.pie(
                    values=service_counts.values,
                    names=service_counts.index,
                    title="Service Distribution"
                )
                st.plotly_chart(fig_services, use_container_width=True)
            
            with col2:
                # Monthly booking trend
                monthly_bookings = filtered_df.groupby(filtered_df['Date'].dt.to_period('M')).size()
                
                fig_trend = px.line(
                    x=monthly_bookings.index.astype(str),
                    y=monthly_bookings.values,
                    title="Monthly Booking Trend"
                )
                st.plotly_chart(fig_trend, use_container_width=True)
            
            # Peak times analysis
            st.subheader("🕐 Peak Times Analysis")
            
            # Create heatmap of bookings by day and hour
            pivot_data = filtered_df.pivot_table(
                values='Duration', 
                index='DayOfWeek', 
                columns='Hour', 
                aggfunc='count', 
                fill_value=0
            )
            
            # Reorder days
            pivot_data = pivot_data.reindex([day for day in day_order if day in pivot_data.index])
            
            fig_heatmap = px.imshow(
                pivot_data,
                title="Booking Heatmap: Day vs Hour",
                color_continuous_scale='Blues',
                aspect='auto'
            )
            fig_heatmap.update_xaxis(title="Hour of Day")
            fig_heatmap.update_yaxis(title="Day of Week")
            st.plotly_chart(fig_heatmap, use_container_width=True)
            
        else:
            st.info("No booking data available for analysis.")
    else:
        st.warning("⚠️ Please connect Google Sheets to view analytics.")

def show_notifications():
    """Show and manage notifications"""
    st.subheader("📢 Notifications & Reminders")
    
    # Notification settings
    st.markdown("### ⚙️ Notification Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Email Notifications**")
        email_new_booking = st.checkbox("New booking received", value=True)
        email_cancellation = st.checkbox("Booking cancelled", value=True)
        email_reminder = st.checkbox("Daily schedule summary", value=True)
        email_no_show = st.checkbox("No-show alerts", value=True)
    
    with col2:
        st.markdown("**SMS Notifications**")
        sms_new_booking = st.checkbox("New booking SMS", value=False)
        sms_reminder = st.checkbox("Appointment reminders", value=True)
        sms_confirmation = st.checkbox("Booking confirmations", value=True)
        sms_follow_up = st.checkbox("Follow-up messages", value=False)
    
    # Recent notifications
    st.markdown("### 📋 Recent Notifications")
    
    # Sample notification data (would be from database in real app)
    notifications = [
        {
            "time": "2 minutes ago",
            "type": "New Booking",
            "message": "John Doe booked a consultation for tomorrow at 2:00 PM",
            "status": "unread"
        },
        {
            "time": "1 hour ago",
            "type": "Reminder Sent",
            "message": "Appointment reminder sent to jane.smith@email.com",
            "status": "read"
        },
        {
            "time": "3 hours ago",
            "type": "Cancellation",
            "message": "Bob Johnson cancelled appointment for today 3:00 PM",
            "status": "read"
        },
        {
            "time": "Yesterday",
            "type": "No-show",
            "message": "Sarah Wilson did not attend scheduled appointment",
            "status": "read"
        }
    ]
    
    for notification in notifications:
        status_icon = "🔵" if notification["status"] == "unread" else "⚪"
        type_icon = {
            "New Booking": "📅",
            "Reminder Sent": "📧",
            "Cancellation": "❌",
            "No-show": "⚠️"
        }.get(notification["type"], "📢")
        
        with st.expander(f"{status_icon} {type_icon} {notification['type']} - {notification['time']}"):
            st.write(notification["message"])
            
            col1, col2 = st.columns(2)
            with col1:
                if notification["status"] == "unread":
                    if st.button("Mark as Read", key=f"read_{notification['time']}"):
                        st.success("Marked as read")
            
            with col2:
                if st.button("Delete", key=f"delete_{notification['time']}"):
                    st.success("Notification deleted")
    
    # Upcoming reminders
    st.markdown("### ⏰ Upcoming Reminders")
    
    if "gsheets_creds" in st.session_state:
        df = get_sheet_as_df("appointments")
        
        if df is not None and not df.empty:
            tomorrow = datetime.now().date() + timedelta(days=1)
            upcoming = df[
                (pd.to_datetime(df['Date']).dt.date == tomorrow) &
                (df['Status'].isin(['Scheduled', 'Confirmed']))
            ]
            
            if not upcoming.empty:
                st.markdown(f"**{len(upcoming)} reminders to send tomorrow:**")
                
                for _, appointment in upcoming.iterrows():
                    st.markdown(f"- 📧 {appointment['Customer']} at {appointment['Time']} ({appointment['Service']})")
            else:
                st.info("No reminders scheduled for tomorrow")
    
    # Manual notification sender
    st.markdown("### 📤 Send Manual Notification")
    
    with st.form("manual_notification"):
        col1, col2 = st.columns(2)
        
        with col1:
            recipient = st.text_input("Recipient (email or phone)")
            notification_type = st.selectbox("Type", ["Email", "SMS"])
        
        with col2:
            subject = st.text_input("Subject")
            message = st.text_area("Message")
        
        if st.form_submit_button("📤 Send Notification"):
            if recipient and message:
                st.success(f"✅ {notification_type} sent to {recipient}")
            else:
                st.error("Please fill in recipient and message")

def show_todays_schedule():
    """Show today's appointment schedule"""
    if "gsheets_creds" in st.session_state:
        df = get_sheet_as_df("appointments")
        
        if df is not None and not df.empty:
            today = datetime.now().date()
            today_appointments = df[pd.to_datetime(df['Date']).dt.date == today]
            
            if not today_appointments.empty:
                today_appointments = today_appointments.sort_values('Time')
                
                for _, appointment in today_appointments.iterrows():
                    status_color = {
                        'Scheduled': '🟡',
                        'Completed': '🟢',
                        'Cancelled': '🔴',
                        'No-show': '⚫'
                    }.get(appointment['Status'], '⚪')
                    
                    st.markdown(f"""
                    {status_color} **{appointment['Time']}** - {appointment['Customer']}  
                    {appointment['Service']} ({appointment['Duration']} min)
                    """)
            else:
                st.info("No appointments scheduled for today")
        else:
            st.info("No appointment data available")
    else:
        st.warning("Connect Google Sheets to view schedule")

def show_recent_bookings():
    """Show recent bookings with quick actions"""
    if "gsheets_creds" in st.session_state:
        df = get_sheet_as_df("appointments")
        
        if df is not None and not df.empty:
            # Get last 10 appointments
            df['DateTime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
            recent_bookings = df.nlargest(10, 'DateTime')
            
            for _, booking in recent_bookings.iterrows():
                with st.expander(f"📅 {booking['Customer']} - {booking['Date']} {booking['Time']}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Service:** {booking['Service']}")
                        st.write(f"**Duration:** {booking['Duration']} min")
                        st.write(f"**Status:** {booking['Status']}")
                    
                    with col2:
                        st.write(f"**Phone:** {booking.get('Phone', 'N/A')}")
                        st.write(f"**Email:** {booking.get('Email', 'N/A')}")
                    
                    with col3:
                        if st.button("✏️ Edit", key=f"edit_recent_{booking.name}"):
                            st.info("Edit functionality would open here")
                        
                        if st.button("❌ Cancel", key=f"cancel_recent_{booking.name}"):
                            update_appointment_status(booking.name, "Cancelled")
        else:
            st.info("No recent bookings to display")

def book_appointment(customer_name, phone, email, appointment_date, appointment_time, service, duration, notes):
    """Book a new appointment"""
    if not customer_name or not service:
        st.error("❌ Please fill in required fields (Customer Name and Service)")
        return
    
    # Check for conflicts
    if check_booking_conflict(appointment_date, appointment_time, duration):
        st.error("❌ Time slot conflict detected. Please choose a different time.")
        return
    
    # Create appointment record
    appointment_id = f"APT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    new_appointment = {
        "ID": appointment_id,
        "Customer": customer_name,
        "Phone": phone,
        "Email": email,
        "Date": appointment_date.strftime("%Y-%m-%d"),
        "Time": appointment_time.strftime("%H:%M"),
        "Service": service,
        "Duration": duration,
        "Status": "Scheduled",
        "Notes": notes,
        "Created_By": st.session_state.user_name,
        "Created_Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    if save_appointment_booking(new_appointment):
        st.success(f"✅ Appointment booked successfully! ID: {appointment_id}")
        st.balloons()
        
        # Send confirmation
        if email:
            st.info(f"📧 Confirmation email sent to {email}")
    else:
        st.error("❌ Failed to book appointment. Please try again.")

def check_booking_conflict(appointment_date, appointment_time, duration):
    """Check for booking conflicts"""
    if "gsheets_creds" not in st.session_state:
        return False
    
    df = get_sheet_as_df("appointments")
    if df is None or df.empty:
        return False
    
    # Convert to datetime for comparison
    new_start = datetime.combine(appointment_date, appointment_time)
    new_end = new_start + timedelta(minutes=duration)
    
    # Check existing appointments on the same date
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    same_day_appointments = df[df['Date'] == appointment_date]
    
    for _, existing in same_day_appointments.iterrows():
        if existing['Status'] in ['Cancelled', 'No-show']:
            continue
        
        existing_start = datetime.combine(
            appointment_date,
            datetime.strptime(existing['Time'], '%H:%M').time()
        )
        existing_end = existing_start + timedelta(minutes=int(existing['Duration']))
        
        # Check for overlap
        if (new_start < existing_end) and (new_end > existing_start):
            return True
    
    return False

def save_appointment_booking(appointment_data):
    """Save appointment booking to Google Sheets"""
    if "gsheets_creds" not in st.session_state:
        return False
    
    try:
        existing_df = get_sheet_as_df("appointments")
        
        if existing_df is not None:
            new_df = pd.concat([existing_df, pd.DataFrame([appointment_data])], ignore_index=True)
        else:
            new_df = pd.DataFrame([appointment_data])
        
        return update_sheet_from_df("appointments", new_df)
    except Exception as e:
        st.error(f"Error saving appointment: {str(e)}")
        return False

def update_appointment_status(appointment_index, new_status):
    """Update appointment status"""
    if "gsheets_creds" not in st.session_state:
        return False
    
    try:
        df = get_sheet_as_df("appointments")
        if df is not None:
            df.loc[appointment_index, 'Status'] = new_status
            if update_sheet_from_df("appointments", df):
                st.success(f"✅ Appointment status updated to {new_status}")
                st.rerun()
        return True
    except Exception as e:
        st.error(f"Error updating appointment: {str(e)}")
        return False

if __name__ == "__main__":
    main()

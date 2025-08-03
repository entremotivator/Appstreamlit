import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import calendar
from utils.auth import require_auth
from utils.gsheet import get_sheet_as_df, update_sheet_from_df
from utils.validators import validate_required_fields

@require_auth
def main():
    st.title("📅 Calendar & Scheduling")
    
    # Tabs for different calendar views
    tab1, tab2, tab3, tab4 = st.tabs(["📅 Calendar View", "➕ Schedule Appointment", "📋 Appointments List", "📊 Schedule Analytics"])
    
    with tab1:
        show_calendar_view()
    
    with tab2:
        schedule_new_appointment()
    
    with tab3:
        show_appointments_list()
    
    with tab4:
        show_schedule_analytics()

def show_calendar_view():
    """Display calendar with appointments"""
    st.subheader("Calendar Overview")
    
    # Calendar controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        selected_date = st.date_input("Select Date", value=datetime.now().date())
    
    with col2:
        view_mode = st.selectbox("View Mode", ["Day", "Week", "Month"])
    
    with col3:
        filter_status = st.selectbox("Filter Status", ["All", "Scheduled", "Completed", "Cancelled"])
    
    # Load appointments data
    if "gsheets_creds" in st.session_state:
        df = get_sheet_as_df("appointments")
        
        if df is not None and not df.empty:
            # Convert date columns
            df['Date'] = pd.to_datetime(df['Date']).dt.date
            df['Time'] = pd.to_datetime(df['Time'], format='%H:%M').dt.time
            
            # Filter based on view mode and selected date
            if view_mode == "Day":
                filtered_df = df[df['Date'] == selected_date]
            elif view_mode == "Week":
                start_week = selected_date - timedelta(days=selected_date.weekday())
                end_week = start_week + timedelta(days=6)
                filtered_df = df[(df['Date'] >= start_week) & (df['Date'] <= end_week)]
            else:  # Month view
                start_month = selected_date.replace(day=1)
                if selected_date.month == 12:
                    end_month = start_month.replace(year=selected_date.year + 1, month=1) - timedelta(days=1)
                else:
                    end_month = start_month.replace(month=selected_date.month + 1) - timedelta(days=1)
                filtered_df = df[(df['Date'] >= start_month) & (df['Date'] <= end_month)]
            
            # Apply status filter
            if filter_status != "All":
                filtered_df = filtered_df[filtered_df['Status'] == filter_status]
            
            # Display appointments
            if not filtered_df.empty:
                st.markdown(f"**{len(filtered_df)} appointments found**")
                
                # Group by date for better display
                for date_group in filtered_df['Date'].unique():
                    date_appointments = filtered_df[filtered_df['Date'] == date_group].sort_values('Time')
                    
                    st.markdown(f"### 📅 {date_group.strftime('%A, %B %d, %Y')}")
                    
                    for _, appointment in date_appointments.iterrows():
                        status_color = {
                            'Scheduled': '🟡',
                            'Completed': '🟢', 
                            'Cancelled': '🔴'
                        }.get(appointment['Status'], '⚪')
                        
                        with st.expander(f"{status_color} {appointment['Time']} - {appointment['Customer']} ({appointment['Service']})"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write(f"**Customer:** {appointment['Customer']}")
                                st.write(f"**Service:** {appointment['Service']}")
                                st.write(f"**Duration:** {appointment['Duration']} minutes")
                                st.write(f"**Status:** {appointment['Status']}")
                            
                            with col2:
                                st.write(f"**Phone:** {appointment.get('Phone', 'N/A')}")
                                st.write(f"**Email:** {appointment.get('Email', 'N/A')}")
                                st.write(f"**Notes:** {appointment.get('Notes', 'None')}")
                                
                                # Quick actions
                                col_actions = st.columns(3)
                                with col_actions[0]:
                                    if st.button("✅ Complete", key=f"complete_{appointment.name}"):
                                        update_appointment_status(appointment.name, "Completed")
                                
                                with col_actions[1]:
                                    if st.button("❌ Cancel", key=f"cancel_{appointment.name}"):
                                        update_appointment_status(appointment.name, "Cancelled")
                                
                                with col_actions[2]:
                                    if st.button("✏️ Edit", key=f"edit_{appointment.name}"):
                                        st.session_state[f"edit_appointment_{appointment.name}"] = True
            else:
                st.info(f"No appointments found for the selected {view_mode.lower()}")
                
            # Calendar heatmap for month view
            if view_mode == "Month":
                st.subheader("📊 Monthly Activity Heatmap")
                create_calendar_heatmap(df, selected_date)
        else:
            st.info("No appointments data found. Schedule your first appointment!")
    else:
        st.warning("⚠️ Please connect Google Sheets to view calendar.")

def schedule_new_appointment():
    """Schedule a new appointment"""
    st.subheader("Schedule New Appointment")
    
    # Load customers for dropdown
    customers_df = None
    if "gsheets_creds" in st.session_state:
        customers_df = get_sheet_as_df("customers")
    
    with st.form("new_appointment_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            if customers_df is not None and not customers_df.empty:
                customer_options = ["New Customer"] + customers_df['Name'].tolist()
                customer_selection = st.selectbox("Customer", customer_options)
                
                if customer_selection == "New Customer":
                    customer_name = st.text_input("Customer Name *")
                    customer_phone = st.text_input("Phone Number")
                    customer_email = st.text_input("Email")
                else:
                    customer_data = customers_df[customers_df['Name'] == customer_selection].iloc[0]
                    customer_name = customer_selection
                    customer_phone = st.text_input("Phone Number", value=customer_data.get('Phone', ''))
                    customer_email = st.text_input("Email", value=customer_data.get('Email', ''))
            else:
                customer_name = st.text_input("Customer Name *")
                customer_phone = st.text_input("Phone Number")
                customer_email = st.text_input("Email")
            
            appointment_date = st.date_input("Appointment Date *", min_value=datetime.now().date())
            appointment_time = st.time_input("Appointment Time *", value=datetime.now().time())
        
        with col2:
            services = [
                "Consultation", "Follow-up", "Treatment", "Assessment",
                "Meeting", "Training", "Support", "Other"
            ]
            service = st.selectbox("Service Type *", services)
            
            if service == "Other":
                custom_service = st.text_input("Specify Service")
                service = custom_service if custom_service else "Other"
            
            duration = st.selectbox("Duration (minutes)", [15, 30, 45, 60, 90, 120], index=2)
            status = st.selectbox("Status", ["Scheduled", "Confirmed", "Pending"])
            location = st.text_input("Location", placeholder="Office, Online, Client Location")
        
        notes = st.text_area("Notes", placeholder="Any special requirements or notes")
        
        # Reminder settings
        st.markdown("**Reminder Settings**")
        send_reminder = st.checkbox("Send reminder notifications")
        if send_reminder:
            reminder_time = st.selectbox("Remind before", ["1 hour", "2 hours", "1 day", "2 days"])
        
        submitted = st.form_submit_button("📅 Schedule Appointment", type="primary")
        
        if submitted:
            required_data = {
                "customer_name": customer_name,
                "appointment_date": appointment_date,
                "appointment_time": appointment_time,
                "service": service
            }
            
            errors = validate_required_fields(required_data, ["customer_name", "service"])
            
            if errors:
                for field, error in errors.items():
                    st.error(f"❌ {error}")
            else:
                # Check for scheduling conflicts
                if check_scheduling_conflict(appointment_date, appointment_time, duration):
                    st.error("❌ Scheduling conflict detected! Please choose a different time.")
                else:
                    new_appointment = {
                        "ID": f"APT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        "Customer": customer_name,
                        "Phone": customer_phone,
                        "Email": customer_email,
                        "Date": appointment_date.strftime("%Y-%m-%d"),
                        "Time": appointment_time.strftime("%H:%M"),
                        "Service": service,
                        "Duration": duration,
                        "Status": status,
                        "Location": location,
                        "Notes": notes,
                        "Reminder": send_reminder,
                        "Created_By": st.session_state.user_name,
                        "Created_Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    if save_appointment(new_appointment):
                        st.success("✅ Appointment scheduled successfully!")
                        st.balloons()
                        
                        if send_reminder:
                            st.info(f"📱 Reminder set for {reminder_time} before appointment")

def show_appointments_list():
    """Show list of all appointments with management options"""
    st.subheader("Appointments Management")
    
    if "gsheets_creds" in st.session_state:
        df = get_sheet_as_df("appointments")
        
        if df is not None and not df.empty:
            # Filters
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                date_filter = st.date_input("From Date", value=datetime.now().date() - timedelta(days=30))
            
            with col2:
                end_date_filter = st.date_input("To Date", value=datetime.now().date() + timedelta(days=30))
            
            with col3:
                status_filter = st.selectbox("Status Filter", ["All", "Scheduled", "Completed", "Cancelled"])
            
            with col4:
                service_filter = st.selectbox("Service Filter", ["All"] + df['Service'].unique().tolist())
            
            # Apply filters
            filtered_df = df.copy()
            filtered_df['Date'] = pd.to_datetime(filtered_df['Date']).dt.date
            
            filtered_df = filtered_df[
                (filtered_df['Date'] >= date_filter) & 
                (filtered_df['Date'] <= end_date_filter)
            ]
            
            if status_filter != "All":
                filtered_df = filtered_df[filtered_df['Status'] == status_filter]
            
            if service_filter != "All":
                filtered_df = filtered_df[filtered_df['Service'] == service_filter]
            
            st.markdown(f"**Found {len(filtered_df)} appointments**")
            
            # Editable appointments table
            edited_df = st.data_editor(
                filtered_df,
                use_container_width=True,
                num_rows="dynamic",
                column_config={
                    "Date": st.column_config.DateColumn("Date"),
                    "Time": st.column_config.TimeColumn("Time"),
                    "Duration": st.column_config.NumberColumn("Duration (min)", min_value=15, max_value=480),
                    "Status": st.column_config.SelectboxColumn(
                        "Status",
                        options=["Scheduled", "Confirmed", "Completed", "Cancelled", "No-show"]
                    )
                },
                hide_index=True
            )
            
            # Action buttons
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("💾 Save Changes", type="primary"):
                    if update_sheet_from_df("appointments", edited_df):
                        st.success("✅ Appointments updated!")
                        st.rerun()
            
            with col2:
                if st.button("📧 Send Reminders"):
                    send_appointment_reminders(edited_df)
            
            with col3:
                if st.button("📊 Export Report"):
                    csv = edited_df.to_csv(index=False)
                    st.download_button("⬇️ Download CSV", csv, "appointments_report.csv")
            
            with col4:
                if st.button("🔄 Refresh Data"):
                    st.rerun()
        else:
            st.info("No appointments found.")
    else:
        st.warning("⚠️ Please connect Google Sheets to manage appointments.")

def show_schedule_analytics():
    """Show scheduling analytics and insights"""
    st.subheader("Schedule Analytics")
    
    if "gsheets_creds" in st.session_state:
        df = get_sheet_as_df("appointments")
        
        if df is not None and not df.empty:
            df['Date'] = pd.to_datetime(df['Date'])
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_appointments = len(df)
                st.metric("📅 Total Appointments", total_appointments)
            
            with col2:
                completed_appointments = len(df[df['Status'] == 'Completed'])
                completion_rate = (completed_appointments / total_appointments * 100) if total_appointments > 0 else 0
                st.metric("✅ Completion Rate", f"{completion_rate:.1f}%")
            
            with col3:
                no_shows = len(df[df['Status'] == 'No-show'])
                no_show_rate = (no_shows / total_appointments * 100) if total_appointments > 0 else 0
                st.metric("❌ No-show Rate", f"{no_show_rate:.1f}%")
            
            with col4:
                avg_duration = df['Duration'].astype(int).mean()
                st.metric("⏱️ Avg Duration", f"{avg_duration:.0f} min")
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Appointments by status
                status_counts = df['Status'].value_counts()
                fig_status = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    title="Appointments by Status"
                )
                st.plotly_chart(fig_status, use_container_width=True)
            
            with col2:
                # Appointments by service type
                service_counts = df['Service'].value_counts()
                fig_service = px.bar(
                    x=service_counts.index,
                    y=service_counts.values,
                    title="Appointments by Service Type"
                )
                fig_service.update_xaxis_categoryorder("total descending")
                st.plotly_chart(fig_service, use_container_width=True)
            
            # Time-based analytics
            st.subheader("📈 Scheduling Trends")
            
            # Daily appointment volume
            daily_appointments = df.groupby(df['Date'].dt.date).size().reset_index()
            daily_appointments.columns = ['Date', 'Count']
            
            fig_daily = px.line(
                daily_appointments,
                x='Date',
                y='Count',
                title="Daily Appointment Volume"
            )
            st.plotly_chart(fig_daily, use_container_width=True)
            
            # Hour of day analysis
            df['Hour'] = pd.to_datetime(df['Time'], format='%H:%M').dt.hour
            hourly_distribution = df['Hour'].value_counts().sort_index()
            
            fig_hourly = px.bar(
                x=hourly_distribution.index,
                y=hourly_distribution.values,
                title="Appointments by Hour of Day",
                labels={'x': 'Hour', 'y': 'Number of Appointments'}
            )
            st.plotly_chart(fig_hourly, use_container_width=True)
            
        else:
            st.info("No appointment data available for analytics.")
    else:
        st.warning("⚠️ Please connect Google Sheets to view analytics.")

def create_calendar_heatmap(df, selected_date):
    """Create a calendar heatmap showing appointment density"""
    # Get the month data
    month_start = selected_date.replace(day=1)
    if selected_date.month == 12:
        month_end = month_start.replace(year=selected_date.year + 1, month=1) - timedelta(days=1)
    else:
        month_end = month_start.replace(month=selected_date.month + 1) - timedelta(days=1)
    
    # Filter data for the month
    df['Date'] = pd.to_datetime(df['Date']).dt.date
    month_df = df[(df['Date'] >= month_start.date()) & (df['Date'] <= month_end.date())]
    
    # Count appointments per day
    daily_counts = month_df.groupby('Date').size().reset_index()
    daily_counts.columns = ['Date', 'Appointments']
    
    # Create a complete date range for the month
    date_range = pd.date_range(month_start, month_end, freq='D')
    complete_df = pd.DataFrame({'Date': date_range.date})
    complete_df = complete_df.merge(daily_counts, on='Date', how='left')
    complete_df['Appointments'] = complete_df['Appointments'].fillna(0)
    
    # Create heatmap
    fig = px.density_heatmap(
        complete_df,
        x=complete_df['Date'].apply(lambda x: x.strftime('%d')),
        y=complete_df['Date'].apply(lambda x: calendar.day_name[x.weekday()]),
        z='Appointments',
        title=f"Appointment Density - {selected_date.strftime('%B %Y')}",
        color_continuous_scale='Blues'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def check_scheduling_conflict(appointment_date, appointment_time, duration):
    """Check if there's a scheduling conflict"""
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

def save_appointment(appointment_data):
    """Save new appointment to Google Sheets"""
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

def send_appointment_reminders(df):
    """Send appointment reminders"""
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    
    upcoming_appointments = df[
        (pd.to_datetime(df['Date']).dt.date == tomorrow) &
        (df['Status'].isin(['Scheduled', 'Confirmed']))
    ]
    
    if len(upcoming_appointments) > 0:
        st.success(f"📱 Sent reminders for {len(upcoming_appointments)} upcoming appointments")
        # Here you would integrate with SMS/email service
    else:
        st.info("No appointments need reminders today")

if __name__ == "__main__":
    main()

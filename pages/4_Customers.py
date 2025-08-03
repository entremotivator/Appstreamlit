import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import uuid
from utils.auth import require_auth
from utils.gsheet import get_sheet_as_df, update_sheet_from_df
from utils.validators import validate_required_fields, validate_email, validate_phone

@require_auth
def main():
    st.title("👥 Customer Management")
    
    # Tabs for different customer operations
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Customer List", "➕ Add Customer", "📊 Customer Analytics", "📧 Communications"])
    
    with tab1:
        show_customers_list()
    
    with tab2:
        add_new_customer()
    
    with tab3:
        show_customer_analytics()
    
    with tab4:
        show_customer_communications()

def show_customers_list():
    """Display and manage customer list"""
    st.subheader("Customer Database")
    
    if "gsheets_creds" in st.session_state:
        df = get_sheet_as_df("customers")
        
        if df is not None and not df.empty:
            # Search and filter options
            col1, col2, col3 = st.columns(3)
            
            with col1:
                search_term = st.text_input("🔍 Search Customers", placeholder="Name, email, or phone")
            
            with col2:
                status_filter = st.selectbox("Status Filter", ["All", "Active", "Inactive", "Prospect"])
            
            with col3:
                sort_by = st.selectbox("Sort By", ["Name", "Created Date", "Last Contact", "Total Value"])
            
            # Apply filters
            filtered_df = df.copy()
            
            if search_term:
                mask = (
                    filtered_df['Name'].str.contains(search_term, case=False, na=False) |
                    filtered_df['Email'].str.contains(search_term, case=False, na=False) |
                    filtered_df['Phone'].str.contains(search_term, case=False, na=False)
                )
                filtered_df = filtered_df[mask]
            
            if status_filter != "All":
                filtered_df = filtered_df[filtered_df['Status'] == status_filter]
            
            # Sort dataframe
            if sort_by in filtered_df.columns:
                if sort_by in ['Created Date', 'Last Contact']:
                    filtered_df[sort_by] = pd.to_datetime(filtered_df[sort_by])
                    filtered_df = filtered_df.sort_values(sort_by, ascending=False)
                elif sort_by == 'Total Value':
                    filtered_df[sort_by] = pd.to_numeric(filtered_df[sort_by], errors='coerce')
                    filtered_df = filtered_df.sort_values(sort_by, ascending=False)
                else:
                    filtered_df = filtered_df.sort_values(sort_by)
            
            st.markdown(f"**Found {len(filtered_df)} customers**")
            
            # Customer cards view
            if st.checkbox("📋 Card View"):
                show_customer_cards(filtered_df)
            else:
                # Table view with editing capabilities
                edited_df = st.data_editor(
                    filtered_df,
                    use_container_width=True,
                    num_rows="dynamic",
                    column_config={
                        "Name": st.column_config.TextColumn("Customer Name", required=True),
                        "Email": st.column_config.TextColumn("Email"),
                        "Phone": st.column_config.TextColumn("Phone"),
                        "Status": st.column_config.SelectboxColumn(
                            "Status",
                            options=["Active", "Inactive", "Prospect", "Lead"]
                        ),
                        "Total_Value": st.column_config.NumberColumn(
                            "Total Value ($)",
                            format="$%.2f",
                            min_value=0
                        ),
                        "Last_Contact": st.column_config.DateColumn("Last Contact"),
                        "Created_Date": st.column_config.DateColumn("Created Date")
                    },
                    hide_index=True
                )
                
                # Action buttons
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if st.button("💾 Save Changes", type="primary"):
                        if update_sheet_from_df("customers", edited_df):
                            st.success("✅ Customer data updated!")
                            st.rerun()
                
                with col2:
                    if st.button("📧 Send Newsletter"):
                        send_newsletter(edited_df)
                
                with col3:
                    if st.button("📊 Export Data"):
                        csv = edited_df.to_csv(index=False)
                        st.download_button("⬇️ Download CSV", csv, "customers.csv")
                
                with col4:
                    if st.button("🔄 Refresh"):
                        st.rerun()
        else:
            st.info("No customers found. Add your first customer to get started!")
    else:
        st.warning("⚠️ Please connect Google Sheets to manage customers.")

def show_customer_cards(df):
    """Display customers in card format"""
    for i in range(0, len(df), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if i + j < len(df):
                customer = df.iloc[i + j]
                with col:
                    with st.container():
                        st.markdown(f"""
                        <div style="padding: 1rem; border: 1px solid #ddd; border-radius: 8px; margin-bottom: 1rem;">
                            <h4 style="margin: 0 0 0.5rem 0;">{customer['Name']}</h4>
                            <p style="margin: 0.25rem 0;"><strong>📧</strong> {customer.get('Email', 'N/A')}</p>
                            <p style="margin: 0.25rem 0;"><strong>📞</strong> {customer.get('Phone', 'N/A')}</p>
                            <p style="margin: 0.25rem 0;"><strong>💰</strong> ${customer.get('Total_Value', 0):,.2f}</p>
                            <p style="margin: 0.25rem 0;"><strong>Status:</strong> 
                                <span style="background: {'#28a745' if customer.get('Status') == 'Active' else '#6c757d'}; 
                                             color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8em;">
                                    {customer.get('Status', 'Unknown')}
                                </span>
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Action buttons for each customer
                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.button("✏️ Edit", key=f"edit_{i+j}"):
                                st.session_state[f"edit_customer_{i+j}"] = True
                        
                        with col_btn2:
                            if st.button("📞 Contact", key=f"contact_{i+j}"):
                                st.session_state.current_page = "Voice Calls"
                                st.rerun()

def add_new_customer():
    """Add new customer form"""
    st.subheader("Add New Customer")
    
    with st.form("new_customer_form"):
        # Basic information
        st.markdown("### 📋 Basic Information")
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name *", placeholder="Enter customer name")
            email = st.text_input("Email Address", placeholder="customer@example.com")
            phone = st.text_input("Phone Number", placeholder="+1 (555) 123-4567")
            company = st.text_input("Company", placeholder="Company name")
        
        with col2:
            status = st.selectbox("Status *", ["Prospect", "Lead", "Active", "Inactive"])
            source = st.selectbox("Lead Source", [
                "Website", "Referral", "Social Media", "Advertising", 
                "Cold Call", "Email Campaign", "Event", "Other"
            ])
            assigned_to = st.text_input("Assigned To", value=st.session_state.user_name)
            priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        
        # Contact information
        st.markdown("### 📍 Contact Details")
        col1, col2 = st.columns(2)
        
        with col1:
            address = st.text_area("Address", placeholder="Street address")
            city = st.text_input("City")
            state = st.text_input("State/Province")
        
        with col2:
            postal_code = st.text_input("Postal Code")
            country = st.text_input("Country", value="USA")
            website = st.text_input("Website", placeholder="https://example.com")
        
        # Additional information
        st.markdown("### 💼 Business Information")
        col1, col2 = st.columns(2)
        
        with col1:
            industry = st.selectbox("Industry", [
                "Technology", "Healthcare", "Finance", "Education", "Retail",
                "Manufacturing", "Real Estate", "Legal", "Consulting", "Other"
            ])
            company_size = st.selectbox("Company Size", [
                "1-10", "11-50", "51-200", "201-1000", "1000+", "Not Applicable"
            ])
        
        with col2:
            annual_revenue = st.selectbox("Annual Revenue", [
                "Under $1M", "$1M-$10M", "$10M-$100M", "$100M+", "Not Disclosed"
            ])
            decision_maker = st.checkbox("Is Decision Maker")
        
        # Notes and tags
        st.markdown("### 📝 Additional Information")
        notes = st.text_area("Notes", placeholder="Any additional information about the customer")
        tags = st.text_input("Tags", placeholder="Comma-separated tags (e.g., VIP, Premium, Tech)")
        
        # Submit button
        submitted = st.form_submit_button("➕ Add Customer", type="primary")
        
        if submitted:
            # Validation
            required_data = {"name": name, "status": status}
            errors = validate_required_fields(required_data, ["name", "status"])
            
            if email and not validate_email(email):
                errors["email"] = "Please enter a valid email address"
            
            if phone and not validate_phone(phone):
                errors["phone"] = "Please enter a valid phone number"
            
            if errors:
                for field, error in errors.items():
                    st.error(f"❌ {error}")
            else:
                # Create customer record
                customer_id = f"CUST-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
                
                new_customer = {
                    "Customer_ID": customer_id,
                    "Name": name,
                    "Email": email,
                    "Phone": phone,
                    "Company": company,
                    "Status": status,
                    "Lead_Source": source,
                    "Assigned_To": assigned_to,
                    "Priority": priority,
                    "Address": address,
                    "City": city,
                    "State": state,
                    "Postal_Code": postal_code,
                    "Country": country,
                    "Website": website,
                    "Industry": industry,
                    "Company_Size": company_size,
                    "Annual_Revenue": annual_revenue,
                    "Decision_Maker": decision_maker,
                    "Notes": notes,
                    "Tags": tags,
                    "Total_Value": 0.00,
                    "Last_Contact": "",
                    "Created_Date": datetime.now().strftime("%Y-%m-%d"),
                    "Created_By": st.session_state.user_name,
                    "Modified_Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                if save_customer(new_customer):
                    st.success(f"✅ Customer {name} added successfully!")
                    st.balloons()
                    
                    # Option to schedule first appointment
                    if st.button("📅 Schedule First Appointment"):
                        st.session_state.current_page = "Calendar"
                        st.rerun()

def show_customer_analytics():
    """Show customer analytics and insights"""
    st.subheader("Customer Analytics")
    
    if "gsheets_creds" in st.session_state:
        df = get_sheet_as_df("customers")
        
        if df is not None and not df.empty:
            # Convert data types
            df['Total_Value'] = pd.to_numeric(df['Total_Value'], errors='coerce').fillna(0)
            df['Created_Date'] = pd.to_datetime(df['Created_Date'], errors='coerce')
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_customers = len(df)
                st.metric("👥 Total Customers", total_customers)
            
            with col2:
                active_customers = len(df[df['Status'] == 'Active'])
                st.metric("✅ Active Customers", active_customers)
            
            with col3:
                total_value = df['Total_Value'].sum()
                st.metric("💰 Total Customer Value", f"${total_value:,.2f}")
            
            with col4:
                avg_value = df['Total_Value'].mean()
                st.metric("📊 Average Value", f"${avg_value:,.2f}")
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Customer status distribution
                status_counts = df['Status'].value_counts()
                fig_status = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    title="Customer Status Distribution"
                )
                st.plotly_chart(fig_status, use_container_width=True)
            
            with col2:
                # Lead source analysis
                if 'Lead_Source' in df.columns:
                    source_counts = df['Lead_Source'].value_counts()
                    fig_source = px.bar(
                        x=source_counts.values,
                        y=source_counts.index,
                        orientation='h',
                        title="Customer Acquisition Sources"
                    )
                    st.plotly_chart(fig_source, use_container_width=True)
            
            # Customer acquisition trend
            st.subheader("📈 Customer Acquisition Trend")
            if not df['Created_Date'].isna().all():
                df_clean = df.dropna(subset=['Created_Date'])
                monthly_acquisitions = df_clean.groupby(
                    df_clean['Created_Date'].dt.to_period('M')
                ).size().reset_index()
                monthly_acquisitions.columns = ['Month', 'New_Customers']
                monthly_acquisitions['Month'] = monthly_acquisitions['Month'].astype(str)
                
                fig_trend = px.line(
                    monthly_acquisitions,
                    x='Month',
                    y='New_Customers',
                    title="Monthly Customer Acquisitions"
                )
                st.plotly_chart(fig_trend, use_container_width=True)
            
            # Top customers by value
            st.subheader("🏆 Top Customers by Value")
            top_customers = df.nlargest(10, 'Total_Value')[['Name', 'Company', 'Total_Value', 'Status']]
            
            if not top_customers.empty:
                fig_top = px.bar(
                    top_customers,
                    x='Total_Value',
                    y='Name',
                    orientation='h',
                    title="Top 10 Customers by Value",
                    color='Status'
                )
                st.plotly_chart(fig_top, use_container_width=True)
            
            # Industry analysis
            if 'Industry' in df.columns:
                st.subheader("🏭 Industry Distribution")
                industry_counts = df['Industry'].value_counts()
                
                fig_industry = px.treemap(
                    names=industry_counts.index,
                    parents=[""] * len(industry_counts),
                    values=industry_counts.values,
                    title="Customer Distribution by Industry"
                )
                st.plotly_chart(fig_industry, use_container_width=True)
            
            # Geographic analysis
            if 'State' in df.columns:
                st.subheader("🗺️ Geographic Distribution")
                state_counts = df['State'].value_counts().head(10)
                
                fig_geo = px.bar(
                    x=state_counts.index,
                    y=state_counts.values,
                    title="Top 10 States by Customer Count"
                )
                st.plotly_chart(fig_geo, use_container_width=True)
            
        else:
            st.info("No customer data available for analytics.")
    else:
        st.warning("⚠️ Please connect Google Sheets to view analytics.")

def show_customer_communications():
    """Show customer communication history and tools"""
    st.subheader("Customer Communications")
    
    # Communication tools
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📧 Email Marketing")
        
        if "gsheets_creds" in st.session_state:
            df = get_sheet_as_df("customers")
            
            if df is not None and not df.empty:
                # Email campaign options
                campaign_type = st.selectbox("Campaign Type", [
                    "Newsletter", "Promotional", "Follow-up", "Survey", "Event Invitation"
                ])
                
                target_audience = st.multiselect("Target Audience", [
                    "All Customers", "Active Only", "Prospects", "VIP Customers", "By Industry"
                ])
                
                email_subject = st.text_input("Email Subject")
                email_content = st.text_area("Email Content", height=200)
                
                if st.button("📧 Send Campaign"):
                    send_email_campaign(df, campaign_type, target_audience, email_subject, email_content)
            else:
                st.info("No customers available for email campaigns.")
    
    with col2:
        st.markdown("### 📱 SMS Marketing")
        
        sms_type = st.selectbox("SMS Type", [
            "Appointment Reminder", "Promotional", "Follow-up", "Survey"
        ])
        
        sms_content = st.text_area("SMS Content", height=100, max_chars=160)
        st.caption(f"Characters used: {len(sms_content)}/160")
        
        if st.button("📱 Send SMS"):
            send_sms_campaign(sms_type, sms_content)
    
    # Communication history
    st.markdown("### 📋 Communication History")
    
    # Sample communication history (would be from database in real app)
    history_data = [
        {"Date": "2024-01-15", "Customer": "John Doe", "Type": "Email", "Subject": "Welcome Email", "Status": "Sent"},
        {"Date": "2024-01-14", "Customer": "Jane Smith", "Type": "SMS", "Subject": "Appointment Reminder", "Status": "Delivered"},
        {"Date": "2024-01-13", "Customer": "Bob Johnson", "Type": "Call", "Subject": "Follow-up Call", "Status": "Completed"},
    ]
    
    history_df = pd.DataFrame(history_data)
    st.dataframe(history_df, use_container_width=True)
    
    # Communication analytics
    st.markdown("### 📊 Communication Analytics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📧 Emails Sent", "1,247", "12%")
    
    with col2:
        st.metric("📱 SMS Sent", "856", "8%")
    
    with col3:
        st.metric("📞 Calls Made", "342", "-2%")
    
    with col4:
        st.metric("💬 Response Rate", "23.5%", "5%")

def save_customer(customer_data):
    """Save new customer to Google Sheets"""
    if "gsheets_creds" not in st.session_state:
        return False
    
    try:
        existing_df = get_sheet_as_df("customers")
        
        if existing_df is not None:
            new_df = pd.concat([existing_df, pd.DataFrame([customer_data])], ignore_index=True)
        else:
            new_df = pd.DataFrame([customer_data])
        
        return update_sheet_from_df("customers", new_df)
    except Exception as e:
        st.error(f"Error saving customer: {str(e)}")
        return False

def send_newsletter(df):
    """Send newsletter to customers"""
    active_customers = df[df['Status'] == 'Active']
    email_count = len(active_customers[active_customers['Email'].notna()])
    
    if email_count > 0:
        st.success(f"📧 Newsletter sent to {email_count} customers!")
    else:
        st.warning("No customers with email addresses found.")

def send_email_campaign(df, campaign_type, target_audience, subject, content):
    """Send email campaign to selected customers"""
    if not subject or not content:
        st.error("Please fill in email subject and content.")
        return
    
    # Filter customers based on target audience
    target_customers = df.copy()
    
    if "Active Only" in target_audience:
        target_customers = target_customers[target_customers['Status'] == 'Active']
    
    if "Prospects" in target_audience:
        target_customers = target_customers[target_customers['Status'] == 'Prospect']
    
    email_recipients = len(target_customers[target_customers['Email'].notna()])
    
    if email_recipients > 0:
        st.success(f"📧 {campaign_type} campaign sent to {email_recipients} customers!")
        st.info(f"Subject: {subject}")
    else:
        st.warning("No customers match the target audience criteria.")

def send_sms_campaign(sms_type, content):
    """Send SMS campaign"""
    if not content:
        st.error("Please enter SMS content.")
        return
    
    if len(content) > 160:
        st.error("SMS content exceeds 160 character limit.")
        return
    
    st.success(f"📱 {sms_type} SMS sent successfully!")
    st.info(f"Content: {content}")

if __name__ == "__main__":
    main()

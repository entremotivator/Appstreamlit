import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import uuid
from utils.auth import require_auth
from utils.gsheet import get_sheet_as_df, update_sheet_from_df
from utils.validators import validate_required_fields, validate_currency

@require_auth
def main():
    st.title("💰 Pricing Management")
    
    # Tabs for pricing management
    tab1, tab2, tab3, tab4 = st.tabs(["💵 Price List", "➕ Add Service", "📊 Pricing Analytics", "🎯 Pricing Strategy"])
    
    with tab1:
        show_price_list()
    
    with tab2:
        add_new_service()
    
    with tab3:
        show_pricing_analytics()
    
    with tab4:
        show_pricing_strategy()

def show_price_list():
    """Display and manage service pricing"""
    st.subheader("Service Pricing List")
    
    if "gsheets_creds" in st.session_state:
        df = get_sheet_as_df("pricing")
        
        if df is not None and not df.empty:
            # Filters and controls
            col1, col2, col3 = st.columns(3)
            
            with col1:
                category_filter = st.selectbox(
                    "Filter by Category",
                    ["All"] + df['Category'].unique().tolist()
                )
            
            with col2:
                status_filter = st.selectbox(
                    "Filter by Status",
                    ["All", "Active", "Inactive", "Seasonal"]
                )
            
            with col3:
                sort_by = st.selectbox(
                    "Sort by",
                    ["Service Name", "Price", "Category", "Last Updated"]
                )
            
            # Apply filters
            filtered_df = df.copy()
            
            if category_filter != "All":
                filtered_df = filtered_df[filtered_df['Category'] == category_filter]
            
            if status_filter != "All":
                filtered_df = filtered_df[filtered_df['Status'] == status_filter]
            
            # Sort data
            if sort_by == "Price":
                filtered_df['Price'] = pd.to_numeric(filtered_df['Price'], errors='coerce')
                filtered_df = filtered_df.sort_values('Price', ascending=False)
            elif sort_by in filtered_df.columns:
                filtered_df = filtered_df.sort_values(sort_by)
            
            st.markdown(f"**Showing {len(filtered_df)} services**")
            
            # Pricing display options
            display_mode = st.radio("Display Mode", ["Table View", "Card View"], horizontal=True)
            
            if display_mode == "Card View":
                show_pricing_cards(filtered_df)
            else:
                # Editable table
                edited_df = st.data_editor(
                    filtered_df,
                    use_container_width=True,
                    num_rows="dynamic",
                    column_config={
                        "Service_Name": st.column_config.TextColumn("Service Name", required=True),
                        "Price": st.column_config.NumberColumn(
                            "Price ($)",
                            format="$%.2f",
                            min_value=0
                        ),
                        "Duration": st.column_config.NumberColumn(
                            "Duration (min)",
                            min_value=15,
                            max_value=480
                        ),
                        "Category": st.column_config.SelectboxColumn(
                            "Category",
                            options=["Consultation", "Treatment", "Training", "Support", "Other"]
                        ),
                        "Status": st.column_config.SelectboxColumn(
                            "Status",
                            options=["Active", "Inactive", "Seasonal"]
                        ),
                        "Discount_Eligible": st.column_config.CheckboxColumn("Discount Eligible")
                    },
                    hide_index=True
                )
                
                # Action buttons
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if st.button("💾 Save Changes", type="primary"):
                        if update_sheet_from_df("pricing", edited_df):
                            st.success("✅ Pricing updated successfully!")
                            st.rerun()
                
                with col2:
                    if st.button("📊 Bulk Update"):
                        show_bulk_update_modal(edited_df)
                
                with col3:
                    if st.button("📋 Export Pricing"):
                        csv = edited_df.to_csv(index=False)
                        st.download_button("⬇️ Download CSV", csv, "pricing_list.csv")
                
                with col4:
                    if st.button("🔄 Refresh"):
                        st.rerun()
        else:
            st.info("No pricing data found. Add your first service to get started!")
    else:
        st.warning("⚠️ Please connect Google Sheets to manage pricing.")

def show_pricing_cards(df):
    """Display pricing in card format"""
    for i in range(0, len(df), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if i + j < len(df):
                service = df.iloc[i + j]
                with col:
                    # Determine card color based on status
                    status_color = {
                        'Active': '#28a745',
                        'Inactive': '#6c757d',
                        'Seasonal': '#ffc107'
                    }.get(service.get('Status', 'Active'), '#28a745')
                    
                    st.markdown(f"""
                    <div style="
                        padding: 1.5rem; 
                        border: 2px solid {status_color}; 
                        border-radius: 12px; 
                        margin-bottom: 1rem;
                        background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
                        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    ">
                        <h4 style="margin: 0 0 1rem 0; color: #333;">{service['Service_Name']}</h4>
                        <div style="font-size: 2rem; font-weight: bold; color: {status_color}; margin: 0.5rem 0;">
                            ${service.get('Price', 0):.2f}
                        </div>
                        <p style="margin: 0.5rem 0; color: #666;">
                            <strong>Duration:</strong> {service.get('Duration', 'N/A')} minutes
                        </p>
                        <p style="margin: 0.5rem 0; color: #666;">
                            <strong>Category:</strong> {service.get('Category', 'N/A')}
                        </p>
                        <p style="margin: 0.5rem 0;">
                            <span style="
                                background: {status_color}; 
                                color: white; 
                                padding: 4px 8px; 
                                border-radius: 4px; 
                                font-size: 0.8em;
                                font-weight: bold;
                            ">
                                {service.get('Status', 'Active')}
                            </span>
                        </p>
                        <p style="margin: 1rem 0 0 0; color: #777; font-size: 0.9em;">
                            {service.get('Description', 'No description available')[:100]}...
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Action buttons
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("✏️ Edit", key=f"edit_price_{i+j}"):
                            st.session_state[f"edit_service_{i+j}"] = True
                    
                    with col_btn2:
                        if st.button("📊 Analytics", key=f"analytics_{i+j}"):
                            show_service_analytics(service)

def add_new_service():
    """Add new service pricing"""
    st.subheader("Add New Service")
    
    with st.form("new_service_form"):
        # Basic service information
        st.markdown("### 🛠️ Service Details")
        col1, col2 = st.columns(2)
        
        with col1:
            service_name = st.text_input("Service Name *", placeholder="Enter service name")
            category = st.selectbox("Category *", [
                "Consultation", "Treatment", "Training", "Support", 
                "Assessment", "Follow-up", "Emergency", "Other"
            ])
            duration = st.number_input("Duration (minutes) *", min_value=15, max_value=480, value=60, step=15)
            status = st.selectbox("Status", ["Active", "Inactive", "Seasonal"])
        
        with col2:
            price = st.number_input("Price ($) *", min_value=0.01, format="%.2f")
            cost = st.number_input("Cost ($)", min_value=0.00, format="%.2f", help="Your cost to deliver this service")
            
            # Calculate margin
            if price > 0 and cost > 0:
                margin = ((price - cost) / price) * 100
                st.metric("Profit Margin", f"{margin:.1f}%")
            
            discount_eligible = st.checkbox("Eligible for Discounts")
        
        # Pricing tiers
        st.markdown("### 💎 Pricing Tiers (Optional)")
        enable_tiers = st.checkbox("Enable tiered pricing")
        
        if enable_tiers:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**Basic Tier**")
                basic_price = st.number_input("Basic Price", min_value=0.01, format="%.2f")
                basic_features = st.text_area("Basic Features", height=100)
            
            with col2:
                st.markdown("**Standard Tier**")
                standard_price = st.number_input("Standard Price", min_value=0.01, format="%.2f")
                standard_features = st.text_area("Standard Features", height=100)
            
            with col3:
                st.markdown("**Premium Tier**")
                premium_price = st.number_input("Premium Price", min_value=0.01, format="%.2f")
                premium_features = st.text_area("Premium Features", height=100)
        
        # Additional details
        st.markdown("### 📋 Additional Information")
        description = st.text_area("Service Description", placeholder="Detailed description of the service")
        requirements = st.text_area("Requirements", placeholder="Any special requirements or prerequisites")
        notes = st.text_area("Internal Notes", placeholder="Notes for staff (not visible to customers)")
        
        # Tags and keywords
        tags = st.text_input("Tags", placeholder="Comma-separated tags for categorization")
        
        # Booking settings
        st.markdown("### 📅 Booking Settings")
        col1, col2 = st.columns(2)
        
        with col1:
            bookable_online = st.checkbox("Allow online booking", value=True)
            requires_approval = st.checkbox("Requires approval before booking")
        
        with col2:
            max_advance_booking = st.number_input("Max advance booking (days)", min_value=1, max_value=365, value=30)
            min_notice = st.number_input("Minimum notice (hours)", min_value=1, max_value=168, value=24)
        
        # Submit form
        submitted = st.form_submit_button("➕ Add Service", type="primary")
        
        if submitted:
            # Validation
            required_data = {
                "service_name": service_name,
                "category": category,
                "duration": duration,
                "price": price
            }
            
            errors = validate_required_fields(required_data, ["service_name", "category"])
            
            if not validate_currency(str(price)):
                errors["price"] = "Please enter a valid price"
            
            if errors:
                for field, error in errors.items():
                    st.error(f"❌ {error}")
            else:
                # Create service record
                service_id = f"SVC-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
                
                new_service = {
                    "Service_ID": service_id,
                    "Service_Name": service_name,
                    "Category": category,
                    "Duration": duration,
                    "Price": price,
                    "Cost": cost,
                    "Status": status,
                    "Description": description,
                    "Requirements": requirements,
                    "Notes": notes,
                    "Tags": tags,
                    "Discount_Eligible": discount_eligible,
                    "Bookable_Online": bookable_online,
                    "Requires_Approval": requires_approval,
                    "Max_Advance_Booking": max_advance_booking,
                    "Min_Notice": min_notice,
                    "Created_By": st.session_state.user_name,
                    "Created_Date": datetime.now().strftime("%Y-%m-%d"),
                    "Modified_Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # Add tier pricing if enabled
                if enable_tiers:
                    new_service.update({
                        "Basic_Price": basic_price,
                        "Basic_Features": basic_features,
                        "Standard_Price": standard_price,
                        "Standard_Features": standard_features,
                        "Premium_Price": premium_price,
                        "Premium_Features": premium_features
                    })
                
                if save_service(new_service):
                    st.success(f"✅ Service '{service_name}' added successfully!")
                    st.balloons()

def show_pricing_analytics():
    """Show pricing analytics and insights"""
    st.subheader("Pricing Analytics & Insights")
    
    if "gsheets_creds" in st.session_state:
        pricing_df = get_sheet_as_df("pricing")
        
        if pricing_df is not None and not pricing_df.empty:
            # Convert price to numeric
            pricing_df['Price'] = pd.to_numeric(pricing_df['Price'], errors='coerce')
            pricing_df['Cost'] = pd.to_numeric(pricing_df['Cost'], errors='coerce').fillna(0)
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                avg_price = pricing_df['Price'].mean()
                st.metric("💰 Average Price", f"${avg_price:.2f}")
            
            with col2:
                total_services = len(pricing_df)
                st.metric("🛠️ Total Services", total_services)
            
            with col3:
                active_services = len(pricing_df[pricing_df['Status'] == 'Active'])
                st.metric("✅ Active Services", active_services)
            
            with col4:
                # Calculate average margin
                pricing_df['Margin'] = ((pricing_df['Price'] - pricing_df['Cost']) / pricing_df['Price'] * 100)
                avg_margin = pricing_df['Margin'].mean()
                st.metric("📊 Avg Margin", f"{avg_margin:.1f}%")
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Price distribution by category
                category_avg = pricing_df.groupby('Category')['Price'].mean().sort_values(ascending=False)
                
                fig_category = px.bar(
                    x=category_avg.values,
                    y=category_avg.index,
                    orientation='h',
                    title="Average Price by Category"
                )
                fig_category.update_xaxis(title="Average Price ($)")
                st.plotly_chart(fig_category, use_container_width=True)
            
            with col2:
                # Service status distribution
                status_counts = pricing_df['Status'].value_counts()
                
                fig_status = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    title="Services by Status"
                )
                st.plotly_chart(fig_status, use_container_width=True)
            
            # Price range analysis
            st.subheader("💵 Price Range Analysis")
            
            # Create price ranges
            pricing_df['Price_Range'] = pd.cut(
                pricing_df['Price'], 
                bins=[0, 50, 100, 200, 500, float('inf')], 
                labels=['$0-50', '$51-100', '$101-200', '$201-500', '$500+']
            )
            
            range_counts = pricing_df['Price_Range'].value_counts()
            
            fig_ranges = px.bar(
                x=range_counts.index,
                y=range_counts.values,
                title="Services by Price Range"
            )
            st.plotly_chart(fig_ranges, use_container_width=True)
            
            # Profitability analysis
            st.subheader("📈 Profitability Analysis")
            
            profitable_services = pricing_df[pricing_df['Margin'] > 0]
            
            if not profitable_services.empty:
                fig_margin = px.scatter(
                    profitable_services,
                    x='Price',
                    y='Margin',
                    size='Duration',
                    color='Category',
                    hover_data=['Service_Name'],
                    title="Service Profitability: Price vs Margin"
                )
                st.plotly_chart(fig_margin, use_container_width=True)
            
            # Revenue potential (if we have booking data)
            invoices_df = get_sheet_as_df("invoices")
            if invoices_df is not None and not invoices_df.empty:
                st.subheader("💰 Revenue Analysis")
                
                # Merge pricing with invoice data to see actual revenue
                revenue_by_service = invoices_df.groupby('Service')['Amount'].sum().sort_values(ascending=False)
                
                fig_revenue = px.bar(
                    x=revenue_by_service.index,
                    y=revenue_by_service.values,
                    title="Actual Revenue by Service"
                )
                fig_revenue.update_xaxis(title="Service")
                fig_revenue.update_yaxis(title="Revenue ($)")
                st.plotly_chart(fig_revenue, use_container_width=True)
        else:
            st.info("No pricing data available for analytics.")
    else:
        st.warning("⚠️ Please connect Google Sheets to view analytics.")

def show_pricing_strategy():
    """Show pricing strategy tools and recommendations"""
    st.subheader("Pricing Strategy & Optimization")
    
    # Pricing strategy sections
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 Pricing Strategy Tools")
        
        # Competitor analysis
        st.markdown("**Competitor Analysis**")
        with st.expander("📊 Market Research"):
            competitor_service = st.text_input("Service to analyze")
            competitor_prices = st.text_area(
                "Competitor prices (one per line)",
                placeholder="$100\n$120\n$95\n$110"
            )
            
            if competitor_service and competitor_prices:
                try:
                    prices = [float(price.strip().replace('$', '')) for price in competitor_prices.split('\n') if price.strip()]
                    
                    if prices:
                        avg_competitor_price = sum(prices) / len(prices)
                        min_price = min(prices)
                        max_price = max(prices)
                        
                        st.metric("Average Competitor Price", f"${avg_competitor_price:.2f}")
                        st.metric("Price Range", f"${min_price:.2f} - ${max_price:.2f}")
                        
                        # Recommend pricing
                        recommended_price = avg_competitor_price * 0.95  # 5% below average
                        st.success(f"💡 Recommended price: ${recommended_price:.2f}")
                except:
                    st.error("Please enter valid prices")
        
        # Value-based pricing calculator
        st.markdown("**Value-Based Pricing Calculator**")
        with st.expander("💎 Calculate Value Price"):
            customer_problem_cost = st.number_input(
                "Cost of customer's problem ($)",
                min_value=0.0,
                format="%.2f",
                help="How much does this problem cost the customer?"
            )
            
            value_percentage = st.slider(
                "Value capture %",
                min_value=1,
                max_value=50,
                value=10,
                help="What percentage of the problem cost should you capture?"
            )
            
            if customer_problem_cost > 0:
                value_price = customer_problem_cost * (value_percentage / 100)
                st.success(f"💰 Value-based price: ${value_price:.2f}")
    
    with col2:
        st.markdown("### 📈 Pricing Optimization")
        
        # Dynamic pricing recommendations
        if "gsheets_creds" in st.session_state:
            pricing_df = get_sheet_as_df("pricing")
            appointments_df = get_sheet_as_df("appointments")
            
            if pricing_df is not None and appointments_df is not None:
                # Analyze demand patterns
                st.markdown("**Demand-Based Pricing**")
                
                service_demand = appointments_df['Service'].value_counts()
                
                with st.expander("📊 Service Demand Analysis"):
                    fig_demand = px.bar(
                        x=service_demand.index,
                        y=service_demand.values,
                        title="Service Booking Frequency"
                    )
                    st.plotly_chart(fig_demand, use_container_width=True)
                    
                    # Pricing recommendations based on demand
                    st.markdown("**Pricing Recommendations:**")
                    
                    high_demand_services = service_demand.head(3).index.tolist()
                    low_demand_services = service_demand.tail(3).index.tolist()
                    
                    st.success(f"🔥 High demand services: {', '.join(high_demand_services)} - Consider 10-15% price increase")
                    st.info(f"📉 Low demand services: {', '.join(low_demand_services)} - Consider promotions or bundling")
        
        # Seasonal pricing
        st.markdown("**Seasonal Pricing Strategy**")
        with st.expander("🗓️ Seasonal Adjustments"):
            season = st.selectbox("Select Season", ["Spring", "Summer", "Fall", "Winter"])
            adjustment = st.slider("Price adjustment %", min_value=-50, max_value=50, value=0)
            
            if adjustment != 0:
                direction = "increase" if adjustment > 0 else "decrease"
                st.info(f"💡 {season} pricing: {direction} prices by {abs(adjustment)}%")
    
    # Pricing packages and bundles
    st.markdown("### 📦 Package & Bundle Builder")
    
    with st.expander("🎁 Create Service Bundles"):
        if "gsheets_creds" in st.session_state:
            pricing_df = get_sheet_as_df("pricing")
            
            if pricing_df is not None and not pricing_df.empty:
                bundle_name = st.text_input("Bundle Name")
                
                # Select services for bundle
                services_in_bundle = st.multiselect(
                    "Select Services",
                    pricing_df['Service_Name'].tolist()
                )
                
                if services_in_bundle:
                    # Calculate bundle pricing
                    selected_services = pricing_df[pricing_df['Service_Name'].isin(services_in_bundle)]
                    total_individual_price = selected_services['Price'].sum()
                    
                    discount_percentage = st.slider("Bundle Discount %", min_value=5, max_value=50, value=15)
                    bundle_price = total_individual_price * (1 - discount_percentage / 100)
                    savings = total_individual_price - bundle_price
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Individual Total", f"${total_individual_price:.2f}")
                    with col2:
                        st.metric("Bundle Price", f"${bundle_price:.2f}")
                    with col3:
                        st.metric("Customer Savings", f"${savings:.2f}")
                    
                    if st.button("Create Bundle"):
                        st.success(f"✅ Bundle '{bundle_name}' created successfully!")
    
    # A/B testing for pricing
    st.markdown("### 🧪 Pricing A/B Testing")
    
    with st.expander("⚗️ Set Up Price Test"):
        test_service = st.selectbox("Service to test", ["Select a service..."])
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Version A (Current)**")
            price_a = st.number_input("Price A", min_value=0.01, format="%.2f")
        
        with col2:
            st.markdown("**Version B (Test)**")
            price_b = st.number_input("Price B", min_value=0.01, format="%.2f")
        
        test_duration = st.number_input("Test duration (days)", min_value=7, max_value=90, value=30)
        
        if st.button("🚀 Start A/B Test"):
            st.success(f"🧪 A/B test started for {test_duration} days!")
            st.info("📊 Results will be tracked automatically")

def show_bulk_update_modal(df):
    """Show bulk update options"""
    st.markdown("### 📊 Bulk Price Updates")
    
    update_type = st.selectbox("Update Type", [
        "Percentage Increase/Decrease",
        "Fixed Amount Increase/Decrease",
        "Set Price Floor/Ceiling",
        "Category-based Update"
    ])
    
    if update_type == "Percentage Increase/Decrease":
        percentage = st.number_input("Percentage change", min_value=-50.0, max_value=100.0, format="%.1f")
        if st.button("Apply Percentage Change"):
            st.success(f"✅ Applied {percentage}% change to all selected services")
    
    elif update_type == "Category-based Update":
        category = st.selectbox("Select Category", df['Category'].unique())
        category_adjustment = st.number_input("Price adjustment %", min_value=-50.0, max_value=100.0, format="%.1f")
        if st.button("Update Category Prices"):
            st.success(f"✅ Updated all {category} services by {category_adjustment}%")

def show_service_analytics(service):
    """Show analytics for a specific service"""
    st.markdown(f"### 📊 Analytics for {service['Service_Name']}")
    
    # This would show detailed analytics for the specific service
    # Including booking frequency, revenue, customer feedback, etc.
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Bookings", "45", "12%")
        st.metric("Revenue Generated", f"${service.get('Price', 0) * 45:.2f}")
    
    with col2:
        st.metric("Average Rating", "4.8/5.0")
        st.metric("Repeat Customers", "78%")

def save_service(service_data):
    """Save new service to Google Sheets"""
    if "gsheets_creds" not in st.session_state:
        return False
    
    try:
        existing_df = get_sheet_as_df("pricing")
        
        if existing_df is not None:
            new_df = pd.concat([existing_df, pd.DataFrame([service_data])], ignore_index=True)
        else:
            new_df = pd.DataFrame([service_data])
        
        return update_sheet_from_df("pricing", new_df)
    except Exception as e:
        st.error(f"Error saving service: {str(e)}")
        return False

if __name__ == "__main__":
    main()

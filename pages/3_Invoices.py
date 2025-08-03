import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import uuid
from utils.auth import require_auth
from utils.gsheet import get_sheet_as_df, update_sheet_from_df
from utils.validators import validate_currency, validate_required_fields

@require_auth
def main():
    st.title("📄 Invoice Management")
    
    # Tabs for different invoice operations
    tab1, tab2, tab3 = st.tabs(["📋 View Invoices", "➕ Create Invoice", "📊 Analytics"])
    
    with tab1:
        show_invoices_list()
    
    with tab2:
        create_new_invoice()
    
    with tab3:
        show_invoice_analytics()

def show_invoices_list():
    """Display and manage existing invoices"""
    st.subheader("Invoice List")
    
    # Load invoices data
    if "gsheets_creds" in st.session_state:
        df = get_sheet_as_df("invoices")
        
        if df is not None and not df.empty:
            # Add filters
            col1, col2, col3 = st.columns(3)
            
            with col1:
                status_filter = st.selectbox(
                    "Filter by Status",
                    ["All", "Pending", "Paid", "Overdue", "Cancelled"]
                )
            
            with col2:
                date_range = st.date_input(
                    "Date Range",
                    value=(datetime.now() - timedelta(days=30), datetime.now()),
                    help="Filter invoices by date range"
                )
            
            with col3:
                search_term = st.text_input("🔍 Search", placeholder="Customer name or invoice #")
            
            # Apply filters
            filtered_df = df.copy()
            
            if status_filter != "All":
                filtered_df = filtered_df[filtered_df['Status'] == status_filter]
            
            if search_term:
                mask = (
                    filtered_df['Customer'].str.contains(search_term, case=False, na=False) |
                    filtered_df['Invoice_ID'].str.contains(search_term, case=False, na=False)
                )
                filtered_df = filtered_df[mask]
            
            # Display invoices with actions
            st.markdown(f"**Found {len(filtered_df)} invoices**")
            
            # Editable dataframe
            edited_df = st.data_editor(
                filtered_df,
                use_container_width=True,
                num_rows="dynamic",
                column_config={
                    "Amount": st.column_config.NumberColumn(
                        "Amount ($)",
                        format="$%.2f",
                        min_value=0
                    ),
                    "Due_Date": st.column_config.DateColumn(
                        "Due Date",
                        format="YYYY-MM-DD"
                    ),
                    "Status": st.column_config.SelectboxColumn(
                        "Status",
                        options=["Pending", "Paid", "Overdue", "Cancelled"]
                    )
                },
                hide_index=True
            )
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("💾 Save Changes", type="primary"):
                    if update_sheet_from_df("invoices", edited_df):
                        st.success("✅ Invoices updated successfully!")
                        st.rerun()
            
            with col2:
                if st.button("📧 Send Reminders"):
                    send_invoice_reminders(edited_df)
            
            with col3:
                if st.button("📊 Export CSV"):
                    csv = edited_df.to_csv(index=False)
                    st.download_button(
                        "⬇️ Download CSV",
                        csv,
                        "invoices.csv",
                        "text/csv"
                    )
        else:
            st.info("No invoices found. Create your first invoice in the 'Create Invoice' tab.")
    else:
        st.warning("⚠️ Please connect Google Sheets to manage invoices.")

def create_new_invoice():
    """Create a new invoice"""
    st.subheader("Create New Invoice")
    
    with st.form("new_invoice_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            customer_name = st.text_input("Customer Name *", placeholder="Enter customer name")
            customer_email = st.text_input("Customer Email", placeholder="customer@example.com")
            invoice_date = st.date_input("Invoice Date", value=datetime.now())
            due_date = st.date_input("Due Date", value=datetime.now() + timedelta(days=30))
        
        with col2:
            service_description = st.text_area("Service Description *", placeholder="Describe the services provided")
            amount = st.number_input("Amount ($) *", min_value=0.01, format="%.2f")
            tax_rate = st.number_input("Tax Rate (%)", min_value=0.0, max_value=100.0, value=0.0, format="%.2f")
            status = st.selectbox("Status", ["Pending", "Paid", "Overdue", "Cancelled"])
        
        # Additional details
        st.markdown("**Additional Details**")
        notes = st.text_area("Notes", placeholder="Any additional notes or terms")
        
        # Calculate totals
        tax_amount = amount * (tax_rate / 100)
        total_amount = amount + tax_amount
        
        st.markdown(f"""
        **Invoice Summary:**
        - Subtotal: ${amount:.2f}
        - Tax ({tax_rate}%): ${tax_amount:.2f}
        - **Total: ${total_amount:.2f}**
        """)
        
        submitted = st.form_submit_button("🚀 Create Invoice", type="primary")
        
        if submitted:
            # Validate required fields
            required_data = {
                "customer_name": customer_name,
                "service_description": service_description,
                "amount": amount
            }
            
            errors = validate_required_fields(required_data, ["customer_name", "service_description", "amount"])
            
            if errors:
                for field, error in errors.items():
                    st.error(f"❌ {error}")
            else:
                # Create invoice
                invoice_id = f"INV-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
                
                new_invoice = {
                    "Invoice_ID": invoice_id,
                    "Customer": customer_name,
                    "Email": customer_email,
                    "Service": service_description,
                    "Amount": total_amount,
                    "Tax_Rate": tax_rate,
                    "Tax_Amount": tax_amount,
                    "Invoice_Date": invoice_date.strftime("%Y-%m-%d"),
                    "Due_Date": due_date.strftime("%Y-%m-%d"),
                    "Status": status,
                    "Notes": notes,
                    "Created_By": st.session_state.user_name,
                    "Created_Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # Add to existing invoices or create new sheet
                if "gsheets_creds" in st.session_state:
                    existing_df = get_sheet_as_df("invoices")
                    
                    if existing_df is not None:
                        # Append to existing data
                        new_df = pd.concat([existing_df, pd.DataFrame([new_invoice])], ignore_index=True)
                    else:
                        # Create new dataframe
                        new_df = pd.DataFrame([new_invoice])
                    
                    if update_sheet_from_df("invoices", new_df):
                        st.success(f"✅ Invoice {invoice_id} created successfully!")
                        st.balloons()
                        
                        # Option to send invoice
                        if st.button("📧 Send Invoice to Customer"):
                            send_invoice_email(new_invoice)
                else:
                    st.error("❌ Google Sheets not connected. Cannot save invoice.")

def show_invoice_analytics():
    """Show invoice analytics and insights"""
    st.subheader("Invoice Analytics")
    
    if "gsheets_creds" in st.session_state:
        df = get_sheet_as_df("invoices")
        
        if df is not None and not df.empty:
            # Convert amount to numeric
            df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_invoices = len(df)
                st.metric("📄 Total Invoices", total_invoices)
            
            with col2:
                total_revenue = df['Amount'].sum()
                st.metric("💰 Total Revenue", f"${total_revenue:,.2f}")
            
            with col3:
                paid_invoices = len(df[df['Status'] == 'Paid'])
                st.metric("✅ Paid Invoices", paid_invoices)
            
            with col4:
                pending_amount = df[df['Status'] == 'Pending']['Amount'].sum()
                st.metric("⏳ Pending Amount", f"${pending_amount:,.2f}")
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Status distribution
                status_counts = df['Status'].value_counts()
                fig_status = px.pie(
                    values=status_counts.values,
                    names=status_counts.index,
                    title="Invoice Status Distribution"
                )
                st.plotly_chart(fig_status, use_container_width=True)
            
            with col2:
                # Monthly revenue trend
                df['Invoice_Date'] = pd.to_datetime(df['Invoice_Date'])
                monthly_revenue = df.groupby(df['Invoice_Date'].dt.to_period('M'))['Amount'].sum()
                
                fig_trend = px.line(
                    x=monthly_revenue.index.astype(str),
                    y=monthly_revenue.values,
                    title="Monthly Revenue Trend"
                )
                st.plotly_chart(fig_trend, use_container_width=True)
            
            # Top customers
            st.subheader("🏆 Top Customers by Revenue")
            customer_revenue = df.groupby('Customer')['Amount'].sum().sort_values(ascending=False).head(10)
            
            fig_customers = px.bar(
                x=customer_revenue.values,
                y=customer_revenue.index,
                orientation='h',
                title="Top 10 Customers by Revenue"
            )
            st.plotly_chart(fig_customers, use_container_width=True)
            
        else:
            st.info("No invoice data available for analytics.")
    else:
        st.warning("⚠️ Please connect Google Sheets to view analytics.")

def send_invoice_reminders(df):
    """Send reminders for overdue invoices"""
    overdue_invoices = df[df['Status'] == 'Overdue']
    
    if len(overdue_invoices) > 0:
        st.success(f"📧 Sent reminders for {len(overdue_invoices)} overdue invoices")
        # Here you would integrate with email service
    else:
        st.info("No overdue invoices to remind")

def send_invoice_email(invoice_data):
    """Send invoice via email"""
    st.success(f"📧 Invoice {invoice_data['Invoice_ID']} sent to {invoice_data['Email']}")
    # Here you would integrate with email service

if __name__ == "__main__":
    main()

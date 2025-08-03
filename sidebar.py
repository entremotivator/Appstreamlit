import streamlit as st
import json
from utils.gsheet import test_gsheet_connection
from utils.auth import logout_user
from datetime import datetime

def show_sidebar():
    with st.sidebar:
        # User info header
        st.markdown(f"""
        <div class="user-header">
            <h3>👋 Welcome, {st.session_state.get('user_name', 'User')}!</h3>
            <p><small>Last login: {st.session_state.get('last_login', 'N/A')}</small></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.divider()
        
        # Google Sheets Configuration
        st.markdown("### 📊 Google Sheets Setup")
        
        if "gsheets_creds" not in st.session_state:
            st.warning("⚠️ Google Sheets not connected")
            
            json_file = st.file_uploader(
                "Upload Service Account JSON",
                type="json",
                help="Upload your Google Service Account credentials"
            )
            
            if json_file:
                try:
                    creds_data = json.load(json_file)
                    
                    # Validate JSON structure
                    required_fields = ["type", "project_id", "private_key", "client_email"]
                    if all(field in creds_data for field in required_fields):
                        
                        with st.spinner("Testing connection..."):
                            if test_gsheet_connection(creds_data):
                                st.session_state.gsheets_creds = creds_data
                                st.success("✅ Google Sheets connected successfully!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to connect to Google Sheets")
                    else:
                        st.error("❌ Invalid service account JSON format")
                        
                except json.JSONDecodeError:
                    st.error("❌ Invalid JSON file")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        else:
            st.success("✅ Google Sheets Connected")
            if st.button("🔄 Reconnect", help="Upload new credentials"):
                del st.session_state.gsheets_creds
                st.rerun()
        
        st.divider()
        
        # Navigation Menu
        st.markdown("### 🧭 Navigation")
        
        pages = [
            {"name": "Dashboard", "icon": "📊", "desc": "Overview & Analytics"},
            {"name": "Calendar", "icon": "📅", "desc": "Schedule & Events"},
            {"name": "Invoices", "icon": "📄", "desc": "Billing & Payments"},
            {"name": "Customers", "icon": "👥", "desc": "Client Management"},
            {"name": "Appointments", "icon": "🕐", "desc": "Booking System"},
            {"name": "Pricing", "icon": "💰", "desc": "Service Rates"},
            {"name": "AI Chat", "icon": "🤖", "desc": "AI Assistant"},
            {"name": "Voice Calls", "icon": "📞", "desc": "Outbound Calling"},
            {"name": "Call Center", "icon": "🎧", "desc": "Support Center"}
        ]
        
        for page in pages:
            if st.button(
                f"{page['icon']} {page['name']}",
                help=page['desc'],
                use_container_width=True,
                type="primary" if st.session_state.get('current_page') == page['name'] else "secondary"
            ):
                st.session_state.current_page = page['name']
                st.rerun()
        
        st.divider()
        
        # System Status
        st.markdown("### ⚡ System Status")
        
        status_items = [
            ("Google Sheets", "🟢" if "gsheets_creds" in st.session_state else "🔴"),
            ("Database", "🟢"),  # Placeholder
            ("API Services", "🟢"),  # Placeholder
        ]
        
        for item, status in status_items:
            st.markdown(f"{status} {item}")
        
        st.divider()
        
        # Settings and Logout
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("⚙️ Settings", use_container_width=True):
                st.session_state.current_page = "Settings"
                st.rerun()
        
        with col2:
            if st.button("🚪 Logout", use_container_width=True):
                logout_user()
                st.rerun()
        
        # Footer info
        st.markdown("""
        <div style="margin-top: 2rem; padding: 1rem; background: #f0f2f6; border-radius: 0.5rem;">
            <small>
                <strong>Version:</strong> 2.0.0<br>
                <strong>Build:</strong> {}<br>
                <strong>Support:</strong> help@business.com
            </small>
        </div>
        """.format(datetime.now().strftime("%Y%m%d")), unsafe_allow_html=True)

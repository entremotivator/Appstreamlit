import streamlit as st
import time
from utils.auth import authenticate_user, create_user_session
from utils.validators import validate_email

def show_login():
    # Create centered login form
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div class="login-container">
            <h1 style="text-align: center; color: #1f77b4; margin-bottom: 2rem;">
                🏢 Business Management Suite
            </h1>
        </div>
        """, unsafe_allow_html=True)
        
        # Login form
        with st.form("login_form", clear_on_submit=False):
            st.markdown("### 🔐 Login to Your Account")
            
            email = st.text_input(
                "Email Address",
                placeholder="Enter your email",
                help="Use your registered email address"
            )
            
            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                help="Minimum 6 characters required"
            )
            
            remember_me = st.checkbox("Remember me for 30 days")
            
            col_login, col_register = st.columns(2)
            
            with col_login:
                login_clicked = st.form_submit_button(
                    "🚀 Login",
                    use_container_width=True,
                    type="primary"
                )
            
            with col_register:
                register_clicked = st.form_submit_button(
                    "📝 Register",
                    use_container_width=True
                )
        
        # Handle login
        if login_clicked:
            if not email or not password:
                st.error("⚠️ Please fill in all fields")
            elif not validate_email(email):
                st.error("⚠️ Please enter a valid email address")
            else:
                with st.spinner("Authenticating..."):
                    time.sleep(1)  # Simulate authentication delay
                    
                    auth_result = authenticate_user(email, password)
                    
                    if auth_result["success"]:
                        create_user_session(auth_result["user"], remember_me)
                        st.success("✅ Login successful! Redirecting...")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ {auth_result['message']}")
        
        # Handle registration
        if register_clicked:
            st.info("🚧 Registration feature coming soon! Contact admin for access.")
        
        # Demo credentials info
        with st.expander("🔍 Demo Credentials"):
            st.info("""
            **Demo Account:**
            - Email: demo@business.com
            - Password: demo123
            
            **Admin Account:**
            - Email: admin@business.com  
            - Password: admin123
            """)
        
        # Footer
        st.markdown("""
        <div style="text-align: center; margin-top: 3rem; color: #666;">
            <small>© 2024 Business Management Suite. All rights reserved.</small>
        </div>
        """, unsafe_allow_html=True)

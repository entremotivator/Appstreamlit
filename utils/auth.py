import streamlit as st
import hashlib
import time
from datetime import datetime, timedelta
from utils.config import get_config

# Demo users database (replace with real database)
DEMO_USERS = {
    "demo@business.com": {
        "password_hash": hashlib.sha256("demo123".encode()).hexdigest(),
        "name": "Demo User",
        "role": "user",
        "created": "2024-01-01"
    },
    "admin@business.com": {
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "name": "Admin User", 
        "role": "admin",
        "created": "2024-01-01"
    }
}

def hash_password(password):
    """Hash password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(email, password):
    """Authenticate user credentials"""
    try:
        if email in DEMO_USERS:
            user_data = DEMO_USERS[email]
            if user_data["password_hash"] == hash_password(password):
                return {
                    "success": True,
                    "user": {
                        "email": email,
                        "name": user_data["name"],
                        "role": user_data["role"]
                    }
                }
        
        return {
            "success": False,
            "message": "Invalid email or password"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Authentication error: {str(e)}"
        }

def create_user_session(user_data, remember_me=False):
    """Create user session"""
    st.session_state.logged_in = True
    st.session_state.user_email = user_data["email"]
    st.session_state.user_name = user_data["name"]
    st.session_state.user_role = user_data["role"]
    st.session_state.login_time = datetime.now()
    st.session_state.last_login = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Set session expiry
    if remember_me:
        st.session_state.session_expiry = datetime.now() + timedelta(days=30)
    else:
        st.session_state.session_expiry = datetime.now() + timedelta(minutes=get_config("session_timeout", 30))

def check_session_validity():
    """Check if current session is still valid"""
    if not st.session_state.get("logged_in", False):
        return False
    
    if "session_expiry" in st.session_state:
        if datetime.now() > st.session_state.session_expiry:
            logout_user()
            return False
    
    # Update last activity
    st.session_state.last_activity = datetime.now()
    return True

def logout_user():
    """Logout user and clear session"""
    keys_to_clear = [
        "logged_in", "user_email", "user_name", "user_role",
        "login_time", "session_expiry", "gsheets_creds",
        "data_cache", "notifications"
    ]
    
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

def require_auth(func):
    """Decorator to require authentication"""
    def wrapper(*args, **kwargs):
        if not check_session_validity():
            st.error("🔒 Please login to access this page")
            st.stop()
        return func(*args, **kwargs)
    return wrapper

def require_role(required_role):
    """Decorator to require specific role"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not check_session_validity():
                st.error("🔒 Please login to access this page")
                st.stop()
            
            user_role = st.session_state.get("user_role", "user")
            if user_role != required_role and user_role != "admin":
                st.error("🚫 Insufficient permissions")
                st.stop()
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

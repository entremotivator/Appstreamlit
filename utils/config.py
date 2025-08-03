import streamlit as st
import os
from datetime import datetime, timedelta

def load_config():
    """Load application configuration"""
    if "config" not in st.session_state:
        st.session_state.config = {
            "app_name": "Business Management Suite",
            "version": "2.0.0",
            "debug": os.getenv("DEBUG", "False").lower() == "true",
            "session_timeout": 30,  # minutes
            "max_file_size": 10,  # MB
            "supported_formats": ["csv", "xlsx", "json"],
            "api_endpoints": {
                "vapi": os.getenv("VAPI_API_URL", "https://api.vapi.ai"),
                "n8n": os.getenv("N8N_WEBHOOK_URL", ""),
            },
            "features": {
                "voice_calls": True,
                "ai_chat": True,
                "real_time_sync": True,
                "notifications": True,
            }
        }

def init_session_state():
    """Initialize session state variables"""
    defaults = {
        "logged_in": False,
        "user_id": None,
        "user_name": None,
        "user_email": None,
        "user_role": "user",
        "login_time": None,
        "last_activity": datetime.now(),
        "current_page": "Dashboard",
        "notifications": [],
        "theme": "light",
        "data_cache": {},
        "sync_status": {},
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def get_config(key, default=None):
    """Get configuration value"""
    return st.session_state.config.get(key, default)

def update_last_activity():
    """Update user's last activity timestamp"""
    st.session_state.last_activity = datetime.now()

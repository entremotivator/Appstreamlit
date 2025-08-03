import streamlit as st
import pandas as pd
import pygsheets
from typing import Optional, Dict, Any
import time
from utils.validators import validate_dataframe

@st.cache_resource
def get_gsheet_client(creds_data: Dict[str, Any]):
    """Get authenticated Google Sheets client"""
    try:
        return pygsheets.authorize(service_account_info=creds_data)
    except Exception as e:
        st.error(f"Failed to authenticate with Google Sheets: {str(e)}")
        return None

def test_gsheet_connection(creds_data: Dict[str, Any]) -> bool:
    """Test Google Sheets connection"""
    try:
        client = pygsheets.authorize(service_account_info=creds_data)
        # Try to list spreadsheets to test connection
        client.list_ssheets()
        return True
    except Exception as e:
        st.error(f"Connection test failed: {str(e)}")
        return False

def get_sheet_as_df(sheet_name: str, worksheet_index: int = 0) -> Optional[pd.DataFrame]:
    """Get Google Sheet as DataFrame with error handling"""
    if "gsheets_creds" not in st.session_state:
        st.error("Google Sheets credentials not found")
        return None
    
    try:
        client = get_gsheet_client(st.session_state.gsheets_creds)
        if not client:
            return None
        
        with st.spinner(f"Loading {sheet_name}..."):
            sheet = client.open(sheet_name)
            worksheet = sheet[worksheet_index]
            df = worksheet.get_as_df()
            
            # Cache the data
            cache_key = f"{sheet_name}_{worksheet_index}"
            st.session_state.data_cache[cache_key] = {
                "data": df,
                "timestamp": time.time()
            }
            
            return df
            
    except pygsheets.SpreadsheetNotFound:
        st.error(f"Spreadsheet '{sheet_name}' not found. Please check the name and permissions.")
        return None
    except pygsheets.WorksheetNotFound:
        st.error(f"Worksheet index {worksheet_index} not found in '{sheet_name}'.")
        return None
    except Exception as e:
        st.error(f"Error loading sheet: {str(e)}")
        return None

def update_sheet_from_df(sheet_name: str, df: pd.DataFrame, worksheet_index: int = 0) -> bool:
    """Update Google Sheet from DataFrame with validation"""
    if "gsheets_creds" not in st.session_state:
        st.error("Google Sheets credentials not found")
        return False
    
    try:
        client = get_gsheet_client(st.session_state.gsheets_creds)
        if not client:
            return False
        
        # Validate DataFrame
        if df.empty:
            st.warning("No data to update")
            return False
        
        with st.spinner(f"Updating {sheet_name}..."):
            sheet = client.open(sheet_name)
            worksheet = sheet[worksheet_index]
            
            # Clear existing data and update
            worksheet.clear()
            worksheet.set_dataframe(df, (1, 1), copy_head=True)
            
            # Update cache
            cache_key = f"{sheet_name}_{worksheet_index}"
            st.session_state.data_cache[cache_key] = {
                "data": df,
                "timestamp": time.time()
            }
            
            # Update sync status
            st.session_state.sync_status[sheet_name] = {
                "last_sync": time.time(),
                "status": "success"
            }
            
            return True
            
    except Exception as e:
        st.error(f"Error updating sheet: {str(e)}")
        st.session_state.sync_status[sheet_name] = {
            "last_sync": time.time(),
            "status": "error",
            "error": str(e)
        }
        return False

def create_new_sheet(sheet_name: str, df: pd.DataFrame) -> bool:
    """Create new Google Sheet with data"""
    if "gsheets_creds" not in st.session_state:
        st.error("Google Sheets credentials not found")
        return False
    
    try:
        client = get_gsheet_client(st.session_state.gsheets_creds)
        if not client:
            return False
        
        with st.spinner(f"Creating {sheet_name}..."):
            # Create new spreadsheet
            sheet = client.create(sheet_name)
            worksheet = sheet[0]
            
            # Add data
            worksheet.set_dataframe(df, (1, 1), copy_head=True)
            
            st.success(f"Created new sheet: {sheet_name}")
            return True
            
    except Exception as e:
        st.error(f"Error creating sheet: {str(e)}")
        return False

def get_cached_data(sheet_name: str, worksheet_index: int = 0, max_age: int = 300) -> Optional[pd.DataFrame]:
    """Get cached data if available and not expired"""
    cache_key = f"{sheet_name}_{worksheet_index}"
    
    if cache_key in st.session_state.data_cache:
        cached_item = st.session_state.data_cache[cache_key]
        age = time.time() - cached_item["timestamp"]
        
        if age < max_age:  # 5 minutes default
            return cached_item["data"]
    
    return None

def list_available_sheets() -> list:
    """List all available Google Sheets"""
    if "gsheets_creds" not in st.session_state:
        return []
    
    try:
        client = get_gsheet_client(st.session_state.gsheets_creds)
        if not client:
            return []
        
        sheets = client.list_ssheets()
        return [sheet.title for sheet in sheets]
        
    except Exception as e:
        st.error(f"Error listing sheets: {str(e)}")
        return []

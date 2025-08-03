import re
import pandas as pd
from typing import Any, Dict, List

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    # Check if it's 10-15 digits long
    return 10 <= len(digits_only) <= 15

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Dict[str, str]:
    """Validate required fields in data"""
    errors = {}
    for field in required_fields:
        if field not in data or not data[field] or str(data[field]).strip() == "":
            errors[field] = f"{field.replace('_', ' ').title()} is required"
    return errors

def validate_dataframe(df: pd.DataFrame, required_columns: List[str]) -> Dict[str, str]:
    """Validate DataFrame structure"""
    errors = {}
    
    if df.empty:
        errors["data"] = "No data provided"
        return errors
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        errors["columns"] = f"Missing required columns: {', '.join(missing_columns)}"
    
    return errors

def validate_currency(amount: str) -> bool:
    """Validate currency amount"""
    try:
        float_amount = float(str(amount).replace('$', '').replace(',', ''))
        return float_amount >= 0
    except (ValueError, TypeError):
        return False

def validate_date_format(date_str: str, format_str: str = "%Y-%m-%d") -> bool:
    """Validate date format"""
    try:
        pd.to_datetime(date_str, format=format_str)
        return True
    except (ValueError, TypeError):
        return False

def sanitize_input(text: str) -> str:
    """Sanitize user input"""
    if not isinstance(text, str):
        text = str(text)
    
    # Remove potentially harmful characters
    text = re.sub(r'[<>"\']', '', text)
    # Limit length
    text = text[:1000]
    # Strip whitespace
    text = text.strip()
    
    return text

import requests
import os
import logging

logger = logging.getLogger(__name__)

def format_phone_number(phone_number):
    """
    Format phone number while preserving international format
    """
    if not phone_number:
        return phone_number
    
    # Convert to string and remove any whitespace
    phone_number = str(phone_number).strip()
    
    # Remove any non-digit characters except the leading +
    if phone_number.startswith('+'):
        # Keep the + for international format
        cleaned = '+' + ''.join(filter(str.isdigit, phone_number[1:]))
    else:
        # Remove all non-digit characters
        cleaned = ''.join(filter(str.isdigit, phone_number))
    
    return cleaned

def validate_whatsapp_webhook_data(data):
    """
    Validate the structure of incoming WhatsApp webhook data
    """
    if not data or 'entry' not in data:
        return False, "Missing 'entry'"
        
    entry = data['entry'][0]
    if 'changes' not in entry:
        return False, "Missing 'changes'"
        
    changes = entry['changes'][0]
    if 'value' not in changes:
        return False, "Missing 'value'"
        
    value = changes['value']
    if 'messages' not in value:
        return False, "Missing 'messages'"
        
    return True, "Valid"

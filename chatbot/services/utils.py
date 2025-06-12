import requests
import os
import logging

logger = logging.getLogger(__name__)

def format_phone_number(phone_number):
    """
    Format phone number to include country code
    """
    phone_number = str(phone_number)
    if not phone_number.startswith('254'):
        phone_number = '254' + phone_number.lstrip('0')
    return phone_number

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

import requests
import os
import logging
from flask import jsonify, request
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

def verify_webhook():
    # Handle webhook verification from Meta
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    verify_token = os.getenv('WHATSAPP_VERIFY_TOKEN')
    
    if mode and token:
        if mode == 'subscribe' and token == verify_token:
            return challenge
        return jsonify({"error": "Invalid verification token"}), 403

def process_whatsapp_message(data):
    try:
        logger.info(f"Received WhatsApp webhook data: {data}")
        
        # Check if data exists and has required structure
        if not data or 'entry' not in data:
            logger.error("Invalid webhook data: Missing 'entry'")
            return jsonify({"error": "Invalid webhook data"}), 400
            
        entry = data['entry'][0]
        if 'changes' not in entry:
            logger.error("Invalid webhook data: Missing 'changes'")
            return jsonify({"error": "Invalid webhook data"}), 400
            
        changes = entry['changes'][0]
        if 'value' not in changes:
            logger.error("Invalid webhook data: Missing 'value'")
            return jsonify({"error": "Invalid webhook data"}), 400
            
        value = changes['value']
        if 'messages' not in value:
            logger.error("Invalid webhook data: Missing 'messages'")
            return jsonify({"error": "Invalid webhook data"}), 400
            
        messages = value['messages'][0]
        
        phone_number = messages.get('from')
        
        # Handle text messages
        if 'text' in messages:
            message = messages.get('text', {}).get('body', '')
            if not phone_number or not message:
                logger.error(f"Missing required fields: phone={phone_number}, message={message}")
                return jsonify({"error": "Missing required fields"}), 400
                
            return handle_user_message({
                'phone_number': phone_number,
                'message': message
            })
        
        # Handle button responses
        elif 'interactive' in messages:
            interactive = messages.get('interactive', {})
            if 'button_reply' in interactive:
                button_id = interactive['button_reply'].get('id')
                if not phone_number or not button_id:
                    logger.error(f"Missing required fields: phone={phone_number}, button_id={button_id}")
                    return jsonify({"error": "Missing required fields"}), 400
                    
                return handle_user_message({
                    'phone_number': phone_number,
                    'button_id': button_id
                })
        
        logger.error("Unsupported message type")
        return jsonify({"error": "Unsupported message type"}), 400
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

def send_whatsapp_interactive_message(phone_number, header, body, footer, buttons):
    """
    Send an interactive WhatsApp message with buttons
    """
    try:
        WHATSAPP_API_URL = f"https://graph.facebook.com/v17.0/{os.getenv('WHATSAPP_PHONE_ID')}/messages"
        headers = {
            "Authorization": f"Bearer {os.getenv('WHATSAPP_ACCESS_TOKEN')}",
            "Content-Type": "application/json"
        }
        
        # Build buttons array
        button_objects = []
        for i, button in enumerate(buttons):
            button_objects.append({
                "type": "reply",
                "reply": {
                    "id": button["id"],
                    "title": button["text"]
                }
            })
        
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "header": {
                    "type": "text",
                    "text": header
                },
                "body": {
                    "text": body
                },
                "footer": {
                    "text": footer
                },
                "action": {
                    "buttons": button_objects
                }
            }
        }
        
        response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        logger.error(f"WhatsApp API error: {str(e)}")
        raise

def send_whatsapp_text_message(phone_number, message):
    """
    Send a simple text message via WhatsApp
    """
    try:
        WHATSAPP_API_URL = f"https://graph.facebook.com/v17.0/{os.getenv('WHATSAPP_PHONE_ID')}/messages"
        headers = {
            "Authorization": f"Bearer {os.getenv('WHATSAPP_ACCESS_TOKEN')}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {"body": message}
        }
        
        response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        logger.error(f"WhatsApp API error: {str(e)}")
        raise

def handle_button_response(phone_number, button_id):
    """
    Handle responses to button clicks
    """
    try:
        if button_id == "about":
            message = ("🤖 *About Sasabot*\n\n"
                      "Sasabot is an innovative digital transformation platform that helps businesses:\n\n"
                      "✅ Automate customer interactions\n"
                      "✅ Improve response times\n"
                      "✅ Enhance service quality\n"
                      "✅ Reduce operational costs\n"
                      "✅ Scale customer support efficiently\n\n"
                      "We make it easy for businesses to connect with their customers through modern messaging platforms.")
        
        elif button_id == "faqs":
            message = ("❓ *Frequently Asked Questions*\n\n"
                      "*Q: What is Sasabot?*\n"
                      "A: Sasabot is a digital transformation platform for businesses to automate customer interactions.\n\n"
                      "*Q: How does it work?*\n"
                      "A: We integrate with your existing systems to provide automated responses and streamline customer communication.\n\n"
                      "*Q: What platforms do you support?*\n"
                      "A: We support WhatsApp, SMS, and other popular messaging platforms.\n\n"
                      "*Q: How much does it cost?*\n"
                      "A: Pricing varies based on your business needs. Contact us for a custom quote.")
        
        elif button_id == "onboarding":
            message = ("🚀 *Begin Your Digital Transformation Journey*\n\n"
                      "Welcome to the onboarding process! We'll help you set up Sasabot for your business.\n\n"
                      "To get started, please provide:\n"
                      "1️⃣ Your business name\n"
                      "2️⃣ Industry type\n"
                      "3️⃣ Current customer volume\n"
                      "4️⃣ Main communication challenges\n\n"
                      "Please reply with your business name to begin.")
        
        else:
            message = "Sorry, I didn't understand that option. Please try again."
        
        return send_whatsapp_text_message(phone_number, message)
        
    except Exception as e:
        logger.error(f"Error handling button response: {str(e)}")
        raise

def is_trigger_word(message):
    """
    Check if the message contains trigger words
    """
    trigger_words = ["hi", "hello", "sasabot"]
    return message.lower().strip() in trigger_words

def clean_phone_number(phone_number):
    """
    Clean and format phone number while preserving international formats
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

def handle_user_message(data):
    """
    Handle incoming user messages with the new flow
    """    try:
        if not data or not isinstance(data, dict):
            return jsonify({"error": "Invalid data format"}), 400
        
        phone_number = data.get('phone_number')
        message = data.get('message')
        button_id = data.get('button_id')  # For button responses
        
        if not phone_number:
            return jsonify({"error": "Missing phone number"}), 400
            
        # Clean phone number while preserving international format
        phone_number = clean_phone_number(phone_number)

        try:
            # Handle button responses
            if button_id:
                response = handle_button_response(phone_number, button_id)
                return jsonify({"message": "Button response sent", "whatsapp_response": response}), 200
            
            # Handle text messages
            if message:
                # Check for trigger words
                if is_trigger_word(message):
                    # Send welcome message with interactive buttons
                    buttons = [
                        {"text": "About Sasabot", "id": "about"},
                        {"text": "FAQs", "id": "faqs"},
                        {"text": "Begin Onboarding", "id": "onboarding"}
                    ]
                    
                    response = send_whatsapp_interactive_message(
                        phone_number,
                        "Welcome to Sasabot",
                        "Glad to have you here. We help businesses transition to digital interactions with their clients, improving speed and the quality of service",
                        "Select an option to start",
                        buttons
                    )
                    
                    return jsonify({"message": "Welcome message sent", "whatsapp_response": response}), 200
                else:
                    # Send a default response for other messages
                    response = send_whatsapp_text_message(
                        phone_number,
                        "Hello! To get started, please send 'Hi', 'Hello', or 'Sasabot' to begin your journey with us."
                    )
                    return jsonify({"message": "Default response sent", "whatsapp_response": response}), 200
            
            return jsonify({"error": "No message or button data provided"}), 400
            
        except Exception as e:
            logger.error(f"Message processing error: {str(e)}")
            return jsonify({"error": "Failed to process message"}), 500
            
    except Exception as e:
        logger.error(f"Message handling error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500
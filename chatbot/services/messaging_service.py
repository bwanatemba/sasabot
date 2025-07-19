import requests
import os
import logging
import uuid
from datetime import datetime
from flask import jsonify, request
from dotenv import load_dotenv
from models import OnboardingState, Customer, Order, OrderItem, Business, Product, ProductVariation, ChatSession, ChatMessage
from services.onboarding_service import onboarding_service

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

def verify_business_webhook(business_id):
    """Handle webhook verification for business-specific webhooks"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    
    # Generate business-specific verify token
    expected_token = f"sasabot_business_verify_{business_id}"
    
    if mode and token:
        if mode == 'subscribe' and token == expected_token:
            return challenge
        return jsonify({"error": "Invalid verification token"}), 403

def handle_system_onboarding_trigger(phone_number):
    """Handle initial system trigger words for onboarding"""
    try:
        # Send welcome message with onboarding options
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
        
        return jsonify({"message": "System welcome message sent", "whatsapp_response": response}), 200
        
    except Exception as e:
        logger.error(f"Error handling system onboarding trigger: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

def handle_system_message(data):
    """
    Handle system-level messages (onboarding only)
    """
    try:
        if not data or not isinstance(data, dict):
            return jsonify({"error": "Invalid data format"}), 400
        
        phone_number = data.get('phone_number')
        message = data.get('message')
        button_id = data.get('button_id')
        
        if not phone_number:
            return jsonify({"error": "Missing phone number"}), 400
            
        # Clean phone number while preserving international format
        phone_number = clean_phone_number(phone_number)

        try:
            # Handle button responses for system interactions
            if button_id:
                response = handle_system_button_response(phone_number, button_id)
                return jsonify({"message": "System button response sent", "whatsapp_response": response}), 200
            
            # Handle text messages for system interactions
            if message:
                # Check if user is in onboarding
                onboarding_state = OnboardingState.objects(phone_number=phone_number).first()
                if onboarding_state:
                    response = onboarding_service.handle_onboarding_response(phone_number, message=message)
                    return jsonify({"message": "Onboarding response sent", "whatsapp_response": response}), 200
                else:
                    # Handle general system-level GPT conversations (not business-specific)
                    # This is for general inquiries about Sasabot platform itself
                    response = handle_system_gpt_conversation(phone_number, message)
                    return jsonify({"message": "System GPT response sent", "whatsapp_response": response}), 200
            
            return jsonify({"error": "No message or button data provided"}), 400
            
        except Exception as e:
            logger.error(f"System message processing error: {str(e)}")
            return jsonify({"error": "Failed to process message"}), 500
            
    except Exception as e:
        logger.error(f"System message handling error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

def handle_system_button_response(phone_number, button_id):
    """
    Handle system-level button responses (onboarding and info only)
    """
    try:
        # Check if user is in onboarding
        onboarding_state = OnboardingState.objects(phone_number=phone_number).first()
        if onboarding_state:
            return onboarding_service.handle_onboarding_response(phone_number, button_id=button_id)
        
        # Handle system menu buttons only
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
            return onboarding_service.start_onboarding(phone_number)
        
        else:
            # Ignore all other button responses - they should be handled by business webhooks
            logger.info(f"Ignoring non-system button response: {button_id}")
            return jsonify({"status": "ok"}), 200
        
        return send_whatsapp_text_message(phone_number, message)
        
    except Exception as e:
        logger.error(f"Error handling system button response: {str(e)}")
        raise

def handle_system_gpt_conversation(phone_number, message):
    """
    Handle system-level GPT conversations for general platform inquiries
    This is separate from business-specific GPT conversations
    """
    try:
        from services.openai_service import process_system_gpt_interaction
        response = process_system_gpt_interaction(phone_number, message)
        return response
        
    except Exception as e:
        logger.error(f"Error in system GPT conversation: {str(e)}")
        # Fallback response
        fallback_msg = ("I'm having trouble processing your request right now. "
                       "For general questions about Sasabot, you can:\n\n"
                       "• Type 'about' for platform information\n"
                       "• Type 'faqs' for frequently asked questions\n"
                       "• Type 'onboarding' to start business registration")
        
        return send_whatsapp_text_message(phone_number, fallback_msg)

def process_business_whatsapp_message(data, business_id):
    """
    Process WhatsApp messages for business-specific webhooks
    This should be used by individual business webhooks to handle:
    - Customer status updates and delivery receipts
    - Business-specific customer interactions
    - Product orders and customer service
    """
    try:
        logger.info(f"Received business webhook data for business {business_id}: {data}")
        
        # Check if data exists and has required structure
        if not data:
            logger.warning("Received empty business webhook data")
            return jsonify({"status": "ok"}), 200
            
        if 'entry' not in data:
            logger.warning("Business webhook data missing 'entry'")
            return jsonify({"status": "ok"}), 200
            
        entry = data['entry'][0]
        if 'changes' not in entry:
            logger.warning("Business webhook data missing 'changes'")
            return jsonify({"status": "ok"}), 200
            
        changes = entry['changes'][0]
        if 'value' not in changes:
            logger.warning("Business webhook data missing 'value'")
            return jsonify({"status": "ok"}), 200
            
        value = changes['value']
        
        # Handle business-specific status updates (delivery receipts, read receipts, etc.)
        if 'statuses' in value:
            logger.info(f"Processing status update for business {business_id}")
            return handle_business_status_update(value['statuses'], business_id)
            
        if 'messages' not in value:
            logger.info("No messages in business webhook data")
            return jsonify({"status": "ok"}), 200
            
        messages = value['messages'][0]
        phone_number = messages.get('from')
        
        # Handle business-specific messages
        if 'text' in messages:
            message = messages.get('text', {}).get('body', '')
            if not phone_number or not message:
                logger.error(f"Missing required fields: phone={phone_number}, message={message}")
                return jsonify({"error": "Missing required fields"}), 400
                
            return handle_business_message({
                'phone_number': phone_number,
                'message': message,
                'business_id': business_id
            })
        
        # Handle button responses for business
        elif 'interactive' in messages:
            interactive = messages.get('interactive', {})
            if 'button_reply' in interactive:
                button_id = interactive['button_reply'].get('id')
                if not phone_number or not button_id:
                    logger.error(f"Missing required fields: phone={phone_number}, button_id={button_id}")
                    return jsonify({"error": "Missing required fields"}), 400
                    
                return handle_business_message({
                    'phone_number': phone_number,
                    'button_id': button_id,
                    'business_id': business_id
                })
            elif 'list_reply' in interactive:
                list_id = interactive['list_reply'].get('id')
                if not phone_number or not list_id:
                    logger.error(f"Missing required fields: phone={phone_number}, list_id={list_id}")
                    return jsonify({"error": "Missing required fields"}), 400
                    
                return handle_business_message({
                    'phone_number': phone_number,
                    'button_id': list_id,
                    'business_id': business_id
                })
        
        logger.info("Business webhook processed successfully")
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"Error processing business WhatsApp webhook: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

def handle_business_status_update(statuses, business_id):
    """Handle status updates for business webhooks"""
    try:
        # Process status updates (delivery receipts, read receipts, etc.)
        for status in statuses:
            message_id = status.get('id')
            status_type = status.get('status')
            timestamp = status.get('timestamp')
            
            logger.info(f"Business {business_id} - Message {message_id} status: {status_type}")
            
            # Here you can add business-specific status handling logic
            # For example, updating message delivery status in the database
            # or sending notifications to the business
            
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"Error handling business status update: {str(e)}")
        return jsonify({"status": "ok"}), 200

def handle_business_message(data):
    """Handle business-specific customer messages"""
    try:
        phone_number = data.get('phone_number')
        message = data.get('message')
        button_id = data.get('button_id')
        business_id = data.get('business_id')
        
        if not phone_number or not business_id:
            return jsonify({"error": "Missing required fields"}), 400
            
        # Clean phone number
        phone_number = clean_phone_number(phone_number)
        
        # Handle button responses for business interactions
        if button_id:
            response = handle_button_response(phone_number, button_id)
            return jsonify({"message": "Business button response sent", "whatsapp_response": response}), 200
        
        # Handle text messages for business interactions
        if message:
            # Check for trigger words - if new conversation, might need to redirect to system
            if is_trigger_word(message):
                # Check if this business has existing customer relationship
                customer = Customer.objects(phone_number=phone_number).first()
                if not customer:
                    # New customer, redirect to system webhook
                    guidance_msg = ("Hi! For initial setup and onboarding, please contact our main system.\n\n"
                                  "Send 'hi' to our main number to get started with Sasabot platform.")
                    return send_whatsapp_text_message(phone_number, guidance_msg)
            
            # Process business-specific GPT interaction
            from services.openai_service import process_gpt_interaction
            response = process_gpt_interaction(phone_number, message, business_id)
            return jsonify({"message": "Business GPT response sent", "gpt_response": response}), 200
        
        return jsonify({"error": "No message or button data provided"}), 400
        
    except Exception as e:
        logger.error(f"Error handling business message: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

def process_whatsapp_message(data):
    try:
        logger.info(f"Received WhatsApp webhook data: {data}")
        
        # Check if data exists and has required structure
        if not data:
            logger.warning("Received empty webhook data")
            return jsonify({"status": "ok"}), 200
            
        if 'entry' not in data:
            logger.warning("Webhook data missing 'entry' - might be a status update")
            return jsonify({"status": "ok"}), 200
            
        entry = data['entry'][0]
        if 'changes' not in entry:
            logger.warning("Webhook data missing 'changes' - might be a status update")
            return jsonify({"status": "ok"}), 200
            
        changes = entry['changes'][0]
        if 'value' not in changes:
            logger.warning("Webhook data missing 'value' - might be a status update")
            return jsonify({"status": "ok"}), 200
            
        value = changes['value']
        
        # Handle status updates (delivery receipts, read receipts, etc.)
        # These should be handled by business-specific webhooks, not the system webhook
        if 'statuses' in value:
            logger.info("Received status update webhook - should be handled by business webhook")
            # System webhook ignores status updates - they belong to business webhooks
            return jsonify({"status": "ok"}), 200
            
        if 'messages' not in value:
            logger.info("No messages in webhook data - might be a status update or other notification")
            return jsonify({"status": "ok"}), 200
            
        messages = value['messages'][0]
        
        phone_number = messages.get('from')
        
        # SYSTEM WEBHOOK - Only handle onboarding and system-level interactions
        # Check if user is in onboarding process
        onboarding_state = OnboardingState.objects(phone_number=phone_number).first()
        if not onboarding_state:
            # Check for system trigger words to start onboarding
            message_text = ""
            if 'text' in messages:
                message_text = messages.get('text', {}).get('body', '').lower().strip()
            
            # Check for system button responses (welcome message buttons)
            system_button_id = ""
            if 'interactive' in messages:
                interactive = messages.get('interactive', {})
                if 'button_reply' in interactive:
                    system_button_id = interactive['button_reply'].get('id', '')
                elif 'list_reply' in interactive:
                    system_button_id = interactive['list_reply'].get('id', '')
            
            # Handle initial trigger words for system onboarding
            if message_text in ["hi", "hello", "sasabot", "start"]:
                logger.info(f"System trigger word detected from {phone_number}: {message_text}")
                return handle_system_onboarding_trigger(phone_number)
            # Handle system welcome message button responses
            elif system_button_id in ["about", "faqs", "onboarding"]:
                logger.info(f"System button response detected from {phone_number}: {system_button_id}")
                return handle_system_message({
                    'phone_number': phone_number,
                    'button_id': system_button_id
                })
            # Handle non-trigger text messages with GPT for general platform inquiries
            elif message_text and 'text' in messages:
                logger.info(f"Non-trigger text message from {phone_number}, sending to GPT: {message_text}")
                return handle_system_message({
                    'phone_number': phone_number,
                    'message': messages.get('text', {}).get('body', '')
                })
            else:
                # Ignore other types of messages (like media) - they should be handled by business-specific webhooks
                logger.info(f"Ignoring non-text message from {phone_number} - should be handled by business webhook")
                return jsonify({"status": "ok"}), 200
        
        # Handle onboarding interactions for users already in onboarding process
        # Handle text messages
        if 'text' in messages:
            message = messages.get('text', {}).get('body', '')
            if not phone_number or not message:
                logger.error(f"Missing required fields: phone={phone_number}, message={message}")
                return jsonify({"error": "Missing required fields"}), 400
                
            return handle_system_message({
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
                    
                return handle_system_message({
                    'phone_number': phone_number,
                    'button_id': button_id
                })
            elif 'list_reply' in interactive:
                list_id = interactive['list_reply'].get('id')
                if not phone_number or not list_id:
                    logger.error(f"Missing required fields: phone={phone_number}, list_id={list_id}")
                    return jsonify({"error": "Missing required fields"}), 400
                    
                return handle_system_message({
                    'phone_number': phone_number,
                    'button_id': list_id  # Use same parameter name for consistency
                })
        
        logger.info("System webhook ignoring non-onboarding message")
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

def send_whatsapp_interactive_message(phone_number, header, body, footer, buttons):
    """
    Send an interactive WhatsApp message with buttons
    """
    try:
        # Validate inputs
        if not phone_number:
            raise ValueError("Phone number is required")
        
        if not buttons or len(buttons) == 0:
            raise ValueError("At least one button is required")
        
        # Set default values for empty strings
        header = header or "Message"
        body = body or "Please select an option"
        footer = footer or "Choose an option"
        
        # Validate WhatsApp configuration
        if not validate_whatsapp_config():
            raise ValueError("WhatsApp configuration is incomplete")
        
        WHATSAPP_API_URL = f"https://graph.facebook.com/v17.0/{os.getenv('WHATSAPP_PHONE_ID')}/messages"
        headers = {
            "Authorization": f"Bearer {os.getenv('WHATSAPP_ACCESS_TOKEN')}",
            "Content-Type": "application/json"
        }
        
        # Validate and truncate text lengths according to WhatsApp limits
        # Header: 60 characters max
        # Body: 1024 characters max  
        # Footer: 60 characters max
        # Also remove any characters that might cause issues
        header_text = header[:60] if len(header) > 60 else header
        body_text = body[:1024] if len(body) > 1024 else body
        footer_text = footer[:60] if len(footer) > 60 else footer
        
        # Clean text to remove potential problematic characters
        header_text = header_text.replace('\r\n', '\n').replace('\r', '\n')
        body_text = body_text.replace('\r\n', '\n').replace('\r', '\n')
        footer_text = footer_text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Build buttons array (max 3 buttons for interactive messages)
        button_objects = []
        for i, button in enumerate(buttons[:3]):  # Limit to 3 buttons
            # Validate button structure
            if not isinstance(button, dict) or 'text' not in button or 'id' not in button:
                logger.error(f"Invalid button structure: {button}")
                continue
                
            # WhatsApp button title must be 20 characters or less
            button_title = button["text"][:20] if len(button["text"]) > 20 else button["text"]
            # WhatsApp button ID must be 256 characters or less and contain only alphanumeric characters, hyphens, and underscores
            button_id = button["id"][:256] if len(button["id"]) > 256 else button["id"]
            
            if not button_title or not button_id:
                logger.error(f"Empty button title or ID: {button}")
                continue
                
            button_objects.append({
                "type": "reply",
                "reply": {
                    "id": button_id,
                    "title": button_title
                }
            })
        
        # If no valid buttons, fall back to text message
        if not button_objects:
            logger.error("No valid buttons found, falling back to text message")
            return send_whatsapp_text_message(phone_number, body_text)
        
        # If more than 3 buttons, add "See all options" button
        if len(buttons) > 3:
            button_objects = button_objects[:2]  # Keep only first 2
            button_objects.append({
                "type": "reply",
                "reply": {
                    "id": "see_all_options",
                    "title": "See all options"
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
                    "text": header_text
                },
                "body": {
                    "text": body_text
                },
                "footer": {
                    "text": footer_text
                },
                "action": {
                    "buttons": button_objects
                }
            }
        }
        
        logger.info(f"Sending WhatsApp interactive message payload: {payload}")
        response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"WhatsApp API error response: {response.text}")
            logger.error(f"WhatsApp API error status: {response.status_code}")
            logger.error(f"WhatsApp API error payload: {payload}")
        
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        logger.error(f"WhatsApp API error: {str(e)}")
        logger.error(f"WhatsApp API error response: {e.response.text if e.response else 'No response'}")
        
        # Fallback to text message if interactive message fails
        fallback_message = f"{header_text}\n\n{body_text}\n\n{footer_text}\n\n"
        for i, button in enumerate(buttons[:3]):
            fallback_message += f"{i+1}. {button['text']}\n"
        fallback_message += "\nPlease reply with the number of your choice."
        
        logger.info("Falling back to text message due to interactive message failure")
        return send_whatsapp_text_message(phone_number, fallback_message)
    
    except Exception as e:
        logger.error(f"Unexpected error in send_whatsapp_interactive_message: {str(e)}", exc_info=True)
        # Final fallback to simple text message
        return send_whatsapp_text_message(phone_number, body or "Please try again later.")

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

def send_whatsapp_document(phone_number, document_url, filename, caption=""):
    """
    Send a document via WhatsApp
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
            "type": "document",
            "document": {
                "link": document_url,
                "filename": filename,
                "caption": caption
            }
        }
        
        response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        logger.error(f"WhatsApp document send error: {str(e)}")
        raise

def generate_order_receipt_pdf(order_id):
    """Generate PDF receipt for an order"""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch
    from io import BytesIO
    import os
    
    try:
        order = Order.objects(id=order_id).first()
        if not order:
            return None
        
        # Create PDF in memory
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Header
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, f"Receipt - Order #{order.order_number}")
        
        # Business info
        c.setFont("Helvetica", 12)
        y_position = height - 80
        c.drawString(50, y_position, f"Business: {order.business.name}")
        y_position -= 20
        c.drawString(50, y_position, f"Phone: {order.business.whatsapp_number}")
        y_position -= 20
        c.drawString(50, y_position, f"Email: {order.business.email or 'N/A'}")
        
        # Customer info
        y_position -= 40
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y_position, "Customer Information:")
        y_position -= 20
        c.setFont("Helvetica", 12)
        c.drawString(50, y_position, f"Phone: {order.customer.phone_number}")
        if order.customer.name:
            y_position -= 20
            c.drawString(50, y_position, f"Name: {order.customer.name}")
        
        # Order details
        y_position -= 40
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y_position, "Order Details:")
        y_position -= 20
        c.setFont("Helvetica", 12)
        c.drawString(50, y_position, f"Order Date: {order.created_at.strftime('%Y-%m-%d %H:%M')}")
        y_position -= 20
        c.drawString(50, y_position, f"Status: {order.status.title()}")
        y_position -= 20
        c.drawString(50, y_position, f"Payment: {order.payment_status.title()}")
        
        # Items
        y_position -= 40
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y_position, "Items:")
        y_position -= 20
        
        c.setFont("Helvetica", 10)
        for item in order.order_items:
            product_name = item.product.name
            if item.variation_id:
                # Find the variation in the product's variations list
                variation = None
                for var in item.product.variations:
                    if var.variation_id == item.variation_id:
                        variation = var
                        break
                if variation:
                    product_name += f" ({variation.name})"
            
            c.drawString(50, y_position, f"{item.quantity}x {product_name}")
            c.drawString(400, y_position, f"KES {item.total_price:.2f}")
            y_position -= 15
        
        # Total
        y_position -= 20
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y_position, f"Total: KES {order.total_amount:.2f}")
        
        # Customization notes
        if order.customization_notes:
            y_position -= 40
            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, y_position, "Customization Notes:")
            y_position -= 15
            c.setFont("Helvetica", 10)
            # Handle long text by wrapping
            lines = order.customization_notes.split('\n')
            for line in lines:
                if len(line) > 80:
                    # Simple word wrap
                    words = line.split(' ')
                    current_line = ""
                    for word in words:
                        if len(current_line + word) < 80:
                            current_line += word + " "
                        else:
                            c.drawString(50, y_position, current_line.strip())
                            y_position -= 12
                            current_line = word + " "
                    if current_line:
                        c.drawString(50, y_position, current_line.strip())
                        y_position -= 12
                else:
                    c.drawString(50, y_position, line)
                    y_position -= 12
        
        c.save()
        
        # Save to file
        buffer.seek(0)
        filename = f"receipt_{order.order_number}.pdf"
        filepath = os.path.join('static', 'receipts', filename)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'wb') as f:
            f.write(buffer.getvalue())
        
        return filepath
        
    except Exception as e:
        logger.error(f"Error generating PDF receipt: {str(e)}")
        return None

def handle_payment_confirmation(phone_number, order_id, mpesa_transaction_id):
    """Handle successful payment confirmation"""
    
    try:
        order = Order.objects(id=order_id).first()
        if not order:
            return send_whatsapp_text_message(phone_number, "Order not found.")
        
        # Update order status
        order.payment_status = 'paid'
        order.status = 'processing'
        order.mpesa_transaction_id = mpesa_transaction_id
        order.save()
        
        # Generate and send receipt
        receipt_path = generate_order_receipt_pdf(str(order.id))
        
        # Send confirmation message
        confirmation_msg = f"✅ Payment confirmed!\n\n"
        confirmation_msg += f"Order: #{order.order_number}\n"
        confirmation_msg += f"Amount: KES {order.total_amount:.2f}\n"
        confirmation_msg += f"Transaction ID: {mpesa_transaction_id}\n\n"
        confirmation_msg += "Your order is now being processed. You'll receive updates on this number."
        
        send_whatsapp_text_message(phone_number, confirmation_msg)
        
        # Send receipt if generated successfully
        if receipt_path:
            receipt_url = f"{os.getenv('BASE_URL', 'https://your-domain.com')}/{receipt_path}"
            send_whatsapp_document(
                phone_number, 
                receipt_url, 
                f"receipt_{order.order_number}.pdf",
                "Your order receipt"
            )
        
        return True
        
    except Exception as e:
        logger.error(f"Error handling payment confirmation: {str(e)}")
        return False

def handle_order_status_update(order_id, new_status):
    """Send WhatsApp notification when order status changes"""
    
    try:
        order = Order.objects(id=order_id).first()
        if not order:
            return False
        
        customer_phone = order.customer.phone_number
        business_name = order.business.name
        
        status_messages = {
            'processing': f"🔄 Your order #{order.order_number} from {business_name} is now being processed.",
            'shipped': f"📦 Great news! Your order #{order.order_number} from {business_name} has been shipped.",
            'delivered': f"✅ Your order #{order.order_number} from {business_name} has been delivered. Thank you for your business!",
            'cancelled': f"❌ Your order #{order.order_number} from {business_name} has been cancelled. If you have questions, please contact us."
        }
        
        message = status_messages.get(new_status, f"Order #{order.order_number} status updated to: {new_status}")
        
        return send_whatsapp_text_message(customer_phone, message)
        
    except Exception as e:
        logger.error(f"Error sending order status update: {str(e)}")
        return False

def send_bulk_message(business_id, message, customer_list=None):
    """Send bulk messages to customers"""
    
    try:
        business = Business.objects(id=business_id).first()
        if not business:
            return {"error": "Business not found"}
        
        # If no customer list provided, get all customers who have chatted with this business
        if not customer_list:
            chat_sessions = ChatSession.objects(business=business_id).all()
            customer_ids = list(set([session.customer.id for session in chat_sessions]))
            customers = Customer.objects(id__in=customer_ids).all()
        else:
            customers = Customer.objects(phone_number__in=customer_list).all()
        
        sent_count = 0
        failed_count = 0
        
        for customer in customers:
            try:
                send_whatsapp_text_message(customer.phone_number, message)
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send message to {customer.phone_number}: {str(e)}")
                failed_count += 1
        
        return {
            "sent": sent_count,
            "failed": failed_count,
            "total": len(customers)
        }
        
    except Exception as e:
        logger.error(f"Error in bulk messaging: {str(e)}")
        return {"error": str(e)}

def create_chat_session(customer_phone, business_id):
    """Create or get existing chat session"""
    import uuid
    
    try:
        # Get or create customer
        customer = Customer.objects(phone_number=customer_phone).first()
        if not customer:
            customer = Customer(phone_number=customer_phone)
            customer.save()
        
        # Check for existing active session
        existing_session = ChatSession.objects(
            customer=customer.id,
            business=business_id
        ).order_by('-created_at').first()
        
        # Create new session if none exists or if last session is old (more than 24 hours)
        if not existing_session or (datetime.utcnow() - existing_session.created_at).days > 0:
            session = ChatSession(
                customer=customer.id,
                business=business_id,
                session_id=str(uuid.uuid4())
            )
            session.save()
            return session
        
        return existing_session
        
    except Exception as e:
        logger.error(f"Error creating chat session: {str(e)}")
        return None

def log_chat_message(session_id, sender_type, message_text, message_type='text', button_data=None):
    """Log a chat message to the database"""
    
    try:
        # Find the chat session
        session = ChatSession.objects(session_id=session_id).first()
        if not session:
            logger.error(f"Chat session not found: {session_id}")
            return None
        
        # Create the message
        message = ChatMessage(
            sender_type=sender_type,
            message_text=message_text,
            message_type=message_type,
            button_data=button_data
        )
        
        # Add message to session
        session.messages.append(message)
        session.save()
        return message
        
    except Exception as e:
        logger.error(f"Error logging chat message: {str(e)}")
        return None

def handle_button_response(phone_number, button_id):
    """
    Handle responses to button clicks
    """
    try:
        # Check if user is in onboarding
        onboarding_state = OnboardingState.objects(phone_number=phone_number).first()
        if onboarding_state:
            return onboarding_service.handle_onboarding_response(phone_number, button_id=button_id)
        
        # Handle main menu buttons
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
            return onboarding_service.start_onboarding(phone_number)
        
        elif button_id.startswith("category_"):
            from services.openai_service import handle_category_selection
            category_id = button_id.split("_")[1]  # Keep as string for MongoDB ObjectId
            return handle_category_selection(phone_number, category_id)
        
        elif button_id.startswith("buy_"):
            product_id = button_id.split("_")[1]  # Keep as string for MongoDB ObjectId
            return initiate_product_purchase(phone_number, product_id)
        
        elif button_id.startswith("variation_"):
            variation_id = button_id.split("_")[1]  # Keep as string for MongoDB ObjectId
            return initiate_variation_purchase(phone_number, variation_id)
        
        elif button_id.startswith("variations_"):
            product_id = button_id.split("_")[1]  # Keep as string for MongoDB ObjectId
            return handle_product_variations(phone_number, product_id)
        
        elif button_id.startswith("more_variations_"):
            parts = button_id.split("_")
            product_id = parts[2]  # Keep as string for MongoDB ObjectId
            page = int(parts[3]) if len(parts) > 3 else 1
            return show_more_variations(phone_number, product_id, page)
        
        elif button_id.startswith("customize_"):
            product_id = button_id.split("_")[1]  # Keep as string for MongoDB ObjectId
            return handle_product_customization(phone_number, product_id)
        
        elif button_id.startswith("confirm_order_"):
            order_id = button_id.split("_")[2]  # Keep as string for MongoDB ObjectId
            return confirm_order_placement(phone_number, order_id)
        
        elif button_id.startswith("cancel_order_"):
            order_id = button_id.split("_")[2]  # Keep as string for MongoDB ObjectId
            return cancel_order(phone_number, order_id)
        
        elif button_id == "dashboard_login":
            message = "*Vendor Dashboard Login:*\n\nClick the link below to access your Vendor Dashboard to change your password, update product catalog and access other functionality:\n\n*https://example.com/login*"
        
        elif button_id == "see_all_options":
            # Handle when more than 3 options were available
            message = "Please specify what you're looking for, and I'll show you the relevant options."
        
        else:
            message = "Sorry, I didn't understand that option. Please try again."
        
        return send_whatsapp_text_message(phone_number, message)
        
    except Exception as e:
        logger.error(f"Error handling button response: {str(e)}")
        raise

def send_whatsapp_list_message(phone_number, header, body, footer, button_text, sections):
    """
    Send an interactive WhatsApp list message
    sections format: [{"title": "Section Title", "rows": [{"id": "row_id", "title": "Row Title", "description": "Row Description"}]}]
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
            "type": "interactive",
            "interactive": {
                "type": "list",
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
                    "button": button_text,
                    "sections": sections
                }
            }
        }
        
        response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        logger.error(f"WhatsApp API error: {str(e)}")
        raise

def handle_product_variations(phone_number, product_id):
    """Handle product variations display with interactive buttons or list"""
    
    product = Product.objects(id=product_id).first()
    if not product:
        return send_whatsapp_text_message(phone_number, "Product not found.")
    
    # Get variations from the product's embedded variations list
    variations = [var for var in product.variations if var.is_active]
    
    if not variations:
        return send_whatsapp_text_message(phone_number, "No variations available for this product.")
    
    total_variations = len(variations)
    
    if total_variations <= 3:
        # If 3 or fewer variations, show as interactive buttons
        buttons = []
        for variation in variations:
            buttons.append({
                "text": f"{variation.name} - KES {variation.price:.2f}",
                "id": f"variation_{variation.variation_id}"
            })
        
        header = f"{product.name} - Variations"
        body = f"Choose from available variations of {product.name}:"
        footer = "Select a variation to purchase"
        
        return send_whatsapp_interactive_message(phone_number, header, body, footer, buttons)
    else:
        # If more than 3 variations, show as list message
        list_rows = []
        for variation in variations:
            list_rows.append({
                "id": f"variation_{variation.variation_id}",
                "title": f"{variation.name}",
                "description": f"KES {variation.price:.2f}"
            })
        
        # Create sections format for WhatsApp list message
        sections = [{
            "title": "Product Variations",
            "rows": list_rows
        }]
        
        return send_whatsapp_list_message(
            phone_number,
            f"{product.name} - Variations",
            f"Choose from available variations of {product.name}:",
            "Select a variation to continue",
            "Select Variation",
            sections
        )

def handle_product_customization(phone_number, product_id):
    """Handle product customization"""
    
    product = Product.objects(id=product_id).first()
    
    if not product or not product.allows_customization:
        return send_whatsapp_text_message(phone_number, "Sorry, customizations not available on this product")
    
    # Store the product ID for the next message (customization request)
    # You might want to store this in a session or temporary storage
    return send_whatsapp_text_message(
        phone_number, 
        f"Kindly describe what customizations you would like done to your {product.name}"
    )

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

def is_mpesa_number(message):
    """Check if message is an Mpesa phone number"""
    cleaned = ''.join(filter(str.isdigit, message))
    return len(cleaned) in [9, 10, 12] and (cleaned.startswith('0') or cleaned.startswith('254'))

def is_trigger_word(message):
    """
    Check if the message contains trigger words
    """
    trigger_words = ["hi", "hello", "sasabot"]
    return message.lower().strip() in trigger_words

# =============================================================================
# DEPRECATED FUNCTIONS - FOR BUSINESS-SPECIFIC WEBHOOKS ONLY
# These functions should NOT be called from the system webhook
# They are kept for backward compatibility and business webhook usage
# =============================================================================

def handle_user_message(data):
    """
    Handle incoming user messages with the new flow
    """
    try:
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
                # Check if user is in onboarding
                onboarding_state = OnboardingState.objects(phone_number=phone_number).first()
                if onboarding_state:
                    response = onboarding_service.handle_onboarding_response(phone_number, message=message)
                    return jsonify({"message": "Onboarding response sent", "whatsapp_response": response}), 200
                
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
                
                # Check if it's an Mpesa number (for payment)
                elif is_mpesa_number(message):
                    response = handle_mpesa_payment_request(phone_number, message)
                    return jsonify({"message": "Payment processing initiated", "whatsapp_response": response}), 200
                
                # Check if it's a customization request (user is responding to customization prompt)
                elif is_customization_request(phone_number, message):
                    response = handle_customization_input(phone_number, message)
                    return jsonify({"message": "Customization processed", "whatsapp_response": response}), 200
                
                else:
                    # Process with GPT
                    from services.openai_service import process_gpt_interaction
                    response = process_gpt_interaction(phone_number, message)
                    return jsonify({"message": "GPT response sent", "gpt_response": response}), 200
            
            return jsonify({"error": "No message or button data provided"}), 400
            
        except Exception as e:
            logger.error(f"Message processing error: {str(e)}")
            return jsonify({"error": "Failed to process message"}), 500
            
    except Exception as e:
        logger.error(f"Message handling error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

def handle_mpesa_payment_request(phone_number, mpesa_number):
    """Handle Mpesa payment request"""
    
    try:
        # Find the most recent pending order for this customer
        customer = Customer.objects(phone_number=phone_number).first()
        if not customer:
            return send_whatsapp_text_message(phone_number, "No pending orders found. Please place an order first.")
        
        pending_order = Order.objects(
            customer=customer.id,
            payment_status='pending'
        ).order_by('-created_at').first()
        
        if not pending_order:
            return send_whatsapp_text_message(phone_number, "No pending orders found. Please place an order first.")
        
        # Clean the Mpesa number
        clean_mpesa = clean_phone_number(mpesa_number)
        
        # Initiate Mpesa payment
        from services.mpesa_service import mpesa_service
        payment_result = mpesa_service.initiate_stk_push(
            phone_number=clean_mpesa,
            amount=int(pending_order.total_amount),
            order_id=pending_order.order_number,
            account_reference=pending_order.order_number
        )
        
        if payment_result.get('success'):
            message = f"💳 Payment request sent to {clean_mpesa}\n\n"
            message += f"Order: #{pending_order.order_number}\n"
            message += f"Amount: KES {pending_order.total_amount:.2f}\n\n"
            message += "Please check your phone and enter your MPESA PIN to complete the payment."
            
            return send_whatsapp_text_message(phone_number, message)
        else:
            error_message = payment_result.get('message', 'Unknown error')
            return send_whatsapp_text_message(
                phone_number, 
                f"Payment initiation failed: {error_message}. Please try again or contact support."
            )
        
    except Exception as e:
        logger.error(f"Error handling Mpesa payment request: {str(e)}")
        return send_whatsapp_text_message(phone_number, "Sorry, there was an error processing your payment. Please try again.")

def is_customization_request(phone_number, message):
    """Check if the message is a customization request"""
    # This is a simple check - in a real implementation, you might want to store
    # the context in a session or temporary storage to know if the user is
    # responding to a customization prompt
    return False  # Placeholder - implement based on your session management

def handle_customization_input(phone_number, customization_text):
    """Handle customization input from user"""
    
    try:
        # Find the customer's most recent pending order
        customer = Customer.objects(phone_number=phone_number).first()
        if not customer:
            return send_whatsapp_text_message(phone_number, "No orders found.")
        
        pending_order = Order.objects(
            customer=customer.id,
            status='pending'
        ).order_by('-created_at').first()
        
        if not pending_order:
            return send_whatsapp_text_message(phone_number, "No pending orders found.")
        
        # Add customization notes to the order
        pending_order.customization_notes = customization_text
        pending_order.save()
        
        message = f"✅ Customization noted: {customization_text}\n\n"
        message += "Your customization has been added to your order. "
        message += "Please reply with your MPESA number to proceed with payment."
        
        return send_whatsapp_text_message(phone_number, message)
        
    except Exception as e:
        logger.error(f"Error handling customization input: {str(e)}")
        return send_whatsapp_text_message(phone_number, "Sorry, there was an error processing your customization.")

def initiate_product_purchase(phone_number, product_id):
    """Initiate purchase for a product"""
    
    try:
        logger.info(f"Initiating product purchase for phone: {phone_number}, product_id: {product_id}")
        
        # Validate product_id
        if not product_id:
            logger.error("Product ID is None or empty")
            return send_whatsapp_text_message(phone_number, "Product not found.")
        
        product = Product.objects(id=product_id).first()
        if not product:
            logger.error(f"Product not found with ID: {product_id}")
            return send_whatsapp_text_message(phone_number, "Sorry, this product is not available.")
        
        if not product.is_active:
            logger.error(f"Product {product_id} is not active")
            return send_whatsapp_text_message(phone_number, "Sorry, this product is not available.")
        
        # Check if product has variations
        if hasattr(product, 'has_variations') and product.has_variations:
            logger.info(f"Product {product_id} has variations, showing variations")
            return handle_product_variations(phone_number, product_id)
        
        # Get or create customer
        customer = Customer.objects(phone_number=phone_number).first()
        if not customer:
            logger.info(f"Creating new customer for phone: {phone_number}")
            customer = Customer(phone_number=phone_number)
            customer.save()
        
        # Validate product price
        if not hasattr(product, 'price') or product.price is None:
            logger.error(f"Product {product_id} has no price")
            return send_whatsapp_text_message(phone_number, "Product price not available.")
        
        # Create order with embedded order item
        order_item = OrderItem(
            product=product.id,
            quantity=1,
            unit_price=product.price,
            total_price=product.price
        )
        
        order = Order(
            order_number=Order.generate_order_number(),
            customer=customer.id,
            business=product.business.id,
            total_amount=product.price,
            status='pending',
            payment_status='pending',
            order_items=[order_item]
        )
        order.save()
        
        logger.info(f"Order created successfully: {order.id}")
        
        # Show order confirmation with payment options
        return show_order_confirmation(phone_number, order.id)
        
    except Exception as e:
        logger.error(f"Error initiating product purchase: {str(e)}", exc_info=True)
        return send_whatsapp_text_message(phone_number, "Sorry, there was an error processing your request.")

def initiate_variation_purchase(phone_number, variation_id):
    """Initiate purchase for a product variation"""
    
    try:
        # Find the product that contains this variation
        product = Product.objects(variations__variation_id=variation_id).first()
        if not product:
            return send_whatsapp_text_message(phone_number, "Product not found.")
        
        # Find the specific variation
        variation = None
        for var in product.variations:
            if var.variation_id == variation_id and var.is_active:
                variation = var
                break
        
        if not variation:
            return send_whatsapp_text_message(phone_number, "Sorry, this variation is not available.")
        
        # Get or create customer
        customer = Customer.objects(phone_number=phone_number).first()
        if not customer:
            customer = Customer(phone_number=phone_number)
            customer.save()
        
        # Create order with embedded order item
        order_item = OrderItem(
            product=product.id,
            variation_id=variation_id,
            quantity=1,
            unit_price=variation.price,
            total_price=variation.price
        )
        
        order = Order(
            order_number=Order.generate_order_number(),
            customer=customer.id,
            business=product.business.id,
            total_amount=variation.price,
            status='pending',
            payment_status='pending',
            order_items=[order_item]
        )
        order.save()
        
        # Show order confirmation with payment options
        return show_order_confirmation(phone_number, order.id)
        
    except Exception as e:
        logger.error(f"Error initiating variation purchase: {str(e)}")
        return send_whatsapp_text_message(phone_number, "Sorry, there was an error processing your request.")

def show_order_confirmation(phone_number, order_id):
    """Show order confirmation with payment options"""
    
    try:
        # Validate order_id
        if not order_id:
            logger.error("Order ID is None or empty")
            return send_whatsapp_text_message(phone_number, "Order not found.")
        
        order = Order.objects(id=order_id).first()
        if not order:
            logger.error(f"Order not found with ID: {order_id}")
            return send_whatsapp_text_message(phone_number, "Order not found.")
        
        # Validate required fields
        if not order.business:
            logger.error(f"Order {order_id} has no business")
            return send_whatsapp_text_message(phone_number, "Order information incomplete.")
        
        if not order.order_items:
            logger.error(f"Order {order_id} has no items")
            return send_whatsapp_text_message(phone_number, "Order has no items.")
        
        # Build order summary
        order_summary = f"Order Summary\n\n"
        order_summary += f"Order #: {order.order_number}\n"
        order_summary += f"Business: {order.business.name}\n\n"
        
        order_summary += "Items:\n"
        for item in order.order_items:
            if not item.product:
                logger.error(f"Order item has no product: {item}")
                continue
                
            product_name = item.product.name
            if item.variation_id:
                # Find the variation in the product's variations list
                variation = None
                for var in item.product.variations:
                    if var.variation_id == item.variation_id:
                        variation = var
                        break
                if variation:
                    product_name += f" ({variation.name})"
            order_summary += f"• {item.quantity}x {product_name} - KES {item.total_price:.2f}\n"
        
        order_summary += f"\nTotal: KES {order.total_amount:.2f}\n\n"
        order_summary += "Please confirm your order to proceed with payment."
        
        # Create confirmation buttons
        buttons = [
            {"text": "Confirm Order", "id": f"confirm_order_{order.id}"},
            {"text": "Cancel", "id": f"cancel_order_{order.id}"}
        ]
        
        # Check if any product in the order allows customization
        has_customizable_product = any(item.product.allows_customization for item in order.order_items)
        if has_customizable_product:
            buttons.insert(1, {"text": "Add Customization", "id": f"customize_{order.order_items[0].product.id}"})
        
        return send_whatsapp_interactive_message(
            phone_number,
            "Order Confirmation",
            order_summary,
            "Choose an option",
            buttons
        )
        
    except Exception as e:
        logger.error(f"Error showing order confirmation: {str(e)}")
        return send_whatsapp_text_message(phone_number, "Sorry, there was an error processing your request.")

def confirm_order_placement(phone_number, order_id):
    """Confirm order and initiate payment"""
    
    try:
        order = Order.objects(id=order_id).first()
        if not order:
            return send_whatsapp_text_message(phone_number, "Order not found.")
        
        # Send payment instructions
        payment_message = f"💳 *Payment Required*\n\n"
        payment_message += f"Order: #{order.order_number}\n"
        payment_message += f"Amount: KES {order.total_amount:.2f}\n\n"
        payment_message += "Please reply with your MPESA number (e.g., 0712345678) to receive a payment prompt."
        
        return send_whatsapp_text_message(phone_number, payment_message)
        
    except Exception as e:
        logger.error(f"Error confirming order placement: {str(e)}")
        return send_whatsapp_text_message(phone_number, "Sorry, there was an error processing your request.")

def cancel_order(phone_number, order_id):
    """Cancel an order"""
    
    try:
        order = Order.objects(id=order_id).first()
        if not order:
            return send_whatsapp_text_message(phone_number, "Order not found.")
        
        # Update order status
        order.status = 'cancelled'
        order.save()
        
        message = f"❌ Order #{order.order_number} has been cancelled.\n\n"
        message += "You can start a new order anytime by typing 'hi' or 'hello'."
        
        return send_whatsapp_text_message(phone_number, message)
        
    except Exception as e:
        logger.error(f"Error cancelling order: {str(e)}")
        return send_whatsapp_text_message(phone_number, "Sorry, there was an error processing your request.")

def show_more_variations(phone_number, product_id, page=1):
    """Show additional product variations using list format (kept for backward compatibility)"""
    
    try:
        product = Product.objects(id=product_id).first()
        if not product:
            return send_whatsapp_text_message(phone_number, "Product not found.")
        
        # Get active variations from the product's embedded variations list
        variations = [var for var in product.variations if var.is_active]
        
        if not variations:
            return send_whatsapp_text_message(phone_number, "No variations available.")
        
        # Create list rows for all variations
        list_rows = []
        for variation in variations:
            list_rows.append({
                "id": f"variation_{variation.variation_id}",
                "title": f"{variation.name}",
                "description": f"KES {variation.price:.2f}"
            })
        
        # Create sections format for WhatsApp list message
        sections = [{
            "title": "All Variations",
            "rows": list_rows
        }]
        
        return send_whatsapp_list_message(
            phone_number,
            f"{product.name} - All Variations",
            f"Here are all available variations of {product.name}:",
            "Select a variation to continue",
            "Select Variation",
            sections
        )
        
    except Exception as e:
        logger.error(f"Error showing more variations: {str(e)}")
        return send_whatsapp_text_message(phone_number, "Sorry, there was an error processing your request.")

def validate_whatsapp_config():
    """Validate that WhatsApp configuration is properly set"""
    required_vars = ['WHATSAPP_PHONE_ID', 'WHATSAPP_ACCESS_TOKEN', 'WHATSAPP_VERIFY_TOKEN']
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required WhatsApp environment variables: {missing_vars}")
        return False
    
    return True
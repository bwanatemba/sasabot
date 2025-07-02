import requests
import os
import logging
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
            elif 'list_reply' in interactive:
                list_id = interactive['list_reply'].get('id')
                if not phone_number or not list_id:
                    logger.error(f"Missing required fields: phone={phone_number}, list_id={list_id}")
                    return jsonify({"error": "Missing required fields"}), 400
                    
                return handle_user_message({
                    'phone_number': phone_number,
                    'button_id': list_id  # Use same parameter name for consistency
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
        
        # Build buttons array (max 3 buttons for interactive messages)
        button_objects = []
        for i, button in enumerate(buttons[:3]):  # Limit to 3 buttons
            button_objects.append({
                "type": "reply",
                "reply": {
                    "id": button["id"],
                    "title": button["text"]
                }
            })
        
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
                variation = item.variation
                product_name += f" ({variation.name})"
            
            c.drawString(50, y_position, f"{item.quantity}x {product_name}")
            c.drawString(400, y_position, f"${item.total_price:.2f}")
            y_position -= 15
        
        # Total
        y_position -= 20
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y_position, f"Total: ${order.total_amount:.2f}")
        
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
        confirmation_msg += f"Amount: ${order.total_amount:.2f}\n"
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
            category_id = int(button_id.split("_")[1])
            return handle_category_selection(phone_number, category_id)
        
        elif button_id.startswith("buy_"):
            product_id = int(button_id.split("_")[1])
            return initiate_product_purchase(phone_number, product_id)
        
        elif button_id.startswith("variation_"):
            variation_id = int(button_id.split("_")[1])
            return initiate_variation_purchase(phone_number, variation_id)
        
        elif button_id.startswith("variations_"):
            product_id = int(button_id.split("_")[1])
            return handle_product_variations(phone_number, product_id)
        
        elif button_id.startswith("more_variations_"):
            product_id = int(button_id.split("_")[2])
            return show_more_variations(phone_number, product_id)
        
        elif button_id.startswith("customize_"):
            product_id = int(button_id.split("_")[1])
            return handle_product_customization(phone_number, product_id)
        
        elif button_id.startswith("confirm_order_"):
            order_id = int(button_id.split("_")[2])
            return confirm_order_placement(phone_number, order_id)
        
        elif button_id.startswith("cancel_order_"):
            order_id = int(button_id.split("_")[2])
            return cancel_order(phone_number, order_id)
        
        elif button_id == "dashboard_login":
            message = "*Vendor Dashboard Login:*\n\nClick the link below to Login to your vendor dashboard to change your password, update product catalog and access other functionality:\n\n*https://your-frontend-domain.vercel.app/login*"
        
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
    """Handle product variations display with interactive buttons"""
    
    product = Product.objects(id=product_id).first()
    if not product:
        return send_whatsapp_text_message(phone_number, "Product not found.")
    
    variations = ProductVariation.objects(product=product_id, is_active=True).all()
    
    if not variations:
        return send_whatsapp_text_message(phone_number, "No variations available for this product.")
    
    # Create buttons for variations (max 3 at a time)
    buttons = []
    for variation in variations[:3]:
        buttons.append({
            "text": f"{variation.name} - ${variation.price:.2f}",
            "id": f"variation_{variation.id}"
        })
    
    if len(variations) > 3:
        # Show a "See more" option for additional variations
        buttons.append({
            "text": "See more options",
            "id": f"more_variations_{product_id}"
        })
    
    header = f"{product.name} - Variations"
    body = f"Choose from available variations of {product.name}:"
    footer = "Select a variation to purchase"
    
    return send_whatsapp_interactive_message(phone_number, header, body, footer, buttons)

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
        from services.mpesa_service import initiate_stk_push
        payment_result = initiate_stk_push(
            phone_number=clean_mpesa,
            amount=int(pending_order.total_amount),
            account_reference=pending_order.order_number,
            transaction_desc=f"Payment for order {pending_order.order_number}"
        )
        
        if payment_result.get('success'):
            message = f"💳 Payment request sent to {clean_mpesa}\n\n"
            message += f"Order: #{pending_order.order_number}\n"
            message += f"Amount: ${pending_order.total_amount:.2f}\n\n"
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
        product = Product.objects(id=product_id).first()
        if not product or not product.is_active:
            return send_whatsapp_text_message(phone_number, "Sorry, this product is not available.")
        
        # Check if product has variations
        if product.has_variations:
            return handle_product_variations(phone_number, product_id)
        
        # Get or create customer
        customer = Customer.objects(phone_number=phone_number).first()
        if not customer:
            customer = Customer(phone_number=phone_number)
            customer.save()
        
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
        
        # Show order confirmation with payment options
        return show_order_confirmation(phone_number, order.id)
        
    except Exception as e:
        logger.error(f"Error initiating product purchase: {str(e)}")
        return send_whatsapp_text_message(phone_number, "Sorry, there was an error processing your request.")

def initiate_variation_purchase(phone_number, variation_id):
    """Initiate purchase for a product variation"""
    
    try:
        variation = ProductVariation.objects(id=variation_id).first()
        if not variation or not variation.is_active:
            return send_whatsapp_text_message(phone_number, "Sorry, this variation is not available.")
        
        product = variation.product
        
        # Get or create customer
        customer = Customer.objects(phone_number=phone_number).first()
        if not customer:
            customer = Customer(phone_number=phone_number)
            customer.save()
        
        # Create order with embedded order item
        order_item = OrderItem(
            product=product.id,
            variation_id=str(variation.id),
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
        order = Order.objects(id=order_id).first()
        if not order:
            return send_whatsapp_text_message(phone_number, "Order not found.")
        
        # Build order summary
        order_summary = f"📋 *Order Summary*\n\n"
        order_summary += f"Order #: {order.order_number}\n"
        order_summary += f"Business: {order.business.name}\n\n"
        
        order_summary += "*Items:*\n"
        for item in order.order_items:
            product_name = item.product.name
            if item.variation_id:
                variation = item.variation
                product_name += f" ({variation.name})"
            order_summary += f"• {item.quantity}x {product_name} - ${item.total_price:.2f}\n"
        
        order_summary += f"\n*Total: ${order.total_amount:.2f}*\n\n"
        order_summary += "Please confirm your order to proceed with payment."
        
        # Create confirmation buttons
        buttons = [
            {"text": "✅ Confirm Order", "id": f"confirm_order_{order.id}"},
            {"text": "❌ Cancel", "id": f"cancel_order_{order.id}"}
        ]
        
        # Check if any product in the order allows customization
        has_customizable_product = any(item.product.allows_customization for item in order.order_items)
        if has_customizable_product:
            buttons.insert(1, {"text": "🎨 Add Customization", "id": f"customize_{order.order_items[0].product.id}"})
        
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
        payment_message += f"Amount: ${order.total_amount:.2f}\n\n"
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
    """Show additional product variations"""
    
    try:
        product = Product.objects(id=product_id).first()
        if not product:
            return send_whatsapp_text_message(phone_number, "Product not found.")
        
        variations = ProductVariation.objects(product=product_id, is_active=True).all()
        
        # Calculate pagination
        per_page = 3
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_variations = variations[start_idx:end_idx]
        
        if not page_variations:
            return send_whatsapp_text_message(phone_number, "No more variations available.")
        
        # Create buttons for this page
        buttons = []
        for variation in page_variations:
            buttons.append({
                "text": f"{variation.name} - ${variation.price:.2f}",
                "id": f"variation_{variation.id}"
            })
        
        # Add navigation buttons if needed
        if end_idx < len(variations):
            buttons.append({
                "text": "More options →",
                "id": f"more_variations_{product_id}_{page + 1}"
            })
        
        header = f"{product.name} - Variations (Page {page})"
        body = f"Choose from available variations of {product.name}:"
        footer = "Select a variation to purchase"
        
        return send_whatsapp_interactive_message(phone_number, header, body, footer, buttons)
        
    except Exception as e:
        logger.error(f"Error showing more variations: {str(e)}")
        return send_whatsapp_text_message(phone_number, "Sorry, there was an error processing your request.")
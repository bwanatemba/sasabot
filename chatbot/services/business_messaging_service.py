import requests
import os
import logging
from datetime import datetime
from flask import jsonify, request
from dotenv import load_dotenv
from models import Customer, CustomerState, Order, OrderItem, OrderIssue, Business, Product, Category, ChatSession, ChatMessage
from services.messaging_service import clean_phone_number

load_dotenv()
logger = logging.getLogger(__name__)

def send_business_whatsapp_text_message(phone_number, message, business):
    """Send a text message using business-specific WhatsApp credentials"""
    try:
        # Use business credentials if available, fallback to global
        access_token = business.whatsapp_api_token or os.getenv('WHATSAPP_ACCESS_TOKEN')
        phone_id = business.whatsapp_phone_id or os.getenv('WHATSAPP_PHONE_ID')
        
        if not access_token or not phone_id:
            logger.error(f"Missing WhatsApp credentials for business {business.name}")
            return {"error": "WhatsApp not configured for this business"}
        
        WHATSAPP_API_URL = f"https://graph.facebook.com/v17.0/{phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "text",
            "text": {"body": message}
        }
        
        response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
        
        if response.status_code == 200:
            logger.info(f"WhatsApp message sent successfully to {phone_number}")
            return response.json()
        else:
            logger.error(f"Failed to send WhatsApp message: {response.status_code} - {response.text}")
            return {"error": f"Failed to send message: {response.status_code}"}
            
    except Exception as e:
        logger.error(f"Error sending business WhatsApp text message: {str(e)}")
        return {"error": str(e)}

def send_business_whatsapp_interactive_message(phone_number, header, body, footer, buttons, business):
    """Send an interactive WhatsApp message using business-specific credentials"""
    try:
        # Use business credentials if available, fallback to global
        access_token = business.whatsapp_api_token or os.getenv('WHATSAPP_ACCESS_TOKEN')
        phone_id = business.whatsapp_phone_id or os.getenv('WHATSAPP_PHONE_ID')
        
        if not access_token or not phone_id:
            logger.error(f"Missing WhatsApp credentials for business {business.name}")
            return {"error": "WhatsApp not configured for this business"}
        
        WHATSAPP_API_URL = f"https://graph.facebook.com/v17.0/{phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Set default values for empty strings
        header = header or "Message"
        body = body or "Please select an option"
        footer = footer or "Choose an option"
        
        # Validate and truncate text lengths according to WhatsApp limits
        header_text = header[:60] if len(header) > 60 else header
        body_text = body[:1024] if len(body) > 1024 else body
        footer_text = footer[:60] if len(footer) > 60 else footer
        
        # Build buttons array (max 3 buttons for interactive messages)
        button_objects = []
        for i, button in enumerate(buttons[:3]):  # Limit to 3 buttons
            # Validate button structure
            if not isinstance(button, dict) or 'text' not in button or 'id' not in button:
                logger.error(f"Invalid button structure: {button}")
                continue
                
            # WhatsApp button title must be 20 characters or less
            button_title = button["text"][:20] if len(button["text"]) > 20 else button["text"]
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
            return send_business_whatsapp_text_message(phone_number, body_text, business)
        
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
        
        response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
        
        if response.status_code == 200:
            logger.info(f"WhatsApp interactive message sent successfully to {phone_number}")
            return response.json()
        else:
            logger.error(f"Failed to send WhatsApp interactive message: {response.status_code} - {response.text}")
            return {"error": f"Failed to send message: {response.status_code}"}
            
    except Exception as e:
        logger.error(f"Error sending business WhatsApp interactive message: {str(e)}")
        return {"error": str(e)}

def send_business_whatsapp_list_message(phone_number, header, body, footer, button_text, sections, business):
    """Send an interactive WhatsApp list message using business-specific credentials"""
    try:
        # Use business credentials if available, fallback to global
        access_token = business.whatsapp_api_token or os.getenv('WHATSAPP_ACCESS_TOKEN')
        phone_id = business.whatsapp_phone_id or os.getenv('WHATSAPP_PHONE_ID')
        
        if not access_token or not phone_id:
            logger.error(f"Missing WhatsApp credentials for business {business.name}")
            return {"error": "WhatsApp not configured for this business"}
        
        WHATSAPP_API_URL = f"https://graph.facebook.com/v17.0/{phone_id}/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
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
        
        if response.status_code == 200:
            logger.info(f"WhatsApp list message sent successfully to {phone_number}")
            return response.json()
        else:
            logger.error(f"Failed to send WhatsApp list message: {response.status_code} - {response.text}")
            return {"error": f"Failed to send message: {response.status_code}"}
            
    except Exception as e:
        logger.error(f"Error sending business WhatsApp list message: {str(e)}")
        return {"error": str(e)}

def is_business_greeting(message):
    """Check if the message is a greeting/trigger word"""
    greeting_words = ['hello', 'hi', 'hey', 'start', 'menu', 'help', 'hola', 'hujambo', 'mambo']
    return any(word.lower() in message.lower() for word in greeting_words)

def process_business_whatsapp_message(data, business):
    """Process WhatsApp messages for a specific business"""
    try:
        logger.info(f"Processing business WhatsApp message for business: {business.name}")
        
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
        if 'statuses' in value:
            logger.info("Received status update webhook")
            return jsonify({"status": "ok"}), 200
            
        if 'messages' not in value:
            logger.info("No messages in webhook data - might be a status update or other notification")
            return jsonify({"status": "ok"}), 200
            
        messages = value['messages'][0]
        phone_number = messages.get('from')
        
        # Handle text messages
        if 'text' in messages:
            message = messages.get('text', {}).get('body', '')
            if not phone_number or not message:
                logger.error(f"Missing required fields: phone={phone_number}, message={message}")
                return jsonify({"error": "Missing required fields"}), 400
                
            return handle_business_user_message({
                'phone_number': phone_number,
                'message': message,
                'business': business
            })
        
        # Handle button responses
        elif 'interactive' in messages:
            interactive = messages.get('interactive', {})
            if 'button_reply' in interactive:
                button_id = interactive['button_reply'].get('id')
                if not phone_number or not button_id:
                    logger.error(f"Missing required fields: phone={phone_number}, button_id={button_id}")
                    return jsonify({"error": "Missing required fields"}), 400
                    
                return handle_business_user_message({
                    'phone_number': phone_number,
                    'button_id': button_id,
                    'business': business
                })
            elif 'list_reply' in interactive:
                list_id = interactive['list_reply'].get('id')
                if not phone_number or not list_id:
                    logger.error(f"Missing required fields: phone={phone_number}, list_id={list_id}")
                    return jsonify({"error": "Missing required fields"}), 400
                    
                return handle_business_user_message({
                    'phone_number': phone_number,
                    'button_id': list_id,  # Use same parameter name for consistency
                    'business': business
                })
        
        logger.error("Unsupported message type")
        return jsonify({"error": "Unsupported message type"}), 400
        
    except Exception as e:
        logger.error(f"Error processing business WhatsApp webhook: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

def handle_business_user_message(data):
    """Handle incoming user messages for business-specific interactions"""
    try:
        phone_number = data.get('phone_number')
        message = data.get('message')
        button_id = data.get('button_id')
        business = data.get('business')
        
        if not phone_number or not business:
            return jsonify({"error": "Missing phone number or business"}), 400
            
        # Clean phone number
        phone_number = clean_phone_number(phone_number)
        
        # Get or create customer
        customer = Customer.objects(phone_number=phone_number).first()
        if not customer:
            customer = Customer(phone_number=phone_number)
            customer.save()
        
        # Check customer state for this business
        customer_state = CustomerState.objects(phone_number=phone_number, business=business).first()
        
        # Handle button responses
        if button_id:
            return handle_business_button_response(phone_number, button_id, business, customer, customer_state)
        
        # Handle text messages
        if message:
            # Check if customer is waiting for data input
            if customer_state and customer_state.current_step:
                return handle_customer_data_input(phone_number, message, business, customer, customer_state)
            
            # Check for greeting/trigger words
            if is_business_greeting(message):
                return send_business_greeting(phone_number, business, customer)
            
            # For all other text messages, send to GPT for business-specific response
            try:
                from services.openai_service import process_gpt_interaction
                gpt_response = process_gpt_interaction(phone_number, message, str(business.id))
                return jsonify({"message": "Business GPT response sent", "gpt_response": gpt_response}), 200
            except Exception as e:
                logger.error(f"Error processing GPT interaction for business {business.name}: {str(e)}")
                # Fallback to generic response if GPT fails
                fallback_result = send_business_whatsapp_text_message(
                    phone_number,
                    f"I'm having trouble processing your request right now. Please try again or contact {business.name} directly for assistance.",
                    business
                )
                return jsonify({"message": "Fallback response sent", "whatsapp_response": fallback_result}), 200
        
        # If neither message nor button_id provided
        return jsonify({"error": "No message or button data provided"}), 400
        
    except Exception as e:
        logger.error(f"Error handling business user message: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

def send_business_greeting(phone_number, business, customer):
    """Send the business-specific greeting message"""
    try:
        body_text = f"Hello! Welcome to {business.name}. How can I assist you today? If you have any questions or need information, feel free to ask. Just type it and our AI assistant will be able to assist you. We are also on hand to help you."
        
        # Define menu options
        menu_options = [
            {"text": "Browse Categories", "id": "browse_categories", "description": "View our product categories"},
            {"text": "View My Orders", "id": "view_orders", "description": "Check your order history and status"},
            {"text": "Issue with Order", "id": "order_issue", "description": "Report a problem with your order"},
            {"text": "Update Your Details", "id": "update_details", "description": "Update your contact information"}
        ]
        
        # Since we have 4 options, use list message instead of buttons
        rows = []
        for option in menu_options:
            rows.append({
                "id": option["id"],
                "title": option["text"][:24],  # WhatsApp title limit
                "description": option["description"][:72]  # WhatsApp description limit
            })
        
        sections = [{"title": "How can we help?", "rows": rows}]
        
        response = send_business_whatsapp_list_message(
            phone_number,
            "Hello Customer",
            body_text,
            "Please choose an option",
            "Select Option",
            sections,
            business
        )
        
        # Save chat message
        save_chat_message(customer, business, 'gpt', body_text, 'interactive')
        
        return jsonify({"message": "Business greeting sent", "whatsapp_response": response}), 200
        
    except Exception as e:
        logger.error(f"Error sending business greeting: {str(e)}")
        return jsonify({"error": "Failed to send greeting"}), 500

def handle_business_button_response(phone_number, button_id, business, customer, customer_state):
    """Handle button responses for business interactions"""
    try:
        if button_id == "browse_categories":
            return send_categories_menu(phone_number, business, customer)
        
        elif button_id == "view_orders":
            return send_customer_orders(phone_number, business, customer)
        
        elif button_id == "order_issue":
            return send_order_issue_menu(phone_number, business, customer)
        
        elif button_id == "update_details":
            return start_details_update(phone_number, business, customer)
        
        elif button_id.startswith("category_"):
            category_id = button_id.replace("category_", "")
            return send_category_products(phone_number, business, customer, category_id)
        
        elif button_id.startswith("order_"):
            order_id = button_id.replace("order_", "")
            return show_order_details(phone_number, business, customer, order_id)
        
        elif button_id.startswith("issue_order_"):
            order_id = button_id.replace("issue_order_", "")
            return start_issue_reporting(phone_number, business, customer, order_id)
        
        else:
            return send_business_whatsapp_text_message(
                phone_number,
                "Sorry, I didn't understand that option. Please try again.",
                business
            )
            
    except Exception as e:
        logger.error(f"Error handling business button response: {str(e)}")
        return jsonify({"error": "Failed to handle button response"}), 500

def send_categories_menu(phone_number, business, customer):
    """Send interactive menu of categories"""
    try:
        categories = Category.objects(business=business)
        
        if not categories:
            return send_business_whatsapp_text_message(
                phone_number,
                f"Sorry, {business.name} doesn't have any categories set up yet. Please check back later.",
                business
            )
        
        if len(categories) <= 3:
            # Use buttons for 3 or fewer categories
            buttons = []
            for category in categories:
                buttons.append({
                    "text": category.name[:20],  # WhatsApp button limit
                    "id": f"category_{category.id}"
                })
            
            response = send_business_whatsapp_interactive_message(
                phone_number,
                "Browse Categories",
                f"Choose a category to browse products from {business.name}:",
                "Select a category",
                buttons,
                business
            )
        else:
            # Use list for more than 3 categories
            rows = []
            for category in categories:
                rows.append({
                    "id": f"category_{category.id}",
                    "title": category.name[:24],  # WhatsApp title limit
                    "description": category.description[:72] if category.description else "Browse products"
                })
            
            sections = [{"title": "Categories", "rows": rows}]
            
            response = send_business_whatsapp_list_message(
                phone_number,
                "Browse Categories",
                f"Choose a category to browse products from {business.name}:",
                "Select a category",
                "Select Category",
                sections,
                business
            )
        
        save_chat_message(customer, business, 'gpt', "Categories menu displayed", 'interactive')
        return jsonify({"message": "Categories menu sent", "whatsapp_response": response}), 200
        
    except Exception as e:
        logger.error(f"Error sending categories menu: {str(e)}")
        return jsonify({"error": "Failed to send categories menu"}), 500

def send_customer_orders(phone_number, business, customer):
    """Send customer's orders (pending orders first)"""
    try:
        # Get customer's orders for this business, prioritizing pending orders
        orders = Order.objects(customer=customer, business=business).order_by('-created_at')[:10]
        
        if not orders:
            return send_business_whatsapp_text_message(
                phone_number,
                f"You don't have any orders with {business.name} yet. Would you like to browse our products?",
                business
            )
        
        if len(orders) <= 3:
            # Use buttons for 3 or fewer orders
            buttons = []
            for order in orders:
                status_emoji = "🟡" if order.status == "pending" else "🟢" if order.status == "completed" else "🔵"
                buttons.append({
                    "text": f"{status_emoji} {order.order_number}",
                    "id": f"order_{order.id}"
                })
            
            response = send_business_whatsapp_interactive_message(
                phone_number,
                "Your Orders",
                f"Here are your recent orders with {business.name}:",
                "Select an order to view details",
                buttons,
                business
            )
        else:
            # Use list for more than 3 orders
            rows = []
            for order in orders:
                status_emoji = "🟡" if order.status == "pending" else "🟢" if order.status == "completed" else "🔵"
                rows.append({
                    "id": f"order_{order.id}",
                    "title": f"{status_emoji} {order.order_number}",
                    "description": f"Status: {order.status.title()} | Amount: KSH {order.total_amount}"
                })
            
            sections = [{"title": "Orders", "rows": rows}]
            
            response = send_business_whatsapp_list_message(
                phone_number,
                "Your Orders",
                f"Here are your recent orders with {business.name}:",
                "Select an order to view details",
                "Select Order",
                sections,
                business
            )
        
        save_chat_message(customer, business, 'gpt', "Customer orders displayed", 'interactive')
        return jsonify({"message": "Customer orders sent", "whatsapp_response": response}), 200
        
    except Exception as e:
        logger.error(f"Error sending customer orders: {str(e)}")
        return jsonify({"error": "Failed to send customer orders"}), 500

def send_order_issue_menu(phone_number, business, customer):
    """Send menu for reporting order issues"""
    try:
        # Get customer's recent orders for this business
        orders = Order.objects(customer=customer, business=business).order_by('-created_at')[:10]
        
        if not orders:
            return send_business_whatsapp_text_message(
                phone_number,
                f"You don't have any orders with {business.name} to report issues for.",
                business
            )
        
        if len(orders) <= 3:
            # Use buttons for 3 or fewer orders
            buttons = []
            for order in orders:
                buttons.append({
                    "text": f"{order.order_number}",
                    "id": f"issue_order_{order.id}"
                })
            
            response = send_business_whatsapp_interactive_message(
                phone_number,
                "Report Order Issue",
                f"Which order would you like to report an issue for?",
                "Select an order",
                buttons,
                business
            )
        else:
            # Use list for more than 3 orders
            rows = []
            for order in orders:
                rows.append({
                    "id": f"issue_order_{order.id}",
                    "title": order.order_number,
                    "description": f"Status: {order.status.title()} | Amount: KSH {order.total_amount}"
                })
            
            sections = [{"title": "Orders", "rows": rows}]
            
            response = send_business_whatsapp_list_message(
                phone_number,
                "Report Order Issue",
                f"Which order would you like to report an issue for?",
                "Select an order",
                "Select Order",
                sections,
                business
            )
        
        save_chat_message(customer, business, 'gpt', "Order issue menu displayed", 'interactive')
        return jsonify({"message": "Order issue menu sent", "whatsapp_response": response}), 200
        
    except Exception as e:
        logger.error(f"Error sending order issue menu: {str(e)}")
        return jsonify({"error": "Failed to send order issue menu"}), 500

def start_details_update(phone_number, business, customer):
    """Start the process of updating customer details"""
    try:
        # Create or update customer state
        customer_state = CustomerState.objects(phone_number=phone_number, business=business).first()
        if not customer_state:
            customer_state = CustomerState(phone_number=phone_number, business=business)
        
        customer_state.current_step = "awaiting_name"
        customer_state.save()
        
        current_name = customer.name if customer.name else "not set"
        
        response = send_business_whatsapp_text_message(
            phone_number,
            f"Let's update your details. Your current name is: {current_name}\n\nPlease type your new name:",
            business
        )
        
        save_chat_message(customer, business, 'gpt', "Started details update process", 'text')
        return jsonify({"message": "Details update started", "whatsapp_response": response}), 200
        
    except Exception as e:
        logger.error(f"Error starting details update: {str(e)}")
        return jsonify({"error": "Failed to start details update"}), 500

def show_order_details(phone_number, business, customer, order_id):
    """Show details of a specific order"""
    try:
        order = Order.objects(id=order_id, customer=customer, business=business).first()
        
        if not order:
            return send_business_whatsapp_text_message(
                phone_number,
                "Sorry, I couldn't find that order.",
                business
            )
        
        # Build order details message
        details = f"*Order Details*\n\n"
        details += f"Order Number: {order.order_number}\n"
        details += f"Status: {order.status.title()}\n"
        details += f"Payment Status: {order.payment_status.title()}\n"
        details += f"Total Amount: KSH {order.total_amount}\n"
        details += f"Order Date: {order.created_at.strftime('%d %B %Y')}\n\n"
        
        details += "*Items Ordered:*\n"
        for item in order.order_items:
            product_name = item.product.name if item.product else "Product"
            details += f"• {product_name} x{item.quantity} - KSH {item.total_price}\n"
        
        if order.customization_notes:
            details += f"\n*Special Instructions:*\n{order.customization_notes}"
        
        response = send_business_whatsapp_text_message(phone_number, details, business)
        
        save_chat_message(customer, business, 'gpt', "Order details displayed", 'text')
        return jsonify({"message": "Order details sent", "whatsapp_response": response}), 200
        
    except Exception as e:
        logger.error(f"Error showing order details: {str(e)}")
        return jsonify({"error": "Failed to show order details"}), 500

def start_issue_reporting(phone_number, business, customer, order_id):
    """Start the process of reporting an issue for an order"""
    try:
        order = Order.objects(id=order_id, customer=customer, business=business).first()
        
        if not order:
            return send_business_whatsapp_text_message(
                phone_number,
                "Sorry, I couldn't find that order.",
                business
            )
        
        # Create or update customer state
        customer_state = CustomerState.objects(phone_number=phone_number, business=business).first()
        if not customer_state:
            customer_state = CustomerState(phone_number=phone_number, business=business)
        
        customer_state.current_step = "awaiting_issue_description"
        customer_state.awaiting_data = {"order_id": str(order_id)}
        customer_state.save()
        
        response = send_business_whatsapp_text_message(
            phone_number,
            f"Please describe the issue you're experiencing with order {order.order_number}:",
            business
        )
        
        save_chat_message(customer, business, 'gpt', f"Started issue reporting for order {order.order_number}", 'text')
        return jsonify({"message": "Issue reporting started", "whatsapp_response": response}), 200
        
    except Exception as e:
        logger.error(f"Error starting issue reporting: {str(e)}")
        return jsonify({"error": "Failed to start issue reporting"}), 500

def handle_customer_data_input(phone_number, message, business, customer, customer_state):
    """Handle customer data input based on current step"""
    try:
        if customer_state.current_step == "awaiting_name":
            # Update customer name
            customer.name = message.strip()
            customer.save()
            
            # Move to email step
            customer_state.current_step = "awaiting_email"
            customer_state.save()
            
            current_email = customer.email if customer.email else "not set"
            
            response = send_business_whatsapp_text_message(
                phone_number,
                f"Great! Name updated to: {customer.name}\n\nYour current email is: {current_email}\n\nPlease type your new email address:",
                business
            )
            
            return jsonify({"message": "Name updated, requesting email", "whatsapp_response": response}), 200
        
        elif customer_state.current_step == "awaiting_email":
            # Update customer email
            customer.email = message.strip()
            customer.save()
            
            # Clear customer state
            customer_state.current_step = None
            customer_state.save()
            
            response = send_business_whatsapp_text_message(
                phone_number,
                f"Perfect! Your details have been updated:\n\nName: {customer.name}\nEmail: {customer.email}\n\nIs there anything else I can help you with today?",
                business
            )
            
            return jsonify({"message": "Details updated successfully", "whatsapp_response": response}), 200
        
        elif customer_state.current_step == "awaiting_issue_description":
            # Save the issue
            order_id = customer_state.awaiting_data.get("order_id")
            order = Order.objects(id=order_id).first()
            
            if order:
                issue = OrderIssue(
                    customer=customer,
                    business=business,
                    order=order,
                    issue_description=message.strip()
                )
                issue.save()
                
                # Clear customer state
                customer_state.current_step = None
                customer_state.awaiting_data = {}
                customer_state.save()
                
                response = send_business_whatsapp_text_message(
                    phone_number,
                    f"Thank you for reporting the issue with order {order.order_number}. Your issue has been recorded and our team is working on it. You'll receive an update soon.",
                    business
                )
                
                save_chat_message(customer, business, 'customer', message, 'text')
                save_chat_message(customer, business, 'gpt', "Issue reported successfully", 'text')
                
                return jsonify({"message": "Issue reported successfully", "whatsapp_response": response}), 200
            else:
                # Clear customer state and send error
                customer_state.current_step = None
                customer_state.awaiting_data = {}
                customer_state.save()
                
                response = send_business_whatsapp_text_message(
                    phone_number,
                    "Sorry, there was an error processing your issue report. Please try again.",
                    business
                )
                
                return jsonify({"message": "Error processing issue", "whatsapp_response": response}), 200
        
        else:
            # Unknown state, clear it
            customer_state.current_step = None
            customer_state.awaiting_data = {}
            customer_state.save()
            
            return send_business_whatsapp_text_message(
                phone_number,
                "I'm not sure what you're referring to. Please use the menu options to get started.",
                business
            )
            
    except Exception as e:
        logger.error(f"Error handling customer data input: {str(e)}")
        return jsonify({"error": "Failed to handle data input"}), 500

def send_category_products(phone_number, business, customer, category_id):
    """Send products for a specific category"""
    try:
        from bson import ObjectId
        category = Category.objects(id=ObjectId(category_id), business=business).first()
        
        if not category:
            return send_business_whatsapp_text_message(
                phone_number,
                "Sorry, I couldn't find that category.",
                business
            )
        
        products = Product.objects(category=category, business=business, is_active=True)
        
        if not products:
            return send_business_whatsapp_text_message(
                phone_number,
                f"Sorry, there are no products available in the {category.name} category right now.",
                business
            )
        
        # Build products message
        message = f"*{category.name} Products*\n\n"
        for i, product in enumerate(products[:10], 1):  # Limit to 10 products
            message += f"{i}. *{product.name}*\n"
            message += f"   Price: KSH {product.price}\n"
            if product.description:
                message += f"   {product.description[:50]}...\n"
            message += "\n"
        
        if len(products) > 10:
            message += f"... and {len(products) - 10} more products.\n\n"
        
        message += f"To place an order, please contact {business.name} directly or visit our store."
        
        response = send_business_whatsapp_text_message(phone_number, message, business)
        
        save_chat_message(customer, business, 'gpt', f"Products for category {category.name} displayed", 'text')
        return jsonify({"message": "Category products sent", "whatsapp_response": response}), 200
        
    except Exception as e:
        logger.error(f"Error sending category products: {str(e)}")
        return jsonify({"error": "Failed to send category products"}), 500

def save_chat_message(customer, business, sender_type, message_text, message_type='text'):
    """Save a chat message to the database"""
    try:
        # Get or create chat session
        session_id = f"{customer.id}_{business.id}"
        chat_session = ChatSession.objects(session_id=session_id).first()
        
        if not chat_session:
            chat_session = ChatSession(
                customer=customer,
                business=business,
                session_id=session_id
            )
        
        # Add message
        message = ChatMessage(
            sender_type=sender_type,
            message_text=message_text,
            message_type=message_type,
            timestamp=datetime.utcnow()
        )
        
        chat_session.messages.append(message)
        chat_session.save()
        
    except Exception as e:
        logger.error(f"Error saving chat message: {str(e)}")

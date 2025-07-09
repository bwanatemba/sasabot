import os
import logging
from openai import OpenAI
from dotenv import load_dotenv
from models import Business, Product, ProductVariation, Category, Order, Customer, ChatSession, ChatMessage
import re

load_dotenv()
logger = logging.getLogger(__name__)

def initialize_openai_client():
    """Initialize OpenAI client with proper configuration"""
    try:
        # Get API key from environment
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        # Clear any proxy-related environment variables that might interfere
        proxy_env_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        original_proxy_values = {}
        for var in proxy_env_vars:
            if var in os.environ:
                original_proxy_values[var] = os.environ[var]
                logger.debug(f"Temporarily clearing {var}={os.environ[var]}")
                del os.environ[var]
        
        try:
            # Create client with explicit parameters to avoid unexpected kwargs
            client_kwargs = {
                'api_key': api_key
            }
            
            # Explicitly set base_url if needed (optional)
            base_url = os.getenv('OPENAI_BASE_URL')
            if base_url:
                client_kwargs['base_url'] = base_url
            
            # Initialize client with controlled parameters
            try:
                client = OpenAI(**client_kwargs)
                logger.info("OpenAI client initialized successfully")
                return client
            except TypeError as te:
                # Handle case where unexpected parameters are being passed
                logger.warning(f"TypeError during OpenAI client initialization: {str(te)}")
                # Fallback to minimal initialization
                client = OpenAI(api_key=api_key)
                logger.info("OpenAI client initialized with fallback method")
                return client
                
        finally:
            # Restore original proxy environment variables
            for var, value in original_proxy_values.items():
                os.environ[var] = value
                logger.debug(f"Restored {var}={value}")
            
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {str(e)}")
        raise

def process_gpt_interaction(phone_number, message, business_id=None):
    """Process GPT interaction with business context"""
    try:
        client = initialize_openai_client()
        
        # Get or create customer using MongoEngine
        from models import Customer, Business
        customer = Customer.objects(phone_number=phone_number).first()
        if not customer:
            customer = Customer(phone_number=phone_number)
            customer.save()
        
        # Determine business context if not provided
        if not business_id:
            business = Business.objects().first()  # For now, use first business
        else:
            business = Business.objects(id=business_id).first()
        
        if not business:
            from services.messaging_service import send_whatsapp_text_message
            return send_whatsapp_text_message(phone_number, "Sorry, I couldn't find the business information.")
        
        # Get or create chat session using MongoEngine
        from models import ChatSession
        session = ChatSession.objects(
            customer=customer.id,
            business=business.id
        ).first()
        
        if not session:
            session = ChatSession(
                customer=customer.id,
                business=business.id,
                session_id=f"{customer.id}_{business.id}_{phone_number}"
            )
            session.save()
        
        # Save customer message using MongoEngine (embedded in session)
        from models import ChatMessage
        customer_message = ChatMessage(
            sender_type='customer',
            message_text=message
        )
        session.messages.append(customer_message)
        session.save()
        
        # Get business custom instructions
        custom_instructions = business.custom_instructions or "You are a helpful customer service assistant."
        
        # Build context with business information
        business_context = f"""
        Business Name: {business.name}
        Business Description: {business.description}
        Business Category: {business.category}
        Custom Instructions: {custom_instructions}
        """
        
        # Check message intent
        intent = determine_intent(message)
        
        if intent == 'order_tracking':
            return handle_order_tracking(phone_number, message, business.id)
        elif intent == 'product_inquiry':
            return handle_product_inquiry(phone_number, business.id)
        elif intent == 'product_id':
            product_id = extract_product_id(message)
            if product_id:
                return handle_product_details(phone_number, product_id, business.id)
        
        # General GPT response
        response = client.chat.completions.create(
            model="ft:gpt-3.5-turbo-1106:meira-africa-education-solutions::AzJSAPGn",
            messages=[
                {"role": "system", "content": f"{business_context}\n\nYou are a customer service assistant for {business.name}. Use the custom instructions to guide your responses. Keep responses helpful and business-focused."},
                {"role": "user", "content": message}
            ]
        )
        
        gpt_response = response.choices[0].message.content
        
        # Save GPT response using MongoEngine (embedded in session)
        gpt_message = ChatMessage(
            sender_type='gpt',
            message_text=gpt_response
        )
        session.messages.append(gpt_message)
        session.save()
        
        # Send response via WhatsApp
        from services.messaging_service import send_whatsapp_text_message
        send_whatsapp_text_message(phone_number, gpt_response)
        
        return gpt_response
    
    except Exception as e:
        logger.error(f"OpenAI interaction error: {str(e)}")
        from services.messaging_service import send_whatsapp_text_message
        send_whatsapp_text_message(phone_number, "Sorry, I'm having trouble processing your request right now.")
        raise

def determine_intent(message):
    """Determine the intent of the customer message"""
    message_lower = message.lower()
    
    # Order tracking keywords
    order_keywords = ['order', 'tracking', 'track', 'status', 'delivery', 'ord']
    if any(keyword in message_lower for keyword in order_keywords):
        return 'order_tracking'
    
    # Product inquiry keywords
    product_keywords = ['product', 'products', 'service', 'services', 'catalog', 'what do you sell', 'what do you offer']
    if any(keyword in message_lower for keyword in product_keywords):
        return 'product_inquiry'
    
    # Check if message contains product ID pattern
    if re.search(r'\b[A-Z0-9]{4,}\b', message):
        return 'product_id'
    
    return 'general'

def extract_product_id(message):
    """Extract product ID from message"""
    pattern = r'\b([A-Z0-9]{4,})\b'
    match = re.search(pattern, message.upper())
    return match.group(1) if match else None

def handle_order_tracking(phone_number, message, business_id):
    """Handle order tracking requests"""
    from services.messaging_service import send_whatsapp_text_message
    return send_whatsapp_text_message(phone_number, "Kindly enter your order number for follow-up")

def handle_product_inquiry(phone_number, business_id):
    """Handle product/service inquiries"""
    from models import Business, Category
    
    business = Business.objects(id=business_id).first()
    categories = Category.objects(business=business_id)
    
    if not categories:
        from services.messaging_service import send_whatsapp_text_message
        return send_whatsapp_text_message(phone_number, "Sorry, no product categories are available at the moment.")
    
    # Create buttons for categories (max 3 buttons)
    buttons = []
    for i, category in enumerate(categories[:3]):
        buttons.append({
            "text": category.name,
            "id": f"category_{category.id}"
        })
    
    from services.messaging_service import send_whatsapp_interactive_message
    return send_whatsapp_interactive_message(
        phone_number,
        f"{business.name} Products/Services",
        "We offer a wide range of products sorted in different categories. You can select a category below to see the products in each category",
        "Select a category to view its products",
        buttons
    )

def handle_product_details(phone_number, product_id, business_id):
    """Handle product details request"""
    from models import Product
    
    product = Product.objects(product_id=product_id, business=business_id).first()
    
    if not product:
        from services.messaging_service import send_whatsapp_text_message
        return send_whatsapp_text_message(phone_number, f"Sorry, product {product_id} not found.")
    
    # Create product message template
    buttons = [
        {"text": "Buy Now", "id": f"buy_{product.id}"},
        {"text": "View Variations", "id": f"variations_{product.id}"}
    ]
    
    if product.allows_customization:
        buttons.append({"text": "Add Customization", "id": f"customize_{product.id}"})
    
    # Prepare body text
    body = f"{product.name}\n${product.price:.2f}\n{product.description or ''}"
    
    from services.messaging_service import send_whatsapp_interactive_message
    return send_whatsapp_interactive_message(
        phone_number,
        "Product Details",  # Could be product image URL if available
        body,
        "Buy Now, View Variations or Customize",
        buttons
    )

def handle_category_selection(phone_number, category_id):
    """Handle category selection"""
    from models import Product
    
    products = Product.objects(category=category_id, is_active=True)
    
    if not products:
        from services.messaging_service import send_whatsapp_text_message
        return send_whatsapp_text_message(phone_number, "Sorry, no products available in this category.")
    
    # Send list of products with their IDs
    product_list = "Available products:\n\n"
    for product in products:
        product_list += f"ID: {product.product_id}\n"
        product_list += f"Name: {product.name}\n"
        product_list += f"Price: ${product.price:.2f}\n\n"
    
    product_list += "Reply with a product ID to see details and purchase options."
    
    from services.messaging_service import send_whatsapp_text_message
    return send_whatsapp_text_message(phone_number, product_list)

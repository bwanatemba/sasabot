import logging
from models import OnboardingState, Vendor, Business, Customer
from services.messaging_service import send_whatsapp_interactive_message, send_whatsapp_text_message
from werkzeug.security import generate_password_hash

logger = logging.getLogger(__name__)

class OnboardingService:
    
    STEPS = {
        'start': 'welcome',
        'welcome': 'collect_name',
        'collect_name': 'collect_email',
        'collect_email': 'collect_phone',
        'collect_phone': 'collect_business_name',
        'collect_business_name': 'collect_business_description',
        'collect_business_description': 'collect_business_whatsapp',
        'collect_business_whatsapp': 'collect_business_email',
        'collect_business_email': 'collect_business_category',
        'collect_business_category': 'complete_registration',
        'complete_registration': 'finished'
    }
    
    def __init__(self):
        pass
    
    def start_onboarding(self, phone_number):
        """Start the onboarding process"""
        try:
            # Check if user already has an onboarding state
            state = OnboardingState.objects(phone_number=phone_number).first()
            if state:
                state.delete()
            
            # Create new onboarding state
            state = OnboardingState(
                phone_number=phone_number,
                current_step='welcome',
                data={}
            )
            state.save()
            
            # Send welcome message
            buttons = [{"text": "Yes. Let's Go!", "id": "lets_go"}]
            
            return send_whatsapp_interactive_message(
                phone_number,
                "Welcome Aboard Sasabot",
                "Hey there, Welcome aboard! My name is Sasha, your onboarding assistant. I'm here to help get your business set up so we can support your marketing and communication goals. Let's start with a few quick details. Ready?",
                "Select a button to start",
                buttons
            )
            
        except Exception as e:
            logger.error(f"Error starting onboarding for {phone_number}: {str(e)}")
            return send_whatsapp_text_message(phone_number, "Sorry, there was an error starting your onboarding. Please try again later.")
    
    def handle_onboarding_response(self, phone_number, message=None, button_id=None):
        """Handle user responses during onboarding"""
        try:
            state = OnboardingState.query.filter_by(phone_number=phone_number).first()
            if not state:
                return send_whatsapp_text_message(phone_number, "Please start onboarding by typing 'hello' or 'hi'.")
            
            current_step = state.current_step
            data = state.data or {}
            
            # Handle button responses
            if button_id:
                if button_id == "lets_go" and current_step == "welcome":
                    return self._move_to_next_step(state, "Great! First, I'd love to know who I'm speaking with. What's your name?")
                elif button_id == "complete_registration" and current_step == "complete_registration":
                    return self._complete_registration(state)
            
            # Handle text responses
            elif message:
                if current_step == "collect_name":
                    data['vendor_name'] = message
                    return self._move_to_next_step(state, f"Nice to meet you, {message}! What's the best email address to reach you at?", data)
                
                elif current_step == "collect_email":
                    data['vendor_email'] = message
                    return self._move_to_next_step(state, "And could I have your phone number, in case we need to get in touch?", data)
                
                elif current_step == "collect_phone":
                    data['vendor_phone'] = message
                    return self._move_to_next_step(state, "Awesome, now let's talk about your business. What's your business called?", data)
                
                elif current_step == "collect_business_name":
                    data['business_name'] = message
                    return self._move_to_next_step(state, "Got it! Can you give me a quick description of what your business does?", data)
                
                elif current_step == "collect_business_description":
                    data['business_description'] = message
                    return self._move_to_next_step(state, "Nice, that helps us tailor our support better. What WhatsApp number does your business use to connect with customers?", data)
                
                elif current_step == "collect_business_whatsapp":
                    data['business_whatsapp'] = message
                    return self._move_to_next_step(state, "And do you use a different email address for business communication? If yes, please drop it below. Type N/A If same as personal or you dont have a business email", data)
                
                elif current_step == "collect_business_email":
                    data['business_email'] = message if message.upper() != "N/A" else None
                    return self._send_category_selection(state, data)
                
                elif current_step == "collect_business_category":
                    data['business_category'] = message
                    return self._send_completion_message(state, data)
            
            return send_whatsapp_text_message(phone_number, "I didn't understand that. Please follow the onboarding steps.")
            
        except Exception as e:
            logger.error(f"Error handling onboarding response for {phone_number}: {str(e)}")
            return send_whatsapp_text_message(phone_number, "Sorry, there was an error processing your response. Please try again.")
    
    def _move_to_next_step(self, state, message, data=None):
        """Move to the next step in onboarding"""
        next_step = self.STEPS.get(state.current_step)
        if next_step:
            state.current_step = next_step
            if data:
                state.data = data
            state.save()
        
        return send_whatsapp_text_message(state.phone_number, message)
    
    def _send_category_selection(self, state, data):
        """Send business category selection"""
        state.current_step = "collect_business_category"
        state.data = data
        state.save()
        
        buttons = [
            {"text": "Electronics", "id": "electronics"},
            {"text": "Food", "id": "food"},
            {"text": "Technology", "id": "technology"}
        ]
        
        return send_whatsapp_interactive_message(
            state.phone_number,
            "Your Business category",
            "What category does your business fall under?",
            "Select a button that represents your business category",
            buttons
        )
    
    def _send_completion_message(self, state, data):
        """Send completion message"""
        state.current_step = "complete_registration"
        state.data = data
        state.save()
        
        buttons = [{"text": "Complete registration", "id": "complete_registration"}]
        
        return send_whatsapp_interactive_message(
            state.phone_number,
            "Complete Sasabot Onboarding",
            "That's everything I need for now!",
            "Click the button to complete registration",
            buttons
        )
    
    def _complete_registration(self, state):
        """Complete the registration process"""
        try:
            data = state.data
            
            # Generate password
            password = Vendor.generate_password()
            
            # Create vendor
            vendor = Vendor(
                name=data.get('vendor_name'),
                email=data.get('vendor_email'),
                phone_number=data.get('vendor_phone', state.phone_number),
                password=generate_password_hash(password)
            )
            vendor.save()
            
            # Create business
            business = Business(
                name=data.get('business_name'),
                description=data.get('business_description'),
                category=data.get('business_category'),
                email=data.get('business_email'),
                whatsapp_number=data.get('business_whatsapp'),
                vendor=vendor
            )
            business.save()
            
            # Create customer record
            customer = Customer.objects(phone_number=state.phone_number).first()
            if not customer:
                customer = Customer(phone_number=state.phone_number)
                customer.save()
            
            # Delete onboarding state
            state.delete()
            
            # Send password message
            buttons = [{"text": "Dashboard Login", "id": "dashboard_login"}]
            
            return send_whatsapp_interactive_message(
                state.phone_number,
                "Your Registration to SasaBot is complete!",
                f"You are successfully registered to SasaBot. You can login to the vendor dashboard to view your business profile, add products and more. Your password is {password}. Keep it safe and do not send it to anybody. You can change your password via your dashboard profile.",
                "Select the button to login to your dashboard",
                buttons
            )
            
        except Exception as e:
            logger.error(f"Error completing registration: {str(e)}")
            return send_whatsapp_text_message(state.phone_number, "Sorry, there was an error completing your registration. Please try again.")

# Create global instance
onboarding_service = OnboardingService()

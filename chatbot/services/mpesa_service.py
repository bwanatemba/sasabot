import os
import logging
import requests
import base64
from datetime import datetime
from models import Order, OrderItem, Customer
from services.messaging_service import send_whatsapp_text_message
import secrets

logger = logging.getLogger(__name__)

class MpesaService:
    def __init__(self):
        self.consumer_key = os.getenv('MPESA_CONSUMER_KEY')
        self.consumer_secret = os.getenv('MPESA_CONSUMER_SECRET')
        self.business_shortcode = os.getenv('MPESA_BUSINESS_SHORTCODE')
        self.passkey = os.getenv('MPESA_PASSKEY')
        self.callback_url = os.getenv('MPESA_CALLBACK_URL', 'https://your-domain.com/mpesa/callback')
        self.base_url = 'https://sandbox.safaricom.co.ke'  # Change to production URL for live
        
    def get_access_token(self):
        """Get OAuth access token from Mpesa"""
        try:
            url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"
            
            # Create authorization header
            credentials = f"{self.consumer_key}:{self.consumer_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {encoded_credentials}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json().get('access_token')
            
        except Exception as e:
            logger.error(f"Error getting Mpesa access token: {str(e)}")
            raise
    
    def generate_password(self):
        """Generate password for STK push"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_string = f"{self.business_shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(password_string.encode()).decode()
        return password, timestamp
    
    def initiate_stk_push(self, phone_number, amount, order_id, account_reference="SasaBot"):
        """Initiate STK push payment"""
        try:
            access_token = self.get_access_token()
            password, timestamp = self.generate_password()
            
            # Format phone number
            if phone_number.startswith('0'):
                phone_number = '254' + phone_number[1:]
            elif phone_number.startswith('+254'):
                phone_number = phone_number[1:]
            elif not phone_number.startswith('254'):
                phone_number = '254' + phone_number
            
            url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "BusinessShortCode": self.business_shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(amount),
                "PartyA": phone_number,
                "PartyB": self.business_shortcode,
                "PhoneNumber": phone_number,
                "CallBackURL": self.callback_url,
                "AccountReference": account_reference,
                "TransactionDesc": f"Payment for order {order_id}"
            }
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('ResponseCode') == '0':
                return {
                    'success': True,
                    'checkout_request_id': result.get('CheckoutRequestID'),
                    'merchant_request_id': result.get('MerchantRequestID'),
                    'message': 'STK push sent successfully'
                }
            else:
                return {
                    'success': False,
                    'message': result.get('ResponseDescription', 'Payment failed')
                }
                
        except Exception as e:
            logger.error(f"Error initiating STK push: {str(e)}")
            return {
                'success': False,
                'message': 'Payment service temporarily unavailable'
            }
    
    def process_callback(self, callback_data):
        """Process Mpesa callback"""
        try:
            stk_callback = callback_data.get('Body', {}).get('stkCallback', {})
            result_code = stk_callback.get('ResultCode')
            checkout_request_id = stk_callback.get('CheckoutRequestID')
            
            if result_code == 0:
                # Payment successful
                callback_metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
                
                transaction_data = {}
                for item in callback_metadata:
                    name = item.get('Name')
                    value = item.get('Value')
                    transaction_data[name] = value
                
                # Update order in database
                self._update_order_payment_status(
                    checkout_request_id,
                    'paid',
                    transaction_data.get('MpesaReceiptNumber'),
                    transaction_data.get('Amount'),
                    transaction_data.get('PhoneNumber')
                )
                
                return {'success': True, 'message': 'Payment processed successfully'}
            else:
                # Payment failed
                self._update_order_payment_status(checkout_request_id, 'failed')
                return {'success': False, 'message': 'Payment failed'}
                
        except Exception as e:
            logger.error(f"Error processing Mpesa callback: {str(e)}")
            return {'success': False, 'message': 'Error processing payment callback'}
    
    def _update_order_payment_status(self, checkout_request_id, status, transaction_id=None, amount=None, phone_number=None):
        """Update order payment status"""
        try:
            # Note: You'll need to store checkout_request_id with the order when initiating payment
            # For now, we'll update based on the most recent pending order for the phone number
            if phone_number:
                # Format phone number to match database
                if phone_number.startswith('254'):
                    phone_number = '+' + phone_number
                
                customer = Customer.objects(phone_number=phone_number).first()
                if customer:
                    order = Order.objects(
                        customer=customer,
                        payment_status='pending'
                    ).order_by('-created_at').first()
                    
                    if order:
                        order.payment_status = status
                        if status == 'paid':
                            order.status = 'paid'
                            order.mpesa_transaction_id = transaction_id
                        elif status == 'failed':
                            order.status = 'cancelled'
                        
                        order.save()
                        
                        # Send confirmation message
                        if status == 'paid':
                            message = f"Payment successful! Your order {order.order_number} has been confirmed. Transaction ID: {transaction_id}"
                        else:
                            message = f"Payment failed for order {order.order_number}. Please try again or contact support."
                        
                        send_whatsapp_text_message(phone_number, message)
                        
        except Exception as e:
            logger.error(f"Error updating order payment status: {str(e)}")

def create_order_and_initiate_payment(phone_number, product_id, business_id, customization_notes=None, variation_id=None):
    """Create order and initiate Mpesa payment"""
    try:
        from models import Product, ProductVariation, Business
        
        # Get customer
        customer = Customer.objects(phone_number=phone_number).first()
        if not customer:
            customer = Customer(phone_number=phone_number)
            customer.save()
        
        # Get product
        product = Product.objects(id=product_id).first()
        if not product:
            return {"success": False, "message": "Product not found"}
        
        # Get business
        business = Business.objects(id=business_id).first()
        if not business:
            return {"success": False, "message": "Business not found"}
        
        # Determine price
        if variation_id:
            variation = ProductVariation.objects(id=variation_id, product=product).first()
            if variation:
                unit_price = variation.price
            else:
                unit_price = product.price
        else:
            unit_price = product.price
        
        # Create order with embedded order items
        order_item = OrderItem(
            product=product,
            variation_id=str(variation.id) if variation_id and ProductVariation.objects(id=variation_id, product=product).first() else None,
            quantity=1,
            unit_price=unit_price,
            total_price=unit_price
        )
        
        order = Order(
            order_number=Order.generate_order_number(),
            customer=customer,
            business=business,
            total_amount=unit_price,
            customization_notes=customization_notes,
            order_items=[order_item]
        )
        order.save()
        
        # Initiate Mpesa payment
        mpesa_service = MpesaService()
        payment_result = mpesa_service.initiate_stk_push(
            phone_number, 
            unit_price, 
            order.order_number,
            f"Order {order.order_number}"
        )
        
        if payment_result['success']:
            send_whatsapp_text_message(
                phone_number, 
                f"Please complete payment of KES {unit_price:.2f} for your order {order.order_number}. Check your phone for the Mpesa prompt."
            )
        else:
            order.status = 'cancelled'
            order.payment_status = 'failed'
            order.save()
            
            send_whatsapp_text_message(
                phone_number,
                f"Sorry, payment could not be initiated. Please try again later. Error: {payment_result['message']}"
            )
        
        return payment_result
        
    except Exception as e:
        logger.error(f"Error creating order and initiating payment: {str(e)}")
        return {"success": False, "message": "Error processing order"}

# Create global instance
mpesa_service = MpesaService()

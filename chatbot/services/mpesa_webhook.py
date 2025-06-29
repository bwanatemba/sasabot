from config.firebase_config import db
from services.subscription_service import calculate_end_date
from services.messaging_service import send_whatsapp_message
from firebase_admin import firestore
from flask import jsonify
import logging
from config.mpesa_config import query_stk_push

logger = logging.getLogger(__name__)

def process_webhook(data):
    try:
        logger.info(f"Received M-Pesa webhook data: {data}")  # Add logging
        
        # Validate webhook data structure
        if not data:
            logger.error("Empty webhook data received")
            return jsonify({"error": "Empty webhook data"}), 400
            
        # Handle both STK callback and C2B notification formats
        if 'Body' in data:
            # STK Push callback
            body = data['Body']
            if 'stkCallback' not in body:
                logger.error("Missing stkCallback in webhook data")
                return jsonify({"error": "Invalid webhook format"}), 400
                
            stkCallback = body['stkCallback']
            result_code = stkCallback.get('ResultCode')
            
            if result_code is None:
                logger.error("Missing ResultCode in webhook data")
                return jsonify({"error": "Missing ResultCode"}), 400
                
            if result_code != 0:
                logger.warning(f"Payment failed: {stkCallback.get('ResultDesc')}")
                return jsonify({"message": "Payment failed", "reason": stkCallback.get('ResultDesc')}), 200
                
            callback_metadata = stkCallback.get('CallbackMetadata', {})
            if not callback_metadata or 'Item' not in callback_metadata:
                logger.error("Missing CallbackMetadata in successful transaction")
                return jsonify({"error": "Invalid success callback format"}), 400
                
            items = callback_metadata['Item']
            
        else:
            # C2B notification
            logger.error("Unsupported webhook format")
            return jsonify({"error": "Unsupported webhook format"}), 400
            
        # Extract payment details
        try:
            phone_number = next((item['Value'] for item in items if item['Name'] == 'PhoneNumber'), None)
            amount = next((item['Value'] for item in items if item['Name'] == 'Amount'), None)
            transaction_id = next((item['Value'] for item in items if item['Name'] == 'MpesaReceiptNumber'), None)
            
            if not all([phone_number, amount, transaction_id]):
                logger.error("Missing required payment details")
                return jsonify({"error": "Missing payment details"}), 400
                
            # Format phone number
            phone_number = str(phone_number)
            if not phone_number.startswith('254'):
                phone_number = '254' + phone_number.lstrip('0')
                
            # Process the payment
            if amount in [10, 50]:
                subscription_end_date = calculate_end_date(amount)
                
                # Store transaction in Firestore
                try:
                    db.collection('Transactions').document(transaction_id).set({
                        'phone_number': phone_number,
                        'amount': amount,
                        'transaction_id': transaction_id,
                        'timestamp': firestore.SERVER_TIMESTAMP,
                        'status': 'completed'
                    })
                    
                    db.collection('Subscribers').document(phone_number).set({
                        'phone_number': phone_number,
                        'payment_plan': 'Quarterly' if amount == 10 else 'Annual',
                        'subscription_start_date': firestore.SERVER_TIMESTAMP,
                        'subscription_end_date': subscription_end_date,
                        'status': 'active',
                        'last_transaction_id': transaction_id
                    }, merge=True)
                    
                except Exception as e:
                    logger.error(f"Database error: {str(e)}")
                    return jsonify({"error": "Database error"}), 500
                    
                # Send confirmation message
                try:
                    send_whatsapp_message(
                        phone_number,
                        f"Thank you for your payment of KES {amount}! Your subscription is now active until {subscription_end_date.strftime('%Y-%m-%d')}."
                    )
                except Exception as e:
                    logger.error(f"Failed to send confirmation message: {str(e)}")
                    # Continue even if message fails
                    
                return jsonify({"message": "Payment processed successfully"}), 200
                
            else:
                logger.error(f"Invalid payment amount: {amount}")
                return jsonify({"error": "Invalid payment amount"}), 400
                
        except Exception as e:
            logger.error(f"Error processing payment details: {str(e)}")
            return jsonify({"error": "Failed to process payment details"}), 400
            
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

def check_payment_status(checkout_request_id):
    response = query_stk_push(checkout_request_id)
    if 'ResultCode' in response:
        if response['ResultCode'] == 0:
            return True, "Payment successful"
        else:
            return False, response.get('ResultDesc', 'Payment failed')
    else:
        return False, "Unable to query payment status"


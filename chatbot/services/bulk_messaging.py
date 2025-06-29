import csv
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError as e:
    PANDAS_AVAILABLE = False
    print(f"Warning: pandas import failed: {e}")
import logging
from flask import jsonify
from models import Customer, ChatSession, Business, Vendor, db
from services.messaging_service import send_whatsapp_text_message, send_whatsapp_interactive_message
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

class BulkMessagingService:
    
    @staticmethod
    def send_bulk_message_to_customers(business_id, message, customer_filter=None, vendor_id=None):
        """
        Send bulk message to customers based on filters
        
        Args:
            business_id: ID of the business sending the message
            message: The message to send
            customer_filter: Dict with filter criteria
            vendor_id: ID of vendor (for permission checking)
        """
        try:
            # Verify permissions
            if vendor_id:
                business = Business.query.filter_by(id=business_id, vendor_id=vendor_id).first()
                if not business:
                    return {"error": "Business not found or access denied"}
            else:
                business = Business.query.get(business_id)
                if not business:
                    return {"error": "Business not found"}
            
            # Get customers based on filter
            customers = BulkMessagingService._get_filtered_customers(business_id, customer_filter)
            
            sent_count = 0
            failed_count = 0
            failed_numbers = []
            
            for customer in customers:
                try:
                    send_whatsapp_text_message(customer.phone_number, message)
                    sent_count += 1
                    logger.info(f"Message sent to {customer.phone_number}")
                except Exception as e:
                    logger.error(f"Failed to send message to {customer.phone_number}: {str(e)}")
                    failed_count += 1
                    failed_numbers.append(customer.phone_number)
            
            # Log the bulk message activity
            BulkMessagingService._log_bulk_message(business_id, message, sent_count, failed_count)
            
            return {
                "success": True,
                "sent": sent_count,
                "failed": failed_count,
                "total": len(customers),
                "failed_numbers": failed_numbers
            }
            
        except Exception as e:
            logger.error(f"Error in bulk messaging: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def send_promotional_message(business_id, header, body, footer, buttons=None, customer_filter=None, vendor_id=None):
        """
        Send interactive promotional message to customers
        """
        try:
            # Verify permissions
            if vendor_id:
                business = Business.query.filter_by(id=business_id, vendor_id=vendor_id).first()
                if not business:
                    return {"error": "Business not found or access denied"}
            else:
                business = Business.query.get(business_id)
                if not business:
                    return {"error": "Business not found"}
            
            # Get customers based on filter
            customers = BulkMessagingService._get_filtered_customers(business_id, customer_filter)
            
            sent_count = 0
            failed_count = 0
            failed_numbers = []
            
            for customer in customers:
                try:
                    if buttons:
                        send_whatsapp_interactive_message(
                            customer.phone_number, header, body, footer, buttons
                        )
                    else:
                        message = f"{header}\n\n{body}\n\n{footer}"
                        send_whatsapp_text_message(customer.phone_number, message)
                    
                    sent_count += 1
                    logger.info(f"Promotional message sent to {customer.phone_number}")
                except Exception as e:
                    logger.error(f"Failed to send promotional message to {customer.phone_number}: {str(e)}")
                    failed_count += 1
                    failed_numbers.append(customer.phone_number)
            
            # Log the promotional campaign
            message_text = f"PROMO: {header} - {body}"
            BulkMessagingService._log_bulk_message(business_id, message_text, sent_count, failed_count)
            
            return {
                "success": True,
                "sent": sent_count,
                "failed": failed_count,
                "total": len(customers),
                "failed_numbers": failed_numbers
            }
            
        except Exception as e:
            logger.error(f"Error in promotional messaging: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def _get_filtered_customers(business_id, customer_filter=None):
        """Get customers based on filter criteria"""
        try:
            # Base query - customers who have chatted with this business
            chat_sessions = ChatSession.query.filter_by(business_id=business_id).all()
            customer_ids = list(set([session.customer_id for session in chat_sessions]))
            
            query = Customer.query.filter(Customer.id.in_(customer_ids))
            
            if customer_filter:
                # Filter by date range
                if customer_filter.get('start_date'):
                    start_date = datetime.strptime(customer_filter['start_date'], '%Y-%m-%d')
                    query = query.filter(Customer.created_at >= start_date)
                
                if customer_filter.get('end_date'):
                    end_date = datetime.strptime(customer_filter['end_date'], '%Y-%m-%d')
                    end_date = end_date.replace(hour=23, minute=59, second=59)
                    query = query.filter(Customer.created_at <= end_date)
                
                # Filter by specific phone numbers
                if customer_filter.get('phone_numbers'):
                    phone_list = customer_filter['phone_numbers']
                    if isinstance(phone_list, str):
                        phone_list = [p.strip() for p in phone_list.split(',')]
                    query = query.filter(Customer.phone_number.in_(phone_list))
                
                # Filter by activity (customers who chatted in last N days)
                if customer_filter.get('active_days'):
                    days_ago = datetime.utcnow() - timedelta(days=int(customer_filter['active_days']))
                    active_sessions = ChatSession.query.filter(
                        ChatSession.business_id == business_id,
                        ChatSession.created_at >= days_ago
                    ).all()
                    active_customer_ids = list(set([session.customer_id for session in active_sessions]))
                    query = query.filter(Customer.id.in_(active_customer_ids))
            
            return query.all()
            
        except Exception as e:
            logger.error(f"Error filtering customers: {str(e)}")
            return []
    
    @staticmethod
    def import_customers_from_csv(business_id, csv_file_path, vendor_id=None):
        """Import customers from CSV file"""
        try:
            # Verify permissions
            if vendor_id:
                business = Business.query.filter_by(id=business_id, vendor_id=vendor_id).first()
                if not business:
                    return {"error": "Business not found or access denied"}
            
            imported_count = 0
            skipped_count = 0
            errors = []
            
            if not PANDAS_AVAILABLE:
                return {"error": "CSV processing is not available due to missing dependencies"}
            
            df = pd.read_csv(csv_file_path)
            
            # Expected columns: phone_number, name (optional), email (optional)
            if 'phone_number' not in df.columns:
                return {"error": "CSV must contain 'phone_number' column"}
            
            for index, row in df.iterrows():
                try:
                    phone_number = str(row['phone_number']).strip()
                    if not phone_number:
                        skipped_count += 1
                        continue
                    
                    # Check if customer already exists
                    existing_customer = Customer.query.filter_by(phone_number=phone_number).first()
                    if existing_customer:
                        skipped_count += 1
                        continue
                    
                    # Create new customer
                    customer = Customer(
                        phone_number=phone_number,
                        name=row.get('name', '').strip() if 'name' in row else None,
                        email=row.get('email', '').strip() if 'email' in row else None
                    )
                    
                    db.session.add(customer)
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
                    skipped_count += 1
            
            db.session.commit()
            
            return {
                "success": True,
                "imported": imported_count,
                "skipped": skipped_count,
                "errors": errors
            }
            
        except Exception as e:
            logger.error(f"Error importing customers from CSV: {str(e)}")
            db.session.rollback()
            return {"error": str(e)}
    
    @staticmethod
    def export_customers_to_csv(business_id, vendor_id=None):
        """Export customers to CSV file"""
        try:
            # Verify permissions
            if vendor_id:
                business = Business.query.filter_by(id=business_id, vendor_id=vendor_id).first()
                if not business:
                    return {"error": "Business not found or access denied"}
            
            # Get customers for this business
            chat_sessions = ChatSession.query.filter_by(business_id=business_id).all()
            customer_ids = list(set([session.customer_id for session in chat_sessions]))
            customers = Customer.query.filter(Customer.id.in_(customer_ids)).all()
            
            # Create CSV data
            csv_data = []
            for customer in customers:
                # Get chat statistics
                customer_sessions = ChatSession.query.filter_by(
                    business_id=business_id, 
                    customer_id=customer.id
                ).count()
                
                csv_data.append({
                    'phone_number': customer.phone_number,
                    'name': customer.name or '',
                    'email': customer.email or '',
                    'created_at': customer.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'chat_sessions': customer_sessions
                })
            
            # Create CSV file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"customers_{business_id}_{timestamp}.csv"
            filepath = os.path.join('static', 'exports', filename)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            if not PANDAS_AVAILABLE:
                return {"error": "CSV export is not available due to missing dependencies"}
            
            df = pd.DataFrame(csv_data)
            df.to_csv(filepath, index=False)
            
            return {
                "success": True,
                "filename": filename,
                "filepath": filepath,
                "count": len(customers)
            }
            
        except Exception as e:
            logger.error(f"Error exporting customers to CSV: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def _log_bulk_message(business_id, message, sent_count, failed_count):
        """Log bulk message activity"""
        try:
            # In a real implementation, you might want to create a BulkMessageLog model
            # For now, just log to file
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "business_id": business_id,
                "message": message[:100] + "..." if len(message) > 100 else message,
                "sent_count": sent_count,
                "failed_count": failed_count
            }
            logger.info(f"Bulk message log: {log_entry}")
            
        except Exception as e:
            logger.error(f"Error logging bulk message: {str(e)}")
    
    @staticmethod
    def get_messaging_analytics(business_id, days=30, vendor_id=None):
        """Get messaging analytics for a business"""
        try:
            # Verify permissions
            if vendor_id:
                business = Business.query.filter_by(id=business_id, vendor_id=vendor_id).first()
                if not business:
                    return {"error": "Business not found or access denied"}
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get chat sessions count
            total_sessions = ChatSession.query.filter_by(business_id=business_id).count()
            recent_sessions = ChatSession.query.filter(
                ChatSession.business_id == business_id,
                ChatSession.created_at >= start_date
            ).count()
            
            # Get unique customers count
            all_sessions = ChatSession.query.filter_by(business_id=business_id).all()
            unique_customers = len(set([session.customer_id for session in all_sessions]))
            
            recent_session_customers = ChatSession.query.filter(
                ChatSession.business_id == business_id,
                ChatSession.created_at >= start_date
            ).all()
            recent_unique_customers = len(set([session.customer_id for session in recent_session_customers]))
            
            return {
                "success": True,
                "analytics": {
                    "total_chat_sessions": total_sessions,
                    "recent_chat_sessions": recent_sessions,
                    "total_unique_customers": unique_customers,
                    "recent_unique_customers": recent_unique_customers,
                    "period_days": days
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting messaging analytics: {str(e)}")
            return {"error": str(e)}

# Convenience functions for easy import
def send_bulk_message(business_id, message, customer_filter=None, vendor_id=None):
    return BulkMessagingService.send_bulk_message_to_customers(business_id, message, customer_filter, vendor_id)

def send_promotional_message(business_id, header, body, footer, buttons=None, customer_filter=None, vendor_id=None):
    return BulkMessagingService.send_promotional_message(business_id, header, body, footer, buttons, customer_filter, vendor_id)

def import_customers_csv(business_id, csv_file_path, vendor_id=None):
    return BulkMessagingService.import_customers_from_csv(business_id, csv_file_path, vendor_id)

def export_customers_csv(business_id, vendor_id=None):
    return BulkMessagingService.export_customers_to_csv(business_id, vendor_id)

def get_messaging_analytics(business_id, days=30, vendor_id=None):
    return BulkMessagingService.get_messaging_analytics(business_id, days, vendor_id)

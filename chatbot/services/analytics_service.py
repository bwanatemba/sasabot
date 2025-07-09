import logging
from flask import jsonify
from datetime import datetime, timedelta
from mongoengine import Q
import json

# Import models at module level to avoid repeated imports
try:
    from models import Business, Vendor, Customer, Order, ChatSession, ChatMessage, Product, Category
except ImportError:
    # Fallback import if models are in a different location
    try:
        from models.mongodb_models import Business, Vendor, Customer, Order, ChatSession, ChatMessage, Product, Category
    except ImportError as e:
        print(f"Failed to import models: {e}")
        # Set to None to handle in functions
        Business = Vendor = Customer = Order = ChatSession = ChatMessage = Product = Category = None

logger = logging.getLogger(__name__)

class AnalyticsService:
    
    @staticmethod
    def get_business_analytics(business_id, days=30, vendor_id=None):
        """Get comprehensive analytics for a business"""
        try:
            # Verify permissions
            if vendor_id:
                business = Business.objects(Q(id=business_id) & Q(vendor=vendor_id)).first()
                if not business:
                    return {"error": "Business not found or access denied"}
            else:
                business = Business.objects(id=business_id).first()
                if not business:
                    return {"error": "Business not found"}
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Customer Analytics
            customer_analytics = AnalyticsService._get_customer_analytics(business_id, start_date)
            
            # Order Analytics
            order_analytics = AnalyticsService._get_order_analytics(business_id, start_date)
            
            # Product Analytics
            product_analytics = AnalyticsService._get_product_analytics(business_id, start_date)
            
            # Chat Analytics
            chat_analytics = AnalyticsService._get_chat_analytics(business_id, start_date)
            
            # Revenue Analytics
            revenue_analytics = AnalyticsService._get_revenue_analytics(business_id, start_date)
            
            return {
                "success": True,
                "business_name": business.name,
                "period_days": days,
                "start_date": start_date.isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "customer_analytics": customer_analytics,
                "order_analytics": order_analytics,
                "product_analytics": product_analytics,
                "chat_analytics": chat_analytics,
                "revenue_analytics": revenue_analytics
            }
            
        except Exception as e:
            logger.error(f"Error getting business analytics: {str(e)}")
            return {
                "error": str(e),
                "success": False,
                "customer_analytics": {
                    "total_customers": 0,
                    "recent_customers": 0,
                    "returning_customers": 0,
                    "customer_growth": 0
                },
                "order_analytics": {
                    "total_orders": 0,
                    "recent_orders": 0,
                    "paid_orders": 0,
                    "pending_orders": 0,
                    "cancelled_orders": 0,
                    "average_order_value": 0.0,
                    "conversion_rate": 0.0
                },
                "product_analytics": {
                    "total_products": 0,
                    "best_sellers": []
                },
                "chat_analytics": {
                    "total_chat_sessions": 0,
                    "recent_chat_sessions": 0,
                    "total_messages": 0,
                    "recent_messages": 0,
                    "average_messages_per_session": 0.0
                },
                "revenue_analytics": {
                    "total_revenue": 0.0,
                    "recent_revenue": 0.0,
                    "daily_revenue": []
                }
            }
    
    @staticmethod
    def get_vendor_analytics(vendor_id, days=30):
        """Get analytics across all businesses for a vendor"""
        try:
            vendor = Vendor.objects(id=vendor_id).first()
            if not vendor:
                return {"error": "Vendor not found"}
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get all businesses for this vendor
            businesses = Business.objects(Q(vendor=vendor_id) & Q(is_active=True))
            business_ids = [str(b.id) for b in businesses]
            
            if not business_ids:
                return {
                    "success": True,
                    "vendor_name": vendor.name,
                    "businesses_count": 0,
                    "message": "No active businesses found"
                }
            
            # Aggregate analytics across all businesses
            total_customers_list = ChatSession.objects(business__in=business_ids).distinct('customer')
            total_customers_qs = len(total_customers_list) if total_customers_list else 0
            
            recent_customers_list = ChatSession.objects(
                Q(business__in=business_ids) & Q(created_at__gte=start_date)
            ).distinct('customer')
            recent_customers_qs = len(recent_customers_list) if recent_customers_list else 0
            
            total_orders_qs = Order.objects(business__in=business_ids).count()
            recent_orders_qs = Order.objects(
                Q(business__in=business_ids) & Q(created_at__gte=start_date)
            ).count()
            
            # Convert QuerySet/cursor results to integers safely
            total_customers = int(total_customers_qs) if total_customers_qs is not None else 0
            recent_customers = int(recent_customers_qs) if recent_customers_qs is not None else 0
            total_orders = int(total_orders_qs) if total_orders_qs is not None else 0
            recent_orders = int(recent_orders_qs) if recent_orders_qs is not None else 0

            # Calculate total revenue and count paid orders
            paid_orders_queryset = Order.objects(
                Q(business__in=business_ids) & Q(payment_status='paid')
            ).only('total_amount')
            total_revenue = sum(order.total_amount for order in paid_orders_queryset)
            paid_orders_count_qs = Order.objects(
                Q(business__in=business_ids) & Q(payment_status='paid')
            ).count()
            paid_orders_count = int(paid_orders_count_qs) if paid_orders_count_qs is not None else 0
            
            recent_paid_orders = Order.objects(
                Q(business__in=business_ids) & Q(payment_status='paid') & Q(created_at__gte=start_date)
            ).only('total_amount')
            recent_revenue = sum(order.total_amount for order in recent_paid_orders)
            
            # Business performance breakdown
            business_performance = []
            for business in businesses:
                business_analytics = AnalyticsService.get_business_analytics(business.id, days)
                if business_analytics.get('success'):
                    business_performance.append({
                        "business_id": business.id,
                        "business_name": business.name,
                        "customers": business_analytics.get('customer_analytics', {}).get('total_customers', 0),
                        "orders": business_analytics.get('order_analytics', {}).get('total_orders', 0),
                        "revenue": business_analytics.get('revenue_analytics', {}).get('total_revenue', 0)
                    })
            
            return {
                "success": True,
                "vendor_name": vendor.name,
                "period_days": days,
                "businesses_count": len(businesses),
                "summary": {
                    "total_customers": total_customers,
                    "recent_customers": recent_customers,
                    "total_orders": total_orders,
                    "recent_orders": recent_orders,
                    "total_revenue": float(total_revenue) if total_revenue is not None else 0.0,
                    "recent_revenue": float(recent_revenue) if recent_revenue is not None else 0.0
                },
                "business_performance": business_performance
            }
            
        except Exception as e:
            logger.error(f"Error getting vendor analytics: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def get_admin_analytics(days=30):
        """Get system-wide analytics for admins"""
        try:
            # Validate days parameter
            if not isinstance(days, int) or days < 1:
                days = 30
                
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Initialize all variables with defaults to prevent NameError
            total_vendors = recent_vendors = 0
            total_businesses = recent_businesses = 0
            total_customers = recent_customers = 0
            total_orders = recent_orders = paid_orders = 0
            total_revenue = recent_revenue = 0
            total_chat_sessions = recent_chat_sessions = 0
            top_businesses_list = []
            
            # Check if models are available
            if any(model is None for model in [Business, Vendor, Customer, Order, ChatSession]):
                return {"error": "Database models not available"}
            
            # Vendor Analytics
            try:
                # Test database connection first
                test_count = Vendor.objects.count()  # This will fail if DB is not connected
                
                total_vendors_qs = Vendor.objects(is_active=True).count()
                recent_vendors_qs = Vendor.objects(
                    Q(is_active=True) & Q(created_at__gte=start_date)
                ).count()
                
                # Convert QuerySet/cursor results to integers safely
                total_vendors = int(total_vendors_qs) if total_vendors_qs is not None else 0
                recent_vendors = int(recent_vendors_qs) if recent_vendors_qs is not None else 0
                    
            except Exception as e:
                logger.error(f"Error getting vendor analytics: {str(e)}")
                total_vendors = recent_vendors = 0
            
            # Business Analytics
            try:
                total_businesses_qs = Business.objects(is_active=True).count()
                recent_businesses_qs = Business.objects(
                    Q(is_active=True) & Q(created_at__gte=start_date)
                ).count()
                
                # Convert QuerySet/cursor results to integers safely
                total_businesses = int(total_businesses_qs) if total_businesses_qs is not None else 0
                recent_businesses = int(recent_businesses_qs) if recent_businesses_qs is not None else 0
                    
            except Exception as e:
                logger.error(f"Error getting business analytics: {str(e)}")
                total_businesses = recent_businesses = 0
            
            # Customer Analytics
            try:
                total_customers_qs = Customer.objects().count()
                recent_customers_qs = Customer.objects(created_at__gte=start_date).count()
                
                # Convert QuerySet/cursor results to integers safely
                total_customers = int(total_customers_qs) if total_customers_qs is not None else 0
                recent_customers = int(recent_customers_qs) if recent_customers_qs is not None else 0
                    
            except Exception as e:
                logger.error(f"Error getting customer analytics: {str(e)}")
                total_customers = recent_customers = 0
            
            # Order Analytics
            try:
                total_orders_qs = Order.objects().count()
                recent_orders_qs = Order.objects(created_at__gte=start_date).count()
                paid_orders_qs = Order.objects(payment_status='paid').count()
                
                # Convert QuerySet/cursor results to integers safely
                total_orders = int(total_orders_qs) if total_orders_qs is not None else 0
                recent_orders = int(recent_orders_qs) if recent_orders_qs is not None else 0
                paid_orders = int(paid_orders_qs) if paid_orders_qs is not None else 0
                    
            except Exception as e:
                logger.error(f"Error getting order analytics: {str(e)}")
                total_orders = recent_orders = paid_orders = 0
            
            # Revenue Analytics
            try:
                all_paid_orders = Order.objects(payment_status='paid').only('total_amount')
                total_revenue = sum(order.total_amount or 0 for order in all_paid_orders)
                
                recent_paid_orders = Order.objects(
                    Q(payment_status='paid') & Q(created_at__gte=start_date)
                ).only('total_amount')
                recent_revenue = sum(order.total_amount or 0 for order in recent_paid_orders)
            except Exception as e:
                logger.error(f"Error calculating revenue: {str(e)}")
                total_revenue = 0
                recent_revenue = 0
            
            # Chat Analytics
            try:
                total_chat_sessions_qs = ChatSession.objects().count()
                recent_chat_sessions_qs = ChatSession.objects(created_at__gte=start_date).count()
                
                # Convert QuerySet/cursor results to integers safely
                total_chat_sessions = int(total_chat_sessions_qs) if total_chat_sessions_qs is not None else 0
                recent_chat_sessions = int(recent_chat_sessions_qs) if recent_chat_sessions_qs is not None else 0
                    
            except Exception as e:
                logger.error(f"Error getting chat analytics: {str(e)}")
                total_chat_sessions = recent_chat_sessions = 0
            
            # Top performing businesses - simplified approach to avoid aggregation issues
            try:
                # Get all paid orders with business info - limit to recent orders for performance
                paid_orders = Order.objects(
                    Q(payment_status='paid') & Q(created_at__gte=start_date)
                ).only('business', 'total_amount').limit(1000)  # Limit for performance
                
                # Group by business manually
                paid_orders_by_business = {}
                
                for order in paid_orders:
                    try:
                        if order.business and order.total_amount:
                            business_id = str(order.business.id)
                            business_name = order.business.name
                            
                            if business_id not in paid_orders_by_business:
                                paid_orders_by_business[business_id] = {
                                    'order_count': 0,
                                    'revenue': 0,
                                    'business_name': business_name
                                }
                            paid_orders_by_business[business_id]['order_count'] += 1
                            paid_orders_by_business[business_id]['revenue'] += (order.total_amount or 0)
                    except Exception as order_error:
                        logger.error(f"Error processing order: {str(order_error)}")
                        continue
                
                # Sort by revenue and get top 10
                if paid_orders_by_business:
                    sorted_businesses = sorted(
                        paid_orders_by_business.items(), 
                        key=lambda x: x[1]['revenue'], 
                        reverse=True
                    )[:10]
                    
                    top_businesses_list = []
                    for business_id, data in sorted_businesses:
                        top_businesses_list.append({
                            "business_id": business_id,
                            "business_name": data['business_name'],
                            "order_count": data['order_count'],
                            "revenue": float(data['revenue'])
                        })
                else:
                    top_businesses_list = []
                    
            except Exception as e:
                logger.error(f"Error getting top businesses: {str(e)}")
                top_businesses_list = []
            
            # Get revenue chart data
            try:
                revenue_chart_data = AnalyticsService._get_revenue_chart_data(days)
            except Exception as e:
                logger.error(f"Error getting revenue chart data: {str(e)}")
                revenue_chart_data = {'labels': [], 'data': []}
            
            return {
                "success": True,
                "period_days": days,
                "summary": {
                    "total_vendors": total_vendors,
                    "recent_vendors": recent_vendors,
                    "total_businesses": total_businesses,
                    "recent_businesses": recent_businesses,
                    "total_customers": total_customers,
                    "recent_customers": recent_customers,
                    "total_orders": total_orders,
                    "recent_orders": recent_orders,
                    "paid_orders": paid_orders,
                    "total_revenue": float(total_revenue) if total_revenue is not None else 0.0,
                    "recent_revenue": float(recent_revenue) if recent_revenue is not None else 0.0,
                    "total_chat_sessions": total_chat_sessions,
                    "recent_chat_sessions": recent_chat_sessions
                },
                "top_businesses": top_businesses_list,
                "revenue_chart_data": revenue_chart_data
            }
            
        except Exception as e:
            logger.error(f"Error getting admin analytics: {str(e)}")
            # Return minimal fallback data instead of error
            return {
                "success": True,
                "period_days": days,
                "error_message": f"Limited data due to: {str(e)}",
                "summary": {
                    "total_vendors": 0,
                    "recent_vendors": 0,
                    "total_businesses": 0,
                    "recent_businesses": 0,
                    "total_customers": 0,
                    "recent_customers": 0,
                    "total_orders": 0,
                    "recent_orders": 0,
                    "paid_orders": 0,
                    "total_revenue": 0,
                    "recent_revenue": 0,
                    "total_chat_sessions": 0,
                    "recent_chat_sessions": 0
                },
                "top_businesses": [],
                "revenue_chart_data": {"labels": [], "data": []}
            }
    
    @staticmethod
    def get_export_data(business_id, data_type, vendor_id=None, start_date=None, end_date=None):
        """Export data for analytics"""
        try:
            # Verify permissions
            if vendor_id:
                business = Business.objects(Q(id=business_id) & Q(vendor=vendor_id)).first()
                if not business:
                    return {"error": "Business not found or access denied"}
            
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            else:
                start_date = datetime.utcnow() - timedelta(days=30)
            
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                end_date = end_date.replace(hour=23, minute=59, second=59)
            else:
                end_date = datetime.utcnow()
            
            if data_type == 'orders':
                return AnalyticsService._export_orders(business_id, start_date, end_date)
            elif data_type == 'customers':
                return AnalyticsService._export_customers(business_id, start_date, end_date)
            elif data_type == 'products':
                return AnalyticsService._export_products(business_id, start_date, end_date)
            elif data_type == 'chats':
                return AnalyticsService._export_chats(business_id, start_date, end_date)
            else:
                return {"error": "Invalid data type"}
            
        except Exception as e:
            logger.error(f"Error exporting data: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def _export_orders(business_id, start_date, end_date):
        """Export orders data"""
        try:
            orders = Order.objects(
                Q(business=business_id) & 
                Q(created_at__gte=start_date) & 
                Q(created_at__lte=end_date)
            )
            
            export_data = []
            for order in orders:
                export_data.append({
                    "order_number": order.order_number,
                    "customer_phone": order.customer.phone_number if order.customer else '',
                    "customer_name": order.customer.name if order.customer and order.customer.name else '',
                    "total_amount": order.total_amount,
                    "status": order.status,
                    "payment_status": order.payment_status,
                    "payment_method": order.payment_method if hasattr(order, 'payment_method') else '',
                    "created_at": order.created_at.isoformat(),
                    "customization_notes": order.customization_notes if hasattr(order, 'customization_notes') else ''
                })
            
            return {"success": True, "data": export_data}
            
        except Exception as e:
            logger.error(f"Error exporting orders: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def _export_customers(business_id, start_date, end_date):
        """Export customers data"""
        try:
            # Get customers who have chatted with this business in the date range
            chat_sessions = ChatSession.objects(
                Q(business=business_id) & 
                Q(created_at__gte=start_date) & 
                Q(created_at__lte=end_date)
            ).distinct('customer')
            
            customer_ids = [session.customer.id for session in ChatSession.objects(
                Q(business=business_id) & 
                Q(created_at__gte=start_date) & 
                Q(created_at__lte=end_date)
            ).only('customer')]
            
            customers = Customer.objects(id__in=customer_ids)
            
            export_data = []
            for customer in customers:
                # Get chat and order statistics
                chat_sessions_count_qs = ChatSession.objects(
                    Q(business=business_id) & Q(customer=customer.id)
                ).count()
                chat_sessions_count = int(chat_sessions_count_qs) if chat_sessions_count_qs is not None else 0
                
                orders_count_qs = Order.objects(
                    Q(business=business_id) & Q(customer=customer.id)
                ).count()
                orders_count = int(orders_count_qs) if orders_count_qs is not None else 0
                
                paid_orders = Order.objects(
                    Q(business=business_id) & 
                    Q(customer=customer.id) & 
                    Q(payment_status='paid')
                ).only('total_amount')
                total_spent = sum(order.total_amount for order in paid_orders)
                
                export_data.append({
                    "phone_number": customer.phone_number,
                    "name": customer.name or '',
                    "email": customer.email or '',
                    "created_at": customer.created_at.isoformat(),
                    "chat_sessions": chat_sessions_count,
                    "orders": orders_count,
                    "total_spent": float(total_spent)
                })
            
            return {"success": True, "data": export_data}
            
        except Exception as e:
            logger.error(f"Error exporting customers: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def _export_products(business_id, start_date, end_date):
        """Export products performance data"""
        try:
            from models import OrderItem
            
            products = Product.objects(business=business_id)
            
            export_data = []
            for product in products:
                # Get sales data for the period using aggregation
                pipeline = [
                    {"$match": {
                        "business": business_id,
                        "payment_status": "paid",
                        "created_at": {"$gte": start_date, "$lte": end_date}
                    }},
                    {"$unwind": "$order_items"},
                    {"$match": {"order_items.product": str(product.id)}},
                    {"$group": {
                        "_id": None,
                        "total_sold": {"$sum": "$order_items.quantity"},
                        "total_revenue": {"$sum": "$order_items.total_price"},
                        "unique_customers": {"$addToSet": "$customer"}
                    }},
                    {"$project": {
                        "total_sold": 1,
                        "total_revenue": 1,
                        "unique_customers": {"$size": "$unique_customers"}
                    }}
                ]
                
                sales_data = list(Order.objects.aggregate(pipeline))
                
                if sales_data:
                    data = sales_data[0]
                    total_sold = data.get('total_sold', 0)
                    total_revenue = data.get('total_revenue', 0)
                    unique_customers = data.get('unique_customers', 0)
                else:
                    total_sold = total_revenue = unique_customers = 0
                
                export_data.append({
                    "product_id": product.product_id if hasattr(product, 'product_id') else str(product.id),
                    "product_name": product.name,
                    "category": product.category.name if product.category else '',
                    "price": product.price,
                    "is_active": product.is_active,
                    "allows_customization": product.allows_customization if hasattr(product, 'allows_customization') else False,
                    "has_variations": product.has_variations if hasattr(product, 'has_variations') else False,
                    "total_sold": total_sold,
                    "total_revenue": float(total_revenue),
                    "unique_customers": unique_customers,
                    "created_at": product.created_at.isoformat()
                })
            
            return {"success": True, "data": export_data}
            
        except Exception as e:
            logger.error(f"Error exporting products: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def _export_chats(business_id, start_date, end_date):
        """Export chat sessions data"""
        try:
            chat_sessions = ChatSession.objects(
                Q(business=business_id) & 
                Q(created_at__gte=start_date) & 
                Q(created_at__lte=end_date)
            )
            
            export_data = []
            for session in chat_sessions:
                message_count_qs = ChatMessage.objects(session=session.id).count()
                message_count = int(message_count_qs) if message_count_qs is not None else 0
                
                export_data.append({
                    "session_id": session.session_id if hasattr(session, 'session_id') else str(session.id),
                    "customer_phone": session.customer.phone_number if session.customer else '',
                    "customer_name": session.customer.name if session.customer and session.customer.name else '',
                    "created_at": session.created_at.isoformat(),
                    "message_count": message_count
                })
            
            return {"success": True, "data": export_data}
            
        except Exception as e:
            logger.error(f"Error exporting chats: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def get_system_export_data(data_type, start_date=None, end_date=None):
        """Export system-wide data for admins"""
        try:
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            else:
                start_date = datetime.utcnow() - timedelta(days=30)
            
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                end_date = end_date.replace(hour=23, minute=59, second=59)
            else:
                end_date = datetime.utcnow()
            
            if data_type == 'orders':
                return AnalyticsService._export_system_orders(start_date, end_date)
            elif data_type == 'customers':
                return AnalyticsService._export_system_customers(start_date, end_date)
            elif data_type == 'businesses':
                return AnalyticsService._export_system_businesses(start_date, end_date)
            elif data_type == 'vendors':
                return AnalyticsService._export_system_vendors(start_date, end_date)
            elif data_type == 'chats':
                return AnalyticsService._export_system_chats(start_date, end_date)
            else:
                return {"error": "Invalid data type"}
            
        except Exception as e:
            logger.error(f"Error exporting system data: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def _export_system_orders(start_date, end_date):
        """Export all orders system-wide"""
        try:
            orders = Order.objects(created_at__gte=start_date, created_at__lte=end_date)
            
            export_data = []
            for order in orders:
                export_data.append({
                    "order_id": str(order.id),
                    "business_name": order.business.name if order.business else '',
                    "vendor_name": order.business.vendor.name if order.business and order.business.vendor else '',
                    "customer_name": order.customer.name if order.customer else '',
                    "customer_phone": order.customer.phone_number if order.customer else '',
                    "total_amount": float(order.total_amount) if order.total_amount else 0.0,
                    "payment_status": order.payment_status,
                    "order_status": order.status,
                    "created_at": order.created_at.isoformat(),
                    "updated_at": order.updated_at.isoformat() if order.updated_at else ''
                })
            
            return {"success": True, "data": export_data}
            
        except Exception as e:
            logger.error(f"Error exporting system orders: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def _export_system_customers(start_date, end_date):
        """Export all customers system-wide"""
        try:
            customers = Customer.objects(created_at__gte=start_date, created_at__lte=end_date)
            
            export_data = []
            for customer in customers:
                # Get customer's order count and total spent
                order_count_qs = Order.objects(customer=customer).count()
                order_count = int(order_count_qs) if order_count_qs is not None else 0
                
                paid_orders = Order.objects(customer=customer, payment_status='paid').only('total_amount')
                total_spent = sum(order.total_amount or 0 for order in paid_orders)
                
                export_data.append({
                    "customer_id": str(customer.id),
                    "name": customer.name,
                    "phone": customer.phone_number,
                    "email": customer.email or '',
                    "order_count": order_count,
                    "total_spent": float(total_spent),
                    "created_at": customer.created_at.isoformat(),
                    "last_activity": customer.last_activity.isoformat() if hasattr(customer, 'last_activity') and customer.last_activity else ''
                })
            
            return {"success": True, "data": export_data}
            
        except Exception as e:
            logger.error(f"Error exporting system customers: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def _export_system_businesses(start_date, end_date):
        """Export all businesses system-wide"""
        try:
            businesses = Business.objects(created_at__gte=start_date, created_at__lte=end_date)
            
            export_data = []
            for business in businesses:
                # Get business statistics
                order_count_qs = Order.objects(business=business).count()
                order_count = int(order_count_qs) if order_count_qs is not None else 0
                
                paid_orders = Order.objects(business=business, payment_status='paid').only('total_amount')
                total_revenue = sum(order.total_amount or 0 for order in paid_orders)
                
                # Fix: distinct() returns a list, so we need to count the length
                customer_distinct_list = ChatSession.objects(business=business).distinct('customer')
                customer_count = len(customer_distinct_list) if customer_distinct_list else 0
                
                export_data.append({
                    "business_id": str(business.id),
                    "name": business.name,
                    "vendor_name": business.vendor.name if business.vendor else '',
                    "phone": business.whatsapp_number,
                    "email": business.email or '',
                    "category": business.category,
                    "is_active": business.is_active,
                    "order_count": order_count,
                    "total_revenue": float(total_revenue),
                    "customer_count": customer_count,
                    "created_at": business.created_at.isoformat(),
                    "whatsapp_number": business.whatsapp_number or ''
                })
            
            return {"success": True, "data": export_data}
            
        except Exception as e:
            logger.error(f"Error exporting system businesses: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def _export_system_vendors(start_date, end_date):
        """Export all vendors system-wide"""
        try:
            vendors = Vendor.objects(created_at__gte=start_date, created_at__lte=end_date)
            
            export_data = []
            for vendor in vendors:
                # Get vendor statistics
                business_count_qs = Business.objects(vendor=vendor).count()
                business_count = int(business_count_qs) if business_count_qs is not None else 0
                
                vendor_businesses = Business.objects(vendor=vendor)
                total_orders_qs = Order.objects(business__in=vendor_businesses).count()
                total_orders = int(total_orders_qs) if total_orders_qs is not None else 0
                
                paid_orders = Order.objects(business__in=vendor_businesses, payment_status='paid').only('total_amount')
                total_revenue = sum(order.total_amount or 0 for order in paid_orders)
                
                export_data.append({
                    "vendor_id": str(vendor.id),
                    "name": vendor.name,
                    "email": vendor.email,
                    "phone": vendor.phone_number or '',
                    "is_active": vendor.is_active,
                    "business_count": business_count,
                    "total_orders": total_orders,
                    "total_revenue": float(total_revenue),
                    "created_at": vendor.created_at.isoformat(),
                    "last_login": vendor.last_login.isoformat() if hasattr(vendor, 'last_login') and vendor.last_login else ''
                })
            
            return {"success": True, "data": export_data}
            
        except Exception as e:
            logger.error(f"Error exporting system vendors: {str(e)}")
            return {"error": str(e)}
    
    @staticmethod
    def _export_system_chats(start_date, end_date):
        """Export all chat sessions system-wide"""
        try:
            sessions = ChatSession.objects(created_at__gte=start_date, created_at__lte=end_date)
            
            export_data = []
            for session in sessions:
                message_count_qs = ChatMessage.objects(session=session).count()
                message_count = int(message_count_qs) if message_count_qs is not None else 0
                
                export_data.append({
                    "session_id": str(session.id),
                    "business_name": session.business.name if session.business else '',
                    "vendor_name": session.business.vendor.name if session.business and session.business.vendor else '',
                    "customer_name": session.customer.name if session.customer else '',
                    "customer_phone": session.customer.phone_number if session.customer else '',
                    "message_count": message_count,
                    "created_at": session.created_at.isoformat(),
                    "last_message": session.last_message_at.isoformat() if hasattr(session, 'last_message_at') and session.last_message_at else ''
                })
            
            return {"success": True, "data": export_data}
            
        except Exception as e:
            logger.error(f"Error exporting system chats: {str(e)}")
            return {"error": str(e)}

    @staticmethod
    def health_check():
        """Simple health check for analytics service"""
        try:
            # Check if models are available
            if Vendor is None:
                return {"status": "error", "message": "Models not available"}
            
            # Try a simple query
            count = Vendor.objects.count()
            return {"status": "healthy", "vendor_count": count}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def _get_customer_analytics(business_id, start_date):
        """Get customer analytics for a business"""
        try:
            total_customers_list = ChatSession.objects(business=business_id).distinct('customer')
            total_customers = len(total_customers_list) if total_customers_list else 0
            
            recent_customers_list = ChatSession.objects(
                Q(business=business_id) & Q(created_at__gte=start_date)
            ).distinct('customer')
            recent_customers = len(recent_customers_list) if recent_customers_list else 0
            
            returning_customers = 0
            customer_growth = (recent_customers / total_customers * 100) if total_customers > 0 else 0
            
            return {
                "total_customers": total_customers,
                "recent_customers": recent_customers,
                "returning_customers": returning_customers,
                "customer_growth": round(customer_growth, 2)
            }
        except Exception as e:
            logger.error(f"Error getting customer analytics: {str(e)}")
            return {"total_customers": 0, "recent_customers": 0, "returning_customers": 0, "customer_growth": 0}

    @staticmethod
    def _get_order_analytics(business_id, start_date):
        """Get order analytics for a business"""
        try:
            total_orders = Order.objects(business=business_id).count()
            total_orders = int(total_orders) if total_orders is not None else 0
            
            recent_orders = Order.objects(Q(business=business_id) & Q(created_at__gte=start_date)).count()
            recent_orders = int(recent_orders) if recent_orders is not None else 0
            
            paid_orders = Order.objects(Q(business=business_id) & Q(payment_status='paid')).count()
            paid_orders = int(paid_orders) if paid_orders is not None else 0
            
            pending_orders = Order.objects(Q(business=business_id) & Q(payment_status='pending')).count()
            pending_orders = int(pending_orders) if pending_orders is not None else 0
            
            cancelled_orders = Order.objects(Q(business=business_id) & Q(status='cancelled')).count()
            cancelled_orders = int(cancelled_orders) if cancelled_orders is not None else 0
            
            paid_order_amounts = Order.objects(Q(business=business_id) & Q(payment_status='paid')).only('total_amount')
            total_revenue = sum(order.total_amount or 0 for order in paid_order_amounts)
            average_order_value = (total_revenue / paid_orders) if paid_orders > 0 else 0
            conversion_rate = (paid_orders / total_orders * 100) if total_orders > 0 else 0
            
            return {
                "total_orders": total_orders,
                "recent_orders": recent_orders,
                "paid_orders": paid_orders,
                "pending_orders": pending_orders,
                "cancelled_orders": cancelled_orders,
                "average_order_value": round(average_order_value, 2),
                "conversion_rate": round(conversion_rate, 2)
            }
        except Exception as e:
            logger.error(f"Error getting order analytics: {str(e)}")
            return {"total_orders": 0, "recent_orders": 0, "paid_orders": 0, "pending_orders": 0, "cancelled_orders": 0, "average_order_value": 0.0, "conversion_rate": 0.0}

    @staticmethod
    def _get_product_analytics(business_id, start_date):
        """Get product analytics for a business"""
        try:
            total_products = Product.objects(business=business_id).count()
            total_products = int(total_products) if total_products is not None else 0
            
            return {
                "total_products": total_products,
                "best_sellers": []
            }
        except Exception as e:
            logger.error(f"Error getting product analytics: {str(e)}")
            return {"total_products": 0, "best_sellers": []}

    @staticmethod
    def _get_chat_analytics(business_id, start_date):
        """Get chat analytics for a business"""
        try:
            total_chat_sessions = ChatSession.objects(business=business_id).count()
            total_chat_sessions = int(total_chat_sessions) if total_chat_sessions is not None else 0
            
            recent_chat_sessions = ChatSession.objects(Q(business=business_id) & Q(created_at__gte=start_date)).count()
            recent_chat_sessions = int(recent_chat_sessions) if recent_chat_sessions is not None else 0
            
            total_messages = ChatMessage.objects(session__in=ChatSession.objects(business=business_id)).count()
            total_messages = int(total_messages) if total_messages is not None else 0
            
            recent_messages = ChatMessage.objects(Q(session__in=ChatSession.objects(business=business_id)) & Q(created_at__gte=start_date)).count()
            recent_messages = int(recent_messages) if recent_messages is not None else 0
            
            average_messages_per_session = (total_messages / total_chat_sessions) if total_chat_sessions > 0 else 0
            
            return {
                "total_chat_sessions": total_chat_sessions,
                "recent_chat_sessions": recent_chat_sessions,
                "total_messages": total_messages,
                "recent_messages": recent_messages,
                "average_messages_per_session": round(average_messages_per_session, 2)
            }
        except Exception as e:
            logger.error(f"Error getting chat analytics: {str(e)}")
            return {"total_chat_sessions": 0, "recent_chat_sessions": 0, "total_messages": 0, "recent_messages": 0, "average_messages_per_session": 0.0}

    @staticmethod
    def _get_revenue_analytics(business_id, start_date):
        """Get revenue analytics for a business"""
        try:
            paid_orders = Order.objects(Q(business=business_id) & Q(payment_status='paid')).only('total_amount')
            total_revenue = sum(order.total_amount or 0 for order in paid_orders)
            
            recent_paid_orders = Order.objects(Q(business=business_id) & Q(payment_status='paid') & Q(created_at__gte=start_date)).only('total_amount')
            recent_revenue = sum(order.total_amount or 0 for order in recent_paid_orders)
            
            return {
                "total_revenue": float(total_revenue),
                "recent_revenue": float(recent_revenue),
                "daily_revenue": []
            }
        except Exception as e:
            logger.error(f"Error getting revenue analytics: {str(e)}")
            return {"total_revenue": 0.0, "recent_revenue": 0.0, "daily_revenue": []}

    @staticmethod
    def _get_revenue_chart_data(days=30):
        """Generate daily revenue data for charts"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Create date range for the chart
            date_range = []
            current_date = start_date
            while current_date <= end_date:
                date_range.append(current_date.date())
                current_date += timedelta(days=1)
            
            # Initialize revenue data for each day
            revenue_by_date = {date: 0 for date in date_range}
            
            # Get all paid orders within the date range
            paid_orders = Order.objects(
                Q(payment_status='paid') & 
                Q(created_at__gte=start_date) & 
                Q(created_at__lte=end_date)
            ).only('total_amount', 'created_at')
            
            # Group orders by date and sum revenue
            for order in paid_orders:
                if order.created_at and order.total_amount:
                    order_date = order.created_at.date()
                    if order_date in revenue_by_date:
                        revenue_by_date[order_date] += float(order.total_amount)
            
            # Format data for chart
            labels = []
            data = []
            
            for date in date_range:
                labels.append(date.strftime('%b %d'))
                data.append(revenue_by_date[date])
            
            return {
                'labels': labels,
                'data': data
            }
            
        except Exception as e:
            logger.error(f"Error generating revenue chart data: {str(e)}")
            # Return empty chart data as fallback
            return {
                'labels': [],
                'data': []
            }

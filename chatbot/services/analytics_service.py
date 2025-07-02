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
            return {"error": str(e)}
    
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
            total_customers = ChatSession.objects(business__in=business_ids).distinct('customer').count()
            
            recent_customers = ChatSession.objects(
                Q(business__in=business_ids) & Q(created_at__gte=start_date)
            ).distinct('customer').count()
            
            total_orders = Order.objects(business__in=business_ids).count()
            recent_orders = Order.objects(
                Q(business__in=business_ids) & Q(created_at__gte=start_date)
            ).count()
            
            # Calculate total revenue and count paid orders
            paid_orders_queryset = Order.objects(
                Q(business__in=business_ids) & Q(payment_status='paid')
            ).only('total_amount')
            total_revenue = sum(order.total_amount for order in paid_orders_queryset)
            paid_orders_count = Order.objects(
                Q(business__in=business_ids) & Q(payment_status='paid')
            ).count()
            
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
                    "total_revenue": float(total_revenue),
                    "recent_revenue": float(recent_revenue)
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
                Vendor.objects.count()  # This will fail if DB is not connected
                
                total_vendors = Vendor.objects(is_active=True).count()
                recent_vendors = Vendor.objects(
                    Q(is_active=True) & Q(created_at__gte=start_date)
                ).count()
            except Exception as e:
                logger.error(f"Error getting vendor analytics: {str(e)}")
                total_vendors = recent_vendors = 0
            
            # Business Analytics
            try:
                total_businesses = Business.objects(is_active=True).count()
                recent_businesses = Business.objects(
                    Q(is_active=True) & Q(created_at__gte=start_date)
                ).count()
            except Exception as e:
                logger.error(f"Error getting business analytics: {str(e)}")
                total_businesses = recent_businesses = 0
            
            # Customer Analytics
            try:
                total_customers = Customer.objects().count()
                recent_customers = Customer.objects(created_at__gte=start_date).count()
            except Exception as e:
                logger.error(f"Error getting customer analytics: {str(e)}")
                total_customers = recent_customers = 0
            
            # Order Analytics
            try:
                total_orders = Order.objects().count()
                recent_orders = Order.objects(created_at__gte=start_date).count()
                paid_orders = Order.objects(payment_status='paid').count()
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
                total_chat_sessions = ChatSession.objects().count()
                recent_chat_sessions = ChatSession.objects(created_at__gte=start_date).count()
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
                    "total_revenue": float(total_revenue),
                    "recent_revenue": float(recent_revenue),
                    "total_chat_sessions": total_chat_sessions,
                    "recent_chat_sessions": recent_chat_sessions
                },
                "top_businesses": top_businesses_list
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
                "top_businesses": []
            }
    
    @staticmethod
    def _get_customer_analytics(business_id, start_date):
        """Get customer analytics for a business"""
        try:
            # Total customers who have chatted with this business
            total_customers = ChatSession.objects(business=business_id).distinct('customer').count()
            
            # Recent customers
            recent_customers = ChatSession.objects(
                Q(business=business_id) & Q(created_at__gte=start_date)
            ).distinct('customer').count()
            
            # Returning customers (customers with multiple chat sessions)
            customer_sessions = ChatSession.objects(business=business_id).aggregate([
                {"$group": {"_id": "$customer", "session_count": {"$sum": 1}}},
                {"$match": {"session_count": {"$gt": 1}}},
                {"$count": "returning_customers"}
            ])
            returning_customers = list(customer_sessions)[0].get('returning_customers', 0) if list(customer_sessions) else 0
            
            return {
                "total_customers": total_customers,
                "recent_customers": recent_customers,
                "returning_customers": returning_customers,
                "customer_growth": recent_customers
            }
            
        except Exception as e:
            logger.error(f"Error getting customer analytics: {str(e)}")
            return {}
    
    @staticmethod
    def _get_order_analytics(business_id, start_date):
        """Get order analytics for a business"""
        try:
            total_orders = Order.objects(business=business_id).count()
            recent_orders = Order.objects(
                Q(business=business_id) & Q(created_at__gte=start_date)
            ).count()
            
            paid_orders = Order.objects(
                Q(business=business_id) & Q(payment_status='paid')
            ).count()
            
            pending_orders = Order.objects(
                Q(business=business_id) & Q(payment_status='pending')
            ).count()
            
            cancelled_orders = Order.objects(
                Q(business=business_id) & Q(status='cancelled')
            ).count()
            
            # Average order value
            paid_orders_list = Order.objects(
                Q(business=business_id) & Q(payment_status='paid')
            ).only('total_amount')
            
            if paid_orders_list:
                avg_order_value = sum(order.total_amount for order in paid_orders_list) / len(paid_orders_list)
            else:
                avg_order_value = 0
            
            return {
                "total_orders": total_orders,
                "recent_orders": recent_orders,
                "paid_orders": paid_orders,
                "pending_orders": pending_orders,
                "cancelled_orders": cancelled_orders,
                "average_order_value": float(avg_order_value),
                "conversion_rate": (paid_orders / total_orders * 100) if total_orders > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting order analytics: {str(e)}")
            return {}
    
    @staticmethod
    def _get_product_analytics(business_id, start_date):
        """Get product analytics for a business"""
        try:
            from models import OrderItem
            
            total_products = Product.objects(Q(business=business_id) & Q(is_active=True)).count()
            
            # Best selling products - using aggregation pipeline
            pipeline = [
                {"$match": {"business": business_id}},
                {"$lookup": {
                    "from": "orders",
                    "localField": "_id", 
                    "foreignField": "order_items.product",
                    "as": "orders"
                }},
                {"$unwind": "$orders"},
                {"$match": {"orders.payment_status": "paid"}},
                {"$unwind": "$orders.order_items"},
                {"$match": {"orders.order_items.product": {"$exists": True}}},
                {"$group": {
                    "_id": "$_id",
                    "product_name": {"$first": "$name"},
                    "total_sold": {"$sum": "$orders.order_items.quantity"},
                    "total_revenue": {"$sum": "$orders.order_items.total_price"}
                }},
                {"$sort": {"total_sold": -1}},
                {"$limit": 5}
            ]
            
            best_sellers_data = list(Product.objects.aggregate(pipeline))
            
            best_sellers_list = []
            for product in best_sellers_data:
                best_sellers_list.append({
                    "product_name": product.get("product_name", ""),
                    "total_sold": product.get("total_sold", 0),
                    "total_revenue": float(product.get("total_revenue", 0))
                })
            
            return {
                "total_products": total_products,
                "best_sellers": best_sellers_list
            }
            
        except Exception as e:
            logger.error(f"Error getting product analytics: {str(e)}")
            return {}
    
    @staticmethod
    def _get_chat_analytics(business_id, start_date):
        """Get chat analytics for a business"""
        try:
            total_sessions = ChatSession.objects(business=business_id).count()
            recent_sessions = ChatSession.objects(
                Q(business=business_id) & Q(created_at__gte=start_date)
            ).count()
            
            # Count total messages
            total_messages = 0
            for session in ChatSession.objects(business=business_id).only('id'):
                total_messages += ChatMessage.objects(session=session.id).count()
            
            # Count recent messages
            recent_messages = 0
            for session in ChatSession.objects(business=business_id).only('id'):
                recent_messages += ChatMessage.objects(
                    Q(session=session.id) & Q(timestamp__gte=start_date)
                ).count()
            
            # Average messages per session
            avg_messages_per_session = (total_messages / total_sessions) if total_sessions > 0 else 0
            
            return {
                "total_chat_sessions": total_sessions,
                "recent_chat_sessions": recent_sessions,
                "total_messages": total_messages,
                "recent_messages": recent_messages,
                "average_messages_per_session": round(avg_messages_per_session, 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting chat analytics: {str(e)}")
            return {}
    
    @staticmethod
    def _get_revenue_analytics(business_id, start_date):
        """Get revenue analytics for a business"""
        try:
            # Calculate total revenue
            paid_orders = Order.objects(
                Q(business=business_id) & Q(payment_status='paid')
            ).only('total_amount')
            total_revenue = sum(order.total_amount for order in paid_orders)
            
            # Calculate recent revenue
            recent_paid_orders = Order.objects(
                Q(business=business_id) & Q(payment_status='paid') & Q(created_at__gte=start_date)
            ).only('total_amount')
            recent_revenue = sum(order.total_amount for order in recent_paid_orders)
            
            # Revenue by day for the recent period using aggregation
            pipeline = [
                {"$match": {
                    "business": business_id,
                    "payment_status": "paid",
                    "created_at": {"$gte": start_date}
                }},
                {"$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at"
                        }
                    },
                    "revenue": {"$sum": "$total_amount"}
                }},
                {"$sort": {"_id": 1}}
            ]
            
            daily_revenue_data = list(Order.objects.aggregate(pipeline))
            
            daily_revenue_list = []
            for day in daily_revenue_data:
                daily_revenue_list.append({
                    "date": day["_id"],
                    "revenue": float(day["revenue"])
                })
            
            return {
                "total_revenue": float(total_revenue),
                "recent_revenue": float(recent_revenue),
                "daily_revenue": daily_revenue_list
            }
            
        except Exception as e:
            logger.error(f"Error getting revenue analytics: {str(e)}")
            return {}
    
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
                chat_sessions_count = ChatSession.objects(
                    Q(business=business_id) & Q(customer=customer.id)
                ).count()
                
                orders_count = Order.objects(
                    Q(business=business_id) & Q(customer=customer.id)
                ).count()
                
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
                message_count = ChatMessage.objects(session=session.id).count()
                
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

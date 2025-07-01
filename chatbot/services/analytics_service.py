import logging
from flask import jsonify
from models import Business, Vendor, Customer, Order, ChatSession, ChatMessage, Product, Category
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
import json

logger = logging.getLogger(__name__)

class AnalyticsService:
    
    @staticmethod
    def get_business_analytics(business_id, days=30, vendor_id=None):
        """Get comprehensive analytics for a business"""
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
            vendor = Vendor.query.get(vendor_id)
            if not vendor:
                return {"error": "Vendor not found"}
            
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Get all businesses for this vendor
            businesses = Business.query.filter_by(vendor_id=vendor_id, is_active=True).all()
            business_ids = [b.id for b in businesses]
            
            if not business_ids:
                return {
                    "success": True,
                    "vendor_name": vendor.name,
                    "businesses_count": 0,
                    "message": "No active businesses found"
                }
            
            # Aggregate analytics across all businesses
            total_customers = db.session.query(func.count(func.distinct(Customer.id))).\
                join(ChatSession, Customer.id == ChatSession.customer_id).\
                filter(ChatSession.business_id.in_(business_ids)).scalar()
            
            recent_customers = db.session.query(func.count(func.distinct(Customer.id))).\
                join(ChatSession, Customer.id == ChatSession.customer_id).\
                filter(and_(
                    ChatSession.business_id.in_(business_ids),
                    ChatSession.created_at >= start_date
                )).scalar()
            
            total_orders = Order.query.filter(Order.business_id.in_(business_ids)).count()
            recent_orders = Order.query.filter(and_(
                Order.business_id.in_(business_ids),
                Order.created_at >= start_date
            )).count()
            
            total_revenue = db.session.query(func.sum(Order.total_amount)).\
                filter(and_(
                    Order.business_id.in_(business_ids),
                    Order.payment_status == 'paid'
                )).scalar() or 0
            
            recent_revenue = db.session.query(func.sum(Order.total_amount)).\
                filter(and_(
                    Order.business_id.in_(business_ids),
                    Order.payment_status == 'paid',
                    Order.created_at >= start_date
                )).scalar() or 0
            
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
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Vendor Analytics
            total_vendors = Vendor.query.filter_by(is_active=True).count()
            recent_vendors = Vendor.query.filter(and_(
                Vendor.is_active == True,
                Vendor.created_at >= start_date
            )).count()
            
            # Business Analytics
            total_businesses = Business.query.filter_by(is_active=True).count()
            recent_businesses = Business.query.filter(and_(
                Business.is_active == True,
                Business.created_at >= start_date
            )).count()
            
            # Customer Analytics
            total_customers = Customer.query.count()
            recent_customers = Customer.query.filter(Customer.created_at >= start_date).count()
            
            # Order Analytics
            total_orders = Order.query.count()
            recent_orders = Order.query.filter(Order.created_at >= start_date).count()
            paid_orders = Order.query.filter_by(payment_status='paid').count()
            
            # Revenue Analytics
            total_revenue = db.session.query(func.sum(Order.total_amount)).\
                filter(Order.payment_status == 'paid').scalar() or 0
            
            recent_revenue = db.session.query(func.sum(Order.total_amount)).\
                filter(and_(
                    Order.payment_status == 'paid',
                    Order.created_at >= start_date
                )).scalar() or 0
            
            # Chat Analytics
            total_chat_sessions = ChatSession.query.count()
            recent_chat_sessions = ChatSession.query.filter(ChatSession.created_at >= start_date).count()
            
            # Top performing businesses
            top_businesses = db.session.query(
                Business.id,
                Business.name,
                func.count(Order.id).label('order_count'),
                func.sum(Order.total_amount).label('revenue')
            ).join(Order, Business.id == Order.business_id).\
            filter(Order.payment_status == 'paid').\
            group_by(Business.id, Business.name).\
            order_by(func.sum(Order.total_amount).desc()).\
            limit(10).all()
            
            top_businesses_list = []
            for business in top_businesses:
                top_businesses_list.append({
                    "business_id": business.id,
                    "business_name": business.name,
                    "order_count": business.order_count,
                    "revenue": float(business.revenue or 0)
                })
            
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
            return {"error": str(e)}
    
    @staticmethod
    def _get_customer_analytics(business_id, start_date):
        """Get customer analytics for a business"""
        try:
            # Total customers who have chatted with this business
            total_customers = db.session.query(func.count(func.distinct(Customer.id))).\
                join(ChatSession, Customer.id == ChatSession.customer_id).\
                filter(ChatSession.business_id == business_id).scalar()
            
            # Recent customers
            recent_customers = db.session.query(func.count(func.distinct(Customer.id))).\
                join(ChatSession, Customer.id == ChatSession.customer_id).\
                filter(and_(
                    ChatSession.business_id == business_id,
                    ChatSession.created_at >= start_date
                )).scalar()
            
            # Returning customers (customers with multiple chat sessions)
            returning_customers = db.session.query(func.count(func.distinct(Customer.id))).\
                join(ChatSession, Customer.id == ChatSession.customer_id).\
                filter(ChatSession.business_id == business_id).\
                group_by(Customer.id).\
                having(func.count(ChatSession.id) > 1).count()
            
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
            total_orders = Order.query.filter_by(business_id=business_id).count()
            recent_orders = Order.query.filter(and_(
                Order.business_id == business_id,
                Order.created_at >= start_date
            )).count()
            
            paid_orders = Order.query.filter(and_(
                Order.business_id == business_id,
                Order.payment_status == 'paid'
            )).count()
            
            pending_orders = Order.query.filter(and_(
                Order.business_id == business_id,
                Order.payment_status == 'pending'
            )).count()
            
            cancelled_orders = Order.query.filter(and_(
                Order.business_id == business_id,
                Order.status == 'cancelled'
            )).count()
            
            # Average order value
            avg_order_value = db.session.query(func.avg(Order.total_amount)).\
                filter(and_(
                    Order.business_id == business_id,
                    Order.payment_status == 'paid'
                )).scalar() or 0
            
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
            
            total_products = Product.query.filter_by(business_id=business_id, is_active=True).count()
            
            # Best selling products
            best_sellers = db.session.query(
                Product.name,
                func.sum(OrderItem.quantity).label('total_sold'),
                func.sum(OrderItem.total_price).label('total_revenue')
            ).join(OrderItem, Product.id == OrderItem.product_id).\
            join(Order, OrderItem.order_id == Order.id).\
            filter(and_(
                Product.business_id == business_id,
                Order.payment_status == 'paid'
            )).group_by(Product.id, Product.name).\
            order_by(func.sum(OrderItem.quantity).desc()).\
            limit(5).all()
            
            best_sellers_list = []
            for product in best_sellers:
                best_sellers_list.append({
                    "product_name": product.name,
                    "total_sold": product.total_sold,
                    "total_revenue": float(product.total_revenue)
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
            total_sessions = ChatSession.query.filter_by(business_id=business_id).count()
            recent_sessions = ChatSession.query.filter(and_(
                ChatSession.business_id == business_id,
                ChatSession.created_at >= start_date
            )).count()
            
            total_messages = db.session.query(func.count(ChatMessage.id)).\
                join(ChatSession, ChatMessage.session_id == ChatSession.id).\
                filter(ChatSession.business_id == business_id).scalar()
            
            recent_messages = db.session.query(func.count(ChatMessage.id)).\
                join(ChatSession, ChatMessage.session_id == ChatSession.id).\
                filter(and_(
                    ChatSession.business_id == business_id,
                    ChatMessage.timestamp >= start_date
                )).scalar()
            
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
            total_revenue = db.session.query(func.sum(Order.total_amount)).\
                filter(and_(
                    Order.business_id == business_id,
                    Order.payment_status == 'paid'
                )).scalar() or 0
            
            recent_revenue = db.session.query(func.sum(Order.total_amount)).\
                filter(and_(
                    Order.business_id == business_id,
                    Order.payment_status == 'paid',
                    Order.created_at >= start_date
                )).scalar() or 0
            
            # Revenue by day for the recent period
            daily_revenue = db.session.query(
                func.date(Order.created_at).label('date'),
                func.sum(Order.total_amount).label('revenue')
            ).filter(and_(
                Order.business_id == business_id,
                Order.payment_status == 'paid',
                Order.created_at >= start_date
            )).group_by(func.date(Order.created_at)).\
            order_by(func.date(Order.created_at)).all()
            
            daily_revenue_list = []
            for day in daily_revenue:
                daily_revenue_list.append({
                    "date": day.date.isoformat(),
                    "revenue": float(day.revenue)
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
                business = Business.query.filter_by(id=business_id, vendor_id=vendor_id).first()
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
            orders = Order.query.filter(and_(
                Order.business_id == business_id,
                Order.created_at >= start_date,
                Order.created_at <= end_date
            )).all()
            
            export_data = []
            for order in orders:
                export_data.append({
                    "order_number": order.order_number,
                    "customer_phone": order.customer.phone_number,
                    "customer_name": order.customer.name or '',
                    "total_amount": order.total_amount,
                    "status": order.status,
                    "payment_status": order.payment_status,
                    "payment_method": order.payment_method,
                    "created_at": order.created_at.isoformat(),
                    "customization_notes": order.customization_notes or ''
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
            customers = db.session.query(Customer).\
                join(ChatSession, Customer.id == ChatSession.customer_id).\
                filter(and_(
                    ChatSession.business_id == business_id,
                    ChatSession.created_at >= start_date,
                    ChatSession.created_at <= end_date
                )).distinct().all()
            
            export_data = []
            for customer in customers:
                # Get chat and order statistics
                chat_sessions = ChatSession.query.filter_by(
                    business_id=business_id,
                    customer_id=customer.id
                ).count()
                
                orders = Order.query.filter_by(
                    business_id=business_id,
                    customer_id=customer.id
                ).count()
                
                total_spent = db.session.query(func.sum(Order.total_amount)).\
                    filter(and_(
                        Order.business_id == business_id,
                        Order.customer_id == customer.id,
                        Order.payment_status == 'paid'
                    )).scalar() or 0
                
                export_data.append({
                    "phone_number": customer.phone_number,
                    "name": customer.name or '',
                    "email": customer.email or '',
                    "created_at": customer.created_at.isoformat(),
                    "chat_sessions": chat_sessions,
                    "orders": orders,
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
            
            products = Product.query.filter_by(business_id=business_id).all()
            
            export_data = []
            for product in products:
                # Get sales data for the period
                sales_data = db.session.query(
                    func.sum(OrderItem.quantity).label('total_sold'),
                    func.sum(OrderItem.total_price).label('total_revenue'),
                    func.count(func.distinct(Order.customer_id)).label('unique_customers')
                ).join(Order, OrderItem.order_id == Order.id).\
                filter(and_(
                    OrderItem.product_id == product.id,
                    Order.payment_status == 'paid',
                    Order.created_at >= start_date,
                    Order.created_at <= end_date
                )).first()
                
                export_data.append({
                    "product_id": product.product_id,
                    "product_name": product.name,
                    "category": product.category.name if product.category else '',
                    "price": product.price,
                    "is_active": product.is_active,
                    "allows_customization": product.allows_customization,
                    "has_variations": product.has_variations,
                    "total_sold": sales_data.total_sold or 0,
                    "total_revenue": float(sales_data.total_revenue or 0),
                    "unique_customers": sales_data.unique_customers or 0,
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
            chat_sessions = ChatSession.query.filter(and_(
                ChatSession.business_id == business_id,
                ChatSession.created_at >= start_date,
                ChatSession.created_at <= end_date
            )).all()
            
            export_data = []
            for session in chat_sessions:
                message_count = ChatMessage.query.filter_by(session_id=session.id).count()
                
                export_data.append({
                    "session_id": session.session_id,
                    "customer_phone": session.customer.phone_number,
                    "customer_name": session.customer.name or '',
                    "created_at": session.created_at.isoformat(),
                    "message_count": message_count
                })
            
            return {"success": True, "data": export_data}
            
        except Exception as e:
            logger.error(f"Error exporting chats: {str(e)}")
            return {"error": str(e)}

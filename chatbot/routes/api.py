from flask import Blueprint, request, jsonify
from flask_wtf.csrf import exempt
from services.mpesa_service import mpesa_service
import logging
from flask_login import login_required, current_user
from models import Order, Customer, Product, Business
from datetime import datetime, timedelta
from mongoengine import Q
from services.auth.auth_manager import get_user_role

api_bp = Blueprint('api', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)

@api_bp.route('/mpesa/callback', methods=['POST'])
@exempt
def mpesa_callback():
    """Handle Mpesa payment callbacks"""
    try:
        data = request.get_json()
        logger.info(f"Received Mpesa callback: {data}")
        
        result = mpesa_service.process_callback(data)
        
        if result['success']:
            return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"})
        else:
            return jsonify({"ResultCode": 1, "ResultDesc": "Rejected"})
            
    except Exception as e:
        logger.error(f"Error processing Mpesa callback: {str(e)}")
        return jsonify({"ResultCode": 1, "ResultDesc": "Error processing callback"})

@api_bp.route('/health', methods=['GET'])
@exempt
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "SasaBot API is running"})

@api_bp.route('/webhook/test', methods=['POST'])
@exempt
def test_webhook():
    """Test webhook endpoint for development"""
    data = request.get_json()
    logger.info(f"Test webhook received: {data}")
    return jsonify({"status": "received", "data": data})

@api_bp.route('/analytics/sales-data')
@login_required
def sales_data():
    """Get sales data for charts"""
    try:
        user_role = get_user_role(current_user)
        
        if user_role == 'vendor':
            # Get vendor's businesses
            businesses = Business.objects(vendor=current_user.id)
            business_ids = [str(b.id) for b in businesses]
            if not business_ids:
                return jsonify({'success': True, 'labels': [], 'values': []})
            
            # Get sales data for last 7 days
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=6)
            
            # Query orders for the date range and business IDs
            orders = Order.objects(
                business__in=business_ids,
                status='completed',
                created_at__gte=datetime.combine(start_date, datetime.min.time()),
                created_at__lte=datetime.combine(end_date, datetime.max.time())
            )
            
        else:  # admin or default case
            # Get all sales data
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=6)
            
            orders = Order.objects(
                status='completed',
                created_at__gte=datetime.combine(start_date, datetime.min.time()),
                created_at__lte=datetime.combine(end_date, datetime.max.time())
            )
        
        # Create labels and values arrays
        labels = []
        values = []
        
        for i in range(7):
            date = start_date + timedelta(days=i)
            labels.append(date.strftime('%m/%d'))
            
            # Calculate total sales for this date
            day_start = datetime.combine(date, datetime.min.time())
            day_end = datetime.combine(date, datetime.max.time())
            
            day_orders = [order for order in orders if day_start <= order.created_at <= day_end]
            total = sum(order.total_amount for order in day_orders)
            values.append(float(total))
        
        return jsonify({
            'success': True,
            'labels': labels,
            'values': values
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/analytics/orders-data')
@login_required
def orders_data():
    """Get orders status distribution for charts"""
    try:
        user_role = get_user_role(current_user)
        
        if user_role == 'vendor':
            businesses = Business.objects(vendor=current_user.id)
            business_ids = [str(b.id) for b in businesses]
            if not business_ids:
                return jsonify({'success': True, 'values': [0, 0, 0, 0]})
            
            base_query = Order.objects(business__in=business_ids)
        else:  # admin or default case
            base_query = Order.objects()
        
        pending = base_query.filter(status='pending').count()
        processing = base_query.filter(status='processing').count()
        completed = base_query.filter(status='completed').count()
        cancelled = base_query.filter(status='cancelled').count()
        
        return jsonify({
            'success': True,
            'values': [pending, processing, completed, cancelled]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/analytics/products-data')
@login_required
def products_data():
    """Get top products by stock level"""
    try:
        user_role = get_user_role(current_user)
        
        if user_role == 'vendor':
            businesses = Business.objects(vendor=current_user.id)
            business_ids = [str(b.id) for b in businesses]
            if not business_ids:
                return jsonify({'success': True, 'labels': [], 'values': []})
            
            products = Product.objects(
                business__in=business_ids,
                is_active=True
            ).order_by('-stock_quantity').limit(10)
            
        else:  # admin or default case
            products = Product.objects(
                is_active=True
            ).order_by('-stock_quantity').limit(10)
        
        labels = [p.name[:20] + ('...' if len(p.name) > 20 else '') for p in products]
        values = [p.stock_quantity for p in products]
        
        return jsonify({
            'success': True,
            'labels': labels,
            'values': values
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@api_bp.route('/dashboard/stats')
@login_required
def dashboard_stats():
    """Get real-time dashboard statistics"""
    try:
        user_role = get_user_role(current_user)
        
        if user_role == 'vendor':
            businesses = Business.objects(vendor=current_user.id)
            business_ids = [str(b.id) for b in businesses]
            if not business_ids:
                return jsonify({
                    'success': True,
                    'total_sales': 0,
                    'total_orders': 0,
                    'total_customers': 0,
                    'total_products': 0
                })
            
            # Calculate total sales
            completed_orders = Order.objects(
                business__in=business_ids,
                status='completed'
            )
            total_sales = sum(order.total_amount for order in completed_orders)
            
            total_orders = Order.objects(business__in=business_ids).count()
            total_customers = Customer.objects(business__in=business_ids).count()
            total_products = Product.objects(business__in=business_ids).count()
            
        else:  # admin or default case
            # Calculate total sales
            completed_orders = Order.objects(status='completed')
            total_sales = sum(order.total_amount for order in completed_orders)
            
            total_orders = Order.objects().count()
            total_customers = Customer.objects().count()
            total_products = Product.objects().count()
        
        return jsonify({
            'success': True,
            'total_sales': f"KES {total_sales:,.2f}",
            'total_orders': total_orders,
            'total_customers': total_customers,
            'total_products': total_products
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

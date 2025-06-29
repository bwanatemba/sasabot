from flask import Blueprint, request, jsonify
from services.mpesa_service import mpesa_service
import logging
from flask_login import login_required, current_user
from models import Order, Customer, Product, db
from sqlalchemy import func
from datetime import datetime, timedelta

api_bp = Blueprint('api', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)

@api_bp.route('/mpesa/callback', methods=['POST'])
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
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "message": "SasaBot API is running"})

@api_bp.route('/webhook/test', methods=['POST'])
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
        if current_user.role == 'vendor':
            # Get vendor's business IDs
            business_ids = [b.id for b in current_user.businesses]
            if not business_ids:
                return jsonify({'success': True, 'labels': [], 'values': []})
            
            # Get sales data for last 7 days
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=6)
            
            sales_data = db.session.query(
                func.date(Order.created_at).label('date'),
                func.sum(Order.total_amount).label('total')
            ).filter(
                Order.business_id.in_(business_ids),
                Order.status == 'completed',
                func.date(Order.created_at) >= start_date
            ).group_by(func.date(Order.created_at)).all()
            
        elif current_user.role == 'admin':
            # Get all sales data
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=6)
            
            sales_data = db.session.query(
                func.date(Order.created_at).label('date'),
                func.sum(Order.total_amount).label('total')
            ).filter(
                Order.status == 'completed',
                func.date(Order.created_at) >= start_date
            ).group_by(func.date(Order.created_at)).all()
        
        # Create labels and values arrays
        labels = []
        values = []
        
        for i in range(7):
            date = start_date + timedelta(days=i)
            labels.append(date.strftime('%m/%d'))
            
            # Find sales for this date
            total = 0
            for sale in sales_data:
                if sale.date == date:
                    total = float(sale.total)
                    break
            values.append(total)
        
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
        if current_user.role == 'vendor':
            business_ids = [b.id for b in current_user.businesses]
            if not business_ids:
                return jsonify({'success': True, 'values': [0, 0, 0, 0]})
            
            orders_query = Order.query.filter(Order.business_id.in_(business_ids))
        elif current_user.role == 'admin':
            orders_query = Order.query
        
        pending = orders_query.filter(Order.status == 'pending').count()
        processing = orders_query.filter(Order.status == 'processing').count()
        completed = orders_query.filter(Order.status == 'completed').count()
        cancelled = orders_query.filter(Order.status == 'cancelled').count()
        
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
        if current_user.role == 'vendor':
            business_ids = [b.id for b in current_user.businesses]
            if not business_ids:
                return jsonify({'success': True, 'labels': [], 'values': []})
            
            products = Product.query.filter(
                Product.business_id.in_(business_ids),
                Product.is_active == True
            ).order_by(Product.stock_quantity.desc()).limit(10).all()
            
        elif current_user.role == 'admin':
            products = Product.query.filter(
                Product.is_active == True
            ).order_by(Product.stock_quantity.desc()).limit(10).all()
        
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
        if current_user.role == 'vendor':
            business_ids = [b.id for b in current_user.businesses]
            if not business_ids:
                return jsonify({
                    'success': True,
                    'total_sales': 0,
                    'total_orders': 0,
                    'total_customers': 0,
                    'total_products': 0
                })
            
            total_sales = db.session.query(func.sum(Order.total_amount)).filter(
                Order.business_id.in_(business_ids),
                Order.status == 'completed'
            ).scalar() or 0
            
            total_orders = Order.query.filter(Order.business_id.in_(business_ids)).count()
            total_customers = Customer.query.filter(Customer.business_id.in_(business_ids)).count()
            total_products = Product.query.filter(Product.business_id.in_(business_ids)).count()
            
        elif current_user.role == 'admin':
            total_sales = db.session.query(func.sum(Order.total_amount)).filter(
                Order.status == 'completed'
            ).scalar() or 0
            
            total_orders = Order.query.count()
            total_customers = Customer.query.count()
            total_products = Product.query.count()
        
        return jsonify({
            'success': True,
            'total_sales': f"KES {total_sales:,.2f}",
            'total_orders': total_orders,
            'total_customers': total_customers,
            'total_products': total_products
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

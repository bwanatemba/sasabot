from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from models import Admin, Vendor, Business, Product, Category, Order, Customer, ChatSession, ChatMessage
from services.auth.decorators import admin_required
from services.auth.auth_manager import get_user_role
from werkzeug.security import generate_password_hash
from bson import ObjectId
from mongoengine.errors import DoesNotExist
import csv
import io
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    # Get statistics
    total_vendors = Vendor.objects.count()
    total_businesses = Business.objects.count()
    total_orders = Order.objects.count()
    total_customers = Customer.objects.count()
    
    # Recent activity
    recent_vendors = Vendor.objects.order_by('-created_at').limit(5)
    recent_orders = Order.objects.order_by('-created_at').limit(10)
    
    return render_template('admin/dashboard.html',
                         total_vendors=total_vendors,
                         total_businesses=total_businesses,
                         total_orders=total_orders,
                         total_customers=total_customers,
                         recent_vendors=recent_vendors,
                         recent_orders=recent_orders)

@admin_bp.route('/vendors')
@admin_required
def vendors():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    skip = (page - 1) * per_page
    
    vendors_list = Vendor.objects.skip(skip).limit(per_page)
    total = Vendor.objects.count()
    
    # Create pagination object with iter_pages support
    from services.pagination import Pagination
    vendors = Pagination(page, per_page, total, vendors_list)
    
    return render_template('admin/vendors.html', vendors=vendors)

@admin_bp.route('/vendors/<vendor_id>')
@admin_required
def vendor_detail(vendor_id):
    try:
        vendor = Vendor.objects(id=ObjectId(vendor_id)).first()
        if not vendor:
            flash('Vendor not found.', 'error')
            return redirect(url_for('admin.vendors'))
            
        businesses = Business.objects(vendor=vendor)
        
        # Calculate total products and orders for this vendor
        total_products = 0
        total_orders = 0
        for business in businesses:
            total_products += Product.objects(business=business).count()
            total_orders += Order.objects(business=business).count()
            
        return render_template('admin/vendor_detail.html', 
                             vendor=vendor, 
                             businesses=businesses,
                             total_products=total_products,
                             total_orders=total_orders)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('admin.vendors'))

@admin_bp.route('/businesses')
@admin_required
def businesses():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    skip = (page - 1) * per_page
    
    businesses_list = Business.objects.skip(skip).limit(per_page)
    total = Business.objects.count()
    
    # Create pagination object with iter_pages support
    from services.pagination import Pagination
    businesses = Pagination(page, per_page, total, businesses_list)
    
    return render_template('admin/businesses.html', businesses=businesses)

@admin_bp.route('/businesses/<business_id>')
@admin_required
def business_detail(business_id):
    try:
        business = Business.objects(id=ObjectId(business_id)).first()
        if not business:
            flash('Business not found.', 'error')
            return redirect(url_for('admin.businesses'))
            
        products = Product.objects(business=business)
        categories = Category.objects(business=business)
        orders = Order.objects(business=business).order_by('-created_at').limit(10)
        
        return render_template('admin/business_detail.html',
                             business=business,
                             products=products,
                             categories=categories,
                             orders=orders)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('admin.businesses'))

@admin_bp.route('/businesses/<business_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_business(business_id):
    try:
        business = Business.objects(id=ObjectId(business_id)).first()
        if not business:
            flash('Business not found.', 'error')
            return redirect(url_for('admin.businesses'))
        
        if request.method == 'POST':
            business.name = request.form.get('name')
            business.description = request.form.get('description')
            business.category = request.form.get('category')
            business.email = request.form.get('email')
            business.whatsapp_number = request.form.get('whatsapp_number')
            business.whatsapp_api_token = request.form.get('whatsapp_api_token')
            business.whatsapp_phone_id = request.form.get('whatsapp_phone_id')
            business.custom_instructions = request.form.get('custom_instructions')
            
            business.save()
            flash('Business updated successfully!', 'success')
            return redirect(url_for('admin.business_detail', business_id=business_id))
        
        return render_template('admin/edit_business.html', business=business)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('admin.businesses'))
@admin_bp.route('/orders')
@admin_required
def orders():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status')
    per_page = 20
    skip = (page - 1) * per_page
    
    query = Order.objects
    if status_filter:
        query = query.filter(status=status_filter)
    
    orders_list = query.order_by('-created_at').skip(skip).limit(per_page)
    total = query.count()
    
    # Create pagination object with iter_pages support
    from services.pagination import Pagination
    orders = Pagination(page, per_page, total, orders_list)
    
    return render_template('admin/orders.html', orders=orders, status_filter=status_filter)

@admin_bp.route('/chat-sessions')
@admin_required
def chat_sessions():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    skip = (page - 1) * per_page
    
    sessions_list = ChatSession.objects.order_by('-created_at').skip(skip).limit(per_page)
    total = ChatSession.objects.count()
    
    # Create pagination object with iter_pages support
    from services.pagination import Pagination
    sessions = Pagination(page, per_page, total, sessions_list)
    
    return render_template('admin/chat_sessions.html', sessions=sessions)

@admin_bp.route('/chat-sessions/<session_id>')
@admin_required
def chat_detail(session_id):
    try:
        session = ChatSession.objects(id=ObjectId(session_id)).first()
        if not session:
            flash('Chat session not found.', 'error')
            return redirect(url_for('admin.chat_sessions'))
            
        return render_template('admin/chat_detail.html', session=session)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('admin.chat_sessions'))

@admin_bp.route('/admins')
@admin_required
def admins():
    admins = Admin.objects.all()
    return render_template('admin/admins.html', admins=admins)

@admin_bp.route('/admins/add', methods=['GET', 'POST'])
@admin_required
def add_admin():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        phone_number = request.form.get('phone_number')
        name = request.form.get('name')
        
        # Check if admin already exists
        existing_admin = Admin.objects(email=email).first() or Admin.objects(phone_number=phone_number).first()
        
        if existing_admin:
            flash('Admin with this email or phone number already exists.', 'error')
        else:
            admin = Admin(
                email=email,
                password=generate_password_hash(password),
                phone_number=phone_number,
                name=name
            )
            admin.save()
            flash('Admin added successfully!', 'success')
            return redirect(url_for('admin.admins'))
    
    return render_template('admin/add_admin.html')

@admin_bp.route('/products/<business_id>')
@admin_required
def products(business_id):
    try:
        business = Business.objects(id=ObjectId(business_id)).first()
        if not business:
            flash('Business not found.', 'error')
            return redirect(url_for('admin.businesses'))
            
        page = request.args.get('page', 1, type=int)
        per_page = 20
        skip = (page - 1) * per_page
        
        products_list = Product.objects(business=business).skip(skip).limit(per_page)
        total = Product.objects(business=business).count()
        categories = Category.objects(business=business)
        
        # Create pagination object with iter_pages support
        from services.pagination import Pagination
        products = Pagination(page, per_page, total, products_list)
        
        return render_template('admin/products.html',
                             business=business,
                             products=products,
                             categories=categories)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('admin.businesses'))

@admin_bp.route('/products/<business_id>/add', methods=['GET', 'POST'])
@admin_required
def add_product(business_id):
    try:
        business = Business.objects(id=ObjectId(business_id)).first()
        if not business:
            flash('Business not found.', 'error')
            return redirect(url_for('admin.businesses'))
            
        categories = Category.objects(business=business)
        
        if request.method == 'POST':
            import secrets
            import string
            
            # Generate unique product ID
            product_id = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
            
            category = None
            if request.form.get('category_id'):
                category = Category.objects(id=ObjectId(request.form.get('category_id'))).first()
            
            product = Product(
                product_id=product_id,
                name=request.form.get('name'),
                description=request.form.get('description'),
                price=float(request.form.get('price')),
                business=business,
                category=category,
                allows_customization=bool(request.form.get('allows_customization')),
                has_variations=bool(request.form.get('has_variations'))
            )
            
            product.save()
            flash('Product added successfully!', 'success')
            return redirect(url_for('admin.products', business_id=business_id))
        
        return render_template('admin/add_product.html', business=business, categories=categories)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('admin.businesses'))

# Analytics routes for admin
@admin_bp.route('/analytics')
@admin_required
def analytics():
    try:
        days = request.args.get('days', 30, type=int)
        
        from services.analytics_service import AnalyticsService
        analytics_data = AnalyticsService.get_admin_analytics(days)
        
        # Check if analytics data has an error
        if analytics_data.get('error'):
            flash(f'Analytics Error: {analytics_data["error"]}', 'error')
            # Provide fallback data
            analytics_data = {
                'success': False,
                'error': analytics_data['error'],
                'summary': {
                    'total_vendors': 0,
                    'recent_vendors': 0,
                    'total_businesses': 0,
                    'recent_businesses': 0,
                    'total_customers': 0,
                    'recent_customers': 0,
                    'total_orders': 0,
                    'recent_orders': 0,
                    'paid_orders': 0,
                    'total_revenue': 0,
                    'recent_revenue': 0,
                    'total_chat_sessions': 0,
                    'recent_chat_sessions': 0
                },
                'top_businesses': []
            }
        
        return render_template('admin/analytics.html', 
                             analytics=analytics_data,
                             days=days)
                             
    except Exception as e:
        flash(f'Error loading analytics: {str(e)}', 'error')
        # Provide minimal fallback data
        analytics_data = {
            'success': False,
            'error': str(e),
            'summary': {
                'total_vendors': 0,
                'recent_vendors': 0,
                'total_businesses': 0,
                'recent_businesses': 0,
                'total_customers': 0,
                'recent_customers': 0,
                'total_orders': 0,
                'recent_orders': 0,
                'paid_orders': 0,
                'total_revenue': 0,
                'recent_revenue': 0,
                'total_chat_sessions': 0,
                'recent_chat_sessions': 0
            },
            'top_businesses': []
        }
        return render_template('admin/analytics.html', 
                             analytics=analytics_data,
                             days=30)

@admin_bp.route('/business/<business_id>/analytics')
@admin_required
def business_analytics(business_id):
    try:
        business = Business.objects(id=ObjectId(business_id)).first()
        if not business:
            flash('Business not found.', 'error')
            return redirect(url_for('admin.businesses'))
            
        days = request.args.get('days', 30, type=int)
        
        from services.analytics_service import AnalyticsService
        analytics_data = AnalyticsService.get_business_analytics(str(business.id), days)
        
        return render_template('admin/business_analytics.html', 
                             business=business, 
                             analytics=analytics_data,
                             days=days)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('admin.businesses'))

# Bulk messaging routes for admin
@admin_bp.route('/bulk-messaging')
@admin_required
def bulk_messaging():
    businesses = Business.objects(is_active=True)
    return render_template('admin/bulk_messaging.html', businesses=businesses)

@admin_bp.route('/send-bulk-message', methods=['POST'])
@admin_required
def send_bulk_message():
    from services.bulk_messaging import send_bulk_message
    
    try:
        business_id = request.form.get('business_id')
        message = request.form.get('message')
        customer_filter = {}
        
        # Parse filter options
        if request.form.get('start_date'):
            customer_filter['start_date'] = request.form.get('start_date')
        if request.form.get('end_date'):
            customer_filter['end_date'] = request.form.get('end_date')
        if request.form.get('phone_numbers'):
            customer_filter['phone_numbers'] = request.form.get('phone_numbers')
        if request.form.get('active_days'):
            customer_filter['active_days'] = request.form.get('active_days')
        
        result = send_bulk_message(business_id, message, customer_filter)
        
        if result.get('success'):
            flash(f"Message sent to {result['sent']} customers. {result['failed']} failed.", 'success')
        else:
            flash(f"Error sending bulk message: {result.get('error', 'Unknown error')}", 'error')
        
        return redirect(url_for('admin.bulk_messaging'))
        
    except Exception as e:
        flash(f"Error: {str(e)}", 'error')
        return redirect(url_for('admin.bulk_messaging'))

@admin_bp.route('/export-analytics')
@admin_required
def export_analytics():
    data_type = request.args.get('type', 'orders')
    business_id = request.args.get('business_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    from services.analytics_service import AnalyticsService
    
    try:
        if business_id:
            result = AnalyticsService.get_export_data(business_id, data_type, None, start_date, end_date)
        else:
            # System-wide export
            result = {"error": "System-wide export not implemented yet"}
        
        if result.get('success'):
            # Convert to CSV
            try:
                import pandas as pd
                df = pd.DataFrame(result['data'])
                
                output = io.StringIO()
                df.to_csv(output, index=False)
                output.seek(0)
                
                filename = f"admin_{data_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                
                return send_file(
                    io.BytesIO(output.getvalue().encode()),
                    mimetype='text/csv',
                    as_attachment=True,
                    download_name=filename
                )
            except ImportError:
                return jsonify({"error": "CSV export is not available due to missing dependencies"}), 500
        else:
            flash(f"Export failed: {result.get('error', 'Unknown error')}", 'error')
            return redirect(url_for('admin.analytics'))
    
    except Exception as e:
        flash(f"Error: {str(e)}", 'error')
        return redirect(url_for('admin.analytics'))

@admin_bp.route('/system-reports')
@admin_required
def system_reports():
    """Generate comprehensive system reports"""
    try:
        from services.analytics_service import AnalyticsService
        
        # Get analytics for different periods
        weekly_analytics = AnalyticsService.get_admin_analytics(7)
        monthly_analytics = AnalyticsService.get_admin_analytics(30)
        yearly_analytics = AnalyticsService.get_admin_analytics(365)
        
        return render_template('admin/system_reports.html',
                             weekly=weekly_analytics,
                             monthly=monthly_analytics,
                             yearly=yearly_analytics)
    
    except Exception as e:
        flash(f"Error generating reports: {str(e)}", 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/categories/create', methods=['POST'])
@admin_required
def create_category():
    try:
        data = request.get_json()
        business_id = data.get('business_id')
        name = data.get('name')
        description = data.get('description')
        
        if not business_id or not name:
            return jsonify({'success': False, 'message': 'Business ID and category name are required'})
        
        business = Business.objects(id=ObjectId(business_id)).first()
        if not business:
            return jsonify({'success': False, 'message': 'Business not found'})
        
        # Check if category already exists
        existing_category = Category.objects(business=business, name=name).first()
        if existing_category:
            return jsonify({'success': False, 'message': 'Category with this name already exists'})
        
        # Create new category
        category = Category(
            name=name,
            description=description,
            business=business
        )
        category.save()
        
        return jsonify({
            'success': True,
            'message': 'Category created successfully',
            'category': {
                'id': str(category.id),
                'name': category.name,
                'description': category.description
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from models import Business, Product, Category, Order, Customer, ChatSession, ChatMessage, ProductVariation, OrderItem
from services.auth.decorators import vendor_required
from services.auth.auth_manager import get_user_role
from services.image_service import update_product_image, get_image_url, delete_image_from_gridfs
from werkzeug.utils import secure_filename
from bson import ObjectId
from mongoengine.errors import DoesNotExist
from mongoengine.queryset.visitor import Q
import csv
import io
import os
import secrets
import string
from datetime import datetime, timedelta
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError as e:
    PANDAS_AVAILABLE = False
    print(f"Warning: pandas import failed: {e}")
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

vendor_bp = Blueprint('vendor', __name__, url_prefix='/vendor')

@vendor_bp.route('/dashboard')
@vendor_required
def dashboard():
    # Get vendor's businesses
    if get_user_role(current_user) == 'admin':
        businesses = Business.objects.all()
    else:
        businesses = Business.objects(vendor=current_user)
    
    # Get statistics for vendor's businesses
    business_list = list(businesses)
    
    if business_list:
        total_orders = Order.objects(business__in=business_list).count()
        paid_orders = Order.objects(business__in=business_list, payment_status='paid').count()
        
        # Calculate total revenue
        paid_orders_list = Order.objects(business__in=business_list, payment_status='paid')
        total_revenue = sum(order.total_amount for order in paid_orders_list)
        
        pending_orders = Order.objects(business__in=business_list, status='pending').count()
    else:
        total_orders = paid_orders = total_revenue = pending_orders = 0
    
    # Recent orders
    recent_orders = Order.objects(business__in=business_list).order_by('-created_at').limit(10) if business_list else []
    
    return render_template('vendor/dashboard.html',
                         businesses=businesses,
                         total_orders=total_orders,
                         paid_orders=paid_orders,
                         total_revenue=total_revenue,
                         pending_orders=pending_orders,
                         recent_orders=recent_orders)

@vendor_bp.route('/profile')
@vendor_required
def profile():
    return render_template('vendor/profile.html', vendor=current_user)

@vendor_bp.route('/profile/edit', methods=['GET', 'POST'])
@vendor_required
def edit_profile():
    if request.method == 'POST':
        current_user.name = request.form.get('name')
        current_user.email = request.form.get('email')
        current_user.phone_number = request.form.get('phone_number')
        
        current_user.save()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('vendor.profile'))
    
    return render_template('vendor/edit_profile.html', vendor=current_user)

@vendor_bp.route('/businesses')
@vendor_required
def businesses():
    if get_user_role(current_user) == 'admin':
        businesses = Business.objects.all()
    else:
        businesses = Business.objects(vendor=current_user)
    
    return render_template('vendor/businesses.html', businesses=businesses)

@vendor_bp.route('/businesses/add', methods=['GET', 'POST'])
@vendor_required
def add_business():
    if request.method == 'POST':
        business = Business(
            name=request.form.get('name'),
            description=request.form.get('description'),
            category=request.form.get('category'),
            email=request.form.get('email'),
            whatsapp_number=request.form.get('whatsapp_number'),
            vendor=current_user
        )
        
        business.save()
        flash('Business added successfully!', 'success')
        return redirect(url_for('vendor.businesses'))
    
    return render_template('vendor/add_business.html')

@vendor_bp.route('/businesses/<business_id>')
@vendor_required
def business_detail(business_id):
    try:
        business = Business.objects(id=ObjectId(business_id)).first()
        
        if not business:
            flash('Business not found.', 'error')
            return redirect(url_for('vendor.businesses'))
        
        # Check if vendor owns this business or is admin
        if get_user_role(current_user) != 'admin' and business.vendor != current_user:
            flash('Access denied.', 'error')
            return redirect(url_for('vendor.businesses'))
        
        products = Product.objects(business=business)
        categories = Category.objects(business=business)
        orders = Order.objects(business=business).order_by('-created_at').limit(10)
        
        return render_template('vendor/business_detail.html',
                             business=business,
                             products=products,
                             categories=categories,
                             orders=orders)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('vendor.businesses'))

@vendor_bp.route('/businesses/<business_id>/edit', methods=['GET', 'POST'])
@vendor_required
def edit_business(business_id):
    try:
        business = Business.objects(id=ObjectId(business_id)).first()
        
        if not business:
            flash('Business not found.', 'error')
            return redirect(url_for('vendor.businesses'))
        
        # Check if vendor owns this business or is admin
        if get_user_role(current_user) != 'admin' and business.vendor != current_user:
            flash('Access denied.', 'error')
            return redirect(url_for('vendor.businesses'))
        
        if request.method == 'POST':
            business.name = request.form.get('name')
            business.description = request.form.get('description')
            business.category = request.form.get('category')
            business.email = request.form.get('email')
            business.whatsapp_number = request.form.get('whatsapp_number')
            business.custom_instructions = request.form.get('custom_instructions')
            
            business.save()
            flash('Business updated successfully!', 'success')
            return redirect(url_for('vendor.business_detail', business_id=business_id))
        
        return render_template('vendor/edit_business.html', business=business)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('vendor.businesses'))

@vendor_bp.route('/businesses/<business_id>/whatsapp-config', methods=['GET', 'POST'])
@vendor_required
def whatsapp_config(business_id):
    try:
        business = Business.objects(id=ObjectId(business_id)).first()
        
        if not business:
            flash('Business not found.', 'error')
            return redirect(url_for('vendor.businesses'))
        
        # Check if vendor owns this business or is admin
        if get_user_role(current_user) != 'admin' and business.vendor != current_user:
            flash('Access denied.', 'error')
            return redirect(url_for('vendor.businesses'))
        
        if request.method == 'POST':
            business.whatsapp_api_token = request.form.get('whatsapp_api_token')
            business.whatsapp_phone_id = request.form.get('whatsapp_phone_id')
            
            business.save()
            flash('WhatsApp configuration updated successfully!', 'success')
            return redirect(url_for('vendor.business_detail', business_id=business_id))
        
        return render_template('vendor/whatsapp_config.html', business=business)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('vendor.businesses'))

@vendor_bp.route('/products/<business_id>')
@vendor_required
def products(business_id):
    try:
        business = Business.objects(id=ObjectId(business_id)).first()
        
        if not business:
            flash('Business not found.', 'error')
            return redirect(url_for('vendor.businesses'))
        
        # Check if vendor owns this business or is admin
        if get_user_role(current_user) != 'admin' and business.vendor != current_user:
            flash('Access denied.', 'error')
            return redirect(url_for('vendor.businesses'))
        
        products = Product.objects(business=business)
        categories = Category.objects(business=business)
        
        return render_template('vendor/products.html',
                             business=business,
                             products=products,
                             categories=categories)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('vendor.businesses'))

@vendor_bp.route('/products/<business_id>/add', methods=['GET', 'POST'])
@vendor_required
def add_product(business_id):
    try:
        business = Business.objects(id=ObjectId(business_id)).first()
        
        if not business:
            flash('Business not found.', 'error')
            return redirect(url_for('vendor.businesses'))
        
        # Check if vendor owns this business or is admin
        if get_user_role(current_user) != 'admin' and business.vendor != current_user:
            flash('Access denied.', 'error')
            return redirect(url_for('vendor.businesses'))
        
        categories = Category.objects(business=business)
        
        if request.method == 'POST':
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
            
            # Handle image upload
            if 'product_image' in request.files:
                image_file = request.files['product_image']
                if image_file and image_file.filename != '':
                    try:
                        update_product_image(product, image_file)
                        flash('Product and image uploaded successfully!', 'success')
                    except Exception as e:
                        flash(f'Product saved but image upload failed: {str(e)}', 'warning')
            
            product.save()
            
            if 'product_image' not in request.files or not request.files['product_image'].filename:
                flash('Product added successfully!', 'success')
            
            return redirect(url_for('vendor.products', business_id=business_id))
        
        return render_template('vendor/add_product.html', business=business, categories=categories)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('vendor.businesses'))

@vendor_bp.route('/products/<product_id>/edit', methods=['GET', 'POST'])
@vendor_required
def edit_product(product_id):
    try:
        product = Product.objects(id=ObjectId(product_id)).first()
        
        if not product:
            flash('Product not found.', 'error')
            return redirect(url_for('vendor.businesses'))
        
        # Check if vendor owns this product's business or is admin
        if get_user_role(current_user) != 'admin' and product.business.vendor != current_user:
            flash('Access denied.', 'error')
            return redirect(url_for('vendor.businesses'))
        
        categories = Category.objects(business=product.business)
        
        if request.method == 'POST':
            product.name = request.form.get('name')
            product.description = request.form.get('description')
            product.price = float(request.form.get('price'))
            
            if request.form.get('category_id'):
                product.category = Category.objects(id=ObjectId(request.form.get('category_id'))).first()
            else:
                product.category = None
                
            product.allows_customization = bool(request.form.get('allows_customization'))
            product.has_variations = bool(request.form.get('has_variations'))
            product.is_active = bool(request.form.get('is_active'))
            
            # Handle image upload
            if 'product_image' in request.files:
                image_file = request.files['product_image']
                if image_file and image_file.filename != '':
                    try:
                        update_product_image(product, image_file)
                        flash('Product and image updated successfully!', 'success')
                    except Exception as e:
                        flash(f'Product updated but image upload failed: {str(e)}', 'warning')
                else:
                    flash('Product updated successfully!', 'success')
            else:
                flash('Product updated successfully!', 'success')
            
            product.save()
            return redirect(url_for('vendor.products', business_id=str(product.business.id)))
        
        return render_template('vendor/edit_product.html', 
                             business=product.business, 
                             product=product, 
                             categories=categories)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('vendor.businesses'))

@vendor_bp.route('/products/<product_id>/toggle-status', methods=['POST'])
@vendor_required  
def toggle_product_status(product_id):
    try:
        product = Product.objects(id=ObjectId(product_id)).first()
        
        if not product:
            return jsonify({'success': False, 'message': 'Product not found'})
        
        # Check if vendor owns this product's business or is admin
        if get_user_role(current_user) != 'admin' and product.business.vendor != current_user:
            return jsonify({'success': False, 'message': 'Access denied'})
        
        product.is_active = not product.is_active
        product.save()
        
        return jsonify({
            'success': True, 
            'message': f'Product {"activated" if product.is_active else "deactivated"} successfully',
            'is_active': product.is_active
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@vendor_bp.route('/products/<product_id>/delete', methods=['DELETE'])
@vendor_required
def delete_product(product_id):
    try:
        product = Product.objects(id=ObjectId(product_id)).first()
        
        if not product:
            return jsonify({'success': False, 'message': 'Product not found'})
        
        # Check if vendor owns this product's business or is admin
        if get_user_role(current_user) != 'admin' and product.business.vendor != current_user:
            return jsonify({'success': False, 'message': 'Access denied'})
        
        product.delete()
        return jsonify({'success': True, 'message': 'Product deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@vendor_bp.route('/products/<product_id>/delete-image', methods=['POST'])
@vendor_required
def delete_product_image(product_id):
    try:
        product = Product.objects(id=ObjectId(product_id)).first()
        
        if not product:
            return jsonify({'success': False, 'message': 'Product not found'})
        
        # Check if vendor owns this product's business or is admin
        if get_user_role(current_user) != 'admin' and product.business.vendor != current_user:
            return jsonify({'success': False, 'message': 'Access denied'})
        
        # Delete image if exists
        if product.image_file_id:
            if delete_image_from_gridfs(product.image_file_id):
                product.image_file_id = None
                product.image_filename = None
                product.image_content_type = None
                product.save()
                return jsonify({'success': True, 'message': 'Image deleted successfully'})
            else:
                return jsonify({'success': False, 'message': 'Failed to delete image'})
        else:
            return jsonify({'success': False, 'message': 'No image to delete'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@vendor_bp.route('/categories/<business_id>')
@vendor_required
def categories(business_id):
    try:
        business = Business.objects(id=ObjectId(business_id)).first()
        
        if not business:
            flash('Business not found.', 'error')
            return redirect(url_for('vendor.businesses'))
        
        # Check if vendor owns this business or is admin
        if get_user_role(current_user) != 'admin' and business.vendor != current_user:
            flash('Access denied.', 'error')
            return redirect(url_for('vendor.businesses'))
        
        categories = Category.objects(business=business)
        
        return render_template('vendor/categories.html',
                             business=business,
                             categories=categories)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('vendor.businesses'))

@vendor_bp.route('/categories/<business_id>/add', methods=['GET', 'POST'])
@vendor_required
def add_category(business_id):
    try:
        business = Business.objects(id=ObjectId(business_id)).first()
        
        if not business:
            flash('Business not found.', 'error')
            return redirect(url_for('vendor.businesses'))
        
        # Check if vendor owns this business or is admin
        if get_user_role(current_user) != 'admin' and business.vendor != current_user:
            flash('Access denied.', 'error')
            return redirect(url_for('vendor.businesses'))
        
        if request.method == 'POST':
            category = Category(
                name=request.form.get('name'),
                description=request.form.get('description'),
                business=business
            )
            category.save()
            flash('Category added successfully!', 'success')
            return redirect(url_for('vendor.categories', business_id=business_id))
        
        return render_template('vendor/add_category.html', business=business)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('vendor.businesses'))

@vendor_bp.route('/orders/<business_id>')
@vendor_required
def orders(business_id):
    try:
        business = Business.objects(id=ObjectId(business_id)).first()
        
        if not business:
            flash('Business not found.', 'error')
            return redirect(url_for('vendor.businesses'))
        
        # Check if vendor owns this business or is admin
        if get_user_role(current_user) != 'admin' and business.vendor != current_user:
            flash('Access denied.', 'error')
            return redirect(url_for('vendor.businesses'))
        
        status_filter = request.args.get('status')
        orders_query = Order.objects(business=business)
        
        if status_filter:
            orders_query = orders_query.filter(status=status_filter)
        
        orders = orders_query.order_by('-created_at')
        
        return render_template('vendor/orders.html',
                             business=business,
                             orders=orders,
                             status_filter=status_filter)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('vendor.businesses'))

@vendor_bp.route('/orders/<order_id>/update-status', methods=['POST'])
@vendor_required
def update_order_status(order_id):
    try:
        order = Order.objects(id=ObjectId(order_id)).first()
        
        if not order:
            return jsonify({'success': False, 'message': 'Order not found'})
        
        # Check if vendor owns this order's business or is admin
        if get_user_role(current_user) != 'admin' and order.business.vendor != current_user:
            return jsonify({'success': False, 'message': 'Access denied'})
        
        new_status = request.json.get('status')
        if new_status in ['pending', 'processing', 'delivered', 'cancelled']:
            order.status = new_status
            order.save()
            
            # Send WhatsApp notification to customer
            from services.messaging_service import send_whatsapp_text_message
            customer_phone = order.customer.phone_number
            message = f"Your order {order.order_number} status has been updated to: {new_status.title()}"
            
            try:
                send_whatsapp_text_message(customer_phone, message)
            except Exception as e:
                # Log error but don't fail the status update
                pass
            
            return jsonify({'success': True, 'message': 'Order status updated successfully'})
        
        return jsonify({'success': False, 'message': 'Invalid status'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@vendor_bp.route('/chat-sessions/<business_id>')
@vendor_required
def chat_sessions(business_id):
    try:
        business = Business.objects(id=ObjectId(business_id)).first()
        
        if not business:
            flash('Business not found.', 'error')
            return redirect(url_for('vendor.businesses'))
        
        # Check if vendor owns this business or is admin
        if get_user_role(current_user) != 'admin' and business.vendor != current_user:
            flash('Access denied.', 'error')
            return redirect(url_for('vendor.businesses'))
        
        sessions = ChatSession.objects(business=business).order_by('-created_at')
        
        return render_template('vendor/chat_sessions.html',
                             business=business,
                             sessions=sessions)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('vendor.businesses'))

@vendor_bp.route('/analytics/<business_id>')
@vendor_required
def analytics(business_id):
    try:
        business = Business.objects(id=ObjectId(business_id)).first()
        
        if not business:
            flash('Business not found.', 'error')
            return redirect(url_for('vendor.businesses'))
        
        # Check if vendor owns this business or is admin
        if get_user_role(current_user) != 'admin' and business.vendor != current_user:
            flash('Access denied.', 'error')
            return redirect(url_for('vendor.businesses'))
        
        days = request.args.get('days', 30, type=int)
        
        from services.analytics_service import AnalyticsService
        analytics_data = AnalyticsService.get_business_analytics(str(business.id), days)
        
        return render_template('vendor/analytics.html',
                             business=business,
                             analytics=analytics_data,
                             days=days)
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('vendor.businesses'))

@vendor_bp.route('/bulk-messaging')
@vendor_required
def bulk_messaging():
    if get_user_role(current_user) == 'admin':
        businesses = Business.objects.all()
    else:
        businesses = Business.objects(vendor=current_user)
    return render_template('vendor/bulk_messaging.html', businesses=businesses)

@vendor_bp.route('/export-data/<business_id>')
@vendor_required
def export_data(business_id):
    try:
        business = Business.objects(id=ObjectId(business_id)).first()
        
        if not business:
            flash('Business not found.', 'error')
            return redirect(url_for('vendor.businesses'))
        
        # Check if vendor owns this business or is admin
        if get_user_role(current_user) != 'admin' and business.vendor != current_user:
            flash('Access denied.', 'error')
            return redirect(url_for('vendor.businesses'))
        
        # Create CSV data
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['Order Number', 'Customer Phone', 'Product Names', 'Total Amount', 'Status', 'Date'])
        
        # Write order data
        orders = Order.objects(business=business)
        for order in orders:
            product_names = []
            for item in order.order_items:
                product_names.append(f"{item.product.name} (x{item.quantity})")
            
            writer.writerow([
                order.order_number,
                order.customer.phone_number,
                ', '.join(product_names),
                order.total_amount,
                order.status,
                order.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        # Create response
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'{business.name}_orders_export.csv'
        )
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('vendor.businesses'))

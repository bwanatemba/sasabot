from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from models import Business, Product, Category, Order, Customer, ChatSession, ChatMessage, ProductVariation, OrderItem, OrderIssue, Vendor
from services.auth.decorators import vendor_required
from services.auth.auth_manager import get_user_role
from services.image_service import update_product_image, get_image_url, delete_image_from_gridfs
from werkzeug.utils import secure_filename
from bson import ObjectId
from mongoengine.errors import DoesNotExist
from mongoengine.queryset.visitor import Q
import csv
import io
import logging
import os
import random
import secrets
import string
from datetime import datetime, timedelta

# Handle pandas import gracefully
PANDAS_AVAILABLE = False
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError as e:
    logging.getLogger(__name__).warning(f"pandas not available: {e}")
    pd = None

# Handle reportlab import gracefully  
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    REPORTLAB_AVAILABLE = True
except ImportError as e:
    logging.getLogger(__name__).warning(f"reportlab not available: {e}")
    REPORTLAB_AVAILABLE = False

vendor_bp = Blueprint('vendor', __name__, url_prefix='/vendor')

def cleanup_database_connections():
    """Clean up stale database connections"""
    try:
        from mongoengine import disconnect, connect
        import os
        
        # Disconnect existing connections
        disconnect()
        
        # Reconnect with fresh connection
        mongodb_uri = os.getenv('MONGODB_URI')
        if mongodb_uri:
            connect(host=mongodb_uri)
            return True
    except Exception as e:
        logging.getLogger(__name__).error(f"Database cleanup failed: {e}")
    return False

@vendor_bp.route('/dashboard')
@vendor_required
def dashboard():
    logger = logging.getLogger(__name__)
    try:
        logger.info(f"Dashboard accessed by user: {current_user.id if current_user else 'None'}")
        
        # Test database connectivity
        try:
            from mongoengine import connection
            connection.get_db()
            logger.info("Database connection verified")
        except Exception as db_error:
            logger.error(f"Database connection failed: {db_error}")
            # Try to cleanup and reconnect
            if cleanup_database_connections():
                logger.info("Database reconnection successful")
            else:
                flash('Database connection error. Please try again later.', 'error')
                return redirect(url_for('main.index'))
        
        # Validate current user
        if not current_user or not current_user.is_authenticated:
            logger.error("Dashboard access attempted without authentication")
            flash('Authentication required', 'error')
            return redirect(url_for('auth.login'))
        
        # Initialize default values
        businesses = []
        total_orders = paid_orders = total_revenue = pending_orders = 0
        recent_orders = []
        
        # Get vendor's businesses
        user_role = get_user_role(current_user)
        logger.info(f"User role: {user_role}")
        
        if user_role == 'admin':
            businesses = list(Business.objects.all())
            logger.info(f"Admin accessing all businesses, count: {len(businesses)}")
        elif user_role == 'vendor':
            # Ensure vendor exists in database
            try:
                vendor_obj = Vendor.objects(id=current_user.id).first()
                if not vendor_obj:
                    logger.error(f"Vendor object not found for user ID: {current_user.id}")
                    flash('Vendor profile not found. Please contact support.', 'error')
                    return redirect(url_for('main.index'))
                
                businesses = list(Business.objects(vendor=vendor_obj))
                logger.info(f"Vendor accessing their businesses, count: {len(businesses)}")
            except Exception as e:
                logger.error(f"Error fetching vendor businesses: {e}")
                businesses = []
        else:
            logger.warning(f"Invalid user role: {user_role}")
            flash('Invalid user role', 'error')
            return redirect(url_for('main.index'))
        
        # Get statistics for vendor's businesses
        if businesses:
            logger.info(f"Processing statistics for {len(businesses)} businesses")
            
            # Use try-catch for each database query
            try:
                total_orders = Order.objects(business__in=businesses).count()
                logger.info(f"Total orders: {total_orders}")
            except Exception as e:
                logger.error(f"Error getting total orders: {e}")
                total_orders = 0
            
            try:
                paid_orders = Order.objects(business__in=businesses, payment_status='paid').count()
                logger.info(f"Paid orders: {paid_orders}")
            except Exception as e:
                logger.error(f"Error getting paid orders: {e}")
                paid_orders = 0
            
            try:
                # Calculate total revenue with safety checks
                paid_orders_list = Order.objects(business__in=businesses, payment_status='paid')
                total_revenue = 0
                for order in paid_orders_list:
                    if hasattr(order, 'total_amount') and order.total_amount:
                        total_revenue += float(order.total_amount)
                logger.info(f"Total revenue: {total_revenue}")
            except Exception as e:
                logger.error(f"Error calculating revenue: {e}")
                total_revenue = 0
            
            try:
                pending_orders = Order.objects(business__in=businesses, status='pending').count()
                logger.info(f"Pending orders: {pending_orders}")
            except Exception as e:
                logger.error(f"Error getting pending orders: {e}")
                pending_orders = 0
            
            try:
                # Recent orders
                recent_orders = list(Order.objects(business__in=businesses).order_by('-created_at').limit(10))
                logger.info(f"Retrieved {len(recent_orders)} recent orders")
            except Exception as e:
                logger.error(f"Error getting recent orders: {e}")
                recent_orders = []
        else:
            logger.info("No businesses found for user")
        
        # Ensure all template variables are properly set with safe defaults
        template_vars = {
            'businesses': businesses or [],
            'total_orders': max(0, int(total_orders)),
            'paid_orders': max(0, int(paid_orders)),
            'total_revenue': max(0.0, float(total_revenue)),
            'pending_orders': max(0, int(pending_orders)),
            'recent_orders': recent_orders or []
        }
        
        logger.info(f"Template variables: {template_vars}")
        
        # Validate template variables before rendering
        for key, value in template_vars.items():
            if value is None:
                logger.warning(f"Template variable {key} is None, setting to default")
                if key in ['businesses', 'recent_orders']:
                    template_vars[key] = []
                else:
                    template_vars[key] = 0
        
        # Try to render the main template, fallback to simple template if it fails
        try:
            return render_template('vendor/dashboard.html', **template_vars)
        except Exception as template_error:
            logger.error(f"Main template rendering failed: {template_error}")
            try:
                return render_template('vendor/dashboard_fallback.html', **template_vars)
            except Exception as fallback_error:
                logger.error(f"Fallback template also failed: {fallback_error}")
                # Return a very basic response
                return f"""
                <html>
                <head><title>Vendor Dashboard</title></head>
                <body>
                    <h1>Vendor Dashboard</h1>
                    <p>Orders: {template_vars['total_orders']}</p>
                    <p>Revenue: KES {template_vars['total_revenue']}</p>
                    <p>Businesses: {len(template_vars['businesses'])}</p>
                    <a href="/vendor/businesses">View Businesses</a>
                </body>
                </html>
                """, 200
    
    except Exception as e:
        logger.error(f"Error in vendor dashboard: {str(e)}", exc_info=True)
        flash('An error occurred while loading the dashboard. Please try again.', 'error')
        return redirect(url_for('main.index'))

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

@vendor_bp.route('/whatsapp/test', methods=['POST'])
@vendor_required
def test_whatsapp_connection():
    """Test WhatsApp API connection"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400
            
        token = data.get('token')
        phone_id = data.get('phone_id')
        business_id = data.get('business_id')
        
        if not token or not phone_id:
            return jsonify({'success': False, 'message': 'API token and phone ID are required'}), 400
        
        # Import requests for API testing
        import requests
        
        # Test the WhatsApp API connection
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Make a simple API call to verify credentials
        url = f'https://graph.facebook.com/v18.0/{phone_id}'
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return jsonify({'success': True, 'message': 'Connection successful'})
        else:
            error_msg = 'Invalid credentials or phone ID'
            try:
                error_data = response.json()
                if 'error' in error_data and 'message' in error_data['error']:
                    error_msg = error_data['error']['message']
            except:
                pass
            return jsonify({'success': False, 'message': error_msg})
            
    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'message': 'Connection timeout. Please try again.'})
    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'message': f'Connection error: {str(e)}'})
    except Exception as e:
        logging.getLogger(__name__).error(f"WhatsApp test error: {e}")
        return jsonify({'success': False, 'message': 'An error occurred while testing the connection'})

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
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = 10  # Number of products per page
        skip = (page - 1) * per_page
        
        # Get paginated products using MongoEngine skip/limit
        products_query = Product.objects(business=business)
        total = products_query.count()
        products_list = products_query.skip(skip).limit(per_page)
        
        # Calculate order counts for each product
        for product in products_list:
            # Count orders containing this product
            order_count = Order.objects(order_items__product=product).count()
            product.order_count = order_count
        
        # Create pagination object
        from services.pagination import Pagination
        products = Pagination(page, per_page, total, products_list)
        
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
        
        # Calculate order count for this product
        order_count = Order.objects(order_items__product=product).count()
        product.order_count = order_count
        
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

@vendor_bp.route('/categories/<business_id>', methods=['GET', 'POST'])
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
        
        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'add':
                # Create new category
                category = Category(
                    name=request.form.get('name'),
                    description=request.form.get('description'),
                    business=business
                )
                category.save()
                flash('Category added successfully!', 'success')
                return redirect(url_for('vendor.categories', business_id=business_id))
            
            elif action == 'edit':
                # Edit existing category
                category_id = request.form.get('category_id')
                category = Category.objects(id=ObjectId(category_id)).first()
                if category and category.business == business:
                    category.name = request.form.get('name')
                    category.description = request.form.get('description')
                    category.save()
                    flash('Category updated successfully!', 'success')
                else:
                    flash('Category not found or access denied.', 'error')
                return redirect(url_for('vendor.categories', business_id=business_id))
            
            elif action == 'delete':
                # Delete category
                category_id = request.form.get('category_id')
                category = Category.objects(id=ObjectId(category_id)).first()
                if category and category.business == business:
                    # Check if category has products
                    products_count = Product.objects(category=category).count()
                    if products_count == 0:
                        category.delete()
                        flash('Category deleted successfully!', 'success')
                    else:
                        flash('Cannot delete category that has products assigned.', 'error')
                else:
                    flash('Category not found or access denied.', 'error')
                return redirect(url_for('vendor.categories', business_id=business_id))
        
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
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = 20
        skip = (page - 1) * per_page
        
        status_filter = request.args.get('status')
        orders_query = Order.objects(business=business)
        
        if status_filter:
            orders_query = orders_query.filter(status=status_filter)
        
        # Get paginated orders
        total = orders_query.count()
        orders_list = orders_query.order_by('-created_at').skip(skip).limit(per_page)
        
        # Create pagination object
        from services.pagination import Pagination
        orders = Pagination(page, per_page, total, orders_list)
        
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
        # Validate ObjectId format
        try:
            obj_id = ObjectId(order_id)
        except Exception:
            return jsonify({'success': False, 'message': 'Invalid order ID format'})
            
        order = Order.objects(id=obj_id).first()
        
        if not order:
            return jsonify({'success': False, 'message': 'Order not found'})
        
        # Check if vendor owns this order's business or is admin
        if get_user_role(current_user) != 'admin' and order.business.vendor != current_user:
            return jsonify({'success': False, 'message': 'Access denied'})
        
        # Validate request content type
        if not request.is_json:
            return jsonify({'success': False, 'message': 'Request must be JSON'})
            
        new_status = request.json.get('status')
        if not new_status:
            return jsonify({'success': False, 'message': 'Status is required'})
            
        valid_statuses = ['pending', 'paid', 'processing', 'completed', 'delivered', 'cancelled']
        if new_status not in valid_statuses:
            return jsonify({'success': False, 'message': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'})
            
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
            logging.getLogger(__name__).warning(f"WhatsApp notification failed: {e}")
        
        return jsonify({'success': True, 'message': 'Order status updated successfully'})
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error updating order status: {e}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@vendor_bp.route('/order-issues/<business_id>')
@vendor_required
def order_issues(business_id):
    """Display order issues for a specific business"""
    try:
        business = Business.objects(id=ObjectId(business_id)).first()
        
        if not business:
            flash('Business not found.', 'error')
            return redirect(url_for('vendor.businesses'))
        
        # Check if vendor owns this business or is admin
        if get_user_role(current_user) != 'admin' and business.vendor != current_user:
            flash('Access denied.', 'error')
            return redirect(url_for('vendor.businesses'))
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = 20
        skip = (page - 1) * per_page
        
        # Get order issues for this business
        issues_query = OrderIssue.objects(business=business)
        total = issues_query.count()
        issues_list = issues_query.order_by('-created_at').skip(skip).limit(per_page)
        
        # Create pagination object
        from services.pagination import Pagination
        issues = Pagination(page, per_page, total, issues_list)
        
        return render_template('vendor/order_issues.html', 
                             business=business, 
                             issues=issues,
                             active_page='order_issues')
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error loading order issues: {e}")
        flash(f'Error loading order issues: {str(e)}', 'error')
        return redirect(url_for('vendor.businesses'))

@vendor_bp.route('/order-issues/<issue_id>/update-status', methods=['POST'])
@vendor_required
def update_issue_status(issue_id):
    """Update the status of an order issue"""
    try:
        issue = OrderIssue.objects(id=ObjectId(issue_id)).first()
        
        if not issue:
            return jsonify({'success': False, 'message': 'Issue not found'})
        
        # Check if vendor owns this issue's business or is admin
        if get_user_role(current_user) != 'admin' and issue.business.vendor != current_user:
            return jsonify({'success': False, 'message': 'Access denied'})
        
        if not request.is_json:
            return jsonify({'success': False, 'message': 'Request must be JSON'})
            
        new_status = request.json.get('status')
        if not new_status:
            return jsonify({'success': False, 'message': 'Status is required'})
            
        valid_statuses = ['open', 'in_progress', 'resolved', 'closed']
        if new_status not in valid_statuses:
            return jsonify({'success': False, 'message': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'})
            
        issue.status = new_status
        issue.save()
        
        # Send WhatsApp notification to customer
        from services.business_messaging_service import send_business_whatsapp_text_message
        customer_phone = issue.customer.phone_number
        message = f"Update on your issue with order {issue.order.order_number}: Status changed to {new_status.replace('_', ' ').title()}. Thank you for your patience!"
        
        try:
            send_business_whatsapp_text_message(customer_phone, message, issue.business)
        except Exception as e:
            # Log error but don't fail the status update
            logging.getLogger(__name__).warning(f"WhatsApp notification failed: {e}")
        
        return jsonify({'success': True, 'message': 'Issue status updated successfully'})
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error updating issue status: {e}")
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
        
        # Get pagination parameters
        page = request.args.get('page', 1, type=int)
        per_page = 20
        skip = (page - 1) * per_page
        
        # Get paginated sessions
        sessions_query = ChatSession.objects(business=business)
        total = sessions_query.count()
        sessions_list = sessions_query.order_by('-created_at').skip(skip).limit(per_page)
        
        # Create pagination object
        from services.pagination import Pagination
        sessions = Pagination(page, per_page, total, sessions_list)
        
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
        
        return render_template('vendor/business_analytics.html',
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

@vendor_bp.route('/products/<product_id>/variations', methods=['GET', 'POST'])
@vendor_required
def product_variations(product_id):
    try:
        product = Product.objects(id=ObjectId(product_id)).first()
        
        if not product:
            flash('Product not found.', 'error')
            return redirect(url_for('vendor.businesses'))
        
        # Check if vendor owns this product's business or is admin
        if get_user_role(current_user) != 'admin' and product.business.vendor != current_user:
            flash('Access denied.', 'error')
            return redirect(url_for('vendor.businesses'))
        
        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'add_variation':
                # Add new variation
                variation_name = request.form.get('variation_name', '').strip()
                variation_price = request.form.get('variation_price', '').strip()
                variation_description = request.form.get('variation_description', '').strip()
                
                if not variation_name or not variation_price:
                    flash('Variation name and price are required.', 'error')
                    return redirect(url_for('vendor.product_variations', product_id=product_id))
                
                try:
                    price = float(variation_price)
                    if price < 0:
                        flash('Price must be a positive number.', 'error')
                        return redirect(url_for('vendor.product_variations', product_id=product_id))
                except ValueError:
                    flash('Invalid price format.', 'error')
                    return redirect(url_for('vendor.product_variations', product_id=product_id))
                
                # Generate variation ID
                variation_id = f"VAR{random.randint(100000, 999999)}"
                while any(v.variation_id == variation_id for v in product.variations):
                    variation_id = f"VAR{random.randint(100000, 999999)}"
                
                # Create new variation
                new_variation = ProductVariation(
                    variation_id=variation_id,
                    name=variation_name,
                    price=price,
                    description=variation_description
                )
                
                # Add to product
                product.variations.append(new_variation)
                product.has_variations = True
                product.save()
                
                flash('Variation added successfully!', 'success')
                return redirect(url_for('vendor.product_variations', product_id=product_id))
            
            elif action == 'delete_variation':
                variation_id = request.form.get('variation_id')
                if variation_id:
                    # Find and remove variation
                    product.variations = [v for v in product.variations if v.variation_id != variation_id]
                    
                    # Update has_variations flag
                    product.has_variations = len(product.variations) > 0
                    product.save()
                    
                    flash('Variation deleted successfully!', 'success')
                else:
                    flash('Variation not found.', 'error')
                
                return redirect(url_for('vendor.product_variations', product_id=product_id))
            
            elif action == 'toggle_variation':
                variation_id = request.form.get('variation_id')
                if variation_id:
                    # Find and toggle variation status
                    for variation in product.variations:
                        if variation.variation_id == variation_id:
                            variation.is_active = not variation.is_active
                            break
                    
                    product.save()
                    flash('Variation status updated!', 'success')
                else:
                    flash('Variation not found.', 'error')
                
                return redirect(url_for('vendor.product_variations', product_id=product_id))
        
        return render_template('vendor/product_variations.html', product=product)
        
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('vendor.businesses'))

@vendor_bp.route('/orders/<order_id>/details')
@vendor_required
def order_details(order_id):
    """Return order details fragment for modal display"""
    try:
        order = Order.objects(id=ObjectId(order_id)).first()
        
        if not order:
            return '<p class="text-danger">Order not found</p>', 404
        
        # Check if vendor owns this order's business or is admin
        if get_user_role(current_user) != 'admin' and order.business.vendor != current_user:
            return '<p class="text-danger">Access denied</p>', 403
        
        return render_template('admin/order_details_fragment.html', order=order)
        
    except Exception as e:
        return f'<p class="text-danger">Error loading order details: {str(e)}</p>', 500

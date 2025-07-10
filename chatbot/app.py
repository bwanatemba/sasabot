from flask import Flask, request, jsonify, send_from_directory, render_template, flash, redirect, url_for
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect, CSRFError
from services import messaging_service
import os
import logging
from functools import wraps
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Import database and authentication
from database.config import create_database_config, init_database
from services.auth.auth_manager import init_login_manager, get_user_role
from flask_login import current_user

# Import routes
from routes.main import main_bp
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.vendor import vendor_bp
from routes.api import api_bp

load_dotenv()

def setup_logging():
    """
    Set up logging configuration with proper directory creation
    and error handling.
    """
    try:
        # Create logs directory if it doesn't exist
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        # Generate log filename
        log_file = log_dir / f'app_{datetime.now().strftime("%Y%m%d")}.log'
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(str(log_file))
            ]
        )
        
        logger = logging.getLogger(__name__)
        logger.info(f"Logging initialized. Log file: {log_file}")
        return logger
        
    except Exception as e:
        # Set up basic console logging if file logging fails
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to set up file logging: {str(e)}")
        logger.info("Falling back to console logging only")
        return logger

logger = setup_logging()

def create_app():
    """Application factory"""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Initialize CSRF Protection
    csrf = CSRFProtect(app)
    
    # File upload configuration
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size
    app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
    
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Enable CORS for frontend
    CORS(app, origins=[
        "https://*.vercel.app",
        "http://localhost:3000",
        "http://localhost:5000"
    ])
    
    # Database configuration
    app = create_database_config(app)
    
    # Initialize Flask-Login
    init_login_manager(app)
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(vendor_bp)
    app.register_blueprint(api_bp)
    
    # Exempt API routes from CSRF protection
    csrf.exempt(api_bp)
    
    # Template context processors
    @app.context_processor
    def inject_user_role():
        return dict(get_user_role=get_user_role)
    
    @app.context_processor
    def inject_current_user():
        return dict(current_user=current_user)
    
    # Custom template filters
    @app.template_filter('product_count')
    def product_count_filter(business):
        """Get the count of products for a business"""
        from models import Product
        count = Product.objects(business=business).count()
        return int(count) if count is not None else 0
    
    @app.template_filter('order_count')
    def order_count_filter(business):
        """Get the count of orders for a business"""
        from models import Order
        count = Order.objects(business=business).count()
        return int(count) if count is not None else 0
    
    @app.template_filter('category_count')
    def category_count_filter(business):
        """Get the count of categories for a business"""
        from models import Category
        count = Category.objects(business=business).count()
        return int(count) if count is not None else 0
    
    @app.template_filter('category_products')
    def category_products_filter(category):
        """Get products for a category"""
        from models import Product
        return list(Product.objects(category=category))
    
    @app.template_filter('total_messages')
    def total_messages_filter(sessions):
        """Get total count of messages across all sessions"""
        if not sessions or not hasattr(sessions, 'items') or not sessions.items:
            return 0
        total = 0
        for session in sessions.items:
            total += len(session.messages) if session.messages else 0
        return total
    
    # Register error handlers
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        flash('Security token expired or missing. Please try again.', 'error')
        return redirect(request.referrer or url_for('main.index'))
    
    @app.errorhandler(400)
    def handle_bad_request(e):
        # Check if this is an API request or expects JSON response
        if request.path.startswith('/api/') or request.is_json or 'application/json' in request.headers.get('Accept', ''):
            return jsonify({"error": "Bad request, check your JSON payload"}), 400
        else:
            # For form submissions and other requests, show a proper error page
            flash('Bad request. Please check your form data and try again.', 'error')
            return redirect(request.referrer or url_for('main.index'))

    @app.errorhandler(404)
    def handle_not_found(e):
        if request.path.startswith('/api/'):
            return jsonify({"error": "Endpoint not found"}), 404
        return "Page not found", 404

    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        return jsonify({"error": f"Method {request.method} is not allowed for this endpoint"}), 405

    @app.errorhandler(500)
    def handle_server_error(e):
        logger.error(f"Server error: {str(e)}", exc_info=True)
        if request.path.startswith('/api/'):
            return jsonify({"error": "Internal server error occurred"}), 500
        if request.path.startswith('/vendor/'):
            return render_template('errors/500.html'), 500
        return "Internal server error", 500
    
    # Add error logging middleware
    @app.before_request
    def log_request_info():
        if request.path.startswith('/vendor/'):
            logger.info(f"Vendor request: {request.method} {request.path} from {request.remote_addr}")

    @app.after_request
    def log_response_info(response):
        if request.path.startswith('/vendor/') and response.status_code >= 400:
            logger.error(f"Vendor response error: {response.status_code} for {request.path}")
        return response

    # Favicon route
    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static', 'images'),
                                 'favicon.ico', mimetype='image/vnd.microsoft.icon')
    
    # Health check route
    @app.route('/health')
    def health_check():
        try:
            # Test database connection
            from models import Admin
            Admin.objects.first()
            return jsonify({
                "status": "healthy",
                "database": "connected",
                "timestamp": datetime.now().isoformat()
            }), 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return jsonify({
                "status": "unhealthy", 
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }), 500
    
    # Initialize database
    init_database(app)
    
    # Handle Incoming WhatsApp Messages (exempt from CSRF)
    @app.route('/whatsapp/message', methods=['GET', 'POST'])
    @csrf.exempt
    def handle_whatsapp_webhook():
        if request.method == 'GET':
            return messaging_service.verify_webhook()
        return messaging_service.process_whatsapp_message(request.json)
    
    return app

app = create_app()

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            logger.warning('API request made without API key')
            return jsonify({"error": "No API key provided"}), 401
        
        if api_key != os.getenv('API_KEY'):
            logger.warning(f'Invalid API key used: {api_key[:6]}...')
            return jsonify({"error": "Invalid API key"}), 401
        
        return f(*args, **kwargs)
    return decorated_function

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 5000)))


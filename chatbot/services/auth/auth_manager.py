from flask_login import LoginManager
from models import Admin, Vendor
from bson import ObjectId
from mongoengine.errors import DoesNotExist

login_manager = LoginManager()

def init_login_manager(app):
    """Initialize Flask-Login"""
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        try:
            # Try to load admin first
            user = Admin.objects(id=ObjectId(user_id)).first()
            if user:
                return user
            
            # If not admin, try vendor
            user = Vendor.objects(id=ObjectId(user_id)).first()
            return user
        except (DoesNotExist, Exception):
            return None
    
    return login_manager

def get_user_role(user=None):
    """Get the role of the current user"""
    if user is None:
        return None
        
    if isinstance(user, Admin):
        return 'admin'
    elif isinstance(user, Vendor):
        return 'vendor'
    return None

import os
from flask import Flask
from mongoengine import connect
from dotenv import load_dotenv

load_dotenv()

def create_database_config(app):
    """Configure MongoDB database settings"""
    
    # MongoDB configuration
    mongodb_uri = os.getenv('MONGODB_URI')
    if not mongodb_uri:
        raise ValueError("MONGODB_URI environment variable is required")
    
    # Connect to MongoDB Atlas with error handling
    try:
        connect(host=mongodb_uri)
        print(f"Successfully connected to MongoDB")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {str(e)}")
        raise e
    
    # Set Flask configurations for session management
    app.config['SESSION_TYPE'] = 'filesystem'
    
    return app

def init_database(app):
    """Initialize database and create default admin if not exists"""
    
    # Import models here to avoid circular imports
    from models.mongodb_models import Admin
    from werkzeug.security import generate_password_hash
    
    admin_email = os.getenv('ADMIN_EMAIL', 'admin@sasabot.ai')
    admin_password = os.getenv('ADMIN_PASSWORD', 'sasabot@admin')
    admin_phone = os.getenv('ADMIN_PHONE', '0712337845')
    
    try:
        existing_admin = Admin.objects(email=admin_email).first()
        if not existing_admin:
            admin = Admin(
                email=admin_email,
                password=generate_password_hash(admin_password),
                phone_number=admin_phone,
                name='System Administrator'
            )
            admin.save()
            print(f"Created default admin: {admin_email}")
        else:
            print("Default admin already exists")
    except Exception as e:
        print(f"Error initializing admin: {str(e)}")

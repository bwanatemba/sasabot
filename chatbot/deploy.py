#!/usr/bin/env python3
"""
SasaBot Deployment and Setup Script

This script helps set up the SasaBot application environment,
including database initialization, dependency installation,
and basic configuration.
"""

import os
import sys
import subprocess
import secrets
import string
from datetime import datetime

def generate_secret_key(length=32):
    """Generate a secure secret key"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def create_env_file():
    """Create .env file with default configuration"""
    env_content = f"""# SasaBot Environment Configuration
# Generated on {datetime.now().isoformat()}

# Flask Configuration
FLASK_ENV=production
SECRET_KEY={generate_secret_key()}

# Database Configuration
DATABASE_URL=sqlite:///sasabot.db
# For production, use PostgreSQL:
# DATABASE_URL=postgresql://username:password@localhost/sasabot_db

# Admin Credentials (Change these!)
ADMIN_EMAIL=admin@sasabot.ai
ADMIN_PASSWORD=sasabot@admin
ADMIN_PHONE=0712337845
ADMIN_NAME=SasaBot Admin

# WhatsApp API Configuration
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token_here
WHATSAPP_PHONE_ID=your_whatsapp_phone_id_here
WHATSAPP_VERIFY_TOKEN=your_whatsapp_verify_token_here

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Mpesa Configuration (Kenya)
MPESA_CONSUMER_KEY=your_mpesa_consumer_key_here
MPESA_CONSUMER_SECRET=your_mpesa_consumer_secret_here
MPESA_SHORTCODE=your_mpesa_shortcode_here
MPESA_PASSKEY=your_mpesa_passkey_here
MPESA_INITIATOR_NAME=your_mpesa_initiator_name_here
MPESA_SECURITY_CREDENTIAL=your_mpesa_security_credential_here

# Application URLs
BASE_URL=https://your-backend-domain.onrender.com
FRONTEND_URL=https://your-frontend-domain.vercel.app

# Email Configuration (Optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_USE_TLS=True

# Redis Configuration (Optional - for caching)
REDIS_URL=redis://localhost:6379/0

# File Upload Configuration
MAX_CONTENT_LENGTH=16777216  # 16MB
UPLOAD_FOLDER=static/uploads

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ .env file created with default configuration")
        print("⚠️  Please update the .env file with your actual API keys and credentials")
    else:
        print("ℹ️  .env file already exists, skipping creation")

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True, capture_output=True, text=True)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print(f"Error output: {e.stderr}")
        return False
    return True

def create_directories():
    """Create necessary directories"""
    directories = [
        'logs',
        'static/uploads',
        'static/receipts',
        'static/exports',
        'temp'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"📁 Created directory: {directory}")

def init_database():
    """Initialize the database"""
    print("🗄️  Initializing database...")
    try:
        # Import here to avoid issues if dependencies aren't installed yet
        from app import create_app
        from models import db
        from database.config import create_default_admin
        
        app = create_app()
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✅ Database tables created")
            
            # Create default admin
            create_default_admin()
            print("✅ Default admin user created")
            
    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        return False
    return True

def run_tests():
    """Run basic tests"""
    print("🧪 Running basic tests...")
    try:
        # Basic import test
        import app
        import models
        import services.messaging_service
        import services.analytics_service
        import services.bulk_messaging
        print("✅ All modules import successfully")
        
        # Test app creation
        app_instance = app.create_app()
        print("✅ Flask app creates successfully")
        
        return True
    except Exception as e:
        print(f"❌ Tests failed: {e}")
        return False

def display_next_steps():
    """Display next steps for deployment"""
    print("\n" + "="*60)
    print("🎉 SasaBot Setup Complete!")
    print("="*60)
    print("\n📋 Next Steps:")
    print("\n1. 🔧 Configure Environment:")
    print("   - Update .env file with your API keys")
    print("   - Set your WhatsApp Business API credentials")
    print("   - Configure OpenAI API key")
    print("   - Set up Mpesa credentials (for Kenya)")
    
    print("\n2. 🚀 Deploy Backend:")
    print("   - Push code to GitHub repository")
    print("   - Deploy to Render.com (or your preferred platform)")
    print("   - Set environment variables in Render")
    print("   - Configure webhook URL in WhatsApp Business API")
    
    print("\n3. 🌐 Deploy Frontend:")
    print("   - Create frontend repository")
    print("   - Deploy to Vercel (or your preferred platform)")
    print("   - Update API endpoints to point to your backend")
    
    print("\n4. 📱 Test Integration:")
    print("   - Test WhatsApp webhook")
    print("   - Test vendor onboarding flow")
    print("   - Test product ordering and payment")
    print("   - Test admin and vendor dashboards")
    
    print("\n5. 📊 Monitor and Scale:")
    print("   - Monitor logs and analytics")
    print("   - Set up error monitoring (e.g., Sentry)")
    print("   - Configure backup strategies")
    print("   - Scale based on usage")
    
    print("\n🔗 Important URLs:")
    print("   - Backend: Update BASE_URL in .env")
    print("   - Frontend: Update FRONTEND_URL in .env")
    print("   - WhatsApp Webhook: BASE_URL/api/webhook")
    print("   - Mpesa Callback: BASE_URL/api/mpesa/callback")
    
    print("\n📞 Support:")
    print("   - Documentation: Check README.md")
    print("   - Issues: GitHub Issues")
    print("   - Email: admin@sasabot.ai")
    
    print("\n⚠️  Security Reminders:")
    print("   - Change default admin password")
    print("   - Use strong secret keys")
    print("   - Enable HTTPS in production")
    print("   - Regularly update dependencies")
    print("   - Monitor for security vulnerabilities")

def main():
    """Main setup function"""
    print("🤖 SasaBot Setup Script")
    print("=" * 30)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Create directories
    create_directories()
    
    # Create .env file
    create_env_file()
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed during dependency installation")
        sys.exit(1)
    
    # Initialize database
    if not init_database():
        print("❌ Setup failed during database initialization")
        sys.exit(1)
    
    # Run tests
    if not run_tests():
        print("⚠️  Some tests failed, but setup continued")
    
    # Display next steps
    display_next_steps()

if __name__ == "__main__":
    main()

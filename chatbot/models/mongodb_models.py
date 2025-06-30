from mongoengine import Document, EmbeddedDocument, fields
from flask_login import UserMixin
from datetime import datetime
import secrets
import string
import random
import gridfs
from bson import ObjectId

class Admin(Document, UserMixin):
    meta = {'collection': 'admins'}
    
    email = fields.EmailField(required=True, unique=True)
    password = fields.StringField(required=True, max_length=255)
    phone_number = fields.StringField(required=True, max_length=20)
    name = fields.StringField(required=True, max_length=100)
    created_at = fields.DateTimeField(default=datetime.utcnow)
    is_active = fields.BooleanField(default=True)
    
    def get_id(self):
        return str(self.id)

class Vendor(Document, UserMixin):
    meta = {'collection': 'vendors'}
    
    name = fields.StringField(required=True, max_length=100)
    email = fields.EmailField(required=True, unique=True)
    phone_number = fields.StringField(required=True, unique=True, max_length=20)
    password = fields.StringField(required=True, max_length=255)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DateTimeField(default=datetime.utcnow)
    
    def get_id(self):
        return str(self.id)
    
    @staticmethod
    def generate_password(length=12):
        characters = string.ascii_letters + string.digits + "!@#$%"
        return ''.join(secrets.choice(characters) for _ in range(length))

class Business(Document):
    meta = {'collection': 'businesses'}
    
    name = fields.StringField(required=True, max_length=200)
    description = fields.StringField()
    category = fields.StringField(required=True, max_length=100)
    email = fields.EmailField()
    whatsapp_number = fields.StringField(required=True, max_length=20)
    vendor = fields.ReferenceField(Vendor, required=True)
    created_at = fields.DateTimeField(default=datetime.utcnow)
    is_active = fields.BooleanField(default=True)
    
    # WhatsApp API credentials
    whatsapp_api_token = fields.StringField(max_length=500)
    whatsapp_phone_id = fields.StringField(max_length=100)
    
    # Custom instructions for OpenAI
    custom_instructions = fields.StringField()

class Category(Document):
    meta = {'collection': 'categories'}
    
    name = fields.StringField(required=True, max_length=100)
    description = fields.StringField()
    business = fields.ReferenceField(Business, required=True)
    created_at = fields.DateTimeField(default=datetime.utcnow)

class ProductVariation(EmbeddedDocument):
    variation_id = fields.StringField(required=True, max_length=20)
    name = fields.StringField(required=True, max_length=200)
    price = fields.FloatField(required=True)
    description = fields.StringField()
    is_active = fields.BooleanField(default=True)
    created_at = fields.DateTimeField(default=datetime.utcnow)

class Product(Document):
    meta = {'collection': 'products'}
    
    product_id = fields.StringField(required=True, unique=True, max_length=20)
    name = fields.StringField(required=True, max_length=200)
    description = fields.StringField()
    price = fields.FloatField(required=True)
    image_url = fields.URLField()  # For external URLs
    image_file_id = fields.ObjectIdField()  # For GridFS file storage
    image_filename = fields.StringField()  # Original filename
    image_content_type = fields.StringField()  # MIME type
    business = fields.ReferenceField(Business, required=True)
    category = fields.ReferenceField(Category)
    
    # Product features
    allows_customization = fields.BooleanField(default=False)
    has_variations = fields.BooleanField(default=False)
    is_active = fields.BooleanField(default=True)
    
    created_at = fields.DateTimeField(default=datetime.utcnow)
    
    # Embedded variations
    variations = fields.ListField(fields.EmbeddedDocumentField(ProductVariation))
    
    def get_image_url(self):
        """Get the appropriate image URL for this product."""
        if self.image_file_id:
            return f'/images/product/{self.image_file_id}'
        elif self.image_url:
            return self.image_url
        else:
            return '/static/images/default-image.jpg'
    
    def has_image(self):
        """Check if product has an image."""
        return bool(self.image_file_id or self.image_url)

class Customer(Document):
    meta = {'collection': 'customers'}
    
    phone_number = fields.StringField(required=True, unique=True, max_length=20)
    name = fields.StringField(max_length=100)
    email = fields.EmailField()
    created_at = fields.DateTimeField(default=datetime.utcnow)

class OrderItem(EmbeddedDocument):
    product = fields.ReferenceField(Product, required=True)
    variation_id = fields.StringField()  # Reference to variation within product
    quantity = fields.IntField(default=1)
    unit_price = fields.FloatField(required=True)
    total_price = fields.FloatField(required=True)

class Order(Document):
    meta = {'collection': 'orders'}
    
    order_number = fields.StringField(required=True, unique=True, max_length=20)
    customer = fields.ReferenceField(Customer, required=True)
    business = fields.ReferenceField(Business, required=True)
    
    # Order details
    total_amount = fields.FloatField(required=True)
    status = fields.StringField(default='pending', choices=['pending', 'paid', 'processing', 'completed', 'delivered', 'cancelled'])
    payment_status = fields.StringField(default='pending', choices=['pending', 'paid', 'failed'])
    payment_method = fields.StringField(default='mpesa', max_length=50)
    mpesa_transaction_id = fields.StringField(max_length=100)
    
    # Customization
    customization_notes = fields.StringField()
    
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)
    
    # Embedded order items
    order_items = fields.ListField(fields.EmbeddedDocumentField(OrderItem))
    
    @staticmethod
    def generate_order_number():
        return f"ORD{random.randint(100000, 999999)}"
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super(Order, self).save(*args, **kwargs)

class ChatMessage(EmbeddedDocument):
    sender_type = fields.StringField(required=True, choices=['customer', 'gpt', 'vendor'])
    message_text = fields.StringField(required=True)
    message_type = fields.StringField(default='text', choices=['text', 'interactive', 'media'])
    timestamp = fields.DateTimeField(default=datetime.utcnow)
    
    # For interactive messages
    button_data = fields.DictField()

class ChatSession(Document):
    meta = {'collection': 'chat_sessions'}
    
    customer = fields.ReferenceField(Customer, required=True)
    business = fields.ReferenceField(Business, required=True)
    session_id = fields.StringField(required=True, unique=True, max_length=100)
    created_at = fields.DateTimeField(default=datetime.utcnow)
    
    # Embedded messages
    messages = fields.ListField(fields.EmbeddedDocumentField(ChatMessage))

class OnboardingState(Document):
    meta = {'collection': 'onboarding_states'}
    
    phone_number = fields.StringField(required=True, unique=True, max_length=20)
    current_step = fields.StringField(required=True, max_length=50)
    data = fields.DictField()  # Store collected data
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)
    
    def save(self, *args, **kwargs):
        self.updated_at = datetime.utcnow()
        return super(OnboardingState, self).save(*args, **kwargs)

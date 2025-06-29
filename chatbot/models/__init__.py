# Import MongoDB models
from .mongodb_models import (
    Admin, 
    Vendor, 
    Business, 
    Category, 
    Product, 
    ProductVariation, 
    Customer, 
    Order, 
    OrderItem, 
    ChatSession, 
    ChatMessage, 
    OnboardingState
)

# Maintain compatibility with existing code
__all__ = [
    'Admin', 
    'Vendor', 
    'Business', 
    'Category', 
    'Product', 
    'ProductVariation', 
    'Customer', 
    'Order', 
    'OrderItem', 
    'ChatSession', 
    'ChatMessage', 
    'OnboardingState'
]

import os
import gridfs
import pymongo
from PIL import Image
import io
from bson import ObjectId
from werkzeug.utils import secure_filename
from flask import current_app
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
MAX_IMAGE_DIMENSION = 2048  # Max width or height in pixels

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_gridfs():
    """Get GridFS instance from MongoDB connection."""
    try:
        # Get MongoDB connection from mongoengine
        from mongoengine import connection
        db = connection.get_db()
        return gridfs.GridFS(db)
    except Exception as e:
        logger.error(f"Error getting GridFS connection: {str(e)}")
        raise

def validate_image(file):
    """Validate uploaded image file."""
    if not file:
        return False, "No file provided"
    
    if file.filename == '':
        return False, "No file selected"
    
    if not allowed_file(file.filename):
        return False, f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_IMAGE_SIZE:
        return False, f"File too large. Maximum size: {MAX_IMAGE_SIZE // (1024*1024)}MB"
    
    return True, "Valid image file"

def resize_image(image_data, max_dimension=MAX_IMAGE_DIMENSION):
    """Resize image while maintaining aspect ratio."""
    try:
        image = Image.open(io.BytesIO(image_data))
        
        # Convert RGBA to RGB for JPEG compatibility
        if image.mode in ('RGBA', 'LA', 'P'):
            # Create a white background
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        
        # Resize if necessary
        width, height = image.size
        if width > max_dimension or height > max_dimension:
            if width > height:
                new_width = max_dimension
                new_height = int(height * (max_dimension / width))
            else:
                new_height = max_dimension
                new_width = int(width * (max_dimension / height))
            
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Save to bytes
        output = io.BytesIO()
        
        # Determine format based on original file
        format_type = 'JPEG'  # Default to JPEG for better compression
        
        # Use PNG for images that need transparency (though we converted them above)
        if image.mode == 'RGBA':
            format_type = 'PNG'
        
        # Save with optimization
        if format_type == 'JPEG':
            image.save(output, format=format_type, quality=85, optimize=True)
        else:
            image.save(output, format=format_type, optimize=True)
        
        output.seek(0)
        return output.getvalue(), format_type.lower()
        
    except Exception as e:
        logger.error(f"Error resizing image: {str(e)}")
        raise ValueError(f"Error processing image: {str(e)}")

def save_image_to_gridfs(file, filename=None):
    """Save image file to MongoDB GridFS with resizing and optimization."""
    try:
        # Validate file
        is_valid, message = validate_image(file)
        if not is_valid:
            raise ValueError(message)
        
        # Read file data
        file.seek(0)
        file_data = file.read()
        
        # Resize and optimize image
        resized_data, image_format = resize_image(file_data)
        
        # Generate secure filename
        if not filename:
            filename = secure_filename(file.filename)
        
        # Get GridFS instance
        fs = get_gridfs()
        
        # Store in GridFS with metadata
        file_id = fs.put(
            resized_data,
            filename=filename,
            content_type=f'image/{image_format}',
            metadata={
                'original_filename': file.filename,
                'original_size': len(file_data),
                'compressed_size': len(resized_data),
                'image_format': image_format,
                'uploaded_at': datetime.utcnow()
            }
        )
        
        logger.info(f"Image saved to GridFS with ID: {file_id}, Original size: {len(file_data)}, Compressed size: {len(resized_data)}")
        
        return {
            'file_id': file_id,
            'filename': filename,
            'content_type': f'image/{image_format}',
            'original_size': len(file_data),
            'compressed_size': len(resized_data)
        }
        
    except Exception as e:
        logger.error(f"Error saving image to GridFS: {str(e)}")
        raise

def get_image_from_gridfs(file_id):
    """Retrieve image from GridFS by file ID."""
    try:
        fs = get_gridfs()
        
        if isinstance(file_id, str):
            file_id = ObjectId(file_id)
        
        grid_out = fs.get(file_id)
        return {
            'data': grid_out.read(),
            'content_type': grid_out.content_type,
            'filename': grid_out.filename
        }
        
    except gridfs.NoFile:
        logger.warning(f"Image not found in GridFS: {file_id}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving image from GridFS: {str(e)}")
        return None

def delete_image_from_gridfs(file_id):
    """Delete image from GridFS."""
    try:
        fs = get_gridfs()
        
        if isinstance(file_id, str):
            file_id = ObjectId(file_id)
        
        fs.delete(file_id)
        logger.info(f"Image deleted from GridFS: {file_id}")
        return True
        
    except gridfs.NoFile:
        logger.warning(f"Image not found for deletion in GridFS: {file_id}")
        return False
    except Exception as e:
        logger.error(f"Error deleting image from GridFS: {str(e)}")
        return False

def update_product_image(product, image_file):
    """Update product with new image, removing old image if exists."""
    try:
        # Delete old image if exists
        if product.image_file_id:
            delete_image_from_gridfs(product.image_file_id)
        
        # Save new image
        image_info = save_image_to_gridfs(image_file)
        
        # Update product fields
        product.image_file_id = image_info['file_id']
        product.image_filename = image_info['filename']
        product.image_content_type = image_info['content_type']
        
        return True
        
    except Exception as e:
        logger.error(f"Error updating product image: {str(e)}")
        raise

def get_image_url(product):
    """Get the appropriate image URL for a product."""
    if product.image_file_id:
        return f'/images/product/{product.image_file_id}'
    elif product.image_url:
        return product.image_url
    else:
        return '/static/images/no-image-placeholder.png'  # You can add a placeholder image

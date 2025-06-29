from flask import Blueprint, render_template, Response, abort
from services.image_service import get_image_from_gridfs
from bson import ObjectId
from bson.errors import InvalidId

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/contact')
def contact():
    return render_template('contact.html')

@main_bp.route('/images/product/<file_id>')
def serve_product_image(file_id):
    """Serve product images from GridFS."""
    try:
        # Validate ObjectId
        try:
            ObjectId(file_id)
        except InvalidId:
            abort(404)
        
        # Get image from GridFS
        image_data = get_image_from_gridfs(file_id)
        
        if not image_data:
            abort(404)
        
        return Response(
            image_data['data'],
            mimetype=image_data['content_type'],
            headers={
                'Content-Disposition': f'inline; filename="{image_data["filename"]}"',
                'Cache-Control': 'public, max-age=3600'  # Cache for 1 hour
            }
        )
        
    except Exception as e:
        abort(404)

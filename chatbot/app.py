from flask import Flask, request, jsonify
from services import messaging_service
import os
import logging
from functools import wraps
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

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

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

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

@app.errorhandler(400)
def handle_bad_request(e):
    return jsonify({"error": "Bad request, check your JSON payload"}), 400

@app.errorhandler(405)
def handle_method_not_allowed(e):
    return jsonify({"error": f"Method {request.method} is not allowed for this endpoint"}), 405

@app.errorhandler(500)
def handle_server_error(e):
    return jsonify({"error": "Internal server error occurred"}), 500

@app.route('/')
def home():
    return {"message": "Welcome to the API"}, 200

# Handle Incoming WhatsApp Messages
@app.route('/whatsapp/message', methods=['GET', 'POST'])
def handle_whatsapp_webhook():
    if request.method == 'GET':
        return messaging_service.verify_webhook()
    return messaging_service.process_whatsapp_message(request.json)

if __name__ == '__main__':
    app.run(debug=True)


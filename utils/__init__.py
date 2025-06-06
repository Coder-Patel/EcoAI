# Import all apps
from .database import Database
from .auth import Auth

# Module level variables
__version__ = '1.0.0'
__author__ = 'Jwal Patel'

# Default API key
DEFAULT_API_KEY = "AIzaSyASnBJDcTM4puEQSrNLJPPRMgAA0wUzeIU"

# Function to initialize the entire application
def init_app():
    """Initialize the application"""
    auth = Auth()
    return auth, None  # Return None for model if not needed
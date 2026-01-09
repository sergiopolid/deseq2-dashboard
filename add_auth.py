"""
Add HTTP Basic Authentication to Dash App
Usage: Modify app.py to import and use this authentication wrapper
"""

from dash import Dash
import dash_auth
import os

def create_authenticated_app(app_instance, username_password_pairs=None):
    """
    Add HTTP Basic Authentication to a Dash app.
    
    Args:
        app_instance: The Dash app instance
        username_password_pairs: List of (username, password) tuples
                                 If None, uses environment variables or default
    
    Returns:
        Authenticated app instance
    """
    if username_password_pairs is None:
        # Try to get from environment variables
        username = os.getenv('DASH_USERNAME', 'admin')
        password = os.getenv('DASH_PASSWORD', None)
        
        if password is None:
            # Generate a random password (user should change this!)
            import secrets
            password = secrets.token_urlsafe(16)
            print(f"⚠️  WARNING: Using auto-generated password: {password}")
            print(f"⚠️  Set DASH_PASSWORD environment variable for production!")
        
        username_password_pairs = [(username, password)]
    
    # Add authentication
    auth = dash_auth.BasicAuth(
        app_instance,
        username_password_pairs
    )
    
    return app_instance


# Example usage in app.py:
# from add_auth import create_authenticated_app
# app = dash.Dash(...)
# app = create_authenticated_app(app, [('user1', 'pass1'), ('user2', 'pass2')])




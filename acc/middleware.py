"""Middleware for handling database sessions and errors"""

from flask import g
from acc.extensions import db

def setup_middleware(app):
    """Setup application middleware"""
    
    @app.before_request
    def before_request():
        """Clean up any failed transactions before each request"""
        try:
            # Rollback any pending transaction
            if db.session.is_active:
                db.session.rollback()
        except:
            pass
    
    @app.teardown_appcontext
    def teardown_db(exception):
        """Clean up database session after each request"""
        if exception:
            try:
                db.session.rollback()
            except:
                pass
        
        try:
            db.session.remove()
        except:
            pass
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        """Handle all unhandled exceptions"""
        try:
            db.session.rollback()
        except:
            pass
        
        # Re-raise the exception to be handled by Flask
        raise e
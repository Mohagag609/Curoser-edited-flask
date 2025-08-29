"""
Global error handlers for the application
"""
from flask import render_template, request, jsonify, flash, redirect, url_for
from werkzeug.exceptions import HTTPException
import traceback

def register_error_handlers(app):
    """Register error handlers with the Flask app"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'المورد غير موجود', 'status': 404}), 404
        
        flash('⚠️ الصفحة المطلوبة غير موجودة', 'warning')
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'غير مصرح لك بالوصول', 'status': 403}), 403
        
        flash('🚫 غير مصرح لك بالوصول لهذه الصفحة', 'error')
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        # Rollback any failed database transaction
        from acc.extensions import db
        db.session.rollback()
        
        # Log the error details
        app.logger.error(f'Internal error: {error}')
        if hasattr(error, 'original_exception'):
            app.logger.error(f'Original exception: {error.original_exception}')
        app.logger.error(traceback.format_exc())
        
        if request.path.startswith('/api/'):
            return jsonify({
                'error': 'خطأ في الخادم',
                'message': str(error) if app.debug else 'حدث خطأ في معالجة طلبك',
                'status': 500
            }), 500
        
        # Get error details for display (in debug mode only)
        error_details = None
        if app.debug:
            error_details = {
                'type': type(error).__name__,
                'message': str(error),
                'traceback': traceback.format_exc()
            }
        
        flash('❌ عذراً، حدث خطأ في معالجة طلبك. يرجى المحاولة مرة أخرى.', 'error')
        return render_template('errors/500.html', error_details=error_details), 500
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        # Handle database errors specifically
        if 'IntegrityError' in str(type(error)):
            from acc.extensions import db
            db.session.rollback()
            
            # Parse the error message
            error_msg = str(error)
            
            if 'UNIQUE constraint failed' in error_msg:
                flash('⚠️ البيانات المدخلة موجودة مسبقاً', 'warning')
            elif 'FOREIGN KEY constraint failed' in error_msg:
                flash('⚠️ لا يمكن إتمام العملية لوجود بيانات مرتبطة', 'warning')
            elif 'NOT NULL constraint failed' in error_msg:
                flash('⚠️ يرجى ملء جميع الحقول المطلوبة', 'warning')
            else:
                flash(f'⚠️ خطأ في قاعدة البيانات: {error_msg}', 'error')
            
            # Try to redirect back or to index
            return redirect(request.referrer or url_for('main.index'))
        
        # Log unexpected errors
        app.logger.error(f'Unexpected error: {error}')
        app.logger.error(traceback.format_exc())
        
        # Handle as internal server error
        return internal_error(error)
    
    # Add custom error pages
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        # Handle all HTTP exceptions
        if request.path.startswith('/api/'):
            response = e.get_response()
            response.data = jsonify({
                'error': e.description,
                'status': e.code
            }).data
            response.content_type = "application/json"
            return response
        
        # For regular requests, show appropriate error page
        if e.code == 404:
            return not_found_error(e)
        elif e.code == 403:
            return forbidden_error(e)
        elif e.code >= 500:
            return internal_error(e)
        else:
            flash(f'⚠️ {e.description}', 'warning')
            return render_template('errors/generic.html', error=e), e.code
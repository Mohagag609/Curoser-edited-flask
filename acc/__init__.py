from flask import Flask, render_template, request, jsonify
from datetime import datetime
from config import Config
from acc.services.cache_service import cache
from acc.extensions import db
import logging
from logging.handlers import RotatingFileHandler
import os


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    
    # Configure logging
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    # Always log errors to file
    file_handler = RotatingFileHandler('logs/acc.log', maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.ERROR)
    app.logger.addHandler(file_handler)
    
    # Console logging
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    app.logger.addHandler(console_handler)
    
    app.logger.setLevel(logging.INFO)
    app.logger.info('ACC application startup')
    
    # Template context processors
    @app.context_processor
    def inject_globals():
        from acc.services.utils import format_currency
        from acc.services.project_selection import get_current_project
        from acc.models import Project
        
        current_project = get_current_project()
        all_projects = Project.query.filter_by(status='نشط').order_by(Project.name).all()
        
        return {
            'current_year': datetime.now().year,
            'format_currency': format_currency,
            'current_project': current_project,
            'all_projects': all_projects
        }
    
    # Register blueprints

    
    from acc.blueprints.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from acc.blueprints.dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    
    from acc.blueprints.customers import bp as customers_bp
    app.register_blueprint(customers_bp, url_prefix='/customers')
    
    from acc.blueprints.units import bp as units_bp
    app.register_blueprint(units_bp, url_prefix='/units')
    
    from acc.blueprints.partners import bp as partners_bp
    app.register_blueprint(partners_bp, url_prefix='/partners')
    
    from acc.blueprints.contracts import bp as contracts_bp
    app.register_blueprint(contracts_bp, url_prefix='/contracts')
    
    from acc.blueprints.brokers import bp as brokers_bp
    app.register_blueprint(brokers_bp, url_prefix='/brokers')
    
    from acc.blueprints.installments import bp as installments_bp
    app.register_blueprint(installments_bp, url_prefix='/installments')
    
    from acc.blueprints.treasury import bp as treasury_bp
    app.register_blueprint(treasury_bp, url_prefix='/treasury')
    
    from acc.blueprints.vouchers import bp as vouchers_bp
    app.register_blueprint(vouchers_bp, url_prefix='/vouchers')
    
    from acc.blueprints.reports import bp as reports_bp
    app.register_blueprint(reports_bp, url_prefix='/reports')
    
    from acc.blueprints.suppliers import bp as suppliers_bp
    app.register_blueprint(suppliers_bp, url_prefix='/suppliers')
    
    from acc.blueprints.contractors import bp as contractors_bp
    app.register_blueprint(contractors_bp, url_prefix='/contractors')
    
    from acc.blueprints.projects import bp as projects_bp
    app.register_blueprint(projects_bp, url_prefix='/projects')
    
    from acc.blueprints.materials import bp as materials_bp
    app.register_blueprint(materials_bp, url_prefix='/materials')
    
    from acc.blueprints.system import bp as system_bp
    app.register_blueprint(system_bp, url_prefix='/system')
    
    from acc.blueprints.settlement import bp as settlement_bp
    app.register_blueprint(settlement_bp, url_prefix='/settlement')
    
    from acc.blueprints.transfers import bp as transfers_bp
    app.register_blueprint(transfers_bp, url_prefix='/transfers')
    

    
    # Register context processors
    from acc.context_processors import inject_global_vars
    app.context_processor(inject_global_vars)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('error/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        import traceback
        error_details = traceback.format_exc() if app.debug else None
        return render_template('error/500.html', error=error_details), 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        # Log the error with full traceback
        import traceback
        app.logger.error(f'Unhandled exception: {str(e)}\n{traceback.format_exc()}')
        
        # If AJAX request, return JSON error
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': f'❌ خطأ في الخادم: {str(e)}'
            }), 500
        
        # If in debug mode, re-raise to see the full traceback
        if app.debug:
            raise e
            
        # Otherwise show a generic error page
        db.session.rollback()
        return render_template('error/500.html'), 500
    
    return app
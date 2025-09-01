from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_caching import Cache
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
import os

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
cache = Cache()


def create_app(config_name='default'):
    """إنشاء تطبيق Flask"""
    app = Flask(__name__)
    
    # Load configuration
    from config import config
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    
    # Configure logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler('logs/real_estate.log', maxBytes=10240000, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Real Estate System startup')
    
    # Template context processors
    @app.context_processor
    def inject_globals():
        from app.services.utils import format_currency
        from app.services.project_service import get_current_project
        from app.models import Project
        
        current_project = get_current_project()
        all_projects = Project.query.filter_by(status='نشط').order_by(Project.name).all()
        
        return {
            'current_year': datetime.now().year,
            'format_currency': format_currency,
            'current_project': current_project,
            'all_projects': all_projects
        }
    
    # Register blueprints
    from app.views.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.views.dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    
    from app.views.customers import bp as customers_bp
    app.register_blueprint(customers_bp, url_prefix='/customers')
    
    from app.views.units import bp as units_bp
    app.register_blueprint(units_bp, url_prefix='/units')
    
    from app.views.partners import bp as partners_bp
    app.register_blueprint(partners_bp, url_prefix='/partners')
    
    from app.views.contracts import bp as contracts_bp
    app.register_blueprint(contracts_bp, url_prefix='/contracts')
    
    from app.views.brokers import bp as brokers_bp
    app.register_blueprint(brokers_bp, url_prefix='/brokers')
    
    from app.views.installments import bp as installments_bp
    app.register_blueprint(installments_bp, url_prefix='/installments')
    
    from app.views.treasury import bp as treasury_bp
    app.register_blueprint(treasury_bp, url_prefix='/treasury')
    
    from app.views.vouchers import bp as vouchers_bp
    app.register_blueprint(vouchers_bp, url_prefix='/vouchers')
    
    from app.views.reports import bp as reports_bp
    app.register_blueprint(reports_bp, url_prefix='/reports')
    
    from app.views.suppliers import bp as suppliers_bp
    app.register_blueprint(suppliers_bp, url_prefix='/suppliers')
    
    from app.views.contractors import bp as contractors_bp
    app.register_blueprint(contractors_bp, url_prefix='/contractors')
    
    from app.views.projects import bp as projects_bp
    app.register_blueprint(projects_bp, url_prefix='/projects')
    
    from app.views.materials import bp as materials_bp
    app.register_blueprint(materials_bp, url_prefix='/materials')
    
    from app.views.system import bp as system_bp
    app.register_blueprint(system_bp, url_prefix='/system')
    
    from app.views.settlement import bp as settlement_bp
    app.register_blueprint(settlement_bp, url_prefix='/settlement')
    
    from app.views.transfers import bp as transfers_bp
    app.register_blueprint(transfers_bp, url_prefix='/transfers')
    
    # API routes
    from app.views.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        import traceback
        error_details = traceback.format_exc() if app.debug else None
        return render_template('errors/500.html', error=error_details), 500
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        import traceback
        app.logger.error(f'Unhandled exception: {str(e)}\n{traceback.format_exc()}')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': f'❌ خطأ في الخادم: {str(e)}'
            }), 500
        
        if app.debug:
            raise e
            
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    return app
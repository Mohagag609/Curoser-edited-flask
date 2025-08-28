from flask import Flask
from datetime import datetime
from config import Config
from acc.extensions import db, migrate


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Template context processors
    @app.context_processor
    def inject_globals():
        from acc.services.utils import format_currency
        return {
            'current_year': datetime.now().year,
            'format_currency': format_currency
        }
    
    # Register blueprints
    from acc.blueprints.dashboard import bp as dashboard_bp
    app.register_blueprint(dashboard_bp)
    
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
    
    return app
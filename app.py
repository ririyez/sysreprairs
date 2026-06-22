import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import config

# Inisialisasi Flask Extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_name=None):
    """Application Factory"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config['default']))
    
    # Buat folder upload jika belum ada
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Inisialisasi extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Silahkan masuk terlebih dahulu.'
    login_manager.login_message_category = 'warning'
    
    # Register blueprints
    from routes import auth, dashboard, customers, orders, tracking, finance, analytics
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(customers.bp)
    app.register_blueprint(orders.bp)
    app.register_blueprint(tracking.bp)
    app.register_blueprint(finance.bp)
    app.register_blueprint(analytics.bp)
    
    # Context processor untuk template globals
    @app.context_processor
    def inject_config():
        return {'app_name': 'SYSREPAIR'}
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Halaman tidak ditemukan'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Terjadi kesalahan pada server'}, 500
    
    # Create tables
    with app.app_context():
        db.create_all()
        # Buat admin default
        from models import Admin
        if not Admin.query.filter_by(username='admin').first():
            admin = Admin(username='admin', email='admin@sysrepair.com')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('Admin default berhasil dibuat: username=admin, password=admin123')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)

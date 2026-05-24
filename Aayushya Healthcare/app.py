"""
Aayushya Healthcare - Hospital Queue Management System
Clean Flask Application with MySQL/phpMyAdmin Integration
"""
from flask import Flask
import os
from config import config

# Import database and models
from models.db import db

# Import route blueprints
from routes.main import main_bp
from routes.auth import auth_bp
from routes.patient import patient_bp
from routes.doctor import doctor_bp

def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    config_name = config_name or os.environ.get('FLASK_ENV') or 'development'
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(doctor_bp)
    
    return app

# Create application instance
app = create_app()

if __name__ == '__main__':
    # Ensure database exists and is initialized
    print("Initializing Aayushya Healthcare application...")
    
    try:
        from database_manager import ensure_database_exists
        
        # Check and create database if needed
        if ensure_database_exists(app):
            print("\n🚀 Starting Aayushya Healthcare application...")
            print("="*70)
            print("Server running at: http://localhost:5000")
            print("Database: MySQL via XAMPP phpMyAdmin")
            print("Access phpMyAdmin at: http://localhost/phpmyadmin")
            print("="*70 + "\n")
            app.run(debug=True, port=5000)
        else:
            print("\n❌ Application startup failed: Database setup incomplete")
            print("\nTroubleshooting:")
            print("  1. Ensure XAMPP is running")
            print("  2. Start MySQL service in XAMPP Control Panel")
            print("  3. Check database credentials in config.py")
            print("  4. Try running: python database_manager.py")
            
    except Exception as e:
        print(f"\n❌ Application startup failed: {e}")
        import traceback
        traceback.print_exc()
        print("\nPlease check the error above and try again")
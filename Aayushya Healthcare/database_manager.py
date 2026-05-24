"""
Database Manager - Automatic Database Creation and Initialization
Handles database existence check and automatic creation
"""
import pymysql
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError
import sys


class DatabaseManager:
    """Manages database creation and initialization"""
    
    def __init__(self, config):
        """Initialize with Flask app config"""
        self.host = config.get('MYSQL_HOST', 'localhost')
        self.port = config.get('MYSQL_PORT', 3306)
        self.user = config.get('MYSQL_USER', 'root')
        self.password = config.get('MYSQL_PASSWORD', '')
        self.database = config.get('MYSQL_DATABASE', 'aayushya_healthcare')
        
    def check_mysql_connection(self):
        """Check if MySQL server is running and accessible"""
        try:
            connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password
            )
            connection.close()
            return True
        except pymysql.Error as e:
            print(f"❌ MySQL Connection Error: {e}")
            print("\n⚠️  Please ensure:")
            print("   1. XAMPP is running")
            print("   2. MySQL service is started in XAMPP Control Panel")
            print("   3. MySQL credentials are correct")
            return False
    
    def database_exists(self):
        """Check if the database exists"""
        try:
            connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password
            )
            cursor = connection.cursor()
            cursor.execute(f"SHOW DATABASES LIKE '{self.database}'")
            result = cursor.fetchone()
            cursor.close()
            connection.close()
            return result is not None
        except pymysql.Error as e:
            print(f"Error checking database existence: {e}")
            return False
    
    def create_database(self):
        """Create the database if it doesn't exist"""
        try:
            connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password
            )
            cursor = connection.cursor()
            
            # Create database with UTF-8 encoding
            cursor.execute(f"""
                CREATE DATABASE IF NOT EXISTS `{self.database}` 
                CHARACTER SET utf8mb4 
                COLLATE utf8mb4_unicode_ci
            """)
            
            connection.commit()
            cursor.close()
            connection.close()
            
            print(f"✓ Database '{self.database}' created successfully")
            return True
            
        except pymysql.Error as e:
            print(f"❌ Error creating database: {e}")
            return False
    
    def initialize_database(self, app):
        """Initialize database with tables and data"""
        try:
            from models.db import db, init_database
            
            with app.app_context():
                # Create all tables
                db.create_all()
                print("✓ Database tables created successfully")
                
                # Initialize with sample data
                init_database(app)
                
            return True
            
        except Exception as e:
            print(f"❌ Error initializing database: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def setup_database(self, app):
        """Complete database setup process"""
        print("\n" + "="*70)
        print("AAYUSHYA HEALTHCARE - DATABASE SETUP")
        print("="*70)
        
        # Step 1: Check MySQL connection
        print("\n[1/4] Checking MySQL connection...")
        if not self.check_mysql_connection():
            print("\n❌ Setup failed: Cannot connect to MySQL server")
            return False
        print("✓ MySQL server is running and accessible")
        
        # Step 2: Check if database exists
        print("\n[2/4] Checking if database exists...")
        if self.database_exists():
            print(f"✓ Database '{self.database}' already exists")
        else:
            print(f"⚠️  Database '{self.database}' does not exist")
            print(f"   Creating database '{self.database}'...")
            if not self.create_database():
                print("\n❌ Setup failed: Could not create database")
                return False
        
        # Step 3: Initialize database tables
        print("\n[3/4] Initializing database tables...")
        if not self.initialize_database(app):
            print("\n❌ Setup failed: Could not initialize tables")
            return False
        
        # Step 4: Verify setup
        print("\n[4/4] Verifying database setup...")
        if self.verify_setup(app):
            print("✓ Database setup verified successfully")
        else:
            print("⚠️  Database setup completed with warnings")
        
        # Success message
        print("\n" + "="*70)
        print("✅ DATABASE SETUP COMPLETE!")
        print("="*70)
        print(f"\nDatabase: {self.database}")
        print(f"Host: {self.host}:{self.port}")
        print(f"User: {self.user}")
        print("\nYou can now:")
        print("  • Access the application at http://localhost:5000")
        print("  • Manage database at http://localhost/phpmyadmin")
        print("\n" + "="*70 + "\n")
        
        return True
    
    def verify_setup(self, app):
        """Verify that database and tables are properly set up"""
        try:
            from models.db import db, User, Patient, Doctor, Hospital, Appointment
            
            with app.app_context():
                # Check if tables exist by querying them
                user_count = User.query.count()
                patient_count = Patient.query.count()
                doctor_count = Doctor.query.count()
                hospital_count = Hospital.query.count()
                appointment_count = Appointment.query.count()
                
                print(f"   • Users: {user_count}")
                print(f"   • Patients: {patient_count}")
                print(f"   • Doctors: {doctor_count}")
                print(f"   • Hospitals: {hospital_count}")
                print(f"   • Appointments: {appointment_count}")
                
                return True
                
        except Exception as e:
            print(f"   ⚠️  Verification warning: {e}")
            return False
    
    def reset_database(self, app):
        """Drop and recreate the database (use with caution!)"""
        print("\n⚠️  WARNING: This will delete all data in the database!")
        confirm = input("Type 'YES' to confirm database reset: ")
        
        if confirm != 'YES':
            print("Database reset cancelled")
            return False
        
        try:
            connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password
            )
            cursor = connection.cursor()
            
            # Drop database
            cursor.execute(f"DROP DATABASE IF EXISTS `{self.database}`")
            print(f"✓ Database '{self.database}' dropped")
            
            # Create database
            cursor.execute(f"""
                CREATE DATABASE `{self.database}` 
                CHARACTER SET utf8mb4 
                COLLATE utf8mb4_unicode_ci
            """)
            print(f"✓ Database '{self.database}' created")
            
            connection.commit()
            cursor.close()
            connection.close()
            
            # Initialize tables
            self.initialize_database(app)
            
            print("\n✅ Database reset complete!")
            return True
            
        except Exception as e:
            print(f"❌ Error resetting database: {e}")
            return False


def ensure_database_exists(app):
    """
    Convenience function to ensure database exists before starting app
    Returns True if database is ready, False otherwise
    """
    db_manager = DatabaseManager(app.config)
    return db_manager.setup_database(app)


if __name__ == '__main__':
    """Run database setup independently"""
    print("Running standalone database setup...")
    
    # Import app
    from app import app
    
    # Setup database
    db_manager = DatabaseManager(app.config)
    
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == '--reset':
        db_manager.reset_database(app)
    else:
        db_manager.setup_database(app)

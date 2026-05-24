"""
Aayushya Healthcare - Database Setup & Migration Script
This script handles all database setup and migration requirements
Can be run standalone or imported by database_manager
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def setup_and_migrate():
    """Complete database setup and migration"""
    try:
        from app import app, db
        from models.db import Doctor, Hospital, User, Patient, Appointment, Queue
        from sqlalchemy import inspect, text
        from datetime import datetime
        
        with app.app_context():
            print("\n" + "="*70)
            print("AAYUSHYA HEALTHCARE - DATABASE SETUP & MIGRATION")
            print("="*70)
            
            # Step 1: Create all tables
            print("\n[1/6] Creating database tables...")
            db.create_all()
            print("✓ Tables created")
            
            # Step 2: Add missing columns
            print("\n[2/6] Checking for missing columns...")
            inspector = inspect(db.engine)
            
            # Check if hospital_id exists in doctors table
            doctor_columns = [col['name'] for col in inspector.get_columns('doctors')]
            if 'hospital_id' not in doctor_columns:
                print("  → Adding hospital_id to doctors table...")
                with db.engine.connect() as connection:
                    connection.execute(text('ALTER TABLE doctors ADD COLUMN hospital_id INT NULL'))
                    connection.execute(text('''ALTER TABLE doctors ADD CONSTRAINT fk_doctor_hospital 
                                        FOREIGN KEY (hospital_id) REFERENCES hospitals(id) ON DELETE SET NULL'''))
                    connection.commit()
                print("✓ Added hospital_id column")
            else:
                print("✓ hospital_id column already exists")
            
            # Check if email exists in doctors table
            if 'email' not in doctor_columns:
                print("  → Adding email to doctors table...")
                with db.engine.connect() as connection:
                    connection.execute(text('ALTER TABLE doctors ADD COLUMN email VARCHAR(120) NULL'))
                    connection.commit()
                print("✓ Added email column")
            else:
                print("✓ email column already exists")
            
            # Check if phone_number exists in doctors table
            if 'phone_number' not in doctor_columns:
                print("  → Adding phone_number to doctors table...")
                with db.engine.connect() as connection:
                    connection.execute(text('ALTER TABLE doctors ADD COLUMN phone_number VARCHAR(15) NULL'))
                    connection.commit()
                print("✓ Added phone_number column")
            else:
                print("✓ phone_number column already exists")
            
            # Drop insurance columns from patients table if they exist
            print("\n  → Checking for insurance columns in patients table...")
            patient_columns = [col['name'] for col in inspector.get_columns('patients')]
            
            if 'insurance_provider' in patient_columns:
                print("  → Dropping insurance_provider column...")
                with db.engine.connect() as connection:
                    connection.execute(text('ALTER TABLE patients DROP COLUMN insurance_provider'))
                    connection.commit()
                print("✓ Dropped insurance_provider column")
            
            if 'policy_number' in patient_columns:
                print("  → Dropping policy_number column...")
                with db.engine.connect() as connection:
                    connection.execute(text('ALTER TABLE patients DROP COLUMN policy_number'))
                    connection.commit()
                print("✓ Dropped policy_number column")
            
            if 'insurance_provider' not in patient_columns and 'policy_number' not in patient_columns:
                print("✓ Insurance columns already removed")
            
            # Check if phone_number exists in patients table
            if 'phone_number' not in patient_columns:
                print("  → Adding phone_number to patients table...")
                with db.engine.connect() as connection:
                    connection.execute(text('ALTER TABLE patients ADD COLUMN phone_number VARCHAR(15) NULL'))
                    connection.commit()
                print("✓ Added phone_number column")
            else:
                print("✓ phone_number column already exists")
            
            # Step 3: Migrate email data from users to doctors
            print("\n[3/6] Migrating email data from users to doctors...")
            doctors = Doctor.query.all()
            email_migrated = 0
            
            for doctor in doctors:
                if not doctor.email and doctor.user_id:
                    user = User.query.get(doctor.user_id)
                    if user and user.email:
                        doctor.email = user.email
                        email_migrated += 1
            
            if email_migrated > 0:
                db.session.commit()
                print(f"✓ Migrated email for {email_migrated} doctors")
            else:
                print("✓ No email migration needed")
            
            # Step 3.5: Migrate phone numbers from users to doctors and patients
            print("\n[3.5/6] Migrating phone numbers from users to doctors and patients...")
            
            # Migrate doctor phone numbers
            doctors = Doctor.query.all()
            doctor_phone_migrated = 0
            for doctor in doctors:
                if not doctor.phone_number and doctor.user_id:
                    user = User.query.get(doctor.user_id)
                    if user and user.mobile:
                        doctor.phone_number = user.mobile
                        doctor_phone_migrated += 1
            
            # Migrate patient phone numbers
            patients = Patient.query.all()
            patient_phone_migrated = 0
            for patient in patients:
                if not patient.phone_number and patient.user_id:
                    user = User.query.get(patient.user_id)
                    if user and user.mobile:
                        patient.phone_number = user.mobile
                        patient_phone_migrated += 1
            
            if doctor_phone_migrated > 0 or patient_phone_migrated > 0:
                db.session.commit()
                print(f"✓ Migrated phone numbers for {doctor_phone_migrated} doctors and {patient_phone_migrated} patients")
            else:
                print("✓ No phone number migration needed")
            
            # Step 4: Check and initialize data
            print("\n[4/6] Checking initial data...")
            hospital_count = Hospital.query.count()
            doctor_count = Doctor.query.count()
            user_count = User.query.count()
            
            print(f"  Current state:")
            print(f"    • Users: {user_count}")
            print(f"    • Hospitals: {hospital_count}")
            print(f"    • Doctors: {doctor_count}")
            
            # Step 5: Sync doctors to hospitals
            print("\n[5/6] Syncing doctors to hospitals...")
            if doctor_count > 0 and hospital_count > 0:
                doctors_to_update = Doctor.query.filter_by(hospital_id=None).all()
                synced = 0
                
                for doctor in doctors_to_update:
                    # Find matching hospital by specialty or name
                    matching_hospital = None
                    
                    # First try to match by hospital_name field
                    if doctor.hospital_name:
                        matching_hospital = Hospital.query.filter_by(name=doctor.hospital_name).first()
                    
                    # If no match, try to match by specialty
                    if not matching_hospital:
                        for hospital in Hospital.query.all():
                            specialties = hospital.get_specialties_list()
                            if doctor.specialization in specialties:
                                matching_hospital = hospital
                                break
                    
                    # Default to first hospital if no match
                    if not matching_hospital:
                        matching_hospital = Hospital.query.first()
                    
                    if matching_hospital:
                        doctor.hospital_id = matching_hospital.id
                        if not doctor.hospital_name:
                            doctor.hospital_name = matching_hospital.name
                        doctor.updated_at = datetime.utcnow()
                        synced += 1
                
                if synced > 0:
                    db.session.commit()
                    print(f"✓ Synced {synced} doctors to hospitals")
                else:
                    print("✓ All doctors already synced")
            else:
                print("⚠ Not enough data to sync (need both doctors and hospitals)")
            
            # Step 6: Summary
            print("\n[6/6] Database summary...")
            user_count = User.query.count()
            patient_count = Patient.query.count()
            doctor_count = Doctor.query.count()
            hospital_count = Hospital.query.count()
            appointment_count = Appointment.query.count()
            
            print(f"  Final state:")
            print(f"    • Users: {user_count}")
            print(f"    • Patients: {patient_count}")
            print(f"    • Doctors: {doctor_count}")
            print(f"    • Hospitals: {hospital_count}")
            print(f"    • Appointments: {appointment_count}")
            
            # Success message
            print("\n" + "="*70)
            print("✅ DATABASE SETUP COMPLETE!")
            print("="*70 + "\n")
            
            return True
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = setup_and_migrate()
    sys.exit(0 if success else 1)

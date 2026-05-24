"""
Database models for Aayushya Healthcare application - MySQL/phpMyAdmin compatible
Enhanced with Hospital model and location-based features
"""
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pymysql
import json

# Install PyMySQL as MySQLdb
pymysql.install_as_MySQLdb()

db = SQLAlchemy()

class User(db.Model):
    """Base user model for both patients and doctors"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    user_type = db.Column(db.Enum('patient', 'doctor'), nullable=False, default='patient')
    mobile = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('Patient', backref='user', uselist=False, lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<User {self.email} - {self.user_type}>'

class Patient(db.Model):
    """Patient profile model"""
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    
    # Personal Information
    full_name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.Enum('Male', 'Female', 'Other', name='gender_enum'))
    blood_group = db.Column(db.Enum('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-', name='blood_group_enum'))
    
    # Medical Information
    allergies = db.Column(db.Text)
    diseases = db.Column(db.Text)
    medical_history = db.Column(db.Text)
    current_medications = db.Column(db.Text)
    
    # Contact Information
    address = db.Column(db.Text)
    phone_number = db.Column(db.String(15))
    alternate_phone = db.Column(db.String(15))
    
    # Emergency Contact
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(15))
    emergency_contact_relationship = db.Column(db.String(50))
    
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert patient data to dictionary"""
        return {
            'patient_id': self.patient_id,
            'full_name': self.full_name,
            'date_of_birth': str(self.date_of_birth) if self.date_of_birth else None,
            'gender': self.gender,
            'blood_group': self.blood_group,
            'allergies': self.allergies,
            'diseases': self.diseases,
            'medical_history': self.medical_history,
            'current_medications': self.current_medications,
            'address': self.address,
            'phone_number': self.phone_number,
            'alternate_phone': self.alternate_phone,
            'emergency_contact_name': self.emergency_contact_name,
            'emergency_contact_phone': self.emergency_contact_phone,
            'emergency_contact_relationship': self.emergency_contact_relationship,
            'mobile': self.user.mobile if self.user else None,
            'email': self.user.email if self.user else None,
            'created_at': str(self.created_at) if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Patient {self.patient_id} - {self.full_name}>'

class Doctor(db.Model):
    """Doctor profile model"""
    __tablename__ = 'doctors'
    
    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=True)  # Added email column
    license_number = db.Column(db.String(50), unique=True, nullable=False)
    specialization = db.Column(db.String(100), nullable=False)
    qualification = db.Column(db.String(100))
    experience_years = db.Column(db.Integer)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.Enum('Male', 'Female', 'Other'))
    hospital_name = db.Column(db.String(100))
    department = db.Column(db.String(100))
    consultation_fee = db.Column(db.DECIMAL(10, 2))
    address = db.Column(db.Text)
    phone_number = db.Column(db.String(15))
    alternate_phone = db.Column(db.String(15))
    available_days = db.Column(db.String(100))
    available_from = db.Column(db.Time)
    available_to = db.Column(db.Time)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='doctor', uselist=False)
    hospital = db.relationship('Hospital', backref='doctors')
    
    def to_dict(self):
        """Convert doctor data to dictionary"""
        return {
            'id': self.id,
            'doctor_id': self.doctor_id,
            'full_name': self.full_name,
            'email': self.email,
            'license_number': self.license_number,
            'specialization': self.specialization,
            'qualification': self.qualification,
            'experience_years': self.experience_years,
            'department': self.department,
            'consultation_fee': float(self.consultation_fee) if self.consultation_fee else None,
            'hospital_id': self.hospital_id,
            'hospital_name': self.hospital_name,
            'phone_number': self.phone_number,
            'alternate_phone': self.alternate_phone,
            'available_days': self.available_days,
            'available_from': str(self.available_from) if self.available_from else None,
            'available_to': str(self.available_to) if self.available_to else None,
            'created_at': str(self.created_at) if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Doctor {self.doctor_id} - {self.full_name}>'

class Hospital(db.Model):
    """Hospital model for queue management"""
    __tablename__ = 'hospitals'
    
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text, nullable=False)
    phone = db.Column(db.String(15))
    email = db.Column(db.String(120))
    website = db.Column(db.String(200))
    specialties = db.Column(db.Text)  # JSON array of specialties
    current_queue_count = db.Column(db.Integer, default=0)
    average_consultation_time = db.Column(db.Integer, default=5)
    operating_hours_start = db.Column(db.Time)
    operating_hours_end = db.Column(db.Time)
    is_active = db.Column(db.Boolean, default=True)
    rating = db.Column(db.DECIMAL(3, 2), default=4.0)
    total_reviews = db.Column(db.Integer, default=0)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships - using hospital_id as foreign key reference
    appointments = db.relationship('Appointment', backref='hospital_ref', lazy=True, 
                                 primaryjoin="Hospital.id == foreign(Appointment.hospital_id)")
    queue_entries = db.relationship('Queue', backref='hospital_ref', lazy=True,
                                  primaryjoin="Hospital.id == foreign(Queue.hospital_id)")
    
    def get_specialties_list(self):
        """Convert JSON specialties to Python list"""
        if self.specialties:
            try:
                return json.loads(self.specialties)
            except:
                return []
        return []
    
    def set_specialties_list(self, specialties_list):
        """Convert Python list to JSON specialties"""
        self.specialties = json.dumps(specialties_list)
    
    def calculate_estimated_wait_time(self):
        """Calculate estimated wait time based on current queue"""
        return self.current_queue_count * self.average_consultation_time
    
    def to_dict(self):
        """Convert hospital data to dictionary"""
        return {
            'id': self.id,  # Database ID (integer) - THIS IS WHAT WE NEED FOR FOREIGN KEY
            'hospital_id': self.hospital_id,  # String ID
            'name': self.name,
            'address': self.address,
            'phone': self.phone,
            'email': self.email,
            'website': self.website,
            'specialties': self.get_specialties_list(),
            'current_queue_count': self.current_queue_count,
            'average_consultation_time': self.average_consultation_time,
            'estimated_wait_time': self.calculate_estimated_wait_time(),
            'operating_hours_start': str(self.operating_hours_start) if self.operating_hours_start else None,
            'operating_hours_end': str(self.operating_hours_end) if self.operating_hours_end else None,
            'is_active': self.is_active,
            'rating': float(self.rating) if self.rating else 0.0,
            'total_reviews': self.total_reviews,
            'created_at': str(self.created_at) if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Hospital {self.hospital_id} - {self.name}>'

class Appointment(db.Model):
    """Appointment model"""
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.String(20), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    hospital_id = db.Column(db.Integer, db.ForeignKey('hospitals.id'), nullable=False)
    appointment_date = db.Column(db.Date, nullable=False)
    appointment_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.Enum('scheduled', 'confirmed', 'completed', 'cancelled'), default='scheduled')
    notes = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional fields for queue management
    estimated_duration = db.Column(db.Integer, default=5)  # minutes
    queue_position = db.Column(db.Integer)
    estimated_wait_time = db.Column(db.Integer)  # minutes
    travel_time = db.Column(db.Integer)  # minutes
    total_estimated_time = db.Column(db.Integer)  # minutes
    
    # Medical information
    symptoms_description = db.Column(db.Text)
    emergency_level = db.Column(db.String(50))
    patient_age = db.Column(db.Integer)
    patient_gender = db.Column(db.String(20))
    medical_history_summary = db.Column(db.Text)
    current_medications = db.Column(db.Text)
    allergies = db.Column(db.Text)
    priority_score = db.Column(db.Integer)
    is_emergency = db.Column(db.Boolean, default=False)
    patient_notes = db.Column(db.Text)
    doctor_notes = db.Column(db.Text)
    
    # Consultation tracking
    actual_arrival_time = db.Column(db.TIMESTAMP)
    actual_consultation_start = db.Column(db.TIMESTAMP)
    actual_consultation_end = db.Column(db.TIMESTAMP)
    
    def to_dict(self):
        """Convert appointment data to dictionary"""
        # Get hospital name by querying Hospital table
        hospital = Hospital.query.get(self.hospital_id)
        hospital_name = hospital.name if hospital else 'Hospital'
        
        return {
            'id': self.id,
            'appointment_id': self.appointment_id,
            'patient_id': self.patient_id,
            'doctor_id': self.doctor_id,
            'hospital_id': self.hospital_id,
            'hospital_name': hospital_name,
            'appointment_date': str(self.appointment_date) if self.appointment_date else None,
            'appointment_time': str(self.appointment_time) if self.appointment_time else None,
            'status': self.status,
            'notes': self.notes,
            'estimated_duration': self.estimated_duration,
            'queue_position': self.queue_position,
            'estimated_wait_time': self.estimated_wait_time,
            'travel_time': self.travel_time,
            'total_estimated_time': self.total_estimated_time,
            'created_at': str(self.created_at) if self.created_at else None
        }
    
    def __repr__(self):
        return f'<Appointment {self.appointment_id}>'

class Queue(db.Model):
    """Enhanced Queue model for real-time queue management"""
    __tablename__ = 'queue'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    hospital_id = db.Column(db.Integer, nullable=False)
    queue_number = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum('waiting', 'in_progress', 'completed'), default='waiting')
    estimated_time = db.Column(db.Time)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    updated_at = db.Column(db.TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Additional fields for enhanced functionality
    appointment_id = db.Column(db.Integer)  # Link to appointment
    estimated_consultation_time = db.Column(db.Integer, default=5)  # minutes
    actual_start_time = db.Column(db.TIMESTAMP)
    actual_end_time = db.Column(db.TIMESTAMP)
    
    def __repr__(self):
        return f'<Queue {self.queue_number} - Hospital {self.hospital_id}>'

class HospitalReview(db.Model):
    """Hospital Review model"""
    __tablename__ = 'hospital_reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    hospital_id = db.Column(db.Integer, nullable=False)
    patient_id = db.Column(db.Integer, nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    review_text = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Review {self.rating}★ for Hospital {self.hospital_id}>'

def init_database(app):
    """Initialize database with some test data"""
    with app.app_context():
        try:
            # Check if database exists and create tables
            db.create_all()
            print("Database tables created successfully!")
            
            # Count existing data
            user_count = User.query.count()
            patient_count = Patient.query.count()
            doctor_count = Doctor.query.count()
            hospital_count = Hospital.query.count()
            
            # Add sample doctors if less than 5 exist
            if doctor_count < 5:
                sample_doctors = [
                    {
                        "full_name": "Rajesh Kumar",
                        "license_number": "MED-001-2020",
                        "specialization": "General Medicine",
                        "qualification": "MBBS, MD",
                        "experience_years": 10,
                        "department": "General Medicine"
                    },
                    {
                        "full_name": "Priya Singh",
                        "license_number": "MED-002-2018",
                        "specialization": "Cardiology",
                        "qualification": "MBBS, MD Cardiology",
                        "experience_years": 12,
                        "department": "Cardiology"
                    },
                    {
                        "full_name": "Amit Patel",
                        "license_number": "MED-003-2019",
                        "specialization": "Pediatrics",
                        "qualification": "MBBS, DCH",
                        "experience_years": 9,
                        "department": "Pediatrics"
                    },
                    {
                        "full_name": "Deepa Gupta",
                        "license_number": "MED-004-2017",
                        "specialization": "Orthopedics",
                        "qualification": "MBBS, MS Orthopedics",
                        "experience_years": 14,
                        "department": "Orthopedics"
                    },
                    {
                        "full_name": "Vikram Sharma",
                        "license_number": "MED-005-2021",
                        "specialization": "Neurology",
                        "qualification": "MBBS, MD Neurology",
                        "experience_years": 8,
                        "department": "Neurology"
                    }
                ]
                
                # Only add doctors that don't exist
                for i, doctor_data in enumerate(sample_doctors[doctor_count:], start=doctor_count):
                    # Check if this doctor already exists
                    existing = Doctor.query.filter_by(license_number=doctor_data["license_number"]).first()
                    if existing:
                        continue
                    
                    # Create user account for doctor
                    doc_user = User(
                        user_type='doctor',
                        mobile=f'98{i:08d}',
                        email=f'doctor{i+1}@aayushya.com',
                        password=generate_password_hash('password123'),
                        is_active=True
                    )
                    db.session.add(doc_user)
                    db.session.flush()  # Get the user ID
                    
                    # Create doctor profile
                    doctor = Doctor(
                        doctor_id=f'DOC-{i+1:05d}',
                        user_id=doc_user.id,
                        full_name=doctor_data["full_name"],
                        license_number=doctor_data["license_number"],
                        specialization=doctor_data["specialization"],
                        qualification=doctor_data["qualification"],
                        experience_years=doctor_data["experience_years"],
                        department=doctor_data["department"],
                        consultation_fee=500.00,
                        available_days="Monday-Friday"
                    )
                    db.session.add(doctor)
                
                db.session.commit()
                doctor_count = Doctor.query.count()
                print(f"Updated doctor count: {doctor_count}")
            
            # Add sample hospitals if none exist
            if hospital_count == 0:
                sample_hospitals = [
                    {
                        "hospital_id": "H-00001",
                        "name": "Apollo Hospitals",
                        "address": "123 Medical Avenue, New Delhi",
                        "phone": "+91-11-2410-1010",
                        "email": "info@apollohospitals.com",
                        "website": "www.apollohospitals.com",
                        "specialties": ["Cardiology", "Neurology", "Orthopedics", "General Medicine"],
                        "rating": 4.8,
                        "total_reviews": 250
                    },
                    {
                        "hospital_id": "H-00002",
                        "name": "Max Healthcare",
                        "address": "456 Health Street, Mumbai",
                        "phone": "+91-22-4141-4141",
                        "email": "contact@maxhealthcare.com",
                        "website": "www.maxhealthcare.com",
                        "specialties": ["Pediatrics", "Oncology", "Gastroenterology", "Dermatology"],
                        "rating": 4.7,
                        "total_reviews": 180
                    },
                    {
                        "hospital_id": "H-00003",
                        "name": "Fortis Healthcare",
                        "address": "789 Care Road, Bangalore",
                        "phone": "+91-80-4444-4444",
                        "email": "help@fortishealthcare.com",
                        "website": "www.fortishealthcare.com",
                        "specialties": ["Emergency Care", "General Surgery", "Psychiatry", "Urology"],
                        "rating": 4.6,
                        "total_reviews": 150
                    },
                    {
                        "hospital_id": "H-00004",
                        "name": "AIIMS Hospital",
                        "address": "Medical Campus, New Delhi",
                        "phone": "+91-11-2658-8500",
                        "email": "info@aiims.edu",
                        "website": "www.aiims.ac.in",
                        "specialties": ["Teaching Hospital", "Research", "All Specialties"],
                        "rating": 4.5,
                        "total_reviews": 300
                    },
                    {
                        "hospital_id": "H-00005",
                        "name": "Manipal Hospitals",
                        "address": "Old Airport Road, Bangalore",
                        "phone": "+91-80-4455-5555",
                        "email": "patient.care@manipalhospitals.com",
                        "website": "www.manipalhospitals.com",
                        "specialties": ["Nephrology", "Rheumatology", "Ophthalmology", "ENT"],
                        "rating": 4.6,
                        "total_reviews": 200
                    }
                ]
                
                for hospital_data in sample_hospitals:
                    specialties_json = json.dumps(hospital_data["specialties"])
                    hospital = Hospital(
                        hospital_id=hospital_data["hospital_id"],
                        name=hospital_data["name"],
                        address=hospital_data["address"],
                        phone=hospital_data["phone"],
                        email=hospital_data["email"],
                        website=hospital_data["website"],
                        specialties=specialties_json,
                        current_queue_count=0,
                        average_consultation_time=5,
                        is_active=True,
                        rating=hospital_data["rating"],
                        total_reviews=hospital_data["total_reviews"]
                    )
                    db.session.add(hospital)
                
                db.session.commit()
                hospital_count = 5
                print("Sample hospitals added to database!")
            
            print(f"Aayushya Healthcare Database initialized with:")
            print(f"   Users: {user_count}")
            print(f"   Patients: {patient_count}")
            print(f"   Doctors: {doctor_count}")
            print(f"   Hospitals: {hospital_count}")
            
            return True
        except Exception as e:
            print(f"Database initialization failed: {e}")
            return False
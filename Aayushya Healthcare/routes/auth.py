"""
Authentication routes for Aayushya Healthcare application
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
from models.db import db, User, Patient, Doctor

auth_bp = Blueprint('auth', __name__)

# ======================== Authentication Decorators ========================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.patient_login_page'))
        return f(*args, **kwargs)
    return decorated_function

def require_patient(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.patient_login_page'))
        user = User.query.get(session['user_id'])
        if not user or user.user_type != 'patient':
            flash('Please login as patient to access this page', 'warning')
            return redirect(url_for('auth.patient_login_page'))
        return f(*args, **kwargs)
    return decorated_function

def require_doctor(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.doctor_login_page'))
        user = User.query.get(session['user_id'])
        if not user or user.user_type != 'doctor':
            flash('Please login as doctor to access this page', 'warning')
            return redirect(url_for('auth.doctor_login_page'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== Login Pages ====================

@auth_bp.route('/patient/login')
def patient_login_page():
    """Patient login form page"""
    if 'user_id' in session and 'user_type' in session:
        if session['user_type'] == 'patient':
            return redirect(url_for('patient.dashboard'))
        elif session['user_type'] == 'doctor':
            return redirect(url_for('doctor.dashboard'))
    return render_template('patient-login.html')

@auth_bp.route('/doctor/login')
def doctor_login_page():
    """Doctor login form page"""
    if 'user_id' in session and 'user_type' in session:
        if session['user_type'] == 'doctor':
            return redirect(url_for('doctor.dashboard'))
        elif session['user_type'] == 'patient':
            return redirect(url_for('patient.dashboard'))
    return render_template('doctor-login.html')

# ==================== Registration Pages ====================

@auth_bp.route('/patient/register')
def patient_register_page():
    """Patient registration form"""
    return render_template('patient-register.html')

@auth_bp.route('/doctor/register')
def doctor_register_page():
    """Doctor registration form"""
    return render_template('doctor-register.html')

# ==================== API Routes ====================

@auth_bp.route('/api/register/patient', methods=['POST'])
def register_patient():
    """Handle patient registration"""
    try:
        data = request.form
        
        # Validation
        mobile = data.get('mobile', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        confirm_password = data.get('confirmPassword', '').strip()
        name = data.get('fullName', '').strip()
        
        # Check required fields
        if not all([mobile, password, name]):
            return jsonify({"success": False, "message": "Mobile, password, and full name are required"}), 400
        
        if password != confirm_password:
            return jsonify({"success": False, "message": "Passwords do not match"}), 400
        
        if len(password) < 6:
            return jsonify({"success": False, "message": "Password must be at least 6 characters"}), 400
        
        # Check if user already exists
        existing_user = None
        if email:  # Only check email if provided
            existing_user = User.query.filter(
                (User.mobile == mobile) | (User.email == email)
            ).first()
        else:
            existing_user = User.query.filter(User.mobile == mobile).first()
        
        if existing_user:
            return jsonify({"success": False, "message": "Mobile number or email already registered"}), 400
        
        # Create new user
        new_user = User(
            user_type='patient',
            mobile=mobile,
            email=email or f"{mobile}@temp.com",  # Use temp email if not provided
            password=generate_password_hash(password, method='pbkdf2:sha256')
        )
        db.session.add(new_user)
        db.session.commit()
        
        # Generate patient ID
        patient_count = Patient.query.count() + 1
        patient_id = f"P-{patient_count:05d}"
        
        # Parse date of birth if provided
        date_of_birth = None
        if data.get('dob') or data.get('dateOfBirth'):
            dob_value = data.get('dob') or data.get('dateOfBirth')
            try:
                date_of_birth = datetime.strptime(dob_value, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # Helper function to convert empty strings to None
        def get_value_or_none(key):
            value = data.get(key, '').strip()
            return value if value else None
        
        # Create patient profile with ALL fields to prevent data loss
        # Empty strings are converted to None (NULL in database)
        new_patient = Patient(
            patient_id=patient_id,
            user_id=new_user.id,
            full_name=name,
            date_of_birth=date_of_birth,
            gender=get_value_or_none('gender'),
            blood_group=get_value_or_none('bloodGroup'),
            allergies=get_value_or_none('allergies'),
            diseases=get_value_or_none('diseases'),
            medical_history=get_value_or_none('medicalHistory'),
            current_medications=get_value_or_none('currentMedications'),
            address=get_value_or_none('address'),
            phone_number=mobile,  # Store primary phone number
            alternate_phone=get_value_or_none('alternatePhone'),
            emergency_contact_name=get_value_or_none('emergencyContactName'),
            emergency_contact_phone=get_value_or_none('emergencyContactPhone'),
            emergency_contact_relationship=get_value_or_none('emergencyContactRelationship')
        )
        db.session.add(new_patient)
        db.session.commit()
        
        # Create session
        session['user_id'] = new_user.id
        session['user_type'] = 'patient'
        session['patient_id'] = patient_id
        
        return jsonify({
            "success": True, 
            "message": "Registration successful!",
            "patient_id": patient_id,
            "redirect": url_for('patient.dashboard')
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Registration failed: {str(e)}"}), 500

@auth_bp.route('/api/register/doctor', methods=['POST'])
def register_doctor():
    """Handle doctor registration"""
    try:
        from models.db import Hospital
        data = request.form
        
        # Validation
        mobile = data.get('mobile', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        confirm_password = data.get('confirmPassword', '').strip()
        name = data.get('fullName', '').strip()
        license_number = data.get('licenseNumber', '').strip()
        specialization = data.get('specialization', '').strip()
        
        # Check required fields
        if not all([mobile, email, password, name, license_number, specialization]):
            return jsonify({"success": False, "message": "All required fields must be filled"}), 400
        
        if password != confirm_password:
            return jsonify({"success": False, "message": "Passwords do not match"}), 400
        
        if len(password) < 6:
            return jsonify({"success": False, "message": "Password must be at least 6 characters"}), 400
        
        # Check if user already exists
        existing_user = User.query.filter(
            (User.mobile == mobile) | (User.email == email)
        ).first()
        
        if existing_user:
            return jsonify({"success": False, "message": "Mobile number or email already registered"}), 400
        
        # Check if license number already exists
        existing_license = Doctor.query.filter_by(license_number=license_number).first()
        if existing_license:
            return jsonify({"success": False, "message": "License number already registered"}), 400
        
        # Create new user
        new_user = User(
            user_type='doctor',
            mobile=mobile,
            email=email,
            password=generate_password_hash(password, method='pbkdf2:sha256')
        )
        db.session.add(new_user)
        db.session.commit()
        
        # Generate doctor ID
        doctor_count = Doctor.query.count() + 1
        doctor_id = f"D-{doctor_count:05d}"
        
        # Get hospital_id from hospital_name if provided
        hospital_name = data.get('hospitalName', '').strip()
        hospital_id = None
        if hospital_name:
            hospital = Hospital.query.filter_by(name=hospital_name).first()
            if hospital:
                hospital_id = hospital.id
        
        # Parse date of birth if provided
        date_of_birth = None
        if data.get('dateOfBirth'):
            try:
                date_of_birth = datetime.strptime(data.get('dateOfBirth'), '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # Helper function to convert empty strings to None
        def get_value_or_none(key):
            value = data.get(key, '').strip()
            return value if value else None
        
        # Create doctor profile with complete data
        # Empty strings are converted to None (NULL in database)
        new_doctor = Doctor(
            doctor_id=doctor_id,
            user_id=new_user.id,
            full_name=name,
            email=email,  # Save email in doctor table
            license_number=license_number,
            specialization=specialization,
            qualification=get_value_or_none('qualification'),
            experience_years=int(data.get('experienceYears', 0)) if data.get('experienceYears') else None,
            date_of_birth=date_of_birth,
            gender=get_value_or_none('gender'),
            department=get_value_or_none('department'),
            consultation_fee=float(data.get('consultationFee', 0)) if data.get('consultationFee') else None,
            hospital_id=hospital_id,  # Automatically set from hospital name
            hospital_name=hospital_name if hospital_name else None,
            address=get_value_or_none('address'),
            phone_number=mobile,  # Store primary phone number
            alternate_phone=get_value_or_none('alternatePhone'),
            available_days=get_value_or_none('availableDays'),
            available_from=datetime.strptime(data.get('availableFrom', '09:00'), '%H:%M').time() if data.get('availableFrom') else None,
            available_to=datetime.strptime(data.get('availableTo', '17:00'), '%H:%M').time() if data.get('availableTo') else None
        )
        db.session.add(new_doctor)
        db.session.commit()
        
        # Create session
        session['user_id'] = new_user.id
        session['user_type'] = 'doctor'
        session['doctor_id'] = doctor_id
        
        return jsonify({
            "success": True, 
            "message": "Registration successful!",
            "doctor_id": doctor_id,
            "redirect": url_for('doctor.dashboard')
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Registration failed: {str(e)}"}), 500

# ==================== Login Routes ====================

@auth_bp.route('/api/login/patient', methods=['POST'])
def login_patient():
    """Handle patient login with multiple credential types"""
    try:
        data = request.get_json()
        identifier = data.get('identifier', '').strip()
        password = data.get('password', '').strip()
        
        if not identifier or not password:
            return jsonify({"success": False, "message": "Identifier and password are required"}), 400
        
        # Find user by email or mobile
        user = User.query.filter(
            (User.email == identifier) | 
            (User.mobile == identifier)
        ).first()
        
        if not user:
            # Try to find by patient ID
            patient = Patient.query.filter_by(patient_id=identifier).first()
            if patient:
                user = patient.user
        
        if not user or user.user_type != 'patient':
            return jsonify({"success": False, "message": "Invalid credentials. Please check your username, email, phone number, or password."}), 401
        
        if not check_password_hash(user.password, password):
            return jsonify({"success": False, "message": "Invalid credentials. Please check your username, email, phone number, or password."}), 401
        
        # Create session
        session['user_id'] = user.id
        session['user_type'] = 'patient'
        session['patient_id'] = user.patient.patient_id if user.patient else None
        
        return jsonify({
            "success": True, 
            "message": "Login successful!",
            "redirect": url_for('patient.dashboard')
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Login failed: {str(e)}"}), 500

@auth_bp.route('/api/login/doctor', methods=['POST'])
def login_doctor():
    """Handle doctor login"""
    try:
        data = request.get_json()
        identifier = data.get('identifier', '').strip()
        password = data.get('password', '').strip()
        
        if not identifier or not password:
            return jsonify({"success": False, "message": "Email/ID and password are required"}), 400
        
        # Find user by email, mobile, or doctor_id
        user = User.query.filter(
            (User.email == identifier) | (User.mobile == identifier)
        ).first()
        
        if not user:
            # Try to find by doctor ID
            doctor = Doctor.query.filter_by(doctor_id=identifier).first()
            if doctor:
                user = doctor.user
        
        if not user or user.user_type != 'doctor':
            return jsonify({"success": False, "message": "Invalid doctor credentials"}), 401
        
        if not check_password_hash(user.password, password):
            return jsonify({"success": False, "message": "Invalid credentials"}), 401
        
        # Get doctor ID
        doctor = Doctor.query.filter_by(user_id=user.id).first()
        doctor_id = doctor.doctor_id if doctor else None
        
        # Create session
        session['user_id'] = user.id
        session['user_type'] = 'doctor'
        session['doctor_id'] = doctor_id
        
        return jsonify({
            "success": True, 
            "message": "Login successful!",
            "redirect": url_for('doctor.dashboard')
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Login failed: {str(e)}"}), 500

@auth_bp.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('main.index'))
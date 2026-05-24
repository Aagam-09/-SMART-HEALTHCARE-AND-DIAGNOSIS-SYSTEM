"""
Doctor routes for MediQueue application
"""
from flask import Blueprint, render_template, request, jsonify, session
from routes.auth import require_doctor
from models.db import db, User, Doctor, Appointment, Patient, Hospital
from datetime import datetime

doctor_bp = Blueprint('doctor', __name__, url_prefix='/doctor')

@doctor_bp.route('/dashboard')
@require_doctor
def dashboard():
    """Doctor dashboard page"""
    user = User.query.get(session['user_id'])
    doctor = Doctor.query.filter_by(user_id=user.id).first()
    return render_template('doctor-dashboard.html', doctor=doctor, user=user)

@doctor_bp.route('/profile')
@require_doctor
def profile():
    """Doctor profile page"""
    user = User.query.get(session['user_id'])
    doctor = Doctor.query.filter_by(user_id=user.id).first()
    return render_template('doctor-profile.html', doctor=doctor, user=user)

@doctor_bp.route('/api/profile', methods=['GET'])
@require_doctor
def get_profile():
    """Get doctor profile data (API)"""
    user = User.query.get(session['user_id'])
    doctor = Doctor.query.filter_by(user_id=user.id).first()
    return jsonify(doctor.to_dict()), 200

@doctor_bp.route('/api/appointments', methods=['GET'])
@require_doctor
def get_appointments():
    """Get all appointments for the doctor with patient details and queue information"""
    try:
        user = User.query.get(session['user_id'])
        doctor = Doctor.query.filter_by(user_id=user.id).first()
        
        # Get all appointments for this doctor
        appointments = Appointment.query.filter_by(doctor_id=doctor.id).order_by(
            Appointment.appointment_date.asc(),
            Appointment.appointment_time.asc()
        ).all()
        
        appointments_data = []
        for apt in appointments:
            apt_dict = apt.to_dict()
            
            # Get patient info
            patient = Patient.query.get(apt.patient_id)
            if patient:
                apt_dict['patient_name'] = patient.full_name
                apt_dict['patient_id'] = patient.patient_id
                apt_dict['patient_phone'] = patient.user.mobile if patient.user else 'N/A'
                apt_dict['patient_email'] = patient.user.email if patient.user else 'N/A'
                apt_dict['patient_blood_group'] = patient.blood_group or 'Not specified'
                apt_dict['patient_age'] = (datetime.now().year - patient.date_of_birth.year) if patient.date_of_birth else 'N/A'
                apt_dict['patient_gender'] = patient.gender or 'Not specified'
                apt_dict['patient_allergies'] = patient.allergies or 'None'
                apt_dict['patient_medical_history'] = patient.medical_history or 'None'
                apt_dict['patient_current_medications'] = patient.current_medications or 'None'
                apt_dict['patient_address'] = patient.address or 'Not provided'
            
            # Add appointment-specific medical info
            apt_dict['symptoms_description'] = apt.symptoms_description or 'Not specified'
            apt_dict['emergency_level'] = apt.emergency_level or 'normal'
            apt_dict['patient_notes'] = apt.patient_notes or 'None'
            
            # Add queue information
            apt_dict['queue_position'] = apt.queue_position or 'N/A'
            apt_dict['estimated_wait_time'] = apt.estimated_wait_time or 0
            
            # Get hospital info
            hospital = Hospital.query.get(apt.hospital_id)
            if hospital:
                apt_dict['hospital_name'] = hospital.name
                apt_dict['hospital_address'] = hospital.address
                apt_dict['hospital_phone'] = hospital.phone
            
            appointments_data.append(apt_dict)
        
        return jsonify({
            "success": True,
            "appointments": appointments_data,
            "total_count": len(appointments_data)
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error fetching appointments: {str(e)}"}), 500

@doctor_bp.route('/appointment/<appointment_id>')
@require_doctor
def view_appointment(appointment_id):
    """View appointment details page"""
    try:
        user = User.query.get(session['user_id'])
        doctor = Doctor.query.filter_by(user_id=user.id).first()
        
        # Get appointment
        appointment = Appointment.query.filter_by(appointment_id=appointment_id).first()
        if not appointment or appointment.doctor_id != doctor.id:
            return render_template('404.html'), 404
        
        # Get patient details
        patient = Patient.query.get(appointment.patient_id)
        
        # Get hospital details
        hospital = Hospital.query.get(appointment.hospital_id)
        
        return render_template('appointment-detail.html', 
                             appointment=appointment, 
                             patient=patient, 
                             hospital=hospital,
                             doctor=doctor, 
                             user=user)
    except Exception as e:
        return render_template('404.html'), 404

@doctor_bp.route('/api/appointment/<appointment_id>')
@require_doctor
def get_appointment_detail(appointment_id):
    """Get appointment details (API)"""
    try:
        user = User.query.get(session['user_id'])
        doctor = Doctor.query.filter_by(user_id=user.id).first()
        
        # Get appointment
        appointment = Appointment.query.filter_by(appointment_id=appointment_id).first()
        if not appointment or appointment.doctor_id != doctor.id:
            return jsonify({"success": False, "message": "Appointment not found"}), 404
        
        # Get patient details
        patient = Patient.query.get(appointment.patient_id)
        hospital = Hospital.query.get(appointment.hospital_id)
        
        apt_dict = appointment.to_dict()
        
        if patient:
            apt_dict['patient'] = {
                'full_name': patient.full_name,
                'patient_id': patient.patient_id,
                'date_of_birth': str(patient.date_of_birth) if patient.date_of_birth else None,
                'gender': patient.gender,
                'blood_group': patient.blood_group,
                'phone': patient.user.mobile if patient.user else None,
                'allergies': patient.allergies,
                'medical_history': patient.medical_history,
                'current_medications': patient.current_medications,
                'address': patient.address
            }
        
        if hospital:
            apt_dict['hospital'] = {
                'name': hospital.name,
                'address': hospital.address,
                'phone': hospital.phone,
                'email': hospital.email
            }
        
        return jsonify({
            "success": True,
            "appointment": apt_dict
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@doctor_bp.route('/api/update', methods=['PUT'])
@require_doctor
def update_profile():
    """Update doctor profile"""
    try:
        from models.db import Hospital
        user = User.query.get(session['user_id'])
        doctor = Doctor.query.filter_by(user_id=user.id).first()
        data = request.get_json()
        
        # Helper function to convert empty strings to None
        def get_value_or_none(key):
            if key not in data:
                return None
            value = data[key]
            if value is None:
                return None
            if isinstance(value, str):
                value = value.strip()
                return value if value else None
            return value
        
        # Update allowed fields - empty strings converted to None (NULL in database)
        if 'full_name' in data:
            full_name = get_value_or_none('full_name')
            if full_name:
                doctor.full_name = full_name
        if 'email' in data:
            email = get_value_or_none('email')
            if email:
                doctor.email = email
                user.email = email  # Also update user email
        if 'specialization' in data:
            specialization = get_value_or_none('specialization')
            if specialization:
                doctor.specialization = specialization
        if 'qualification' in data:
            doctor.qualification = get_value_or_none('qualification')
        if 'experience_years' in data:
            doctor.experience_years = data['experience_years']
        if 'date_of_birth' in data and data['date_of_birth']:
            try:
                doctor.date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
            except ValueError:
                pass
        if 'gender' in data:
            doctor.gender = get_value_or_none('gender')
        if 'hospital_name' in data:
            hospital_name = get_value_or_none('hospital_name')
            doctor.hospital_name = hospital_name
            # Automatically retrieve hospital_id from hospital name
            if hospital_name:
                hospital = Hospital.query.filter_by(name=hospital_name).first()
                if hospital:
                    doctor.hospital_id = hospital.id
            else:
                doctor.hospital_id = None
        if 'department' in data:
            doctor.department = get_value_or_none('department')
        if 'consultation_fee' in data:
            doctor.consultation_fee = data['consultation_fee']
        if 'address' in data:
            doctor.address = get_value_or_none('address')
        if 'phone_number' in data:
            doctor.phone_number = get_value_or_none('phone_number')
        if 'alternate_phone' in data:
            doctor.alternate_phone = get_value_or_none('alternate_phone')
        if 'available_days' in data:
            doctor.available_days = get_value_or_none('available_days')
        if 'available_from' in data:
            available_from = get_value_or_none('available_from')
            if available_from:
                doctor.available_from = datetime.strptime(available_from, '%H:%M').time()
            else:
                doctor.available_from = None
        if 'available_to' in data:
            available_to = get_value_or_none('available_to')
            if available_to:
                doctor.available_to = datetime.strptime(available_to, '%H:%M').time()
            else:
                doctor.available_to = None
        
        doctor.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"success": True, "message": "Profile updated successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Update failed: {str(e)}"}), 500
"""
Patient routes for Aayushya Healthcare application
"""
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from routes.auth import require_patient
from models.db import db, User, Patient, Hospital, Appointment, Doctor, Queue
from services.queue_service import QueueService
from datetime import datetime, date, timedelta
import uuid
import os

patient_bp = Blueprint('patient', __name__, url_prefix='/patient')

@patient_bp.route('/dashboard')
@require_patient
def dashboard():
    """Patient dashboard page"""
    user = User.query.get(session['user_id'])
    patient = user.patient
    from datetime import datetime
    return render_template('patient-dashboard-professional.html', patient=patient, user=user, now=datetime.now().date())

@patient_bp.route('/profile')
@require_patient
def profile():
    """Patient profile page"""
    user = User.query.get(session['user_id'])
    patient = user.patient
    return render_template('patient-profile.html', patient=patient, user=user)

@patient_bp.route('/api/profile', methods=['GET'])
@require_patient
def get_profile():
    """Get patient profile data (API)"""
    user = User.query.get(session['user_id'])
    patient = user.patient
    return jsonify(patient.to_dict()), 200

@patient_bp.route('/api/update', methods=['PUT'])
@require_patient
def update_profile():
    """Update patient profile"""
    try:
        user = User.query.get(session['user_id'])
        patient = user.patient
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
        
        # Update allowed fields - ensure ALL fields are handled
        # Empty strings are converted to None (NULL in database)
        if 'full_name' in data:
            patient.full_name = data['full_name']
        if 'date_of_birth' in data and data['date_of_birth']:
            try:
                patient.date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
            except ValueError:
                pass
        if 'gender' in data:
            patient.gender = get_value_or_none('gender')
        if 'blood_group' in data:
            patient.blood_group = get_value_or_none('blood_group')
        if 'allergies' in data:
            patient.allergies = get_value_or_none('allergies')
        if 'diseases' in data:
            patient.diseases = get_value_or_none('diseases')
        if 'medical_history' in data:
            patient.medical_history = get_value_or_none('medical_history')
        if 'current_medications' in data:
            patient.current_medications = get_value_or_none('current_medications')
        if 'address' in data:
            patient.address = get_value_or_none('address')
        if 'phone_number' in data:
            patient.phone_number = get_value_or_none('phone_number')
        if 'alternate_phone' in data:
            patient.alternate_phone = get_value_or_none('alternate_phone')
        if 'emergency_contact_name' in data:
            patient.emergency_contact_name = get_value_or_none('emergency_contact_name')
        if 'emergency_contact_phone' in data:
            patient.emergency_contact_phone = get_value_or_none('emergency_contact_phone')
        if 'emergency_contact_relationship' in data:
            patient.emergency_contact_relationship = get_value_or_none('emergency_contact_relationship')
        
        # Update user email if provided
        if 'email' in data:
            email = get_value_or_none('email')
            if email:
                user.email = email
        
        # Update user mobile if provided
        if 'mobile' in data:
            mobile = get_value_or_none('mobile')
            if mobile:
                user.mobile = mobile
        
        patient.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({"success": True, "message": "Profile updated successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Update failed: {str(e)}"}), 500

@patient_bp.route('/api/appointments', methods=['GET'])
@require_patient
def get_appointments():
    """Get patient's appointments"""
    try:
        user = User.query.get(session['user_id'])
        patient = user.patient
        
        appointments = Appointment.query.filter_by(patient_id=patient.id).order_by(
            Appointment.appointment_date.desc(),
            Appointment.appointment_time.desc()
        ).all()
        
        appointments_data = []
        for apt in appointments:
            apt_dict = apt.to_dict()
            
            # Get doctor info
            doctor = Doctor.query.get(apt.doctor_id)
            if doctor:
                apt_dict['doctor_name'] = doctor.full_name
                apt_dict['doctor_specialization'] = doctor.specialization
            
            # Get hospital info
            hospital = Hospital.query.get(apt.hospital_id)
            if hospital:
                apt_dict['hospital_name'] = hospital.name
                apt_dict['hospital_address'] = hospital.address
            
            # Get queue info if available
            queue = Queue.query.filter_by(appointment_id=apt.id).first()
            if queue:
                patients_ahead = queue.queue_number - 1
                estimated_wait = patients_ahead * (hospital.average_consultation_time if hospital else 20)
                apt_dict['queue_info'] = {
                    'queue_number': queue.queue_number,
                    'patients_ahead': patients_ahead,
                    'estimated_wait': f"{estimated_wait} min"
                }
            
            appointments_data.append(apt_dict)
        
        return jsonify({
            "success": True,
            "appointments": appointments_data,
            "total_count": len(appointments_data)
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error fetching appointments: {str(e)}"}), 500

@patient_bp.route('/api/hospitals', methods=['GET'])
@require_patient
def get_hospitals():
    """Get list of all hospitals for appointment booking"""
    try:
        hospitals = Hospital.query.filter_by(is_active=True).all()
        hospitals_data = []
        
        for hospital in hospitals:
            hospital_dict = hospital.to_dict()
            # Get actual current queue count from Queue table
            actual_queue_count = Queue.query.filter_by(
                hospital_id=hospital.id,
                status='waiting'
            ).count()
            hospital_dict['current_queue_count'] = actual_queue_count
            hospitals_data.append(hospital_dict)
        
        return jsonify({
            "success": True,
            "hospitals": hospitals_data,
            "total_count": len(hospitals_data)
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error fetching hospitals: {str(e)}"}), 500

@patient_bp.route('/api/doctors', methods=['GET'])
@require_patient
def get_doctors():
    """Get list of all doctors, optionally filtered by hospital or specialization"""
    try:
        hospital_id = request.args.get('hospital_id')
        specialization = request.args.get('specialization')
        
        query = Doctor.query
        
        if hospital_id:
            query = query.filter_by(hospital_id=int(hospital_id))
        
        if specialization:
            query = query.filter_by(specialization=specialization)
        
        doctors = query.all()
        doctors_data = [doctor.to_dict() for doctor in doctors]
        
        return jsonify({
            "success": True,
            "doctors": doctors_data,
            "total_count": len(doctors_data)
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error fetching doctors: {str(e)}"}), 500

@patient_bp.route('/api/specializations', methods=['GET'])
@require_patient
def get_specializations():
    """Get unique specializations"""
    try:
        specializations = db.session.query(Doctor.specialization).distinct().all()
        specs = [spec[0] for spec in specializations if spec[0]]
        specs.sort()
        
        return jsonify({
            "success": True,
            "specializations": specs
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@patient_bp.route('/api/queue-info', methods=['POST'])
@require_patient
def get_queue_info():
    """Get queue information for hospital, doctor, and date before booking"""
    try:
        data = request.get_json()
        hospital_id = int(data.get('hospital_id', 0))
        doctor_id = int(data.get('doctor_id', 0))
        appointment_date = datetime.strptime(data.get('appointment_date', ''), '%Y-%m-%d').date()
        
        if not all([hospital_id, doctor_id, appointment_date]):
            return jsonify({"success": False, "message": "Missing required fields"}), 400
        
        # Get hospital
        hospital = Hospital.query.get(hospital_id)
        if not hospital:
            return jsonify({"success": False, "message": "Invalid hospital"}), 400
        
        avg_time = hospital.average_consultation_time or 5
        
        # Get all appointments for this doctor on this date
        appointments = Appointment.query.filter_by(
            doctor_id=doctor_id,
            hospital_id=hospital_id,
            appointment_date=appointment_date
        ).order_by(Appointment.appointment_time).all()
        
        # Create hourly slots with queue info
        slots = []
        start_hour = 9  # 9 AM
        end_hour = 17   # 5 PM
        
        for hour in range(start_hour, end_hour):
            slot_time = f"{hour:02d}:00"
            
            # Count appointments in this hour
            appointments_in_slot = [
                apt for apt in appointments
                if apt.appointment_time.hour == hour
            ]
            
            queue_count = len(appointments_in_slot)
            wait_time = queue_count * avg_time
            
            slots.append({
                "time": slot_time,
                "hour": hour,
                "queue_count": queue_count,
                "wait_time": wait_time,
                "wait_time_str": f"{wait_time} min" if queue_count > 0 else "No wait"
            })
        
        return jsonify({
            "success": True,
            "slots": slots,
            "average_time_per_patient": avg_time
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@patient_bp.route('/book-appointment')
@require_patient
def book_appointment():
    """Book appointment page - wizard form"""
    user = User.query.get(session['user_id'])
    patient = user.patient
    return render_template('booking-wizard.html', patient=patient, user=user)

@patient_bp.route('/api/book-appointment', methods=['POST'])
@require_patient
def create_appointment():
    """Create a new appointment"""
    try:
        user = User.query.get(session['user_id'])
        patient = user.patient
        data = request.get_json()
        
        print(f"DEBUG: Received data: {data}")  # Debug log
        
        # Validate required fields - check if they exist and are not None or empty string
        required_fields = ['hospital_id', 'doctor_id', 'appointment_date', 'appointment_time', 'symptoms_description']
        for field in required_fields:
            if field not in data:
                print(f"DEBUG: Field {field} not in data keys: {data.keys()}")
                return jsonify({"success": False, "message": f"Missing required field: {field}"}), 400
            
            # Check if value is None, empty string, or the string 'undefined'
            value = data[field]
            if value is None or (isinstance(value, str) and (value.strip() == '' or value.lower() == 'undefined')):
                print(f"DEBUG: Field {field} has invalid value: {value}")
                return jsonify({"success": False, "message": f"Missing required field: {field}"}), 400
        
        # Parse and validate hospital_id
        try:
            hospital_id = int(data['hospital_id'])
            print(f"DEBUG: Parsed hospital_id: {hospital_id}")
        except (ValueError, TypeError) as e:
            print(f"DEBUG: Failed to parse hospital_id: {e}")
            return jsonify({"success": False, "message": "Invalid hospital selection"}), 400
        
        # Parse and validate doctor_id
        try:
            doctor_id = int(data['doctor_id'])
            print(f"DEBUG: Parsed doctor_id: {doctor_id}")
        except (ValueError, TypeError) as e:
            print(f"DEBUG: Failed to parse doctor_id: {e}")
            return jsonify({"success": False, "message": "Invalid doctor selection"}), 400
        
        # Parse date and time
        try:
            appointment_date = datetime.strptime(data['appointment_date'], '%Y-%m-%d').date()
            appointment_time = datetime.strptime(data['appointment_time'], '%H:%M').time()
        except ValueError:
            return jsonify({"success": False, "message": "Invalid date or time format"}), 400
        
        # Validate date is in future
        if appointment_date < date.today():
            return jsonify({"success": False, "message": "Appointment date cannot be in the past"}), 400
        
        # Verify hospital exists and is active
        hospital = Hospital.query.get(hospital_id)
        if not hospital or not hospital.is_active:
            return jsonify({"success": False, "message": "Invalid hospital selected"}), 400
        
        # Verify doctor exists
        doctor = Doctor.query.get(doctor_id)
        if not doctor:
            return jsonify({"success": False, "message": "Invalid doctor selected"}), 400
        
        # Create appointment
        appointment_id = f"APT-{str(uuid.uuid4())[:8].upper()}"
        appointment = Appointment(
            appointment_id=appointment_id,
            patient_id=patient.id,
            doctor_id=doctor.id,
            hospital_id=hospital.id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            status='scheduled',
            notes=data.get('notes', ''),
            symptoms_description=data.get('symptoms_description', ''),
            emergency_level=data.get('emergency_level', 'normal'),
            current_medications=data.get('current_medications', ''),
            medical_history_summary=data.get('medical_history', ''),
            allergies=data.get('allergies', ''),
            patient_age=patient.date_of_birth.year if patient.date_of_birth else None,
            patient_gender=patient.gender,
            patient_notes=data.get('notes', '')
        )
        
        db.session.add(appointment)
        db.session.flush()
        
        # Calculate proper queue number based on date and doctor
        # For same day: count appointments before this time
        # For future: count appointments on that date
        from datetime import date as date_class
        today = date_class.today()
        
        if appointment_date == today:
            # TODAY: Queue based on time on same day
            queue_count = Appointment.query.filter(
                Appointment.doctor_id == doctor_id,
                Appointment.hospital_id == hospital_id,
                Appointment.appointment_date == today,
                Appointment.appointment_time < appointment_time
            ).count()
        else:
            # FUTURE: Queue based on date
            queue_count = Appointment.query.filter(
                Appointment.doctor_id == doctor_id,
                Appointment.appointment_date == appointment_date,
                Appointment.appointment_time < appointment_time
            ).count()
        
        appointment.queue_position = queue_count + 1
        db.session.commit()
        
        # Create queue entry only for today's appointments
        if appointment_date == today:
            queue_entry = Queue(
                patient_id=patient.id,
                doctor_id=doctor.id,
                hospital_id=hospital.id,
                queue_number=appointment.queue_position,
                appointment_id=appointment.id,
                estimated_consultation_time=hospital.average_consultation_time,
                status='waiting'
            )
            db.session.add(queue_entry)
            db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Appointment booked successfully",
            "appointment_id": appointment.appointment_id,
            "redirect_url": url_for('patient.appointment_success', appointment_id=appointment.appointment_id)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Booking failed: {str(e)}"}), 500

@patient_bp.route('/appointment-confirmed/<appointment_id>')
@require_patient
def appointment_success(appointment_id):
    """Appointment confirmed page"""
    try:
        user = User.query.get(session['user_id'])
        patient = user.patient
        
        # Get appointment
        appointment = Appointment.query.filter(
            Appointment.appointment_id == appointment_id,
            Appointment.patient_id == patient.id
        ).first()
        
        if not appointment:
            return redirect(url_for('patient.dashboard'))
        
        # Get hospital details
        hospital = Hospital.query.get(appointment.hospital_id)
        
        # Get doctor details
        doctor = Doctor.query.get(appointment.doctor_id)
        
        # Get queue information
        queue_entry = Queue.query.filter_by(appointment_id=appointment.id).first()
        queue_number = queue_entry.queue_number if queue_entry else 0
        patients_ahead = queue_number - 1
        estimated_time_minutes = patients_ahead * (hospital.average_consultation_time if hospital else 20)
        
        return render_template('appointment-confirmed.html',
            appointment_id=appointment.appointment_id,
            queue_number=queue_number,
            patients_ahead=patients_ahead,
            estimated_time_minutes=estimated_time_minutes,
            estimated_time_formatted=f"{estimated_time_minutes} minutes",
            hospital_name=hospital.name if hospital else 'N/A',
            hospital_address=hospital.address if hospital else 'N/A',
            hospital_phone=hospital.phone if hospital else 'N/A',
            doctor_name=doctor.full_name if doctor else 'N/A',
            doctor_specialization=doctor.specialization if doctor else 'N/A',
            patient_name=patient.full_name,
            appointment_date=appointment.appointment_date.strftime('%d %B %Y') if appointment.appointment_date else 'N/A',
            appointment_time=appointment.appointment_time.strftime('%I:%M %p') if appointment.appointment_time else 'N/A'
        )
        
    except Exception as e:
        print(f"Error on appointment confirmed page: {e}")
        return redirect(url_for('patient.dashboard'))

@patient_bp.route('/api/cancel-appointment/<appointment_id>', methods=['POST'])
@require_patient
def cancel_appointment(appointment_id):
    """Cancel an appointment"""
    try:
        user = User.query.get(session['user_id'])
        patient = user.patient
        
        appointment = Appointment.query.filter(
            Appointment.appointment_id == appointment_id,
            Appointment.patient_id == patient.id
        ).first()
        
        if not appointment:
            return jsonify({"success": False, "message": "Appointment not found"}), 404
        
        if appointment.status == 'completed':
            return jsonify({"success": False, "message": "Cannot cancel a completed appointment"}), 400
        
        appointment.status = 'cancelled'
        db.session.commit()
        
        return jsonify({"success": True, "message": "Appointment cancelled successfully"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Cancellation failed: {str(e)}"}), 500

@patient_bp.route('/appointment/<appointment_id>')
@require_patient
def appointment_detail(appointment_id):
    """View appointment details"""
    try:
        user = User.query.get(session['user_id'])
        patient = user.patient
        
        appointment = Appointment.query.filter(
            Appointment.appointment_id == appointment_id,
            Appointment.patient_id == patient.id
        ).first()
        
        if not appointment:
            flash('Appointment not found', 'error')
            return redirect(url_for('patient.dashboard'))
        
        # Get related data
        doctor = Doctor.query.get(appointment.doctor_id)
        hospital = Hospital.query.get(appointment.hospital_id)
        queue = Queue.query.filter_by(appointment_id=appointment.id).first()
        
        return render_template('appointment-detail.html',
            appointment=appointment,
            doctor=doctor,
            hospital=hospital,
            queue=queue,
            patient=patient
        )
        
    except Exception as e:
        flash(f'Error loading appointment: {str(e)}', 'error')
        return redirect(url_for('patient.dashboard'))

@patient_bp.route('/api/doctors-by-hospital/<int:hospital_id>')
@require_patient
def get_doctors_by_hospital(hospital_id):
    """Get doctors for a specific hospital with available specializations and queue info"""
    try:
        from datetime import date
        today = date.today()
        
        # Get all doctors for this hospital
        doctors = Doctor.query.filter_by(hospital_id=hospital_id).all()
        
        # Get unique specializations for this hospital
        specializations = list(set([d.specialization for d in doctors if d.specialization]))
        specializations.sort()
        
        doctors_data = []
        for doctor in doctors:
            doctor_dict = doctor.to_dict()
            
            # Get current queue count for this doctor today
            today_appointments = Appointment.query.filter(
                Appointment.doctor_id == doctor.id,
                Appointment.appointment_date == today,
                Appointment.status.in_(['scheduled', 'confirmed'])
            ).count()
            
            # Calculate wait time (5 minutes per patient)
            wait_time = today_appointments * 5
            
            doctor_dict['current_queue'] = today_appointments
            doctor_dict['estimated_wait_minutes'] = wait_time
            doctor_dict['wait_time_text'] = f"{wait_time} min" if wait_time > 0 else "No wait"
            
            doctors_data.append(doctor_dict)
        
        # Sort doctors by wait time (shortest first)
        doctors_data.sort(key=lambda x: x['estimated_wait_minutes'])
        
        return jsonify({
            "success": True,
            "doctors": doctors_data,
            "specializations": specializations,
            "total_count": len(doctors_data)
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500


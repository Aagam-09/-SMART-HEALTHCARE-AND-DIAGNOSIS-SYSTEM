"""
Main routes for Aayushya Healthcare application
"""
from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
from models.db import db, User, Patient, Doctor, Hospital, Appointment, Queue
from services.queue_service import QueueService
from datetime import datetime
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Landing page with patient/doctor selection"""
    return render_template('index.html')

@main_bp.route('/nearby-hospitals')
def nearby_hospitals():
    """Redirect to new book appointment page"""
    # Check if user is logged in
    if 'user_id' not in session or session.get('user_type') != 'patient':
        return redirect(url_for('auth.patient_login_page'))
    return redirect(url_for('patient.book_appointment'))

@main_bp.route('/api/hospitals/nearby', methods=['POST'])
def api_nearby_hospitals():
    """API endpoint to get all hospitals"""
    try:
        hospitals = Hospital.query.filter_by(is_active=True).all()
        hospitals_data = [hospital.to_dict() for hospital in hospitals]
        
        return jsonify({
            "status": "success",
            "hospitals": hospitals_data,
            "total_count": len(hospitals_data)
        }), 200
        
    except Exception as e:
        print(f"Error in hospitals API: {e}")
        return jsonify({"error": "Internal server error"}), 500

@main_bp.route('/api/hospitals/list', methods=['GET'])
def api_hospitals_list():
    """API endpoint to get list of all hospitals for registration forms"""
    try:
        hospitals = Hospital.query.filter_by(is_active=True).order_by(Hospital.name).all()
        hospitals_data = [{"id": h.id, "name": h.name, "address": h.address} for h in hospitals]
        
        return jsonify({
            "success": True,
            "hospitals": hospitals_data,
            "total_count": len(hospitals_data)
        }), 200
        
    except Exception as e:
        print(f"Error in hospitals list API: {e}")
        return jsonify({"success": False, "error": "Internal server error"}), 500

@main_bp.route('/api/test/database')
def test_database():
    """Test database connection and display data"""
    try:
        users = User.query.all()
        patients = Patient.query.all()
        doctors = Doctor.query.all()
        hospitals = Hospital.query.all()
        
        result = {
            "database_status": "connected",
            "total_users": len(users),
            "total_patients": len(patients),
            "total_doctors": len(doctors),
            "total_hospitals": len(hospitals),
            "users": [{"id": u.id, "email": u.email, "type": u.user_type} for u in users],
            "patients": [{"id": p.patient_id, "name": p.full_name} for p in patients],
            "doctors": [{"id": d.doctor_id, "name": d.full_name, "specialization": d.specialization} for d in doctors],
            "hospitals": [{"id": h.hospital_id, "name": h.name, "queue": h.current_queue_count} for h in hospitals]
        }
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"database_status": "error", "message": str(e)}), 500

@main_bp.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@main_bp.errorhandler(500)
def internal_error(error):
    from models.db import db
    db.session.rollback()
    return jsonify({"error": "Internal server error"}), 500

@main_bp.route('/api/appointments/book', methods=['POST'])
def api_book_appointment():
    """API endpoint to book an appointment"""
    try:
        # Check if user is logged in as patient
        if 'user_id' not in session or session.get('user_type') != 'patient':
            return jsonify({"error": "Please login as a patient to book appointments"}), 401
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['hospital_id', 'appointment_date', 'appointment_time', 'specialty']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({"error": f"{field} is required"}), 400
        
        # Get patient
        user = User.query.get(session['user_id'])
        patient = user.patient
        if not patient:
            return jsonify({"error": "Patient profile not found"}), 404
        
        # Get hospital by ID (not hospital_id field)
        hospital = Hospital.query.get(int(data['hospital_id']))
        if not hospital or not hospital.is_active:
            return jsonify({"error": "Hospital not found"}), 404
        
        # Parse date and time
        try:
            appointment_date = datetime.strptime(data['appointment_date'], '%Y-%m-%d').date()
            appointment_time = datetime.strptime(data['appointment_time'], '%H:%M').time()
        except ValueError:
            return jsonify({"error": "Invalid date or time format"}), 400
        
        # Check if appointment date is not in the past
        if appointment_date < datetime.now().date():
            return jsonify({"error": "Cannot book appointments for past dates"}), 400
        
        # Generate appointment ID
        appointment_id = f"APT-{datetime.now().strftime('%Y%m%d')}-{len(Appointment.query.all()) + 1:04d}"
        
        # Get user location if provided
        user_lat = data.get('user_latitude')
        user_lng = data.get('user_longitude')
        
        # Calculate travel time and total estimated time
        travel_time = None
        total_estimated_time = hospital.calculate_estimated_wait_time()
        
        # Create appointment
        appointment = Appointment(
            appointment_id=appointment_id,
            patient_id=patient.id,
            doctor_id=1,  # For now, assign to first doctor - this should be enhanced
            hospital_id=hospital.id,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            estimated_duration=5,  # Default 5 minutes
            status='scheduled',
            queue_position=hospital.current_queue_count + 1,
            estimated_wait_time=hospital.calculate_estimated_wait_time(),
            travel_time=travel_time,
            total_estimated_time=total_estimated_time,
            patient_latitude=user_lat,
            patient_longitude=user_lng,
            notes=data.get('notes', '')
        )
        
        db.session.add(appointment)
        
        # Update hospital queue count
        hospital.current_queue_count += 1
        
        # Add to queue
        queue_entry = Queue(
            patient_id=patient.id,
            doctor_id=1,  # Same as appointment
            hospital_id=hospital.id,
            queue_number=hospital.current_queue_count,
            estimated_consultation_time=5,
            status='waiting'
        )
        
        db.session.add(queue_entry)
        db.session.commit()
        
        # Link appointment to queue entry
        queue_entry.appointment_id = appointment.id
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Appointment booked successfully!",
            "appointment": {
                "appointment_id": appointment_id,
                "hospital_name": hospital.name,
                "appointment_date": str(appointment_date),
                "appointment_time": str(appointment_time),
                "queue_position": appointment.queue_position,
                "estimated_wait_time": appointment.estimated_wait_time,
                "travel_time": travel_time,
                "total_estimated_time": total_estimated_time
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Error booking appointment: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "Failed to book appointment. Please try again."}), 500
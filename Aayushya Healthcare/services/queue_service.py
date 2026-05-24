"""
Queue Management Service for Aayushya Healthcare
Handles queue numbers, estimated wait times, and queue position calculations
"""
from datetime import datetime, timedelta
from models.db import Queue, Appointment, Hospital

class QueueService:
    """Service for managing appointment queues and calculating wait times"""
    
    @staticmethod
    def calculate_queue_number(hospital_id):
        """
        Calculate next queue number for a hospital
        
        Args:
            hospital_id: ID of the hospital
            
        Returns:
            Next queue number for the hospital
        """
        # Get all active queue entries for the hospital
        latest_queue = Queue.query.filter_by(hospital_id=hospital_id).filter(
            Queue.status.in_(['waiting', 'in_progress'])
        ).order_by(Queue.queue_number.desc()).first()
        
        if latest_queue:
            return latest_queue.queue_number + 1
        else:
            return 1
    
    @staticmethod
    def calculate_estimated_time(hospital_id, consultation_time_minutes=5):
        """
        Calculate estimated wait time based on current queue
        
        Args:
            hospital_id: ID of the hospital
            consultation_time_minutes: Average consultation time per patient (default 5 mins)
            
        Returns:
            Dictionary with queue info and estimated times
        """
        # Get hospital details
        hospital = Hospital.query.get(hospital_id)
        if not hospital:
            return None
        
        # Get current queue count
        waiting_queue = Queue.query.filter_by(
            hospital_id=hospital_id,
            status='waiting'
        ).count()
        
        in_progress_queue = Queue.query.filter_by(
            hospital_id=hospital_id,
            status='in_progress'
        ).count()
        
        # Calculate estimated wait time
        # Remaining time for in-progress consultations + waiting queue time
        estimated_wait_minutes = (in_progress_queue * consultation_time_minutes) + (waiting_queue * consultation_time_minutes)
        
        # Calculate estimated time with some buffer (10% additional time for transitions)
        estimated_time_with_buffer = int(estimated_wait_minutes * 1.1)
        
        return {
            'queue_count': waiting_queue,
            'in_progress_count': in_progress_queue,
            'consultation_time': consultation_time_minutes,
            'estimated_wait_minutes': estimated_wait_minutes,
            'estimated_wait_minutes_with_buffer': estimated_time_with_buffer,
            'estimated_completion_time': datetime.now() + timedelta(minutes=estimated_time_with_buffer)
        }
    
    @staticmethod
    def get_queue_position(appointment_id):
        """
        Get the current queue position for an appointment
        
        Args:
            appointment_id: ID of the appointment
            
        Returns:
            Queue position info
        """
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return None
        
        queue_entry = Queue.query.filter_by(appointment_id=appointment_id).first()
        if not queue_entry:
            return None
        
        hospital = appointment.hospital_ref
        
        # Count how many are ahead in queue
        ahead_count = Queue.query.filter_by(
            hospital_id=appointment.hospital_id,
            status='waiting'
        ).filter(Queue.queue_number < queue_entry.queue_number).count()
        
        # Get estimated time info
        estimated_info = QueueService.calculate_estimated_time(
            appointment.hospital_id,
            hospital.average_consultation_time if hospital else 5
        )
        
        return {
            'queue_number': queue_entry.queue_number,
            'status': queue_entry.status,
            'patients_ahead': ahead_count,
            'estimated_time_minutes': estimated_info['estimated_wait_minutes_with_buffer'] if estimated_info else 0,
            'estimated_completion_time': estimated_info['estimated_completion_time'] if estimated_info else None,
            'appointment_id': appointment_id
        }
    
    @staticmethod
    def format_estimated_time(minutes):
        """
        Format estimated time in minutes to a readable string
        
        Args:
            minutes: Number of minutes
            
        Returns:
            Formatted time string (e.g., "15 minutes", "1 hour 30 minutes")
        """
        if minutes < 60:
            return f"{minutes} minutes"
        else:
            hours = minutes // 60
            mins = minutes % 60
            if mins == 0:
                return f"{hours} hour{'s' if hours > 1 else ''}"
            else:
                return f"{hours} hour{'s' if hours > 1 else ''} {mins} minutes"
    
    @staticmethod
    def get_appointment_details_with_queue(appointment_id):
        """
        Get full appointment details including queue information
        
        Args:
            appointment_id: ID of the appointment
            
        Returns:
            Complete appointment info with queue details
        """
        appointment = Appointment.query.get(appointment_id)
        if not appointment:
            return None
        
        queue_info = QueueService.get_queue_position(appointment_id)
        hospital = appointment.hospital_ref
        patient = appointment.patient_id
        
        # Get patient details
        from models.db import Patient
        patient_obj = Patient.query.get(patient)
        
        appointment_data = appointment.to_dict()
        appointment_data['hospital_name'] = hospital.name if hospital else 'N/A'
        appointment_data['hospital_address'] = hospital.address if hospital else 'N/A'
        appointment_data['hospital_phone'] = hospital.phone if hospital else 'N/A'
        appointment_data['patient_name'] = patient_obj.full_name if patient_obj else 'N/A'
        appointment_data['queue_number'] = queue_info['queue_number'] if queue_info else 0
        appointment_data['queue_status'] = queue_info['status'] if queue_info else 'unknown'
        appointment_data['estimated_wait_minutes'] = queue_info['estimated_time_minutes'] if queue_info else 0
        appointment_data['estimated_wait_time_formatted'] = QueueService.format_estimated_time(
            queue_info['estimated_time_minutes'] if queue_info else 0
        )
        appointment_data['patients_ahead'] = queue_info['patients_ahead'] if queue_info else 0
        
        return appointment_data

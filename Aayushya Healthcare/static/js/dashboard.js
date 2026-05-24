// Dashboard JavaScript for MediQueue Application

document.addEventListener('DOMContentLoaded', function() {
    // Initialize dashboard
    initializeDashboard();
    
    // Setup profile update forms
    setupProfileForms();
    
    // Load dashboard data
    loadDashboardData();
});

function initializeDashboard() {
    // Add hover effects to dashboard cards
    document.querySelectorAll('.dashboard-card, .quick-action-btn').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
    
    // Initialize charts if needed
    initializeCharts();
    
    // Setup real-time updates
    setupRealTimeUpdates();
}

function setupProfileForms() {
    // Patient profile update
    const patientProfileForm = document.getElementById('patientProfileForm');
    if (patientProfileForm) {
        patientProfileForm.addEventListener('submit', handlePatientProfileUpdate);
    }
    
    // Doctor profile update
    const doctorProfileForm = document.getElementById('doctorProfileForm');
    if (doctorProfileForm) {
        doctorProfileForm.addEventListener('submit', handleDoctorProfileUpdate);
    }
    
    // Setup form validation
    setupDashboardFormValidation();
}

async function handlePatientProfileUpdate(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const formData = new FormData(form);
    
    // Convert FormData to JSON
    const data = {};
    formData.forEach((value, key) => {
        data[key] = value;
    });
    
    try {
        showLoading(submitBtn);
        
        const response = await fetch('/patient/api/update', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        // Parse JSON defensively (server may sometimes return non-JSON)
        let result = null;
        const raw = await response.text();
        try {
            result = raw ? JSON.parse(raw) : null;
        } catch (err) {
            console.warn('Non-JSON response from /patient/api/update:', raw);
        }
        console.debug('Patient profile update response:', response.status, result);

        // Use HTTP status as the primary success indicator
        if (response.ok) {
            form.querySelectorAll('.alert-error, .alert-danger, #errorAlert, #errorMessage').forEach(el => el.style.display = 'none');
            showAlert((result && result.message) ? result.message : 'Profile updated successfully', 'success');
            // Refresh profile data
            loadPatientProfile();
        } else {
            form.querySelectorAll('.alert-success, #successAlert, #successMessage').forEach(el => el.style.display = 'none');
            const errMsg = (result && result.message) ? result.message : `Update failed (status ${response.status})`;
            showAlert(errMsg, 'danger');
        }
        
    } catch (error) {
        // On exception hide inline success containers and show failure toast
        form.querySelectorAll('.alert-success, #successAlert, #successMessage').forEach(el => el.style.display = 'none');
        showAlert('Profile update failed. Please try again.', 'danger');
        console.error('Profile update error:', error);
    } finally {
        hideLoading(submitBtn);
    }
}

async function handleDoctorProfileUpdate(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const formData = new FormData(form);
    
    // Convert FormData to JSON
    const data = {};
    formData.forEach((value, key) => {
        data[key] = value;
    });
    
    try {
        showLoading(submitBtn);
        
        const response = await fetch('/doctor/api/update', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        // Parse JSON defensively (server may sometimes return non-JSON)
        let result = null;
        const raw = await response.text();
        try {
            result = raw ? JSON.parse(raw) : null;
        } catch (err) {
            console.warn('Non-JSON response from /doctor/api/update:', raw);
        }
        console.debug('Doctor profile update response:', response.status, result);

        // Use HTTP status as the primary success indicator
        if (response.ok) {
            form.querySelectorAll('.alert-error, .alert-danger, #errorAlert, #errorMessage').forEach(el => el.style.display = 'none');
            showAlert((result && result.message) ? result.message : 'Profile updated successfully', 'success');
            // Refresh profile data
            loadDoctorProfile();
        } else {
            form.querySelectorAll('.alert-success, #successAlert, #successMessage').forEach(el => el.style.display = 'none');
            const errMsg = (result && result.message) ? result.message : `Update failed (status ${response.status})`;
            showAlert(errMsg, 'danger');
        }
        
    } catch (error) {
        // On exception hide inline success containers and show failure toast
        form.querySelectorAll('.alert-success, #successAlert, #successMessage').forEach(el => el.style.display = 'none');
        showAlert('Profile update failed. Please try again.', 'danger');
        console.error('Profile update error:', error);
    } finally {
        hideLoading(submitBtn);
    }
}

async function loadDashboardData() {
    try {
        // Load user-specific dashboard data
        const userType = getUserType();
        
        if (userType === 'patient') {
            await loadPatientDashboardData();
        } else if (userType === 'doctor') {
            await loadDoctorDashboardData();
        }
        
    } catch (error) {
        console.error('Dashboard data loading error:', error);
    }
}

async function loadPatientDashboardData() {
    try {
        // Load patient profile
        const profileResponse = await fetch('/patient/api/profile');
        if (profileResponse.ok) {
            const profileData = await profileResponse.json();
            updatePatientDashboard(profileData);
        }
        
        // Load appointments, queue status, etc.
        // This would be implemented when those features are added
        
    } catch (error) {
        console.error('Patient dashboard data error:', error);
    }
}

async function loadDoctorDashboardData() {
    try {
        // Load doctor profile
        const profileResponse = await fetch('/doctor/api/profile');
        if (profileResponse.ok) {
            const profileData = await profileResponse.json();
            updateDoctorDashboard(profileData);
        }
        
        // Load appointments, patient queue, etc.
        // This would be implemented when those features are added
        
    } catch (error) {
        console.error('Doctor dashboard data error:', error);
    }
}

function updatePatientDashboard(profileData) {
    // Update patient-specific dashboard elements
    const welcomeName = document.querySelector('.dashboard-welcome .dashboard-info h2');
    if (welcomeName && profileData.full_name) {
        welcomeName.textContent = `Welcome back, ${profileData.full_name}!`;
    }
    
    const patientId = document.querySelector('.patient-id');
    if (patientId && profileData.patient_id) {
        patientId.textContent = profileData.patient_id;
    }
    
    // Update profile information in cards
    updateProfileCard(profileData);
}

function updateDoctorDashboard(profileData) {
    // Update doctor-specific dashboard elements
    const welcomeName = document.querySelector('.dashboard-welcome .dashboard-info h2');
    if (welcomeName && profileData.full_name) {
        welcomeName.textContent = `Welcome back, Dr. ${profileData.full_name}!`;
    }
    
    const doctorId = document.querySelector('.doctor-id');
    if (doctorId && profileData.doctor_id) {
        doctorId.textContent = profileData.doctor_id;
    }
    
    const specialization = document.querySelector('.doctor-specialization');
    if (specialization && profileData.specialization) {
        specialization.textContent = profileData.specialization;
    }
    
    // Update profile information in cards
    updateProfileCard(profileData);
}

function updateProfileCard(profileData) {
    // Update profile card with latest data
    Object.keys(profileData).forEach(key => {
        const element = document.querySelector(`[data-profile="${key}"]`);
        if (element && profileData[key]) {
            element.textContent = profileData[key];
        }
    });
}

function initializeCharts() {
    // Initialize any charts or graphs
    // This would be implemented when analytics features are added
    
    // Example: Appointment trends chart
    const chartContainer = document.getElementById('appointmentChart');
    if (chartContainer) {
        // Initialize chart library (Chart.js, D3.js, etc.)
        console.log('Charts would be initialized here');
    }
}

function setupRealTimeUpdates() {
    // Setup WebSocket or polling for real-time updates
    // This would be implemented for real-time queue updates
    
    // Example: Poll for queue updates every 30 seconds
    setInterval(() => {
        updateQueueStatus();
    }, 30000);
}

async function updateQueueStatus() {
    try {
        // This would fetch real-time queue status
        // const response = await fetch('/api/queue/status');
        // const queueData = await response.json();
        // updateQueueDisplay(queueData);
        
        console.log('Queue status would be updated here');
    } catch (error) {
        console.error('Queue status update error:', error);
    }
}

function setupDashboardFormValidation() {
    // Setup validation for dashboard forms
    document.querySelectorAll('input[type="email"]').forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value.trim()) {
                validateField(this, MediQueue.validateEmail(this.value), 'Please enter a valid email address');
            }
        });
    });
    
    document.querySelectorAll('input[type="tel"], input[name*="phone"]').forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value.trim()) {
                validateField(this, MediQueue.validatePhone(this.value), 'Please enter a valid phone number');
            }
        });
    });
}

function validateField(field, isValid, errorMessage) {
    const feedback = field.parentNode.querySelector('.invalid-feedback') || 
                    field.parentNode.querySelector('.valid-feedback');
    
    // Remove existing feedback
    if (feedback) {
        feedback.remove();
    }
    
    // Remove existing classes
    field.classList.remove('is-valid', 'is-invalid');
    
    if (field.value.trim() === '') {
        return; // Don't validate empty fields
    }
    
    if (isValid) {
        field.classList.add('is-valid');
    } else {
        field.classList.add('is-invalid');
        const invalidFeedback = document.createElement('div');
        invalidFeedback.className = 'invalid-feedback';
        invalidFeedback.textContent = errorMessage;
        field.parentNode.appendChild(invalidFeedback);
    }
}

function getUserType() {
    // Get user type from URL or session data
    const path = window.location.pathname;
    if (path.includes('/patient/')) {
        return 'patient';
    } else if (path.includes('/doctor/')) {
        return 'doctor';
    }
    return null;
}

// Utility functions
function showAlert(message, type) {
    if (window.MediQueue && window.MediQueue.showAlert) {
        window.MediQueue.showAlert(message, type);
    }
}

function showLoading(button) {
    if (window.MediQueue && window.MediQueue.showLoading) {
        window.MediQueue.showLoading(button);
    }
}

function hideLoading(button) {
    if (window.MediQueue && window.MediQueue.hideLoading) {
        window.MediQueue.hideLoading(button);
    }
}

// Export functions for external use
window.Dashboard = {
    loadPatientProfile: loadPatientDashboardData,
    loadDoctorProfile: loadDoctorDashboardData,
    updateQueueStatus,
    getUserType
};
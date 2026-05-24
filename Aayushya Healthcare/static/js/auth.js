// Authentication JavaScript for MediQueue Application

document.addEventListener('DOMContentLoaded', function() {
    // Patient Login Form
    const patientLoginForm = document.getElementById('patientLoginForm');
    if (patientLoginForm) {
        patientLoginForm.addEventListener('submit', handlePatientLogin);
    }
    
    // Doctor Login Form
    const doctorLoginForm = document.getElementById('doctorLoginForm');
    if (doctorLoginForm) {
        doctorLoginForm.addEventListener('submit', handleDoctorLogin);
    }
    
    // Patient Registration Form
    const patientRegisterForm = document.getElementById('patientRegisterForm');
    if (patientRegisterForm) {
        patientRegisterForm.addEventListener('submit', handlePatientRegistration);
    }
    
    // Doctor Registration Form
    const doctorRegisterForm = document.getElementById('doctorRegisterForm');
    if (doctorRegisterForm) {
        doctorRegisterForm.addEventListener('submit', handleDoctorRegistration);
    }
    
    // Real-time form validation
    setupFormValidation();
});

// Patient Login Handler
async function handlePatientLogin(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const identifier = form.querySelector('#identifier').value.trim();
    const password = form.querySelector('#password').value.trim();
    
    // Clear previous alerts
    clearAlerts();
    
    // Validation
    if (!identifier || !password) {
        showAlert('Please fill in all fields', 'danger');
        return;
    }
    
    try {
        showLoading(submitBtn);
        
        const response = await fetch('/api/login/patient', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                identifier: identifier,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(data.message, 'success');
            setTimeout(() => {
                window.location.href = data.redirect;
            }, 1000);
        } else {
            showAlert(data.message, 'danger');
        }
        
    } catch (error) {
        showAlert('Login failed. Please try again.', 'danger');
        console.error('Login error:', error);
    } finally {
        hideLoading(submitBtn);
    }
}

// Doctor Login Handler
async function handleDoctorLogin(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const identifier = form.querySelector('#identifier').value.trim();
    const password = form.querySelector('#password').value.trim();
    
    // Clear previous alerts
    clearAlerts();
    
    // Validation
    if (!identifier || !password) {
        showAlert('Please fill in all fields', 'danger');
        return;
    }
    
    try {
        showLoading(submitBtn);
        
        const response = await fetch('/api/login/doctor', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                identifier: identifier,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(data.message, 'success');
            setTimeout(() => {
                window.location.href = data.redirect;
            }, 1000);
        } else {
            showAlert(data.message, 'danger');
        }
        
    } catch (error) {
        showAlert('Login failed. Please try again.', 'danger');
        console.error('Login error:', error);
    } finally {
        hideLoading(submitBtn);
    }
}

// Patient Registration Handler
async function handlePatientRegistration(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const formData = new FormData(form);
    
    // Clear previous alerts
    clearAlerts();
    
    // Validation
    const password = formData.get('password');
    const confirmPassword = formData.get('confirmPassword');
    const email = formData.get('email');
    const mobile = formData.get('mobile');
    
    if (password !== confirmPassword) {
        showAlert('Passwords do not match', 'danger');
        return;
    }
    
    if (!MediQueue.validateEmail(email)) {
        showAlert('Please enter a valid email address', 'danger');
        return;
    }
    
    if (!MediQueue.validatePhone(mobile)) {
        showAlert('Please enter a valid phone number', 'danger');
        return;
    }
    
    if (!MediQueue.validatePassword(password)) {
        showAlert('Password must be at least 6 characters long', 'danger');
        return;
    }
    
    try {
        showLoading(submitBtn);
        
        const response = await fetch('/api/register/patient', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(`${data.message} Your Patient ID: ${data.patient_id}`, 'success');
            setTimeout(() => {
                window.location.href = data.redirect;
            }, 2000);
        } else {
            showAlert(data.message, 'danger');
        }
        
    } catch (error) {
        showAlert('Registration failed. Please try again.', 'danger');
        console.error('Registration error:', error);
    } finally {
        hideLoading(submitBtn);
    }
}

// Doctor Registration Handler
async function handleDoctorRegistration(e) {
    e.preventDefault();
    
    const form = e.target;
    const submitBtn = form.querySelector('button[type="submit"]');
    const formData = new FormData(form);
    
    // Clear previous alerts
    clearAlerts();
    
    // Validation
    const password = formData.get('password');
    const confirmPassword = formData.get('confirmPassword');
    const email = formData.get('email');
    const mobile = formData.get('mobile');
    
    if (password !== confirmPassword) {
        showAlert('Passwords do not match', 'danger');
        return;
    }
    
    if (!MediQueue.validateEmail(email)) {
        showAlert('Please enter a valid email address', 'danger');
        return;
    }
    
    if (!MediQueue.validatePhone(mobile)) {
        showAlert('Please enter a valid phone number', 'danger');
        return;
    }
    
    if (!MediQueue.validatePassword(password)) {
        showAlert('Password must be at least 6 characters long', 'danger');
        return;
    }
    
    try {
        showLoading(submitBtn);
        
        const response = await fetch('/api/register/doctor', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showAlert(`${data.message} Your Doctor ID: ${data.doctor_id}`, 'success');
            setTimeout(() => {
                window.location.href = data.redirect;
            }, 2000);
        } else {
            showAlert(data.message, 'danger');
        }
        
    } catch (error) {
        showAlert('Registration failed. Please try again.', 'danger');
        console.error('Registration error:', error);
    } finally {
        hideLoading(submitBtn);
    }
}

// Form Validation Setup
function setupFormValidation() {
    // Email validation
    document.querySelectorAll('input[type="email"]').forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this, MediQueue.validateEmail(this.value), 'Please enter a valid email address');
        });
    });
    
    // Phone validation
    document.querySelectorAll('input[name="mobile"], input[name="alternatePhone"], input[name="emergencyContactPhone"]').forEach(input => {
        input.addEventListener('blur', function() {
            if (this.value.trim()) {
                validateField(this, MediQueue.validatePhone(this.value), 'Please enter a valid phone number');
            }
        });
    });
    
    // Password validation
    document.querySelectorAll('input[name="password"]').forEach(input => {
        input.addEventListener('blur', function() {
            validateField(this, MediQueue.validatePassword(this.value), 'Password must be at least 6 characters long');
        });
    });
    
    // Confirm password validation
    document.querySelectorAll('input[name="confirmPassword"]').forEach(input => {
        input.addEventListener('blur', function() {
            const password = document.querySelector('input[name="password"]').value;
            validateField(this, this.value === password, 'Passwords do not match');
        });
    });
}

// Field Validation Helper
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
        const validFeedback = document.createElement('div');
        validFeedback.className = 'valid-feedback';
        validFeedback.textContent = 'Looks good!';
        field.parentNode.appendChild(validFeedback);
    } else {
        field.classList.add('is-invalid');
        const invalidFeedback = document.createElement('div');
        invalidFeedback.className = 'invalid-feedback';
        invalidFeedback.textContent = errorMessage;
        field.parentNode.appendChild(invalidFeedback);
    }
}

// Utility Functions
function showAlert(message, type) {
    if (window.MediQueue && window.MediQueue.showAlert) {
        window.MediQueue.showAlert(message, type);
    } else {
        // Fallback alert
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.auth-card') || document.querySelector('.container') || document.body;
        container.insertBefore(alertDiv, container.firstChild);
        
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

function showLoading(button) {
    if (window.MediQueue && window.MediQueue.showLoading) {
        window.MediQueue.showLoading(button);
    } else {
        // Fallback loading
        const spinner = document.createElement('span');
        spinner.className = 'loading-spinner';
        spinner.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        button.insertBefore(spinner, button.firstChild);
        button.disabled = true;
    }
}

function hideLoading(button) {
    if (window.MediQueue && window.MediQueue.hideLoading) {
        window.MediQueue.hideLoading(button);
    } else {
        // Fallback loading
        const spinner = button.querySelector('.loading-spinner');
        if (spinner) {
            spinner.remove();
        }
        button.disabled = false;
    }
}

function clearAlerts() {
    document.querySelectorAll('.alert').forEach(alert => {
        alert.remove();
    });
}
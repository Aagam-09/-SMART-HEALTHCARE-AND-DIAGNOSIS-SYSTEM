// Main JavaScript for MediQueue Application

// Enhanced Dark Mode Toggle with Switch
document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.getElementById('darkModeToggle');

    const storedTheme = localStorage.getItem('darkMode');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    const enableDark = storedTheme === null ? prefersDark : storedTheme === 'true';

    document.body.classList.toggle('dark-mode', enableDark);

    if (toggle) toggle.checked = enableDark;

    if (toggle) {
        toggle.addEventListener('change', () => {
            document.body.classList.toggle('dark-mode', toggle.checked);
            localStorage.setItem('darkMode', toggle.checked);
        });
    }
});


// User Options Modal Function
function showUserOptions(userType) {
    const modal = new bootstrap.Modal(document.getElementById('userOptionsModal'));
    const modalTitle = document.getElementById('modalTitle');
    const doctorOptions = document.getElementById('doctorOptions');
    const patientOptions = document.getElementById('patientOptions');
    
    // Hide both options first
    patientOptions.style.display = 'none';
    doctorOptions.style.display = 'none';
    
    if (userType === 'patient') {
        modalTitle.textContent = 'Patient Options';
        patientOptions.style.display = 'block';
        patientOptions.classList.add('animate-fade-in-up');
    } else {
        modalTitle.textContent = 'Doctor Options';
        doctorOptions.style.display = 'block';
        doctorOptions.classList.add('animate-fade-in-up');
    }
    
    modal.show();
    
    // Remove animation class after modal is hidden
    modal._element.addEventListener('hidden.bs.modal', function () {
        patientOptions.classList.remove('animate-fade-in-up');
        doctorOptions.classList.remove('animate-fade-in-up');
    });
}

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const targetId = this.getAttribute('href');
        if (targetId === '#') return;
        
        const targetElement = document.querySelector(targetId);
        if (targetElement) {
            window.scrollTo({
                top: targetElement.offsetTop - 80,
                behavior: 'smooth'
            });
        }
    });
});

// Add scroll effect to navbar
window.addEventListener('scroll', function() {
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        if (window.scrollY > 100) {
            navbar.style.boxShadow = '0 5px 20px rgba(0,0,0,0.1)';
            navbar.style.backdropFilter = 'blur(10px)';
        } else {
            navbar.style.boxShadow = '0 5px 20px rgba(0,0,0,0.05)';
            navbar.style.backdropFilter = 'blur(10px)';
        }
    }
});

// Add ripple effect to buttons
document.querySelectorAll('.btn-custom, .modal-option-btn').forEach(button => {
    button.addEventListener('click', function(e) {
        const ripple = document.createElement('span');
        const rect = this.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = e.clientX - rect.left - size / 2;
        const y = e.clientY - rect.top - size / 2;
        
        ripple.style.cssText = `
            position: absolute;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.7);
            transform: scale(0);
            animation: ripple 0.6s linear;
            width: ${size}px;
            height: ${size}px;
            top: ${y}px;
            left: ${x}px;
        `;
        
        this.appendChild(ripple);
        
        setTimeout(() => ripple.remove(), 600);
    });
});

// Add ripple animation
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Utility functions
function showAlert(message, type = 'info') {
    // Remove any previously shown transient alerts created by this function
    // (use a dedicated class so static inline alert elements are not affected)
    document.querySelectorAll('.mq-toast').forEach(el => el.remove());

    const alertDiv = document.createElement('div');
    alertDiv.className = `alert mq-toast alert-${type} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    const container = document.querySelector('.container') || document.body;
    container.insertBefore(alertDiv, container.firstChild);

    // Auto dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function showLoading(button) {
    const spinner = button.querySelector('.loading-spinner');
    if (spinner) {
        spinner.style.display = 'inline-block';
    }
    button.disabled = true;
}

function hideLoading(button) {
    const spinner = button.querySelector('.loading-spinner');
    if (spinner) {
        spinner.style.display = 'none';
    }
    button.disabled = false;
}

// Form validation utilities
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validatePhone(phone) {
    const re = /^[\+]?[1-9][\d]{0,15}$/;
    return re.test(phone.replace(/\s/g, ''));
}

function validatePassword(password) {
    return password.length >= 6;
}

// Export functions for use in other scripts
window.MediQueue = {
    showAlert,
    showLoading,
    hideLoading,
    validateEmail,
    validatePhone,
    validatePassword,
    showUserOptions
};
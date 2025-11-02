// Main JavaScript file for Building Reservation System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            if (alert.classList.contains('show')) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    });

    // Add loading state to forms
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function() {
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton && !submitButton.disabled) {
                const originalText = submitButton.innerHTML;
                submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Loading...';
                submitButton.disabled = true;
                
                // Re-enable after 10 seconds as fallback
                setTimeout(function() {
                    submitButton.innerHTML = originalText;
                    submitButton.disabled = false;
                }, 1000);
            }
        });
    });

    // Index page specific initialization
    initializeIndexPage();
});

// ========================================
// INDEX PAGE FUNCTIONS
// ========================================

function initializeIndexPage() {
    // Only run on pages with the search form
    const searchForm = document.getElementById('searchForm');
    if (!searchForm) return;

    // Set today's date as minimum
    const today = new Date().toISOString().split('T')[0];
    const dateInput = document.getElementById('slot_date');
    if (dateInput) {
        dateInput.min = today;
        dateInput.value = today;
    }

    // Load buildings on page load
    loadBuildings();

    // Handle building change to load floors
    const buildingSelect = document.getElementById('building_id');
    if (buildingSelect) {
        buildingSelect.addEventListener('change', function() {
            const buildingId = this.value;
            if (buildingId) {
                loadFloors(buildingId);
            } else {
                document.getElementById('floor').innerHTML = '<option value="">Any floor</option>';
            }
        });
    }

    // Handle search form submission
    searchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        if (validateTimeRange()) {
            searchRooms();
        }
    });

    // Handle reservation submission
    const submitButton = document.getElementById('submitReservation');
    if (submitButton) {
        submitButton.addEventListener('click', function() {
            reservationForm.submitReservation();
        });
    }
}

function validateTimeRange() {
    const startHour = document.getElementById('start_hour').value;
    const endHour = document.getElementById('end_hour').value;
    
    // Both times are required
    if (!startHour || !endHour) {
        alert('Please select both start and end times');
        return false;
    }
    
    // Validate that end > start
    if (parseInt(endHour) <= parseInt(startHour)) {
        alert('End time must be after start time');
        return false;
    }
    
    return true;
}

function loadBuildings() {
    fetch('/buildings')
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('building_id');
            select.innerHTML = '<option value="">Any building</option>';
            data.buildings.forEach(building => {
                select.innerHTML += `<option value="${building.building_id}">${building.name}</option>`;
            });
        })
        .catch(error => console.error('Error loading buildings:', error));
}

function loadFloors(buildingId) {
    fetch(`/floors/${buildingId}`)
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById('floor');
            select.innerHTML = '<option value="">Any floor</option>';
            data.floors.forEach(floor => {
                select.innerHTML += `<option value="${floor}">Floor ${floor}</option>`;
            });
        })
        .catch(error => console.error('Error loading floors:', error));
}

function searchRooms() {
    const formData = new FormData(document.getElementById('searchForm'));
    const params = new URLSearchParams(formData);
    
    document.getElementById('searchResults').innerHTML = `
        <div class="text-center py-3">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;

    fetch(`/search?${params}`)
        .then(response => response.json())
        .then(data => {
            displaySearchResults(data.rooms, formData);
        })
        .catch(error => {
            console.error('Error searching rooms:', error);
            document.getElementById('searchResults').innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle"></i>
                    Error searching rooms. Please try again.
                </div>
            `;
        });
}

function displaySearchResults(rooms, searchData) {
    const resultsDiv = document.getElementById('searchResults');
    
    if (rooms.length === 0) {
        resultsDiv.innerHTML = `
            <div class="text-center text-muted py-4">
                <i class="fas fa-calendar-times fa-3x mb-3"></i>
                <h5>No Available Rooms</h5>
                <p>No rooms match your search criteria. Try adjusting your filters.</p>
            </div>
        `;
        return;
    }

    const startHour = searchData.get('start_hour') || '';
    const endHour = searchData.get('end_hour') || '';

    let html = `<div class="row">`;
    rooms.forEach(room => {
        html += `
            <div class="col-md-6 mb-3">
                <div class="card h-100">
                    <div class="card-body">
                        <h6 class="card-title">
                            <i class="fas fa-door-open"></i> Room ${room.room_num}
                        </h6>
                        <p class="card-text mb-2">
                            <strong>Building:</strong> ${room.building_name}<br>
                            <strong>Floor:</strong> ${room.floor}<br>
                            <strong>Capacity:</strong> ${room.capacity} people
                        </p>
                        <button class="btn btn-success btn-sm" onclick="showReservationModal(${room.room_id}, '${room.room_num}', '${room.building_name}', ${room.floor}, ${room.capacity}, '${searchData.get('slot_date')}', '${startHour}', '${endHour}')">
                            <i class="fas fa-calendar-plus"></i> Reserve Room
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
    html += `</div>`;
    
    resultsDiv.innerHTML = html;
}

function showReservationModal(roomId, roomNum, buildingName, floor, capacity, slotDate, startHour, endHour) {
    document.getElementById('modal_room_id').value = roomId;
    document.getElementById('modal_slot_date').value = slotDate;
    document.getElementById('modal_start_hour').value = startHour;
    document.getElementById('modal_end_hour').value = endHour;
    
    // Convert to 12-hour format
    const formatHour = (hour) => {
        hour = parseInt(hour);
        if (hour === 0) return '12:00 AM';
        if (hour < 12) return `${hour}:00 AM`;
        if (hour === 12) return '12:00 PM';
        return `${hour - 12}:00 PM`;
    };
    const timeSlot = `${formatHour(startHour)} - ${formatHour(endHour)}`;
    
    document.getElementById('roomDetails').innerHTML = `
        <strong>Room:</strong> ${roomNum}<br>
        <strong>Building:</strong> ${buildingName}<br>
        <strong>Floor:</strong> ${floor}<br>
        <strong>Capacity:</strong> ${capacity} people<br>
        <strong>Date:</strong> ${slotDate}<br>
        <strong>Time:</strong> ${timeSlot}
    `;
    
    document.getElementById('reserved_by').value = '';
    
    const modal = new bootstrap.Modal(document.getElementById('reservationModal'));
    modal.show();
}

function submitReservation() {
    const formData = new FormData(document.getElementById('reservationForm'));
    const data = Object.fromEntries(formData);
    
    // Validation
    if (!data.reserved_by.trim()) {
        alert('Please enter your name');
        return;
    }
    
    if (!data.start_hour || !data.end_hour) {
        alert('Please select a specific time range for your reservation');
        return;
    }
    
    if (parseInt(data.end_hour) <= parseInt(data.start_hour)) {
        alert('End time must be after start time');
        return;
    }

    fetch('/reserve', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            alert('Reservation submitted successfully! You will be notified once it\'s approved.');
            bootstrap.Modal.getInstance(document.getElementById('reservationModal')).hide();
            searchRooms(); // Refresh results
        }
    })
    .catch(error => {
        console.error('Error submitting reservation:', error);
        alert('Error submitting reservation. Please try again.');
    });
}

// ========================================
// UTILITY FUNCTIONS
// ========================================

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatTime(hour) {
    const startHour = String(hour).padStart(2, '0');
    const endHour = String(hour + 1).padStart(2, '0');
    return `${startHour}:00 - ${endHour}:00`;
}

function showNotification(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-hide after 5 seconds
    setTimeout(function() {
        if (alertDiv.classList.contains('show')) {
            const bsAlert = new bootstrap.Alert(alertDiv);
            bsAlert.close();
        }
    }, 5000);
}

// API helper functions
async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        throw error;
    }
}

// Confirmation dialogs
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Date validation
function validateDate(dateString) {
    const date = new Date(dateString);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    return date >= today;
}

// Time slot validation
function validateTimeSlot(hour) {
    return hour >= 7 && hour <= 16;
}

document.addEventListener('DOMContentLoaded', function() {
    const reservationForm = document.getElementById('reservationModal')
    if (reservationForm) {
        reservationForm.addEventListener('submit', function(e) {
            e.preventDefault();
            submitReservation();
        });
    }
});

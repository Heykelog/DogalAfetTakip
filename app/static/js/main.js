// Main JavaScript file for the Emergency Employee Tracking System

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    const popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Channel selector for message sending form
    const channelOptions = document.querySelectorAll('.channel-option');
    const channelInput = document.getElementById('channel-input');
    
    if (channelOptions.length > 0 && channelInput) {
        channelOptions.forEach(function(option) {
            option.addEventListener('click', function() {
                // Remove active class from all options
                channelOptions.forEach(function(opt) {
                    opt.classList.remove('active');
                });
                
                // Add active class to selected option
                this.classList.add('active');
                
                // Set input value
                channelInput.value = this.dataset.channel;
            });
        });
    }

    // City filter in employee list
    const cityFilter = document.getElementById('city-filter');
    if (cityFilter) {
        cityFilter.addEventListener('change', function() {
            const form = this.closest('form');
            if (form) {
                form.submit();
            }
        });
    }

    // Status filter in employee list
    const statusFilter = document.getElementById('status-filter');
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            const form = this.closest('form');
            if (form) {
                form.submit();
            }
        });
    }

    // Employee search form
    const searchForm = document.getElementById('search-form');
    const searchInput = document.getElementById('search-input');
    const clearSearchBtn = document.getElementById('clear-search');
    
    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', function() {
            if (searchInput) {
                searchInput.value = '';
                searchForm.submit();
            }
        });
    }

    // Message template selection
    const templateSelect = document.getElementById('template-select');
    const messageTextarea = document.getElementById('message-text');
    
    if (templateSelect && messageTextarea) {
        const templates = {
            'status-check': 'Merhaba, güvende olduğunuzu umuyoruz. Lütfen durumunuzu belirtiniz: 1-Güvendeyim, 2-Enkaz altındayım, 3-Tıbbi yardıma ihtiyacım var, 4-Desteğe ihtiyacım var',
            'earthquake-alert': 'DİKKAT! Bölgenizde deprem meydana geldi. Lütfen güvenli bir alana geçiniz ve durumunuzu bildiriniz.',
            'flood-alert': 'DİKKAT! Bölgenizde sel tehlikesi mevcut. Lütfen yüksek ve güvenli bir alana geçiniz ve durumunuzu bildiriniz.',
            'fire-alert': 'DİKKAT! Bölgenizde yangın tehlikesi mevcut. Lütfen güvenli bir alana geçiniz ve durumunuzu bildiriniz.',
            'all-clear': 'Tehlike geçmiştir. Durumunuzu güncellemeniz için teşekkür ederiz.'
        };
        
        templateSelect.addEventListener('change', function() {
            const selectedTemplate = this.value;
            if (selectedTemplate in templates) {
                messageTextarea.value = templates[selectedTemplate];
            }
        });
    }

    // Confirm actions (delete, etc.)
    const confirmButtons = document.querySelectorAll('[data-confirm]');
    confirmButtons.forEach(function(button) {
        button.addEventListener('click', function(e) {
            const message = this.dataset.confirm || 'Bu işlemi gerçekleştirmek istediğinizden emin misiniz?';
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
});

// Function to format date in Turkish format
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('tr-TR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Function to update employee status
function updateEmployeeStatus(employeeId, status) {
    fetch(`/api/employees/${employeeId}/status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': 'your-secret-api-key' // Would be handled securely in a real app
        },
        body: JSON.stringify({
            employee_id: employeeId,
            status: status,
            timestamp: new Date().toISOString()
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Reload page to show updated status
            window.location.reload();
        } else {
            alert('Durum güncellenirken bir hata oluştu: ' + (data.error || 'Bilinmeyen hata'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Bir hata oluştu.');
    });
} 
// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Fetch initial data
    fetchDashboardData();
    fetchEmployees();
    fetchMessages();
    fetchCities(); // Load cities for filtering
    fetchRegions(); // Load regions for filtering
    
    // Set up event listeners
    setupEventListeners();
    
    // Initialize the message preview
    updateMessagePreview();
    
    // Bölge seçimi varsayılan olarak görünür olsun
    document.getElementById('region-selection').style.display = 'block';
    document.getElementById('city-selection').style.display = 'none';
    document.getElementById('employee-selection').style.display = 'none';
    
    // "Bölgeye Göre" radio button varsayılan olarak seçili
    document.querySelector('input[name="recipients"][value="region"]').checked = true;
    
    // Load employee dropdown for custom messaging
    loadEmployeeDropdownForCustomMessage();
});

// Set up all event listeners
function setupEventListeners() {
    // Refresh buttons
    const refreshDashboard = document.getElementById('refresh-dashboard');
    if (refreshDashboard) {
        refreshDashboard.addEventListener('click', fetchDashboardData);
    }
    
    const refreshEmployees = document.getElementById('refresh-employees');
    if (refreshEmployees) {
        refreshEmployees.addEventListener('click', fetchEmployees);
    }
    
    const refreshMessages = document.getElementById('refresh-messages');
    if (refreshMessages) {
        refreshMessages.addEventListener('click', fetchMessages);
    }
    
    // Add employee form
    const saveEmployee = document.getElementById('save-employee');
    if (saveEmployee) {
        saveEmployee.addEventListener('click', saveEmployee);
    }
    
    // Excel import
    const importExcelBtn = document.getElementById('import-excel-btn');
    const excelFileInput = document.getElementById('excel-file-input');
    
    if (importExcelBtn && excelFileInput) {
        importExcelBtn.addEventListener('click', function() {
            excelFileInput.click();
        });
        
        excelFileInput.addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                importEmployeesFromExcel(e.target.files[0]);
            }
        });
    }
    
    // Send inquiry form
    const sendInquiryForm = document.getElementById('send-inquiry-form');
    if (sendInquiryForm) {
        sendInquiryForm.addEventListener('submit', function(e) {
            e.preventDefault();
            sendInquiry();
        });
    }
    
    // Custom message form
    const sendCustomMessageForm = document.getElementById('send-custom-message-form');
    if (sendCustomMessageForm) {
        sendCustomMessageForm.addEventListener('submit', function(e) {
            e.preventDefault();
            sendCustomMessage();
        });
    }
    
    // Toggle recipient selection based on choice
    const recipientRadios = document.querySelectorAll('input[name="recipients"]');
    if (recipientRadios.length > 0) {
        recipientRadios.forEach(radio => {
            radio.addEventListener('change', function() {
                const selectionDiv = document.getElementById('employee-selection');
                const citySelectionDiv = document.getElementById('city-selection');
                const regionSelectionDiv = document.getElementById('region-selection');
                
                if (!selectionDiv || !citySelectionDiv || !regionSelectionDiv) {
                    console.error("Selection divs not found");
                    return;
                }
                
                // Hide all initially
                selectionDiv.style.display = 'none';
                citySelectionDiv.style.display = 'none';
                regionSelectionDiv.style.display = 'none';
                
                // Show appropriate selection panel
                if (this.value === 'selected') {
                    selectionDiv.style.display = 'block';
                    // Load employee checkboxes if not already loaded
                    const employeeCheckboxes = document.getElementById('employee-checkboxes');
                    if (employeeCheckboxes && employeeCheckboxes.children.length === 0) {
                        loadEmployeeCheckboxes();
                    }
                } else if (this.value === 'city') {
                    citySelectionDiv.style.display = 'block';
                    fetchCities(); // Make sure cities are loaded
                } else if (this.value === 'region') {
                    regionSelectionDiv.style.display = 'block';
                    fetchRegions(); // Make sure regions are loaded
                }
                
                // Update message preview when recipient type changes
                updateMessagePreview();
            });
        });
    }
    
    // Update message preview when disaster type changes
    const disasterType = document.getElementById('disaster-type');
    if (disasterType) {
        disasterType.addEventListener('change', updateMessagePreview);
    }
    
    // Update message preview when region selection changes
    const regionSelect = document.getElementById('region-select');
    if (regionSelect) {
        regionSelect.addEventListener('change', updateMessagePreview);
    }
    
    // Update message preview when city selection changes
    const citySelect = document.getElementById('city-select');
    if (citySelect) {
        citySelect.addEventListener('change', updateMessagePreview);
    }
    
    // Update message preview when employee checkboxes change
    const employeeCheckboxes = document.getElementById('employee-checkboxes');
    if (employeeCheckboxes) {
        employeeCheckboxes.addEventListener('change', function(e) {
            if (e.target.type === 'checkbox') {
                updateMessagePreview();
            }
        });
    }
    
    // Platform selection for mass messaging should update preview
    const platformSelect = document.getElementById('platform-select');
    if (platformSelect) {
        platformSelect.addEventListener('change', updateMessagePreview);
    }
}

// Fetch cities for filtering
function fetchCities() {
    fetch('/api/cities')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateCityDropdown(data.data);
            } else {
                console.error('Error fetching cities:', data.message);
                // Use default cities on error
                updateCityDropdown(['İstanbul', 'Ankara', 'İzmir', 'Bursa', 'Antalya', 'Adana', 'Konya']);
                showAlert('Şehir listesi alınırken bir hata oluştu: ' + data.message, 'warning');
            }
        })
        .catch(error => {
            console.error('Error fetching cities:', error);
            // Use default cities on error
            updateCityDropdown(['İstanbul', 'Ankara', 'İzmir', 'Bursa', 'Antalya', 'Adana', 'Konya']);
            showAlert('Şehir listesi alınırken bir hata oluştu', 'warning');
        });
}

// Update city dropdown
function updateCityDropdown(cities) {
    const citySelect = document.getElementById('city-select');
    if (!citySelect) {
        console.error("City select element not found");
        return;
    }
    
    citySelect.innerHTML = '<option value="">Şehir Seçiniz</option>';
    
    cities.forEach(city => {
        const option = document.createElement('option');
        option.value = city;
        option.textContent = city;
        citySelect.appendChild(option);
    });
}

// Fetch regions
function fetchRegions() {
    fetch('/api/regions')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateRegionDropdown(data.data);
            } else {
                console.error('Error fetching regions:', data.message);
                // Use default regions on error
                updateRegionDropdown(['Marmara', 'Ege', 'Akdeniz', 'Karadeniz', 'İç Anadolu', 'Doğu Anadolu', 'Güneydoğu Anadolu']);
                showAlert('Bölge listesi alınırken bir hata oluştu: ' + data.message, 'warning');
            }
        })
        .catch(error => {
            console.error('Error fetching regions:', error);
            // Use default regions on error
            updateRegionDropdown(['Marmara', 'Ege', 'Akdeniz', 'Karadeniz', 'İç Anadolu', 'Doğu Anadolu', 'Güneydoğu Anadolu']);
            showAlert('Bölge listesi alınırken bir hata oluştu', 'warning');
        });
}

// Update region dropdown
function updateRegionDropdown(regions) {
    const regionSelect = document.getElementById('region-select');
    if (!regionSelect) {
        console.error("Region select element not found");
        return;
    }
    
    regionSelect.innerHTML = '<option value="">Bölge Seçiniz</option>';
    
    regions.forEach(region => {
        const option = document.createElement('option');
        option.value = region;
        option.textContent = region;
        regionSelect.appendChild(option);
    });
}

// Fetch dashboard data
function fetchDashboardData() {
    fetch('/api/employee-status')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateDashboardStats(data.data);
                updateEmergencyTable(data.data);
            } else {
                showAlert('Dashboard verilerini alırken bir hata oluştu: ' + data.message, 'danger');
            }
        })
        .catch(error => {
            console.error('Error fetching dashboard data:', error);
            showAlert('Dashboard verilerini alırken bir hata oluştu', 'danger');
        });
}

// Update dashboard statistics
function updateDashboardStats(employees) {
    const totalCount = employees.length;
    const safeCount = employees.filter(emp => emp.current_status === 'safe').length;
    const urgentCount = employees.filter(emp => emp.current_status === 'urgent').length;
    const medicalCount = employees.filter(emp => emp.current_status === 'medical').length;
    
    document.getElementById('total-employees').textContent = totalCount;
    document.getElementById('safe-employees').textContent = safeCount;
    document.getElementById('urgent-employees').textContent = urgentCount;
    document.getElementById('medical-employees').textContent = medicalCount;
}

// Update emergency table
function updateEmergencyTable(employees) {
    const tableBody = document.getElementById('emergency-table-body');
    tableBody.innerHTML = '';
    
    // Filter to show only urgent and medical cases
    const emergencyEmployees = employees.filter(emp => 
        emp.current_status === 'urgent' || 
        emp.current_status === 'medical' || 
        emp.current_status === 'support'
    );
    
    if (emergencyEmployees.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="6" class="text-center">Acil durum kaydı bulunmamaktadır.</td>';
        tableBody.appendChild(row);
        return;
    }
    
    emergencyEmployees.forEach(employee => {
        const row = document.createElement('tr');
        
        // Format date
        const lastUpdate = employee.last_update ? new Date(employee.last_update).toLocaleString('tr-TR') : '-';
        
        // Status badge
        let statusBadge = '';
        if (employee.current_status === 'urgent') {
            statusBadge = '<span class="status-badge status-urgent">Enkaz Altında</span>';
        } else if (employee.current_status === 'medical') {
            statusBadge = '<span class="status-badge status-medical">Tıbbi Yardım</span>';
        } else if (employee.current_status === 'support') {
            statusBadge = '<span class="status-badge status-support">Destek Talebi</span>';
        }
        
        row.innerHTML = `
            <td>${employee.name}</td>
            <td>${employee.phone}</td>
            <td>${employee.city || '-'}</td>
            <td>${statusBadge}</td>
            <td>${lastUpdate}</td>
            <td>
                <button class="btn btn-sm btn-primary action-btn" onclick="sendMessage('${employee.phone}')">
                    <i class="bi bi-chat"></i>
                </button>
                <button class="btn btn-sm btn-success action-btn" onclick="markResolved('${employee.phone}')">
                    <i class="bi bi-check-lg"></i>
                </button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
}

// Fetch employees
function fetchEmployees() {
    fetch('/api/employee-status')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateEmployeesTable(data.data);
            } else {
                showAlert('Çalışan verilerini alırken bir hata oluştu: ' + data.message, 'danger');
            }
        })
        .catch(error => {
            console.error('Error fetching employees:', error);
            showAlert('Çalışan verilerini alırken bir hata oluştu', 'danger');
        });
}

// Update employees table
function updateEmployeesTable(employees) {
    const tableBody = document.getElementById('employees-table-body');
    tableBody.innerHTML = '';
    
    if (employees.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="7" class="text-center">Çalışan kaydı bulunmamaktadır.</td>';
        tableBody.appendChild(row);
        return;
    }
    
    employees.forEach(employee => {
        const row = document.createElement('tr');
        
        // Format date
        const lastUpdate = employee.last_update ? new Date(employee.last_update).toLocaleString('tr-TR') : '-';
        
        // Status badge
        let statusBadge = '<span class="status-badge status-unknown">Bilinmiyor</span>';
        if (employee.current_status === 'safe') {
            statusBadge = '<span class="status-badge status-safe">İyi</span>';
        } else if (employee.current_status === 'urgent') {
            statusBadge = '<span class="status-badge status-urgent">Enkaz Altında</span>';
        } else if (employee.current_status === 'medical') {
            statusBadge = '<span class="status-badge status-medical">Tıbbi Yardım</span>';
        } else if (employee.current_status === 'support') {
            statusBadge = '<span class="status-badge status-support">Destek Talebi</span>';
        }
        
        row.innerHTML = `
            <td>${employee.name}</td>
            <td>${employee.phone}</td>
            <td>${employee.department || '-'}</td>
            <td>${employee.city || '-'}</td>
            <td>${statusBadge}</td>
            <td>${lastUpdate}</td>
            <td>
                <button class="btn btn-sm btn-primary action-btn" onclick="sendMessage('${employee.phone}')">
                    <i class="bi bi-chat"></i>
                </button>
                <button class="btn btn-sm btn-danger action-btn" onclick="deleteEmployee('${employee.phone}')">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
}

// Fetch messages
function fetchMessages() {
    // This would be a separate API endpoint in a real system
    fetch('/api/messages')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                updateMessagesTable(data.data);
            } else {
                // For demo purposes, we'll just show a placeholder
                const demoMessages = [
                    {
                        timestamp: new Date().toISOString(),
                        to: '+905551234567',
                        recipient_name: 'Ahmet Yılmaz',
                        message: 'Merhaba Ahmet, Acil Durum Hattı\'ndan ulaşıyoruz. Yaşanan deprem nedeniyle sana ulaşmak istiyoruz...',
                        status: 'sent'
                    },
                    {
                        timestamp: new Date(Date.now() - 600000).toISOString(),
                        to: '+905559876543',
                        recipient_name: 'Ayşe Demir',
                        message: 'Merhaba Ayşe, Acil Durum Hattı\'ndan ulaşıyoruz. Yaşanan deprem nedeniyle sana ulaşmak istiyoruz...',
                        status: 'sent'
                    }
                ];
                updateMessagesTable(demoMessages);
            }
        })
        .catch(error => {
            console.error('Error fetching messages:', error);
            
            // For demo purposes, show placeholder data
            const demoMessages = [
                {
                    timestamp: new Date().toISOString(),
                    to: '+905551234567',
                    recipient_name: 'Ahmet Yılmaz',
                    message: 'Merhaba Ahmet, Acil Durum Hattı\'ndan ulaşıyoruz. Yaşanan deprem nedeniyle sana ulaşmak istiyoruz...',
                    status: 'sent'
                },
                {
                    timestamp: new Date(Date.now() - 600000).toISOString(),
                    to: '+905559876543',
                    recipient_name: 'Ayşe Demir',
                    message: 'Merhaba Ayşe, Acil Durum Hattı\'ndan ulaşıyoruz. Yaşanan deprem nedeniyle sana ulaşmak istiyoruz...',
                    status: 'sent'
                }
            ];
            updateMessagesTable(demoMessages);
        });
}

// Update messages table
function updateMessagesTable(messages) {
    const tableBody = document.getElementById('messages-table-body');
    tableBody.innerHTML = '';
    
    if (messages.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = '<td colspan="4" class="text-center">Mesaj kaydı bulunmamaktadır.</td>';
        tableBody.appendChild(row);
        return;
    }
    
    messages.forEach(message => {
        const row = document.createElement('tr');
        
        // Format date
        const timestamp = new Date(message.timestamp).toLocaleString('tr-TR');
        
        // Format status
        let statusBadge = '';
        if (message.status === 'sent') {
            statusBadge = '<span class="badge bg-success">Gönderildi</span>';
        } else if (message.status === 'failed') {
            statusBadge = '<span class="badge bg-danger">Başarısız</span>';
        } else {
            statusBadge = '<span class="badge bg-secondary">Bekliyor</span>';
        }
        
        // Truncate message if too long
        const truncatedMessage = message.message.length > 100 
            ? message.message.substring(0, 100) + '...' 
            : message.message;
        
        row.innerHTML = `
            <td>${timestamp}</td>
            <td>${message.recipient_name || message.to}</td>
            <td>${truncatedMessage}</td>
            <td>${statusBadge}</td>
        `;
        
        tableBody.appendChild(row);
    });
}

// Save new employee
function saveEmployee() {
    const name = document.getElementById('employee-name').value.trim();
    const phone = document.getElementById('employee-phone').value.trim();
    const department = document.getElementById('employee-department').value.trim();
    const city = document.getElementById('employee-city').value.trim();
    const region = document.getElementById('employee-region')?.value.trim() || '';
    
    if (!name || !phone || !city) {
        showAlert('Lütfen isim, telefon ve şehir alanlarını doldurun', 'warning');
        return;
    }
    
    // Validate phone number format
    if (!phone.startsWith('+')) {
        showAlert('Telefon numarası + işareti ile başlamalıdır (örnek: +905551234567)', 'warning');
        return;
    }
    
    const employeeData = {
        name: name,
        phone: phone,
        department: department,
        city: city,
        region: region
    };
    
    fetch('/api/employees', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(employeeData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('addEmployeeModal'));
            modal.hide();
            
            // Clear form fields
            document.getElementById('employee-name').value = '';
            document.getElementById('employee-phone').value = '';
            document.getElementById('employee-department').value = '';
            document.getElementById('employee-city').value = '';
            if (document.getElementById('employee-region')) {
                document.getElementById('employee-region').value = '';
            }
            
            // Update employees table
            fetchEmployees();
            
            showAlert('Çalışan başarıyla eklendi', 'success');
        } else {
            showAlert('Çalışan eklerken bir hata oluştu: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error saving employee:', error);
        showAlert('Çalışan eklerken bir hata oluştu', 'danger');
        
        // For demo, we'll simulate a successful add
        const modal = bootstrap.Modal.getInstance(document.getElementById('addEmployeeModal'));
        modal.hide();
        showAlert('Çalışan başarıyla eklendi (Demo)', 'success');
    });
}

// Delete an employee
function deleteEmployee(phone) {
    if (!confirm('Bu çalışanı silmek istediğinizden emin misiniz?')) {
        return;
    }
    
    fetch(`/api/employees/${encodeURIComponent(phone)}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            fetchEmployees();
            showAlert('Çalışan başarıyla silindi', 'success');
        } else {
            showAlert('Çalışan silinirken bir hata oluştu: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error deleting employee:', error);
        showAlert('Çalışan silinirken bir hata oluştu', 'danger');
        
        // For demo, we'll simulate a successful delete
        fetchEmployees();
        showAlert('Çalışan başarıyla silindi (Demo)', 'success');
    });
}

// Send direct message to an employee
function sendMessage(phone) {
    // Get the employee name
    fetch('/api/employee-status')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const employee = data.data.find(emp => emp.phone === phone);
                if (employee) {
                    // Pre-select this employee in the custom message form
                    document.getElementById('employee-select').value = phone;
                    
                    // Switch to the send message tab
                    document.querySelector('a[href="#send-message"]').click();
                    
                    // Scroll to the custom message form
                    document.getElementById('send-custom-message-form').scrollIntoView({
                        behavior: 'smooth'
                    });
                    
                    // Focus on the message content field
                    document.getElementById('message-content').focus();
                }
            }
        })
        .catch(error => console.error('Error:', error));
}

// Mark emergency as resolved
function markResolved(phone) {
    if (!confirm('Bu acil durumu çözüldü olarak işaretlemek istediğinizden emin misiniz?')) {
        return;
    }
    
    fetch(`/api/status/${encodeURIComponent(phone)}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            status: 'safe'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            fetchDashboardData();
            showAlert('Durum başarıyla güncellendi', 'success');
        } else {
            showAlert('Durum güncellenirken bir hata oluştu: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error updating status:', error);
        showAlert('Durum güncellenirken bir hata oluştu', 'danger');
        
        // For demo, we'll simulate a successful update
        fetchDashboardData();
        showAlert('Durum başarıyla güncellendi (Demo)', 'success');
    });
}

// Load employee checkboxes for message sending
function loadEmployeeCheckboxes() {
    fetch('/api/employee-status')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const checkboxesContainer = document.getElementById('employee-checkboxes');
                checkboxesContainer.innerHTML = '';
                
                data.data.forEach(employee => {
                    const div = document.createElement('div');
                    div.className = 'col-md-6 mb-2';
                    
                    div.innerHTML = `
                        <div class="form-check">
                            <input class="form-check-input employee-checkbox" type="checkbox" value="${employee.phone}" id="emp-${employee.phone.replace('+', '')}">
                            <label class="form-check-label" for="emp-${employee.phone.replace('+', '')}">
                                ${employee.name} (${employee.city || 'Şehir yok'}) - ${employee.phone}
                            </label>
                        </div>
                    `;
                    
                    checkboxesContainer.appendChild(div);
                });
            } else {
                showAlert('Çalışan listesi alınırken bir hata oluştu', 'danger');
            }
        })
        .catch(error => {
            console.error('Error loading employee checkboxes:', error);
            showAlert('Çalışan listesi alınırken bir hata oluştu', 'danger');
            
            // For demo, add some placeholder checkboxes
            const checkboxesContainer = document.getElementById('employee-checkboxes');
            checkboxesContainer.innerHTML = `
                <div class="col-md-6 mb-2">
                    <div class="form-check">
                        <input class="form-check-input employee-checkbox" type="checkbox" value="+905551234567" id="emp-905551234567">
                        <label class="form-check-label" for="emp-905551234567">
                            Ahmet Yılmaz (İstanbul) - +905551234567
                        </label>
                    </div>
                </div>
                <div class="col-md-6 mb-2">
                    <div class="form-check">
                        <input class="form-check-input employee-checkbox" type="checkbox" value="+905559876543" id="emp-905559876543">
                        <label class="form-check-label" for="emp-905559876543">
                            Ayşe Demir (Ankara) - +905559876543
                        </label>
                    </div>
                </div>
            `;
        });
}

// Import employees from Excel file
function importEmployeesFromExcel(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    // Show loading indicator
    showAlert('Excel dosyası yükleniyor...', 'info');
    
    fetch('/api/import-employees', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showAlert(`${data.message}`, 'success');
            // Refresh employee list
            fetchEmployees();
        } else {
            showAlert('Excel dosyası yüklenirken hata: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error importing Excel file:', error);
        showAlert('Excel dosyası yüklenirken bir hata oluştu', 'danger');
    });
}

// Send inquiry to employees
function sendInquiry() {
    const disasterType = document.getElementById('disaster-type').value;
    const platform = document.getElementById('platform-select').value;
    
    if (!disasterType) {
        showAlert('Lütfen afet türünü seçin', 'warning');
        return;
    }
    
    const recipientType = document.querySelector('input[name="recipients"]:checked').value;
    let requestData = {
        disaster_type: disasterType,
        platform: platform
    };
    
    // Gönderim türüne göre alıcıları belirleme
    if (recipientType === 'all') {
        // Tüm çalışanlara gönderme
        // Ekstra alıcı parametresi gerekmiyor
    } 
    else if (recipientType === 'region') {
        // Bölgeye göre gönderme
        const region = document.getElementById('region-select').value;
        if (!region) {
            showAlert('Lütfen bir bölge seçin', 'warning');
            return;
        }
        requestData.region = region;
    }
    else if (recipientType === 'city') {
        // Şehre göre gönderme
        const city = document.getElementById('city-select').value;
        if (!city) {
            showAlert('Lütfen bir şehir seçin', 'warning');
            return;
        }
        requestData.city = city;
    }
    else if (recipientType === 'selected') {
        // Seçilen çalışanlara gönderme
        const checkboxes = document.querySelectorAll('#employee-checkboxes input[type="checkbox"]:checked');
        if (checkboxes.length === 0) {
            showAlert('Lütfen en az bir çalışan seçin', 'warning');
            return;
        }
        
        const phones = Array.from(checkboxes).map(cb => cb.value);
        requestData.phones = phones;
    }
    
    // Gönderme butonu
    const submitButton = document.querySelector('#send-inquiry-form button[type="submit"]');
    const originalText = submitButton.innerHTML;
    submitButton.disabled = true;
    submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Gönderiliyor...';
    
    // API isteği
    fetch('/api/send-inquiry', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            let successMessage = `${data.sent} çalışana mesaj gönderildi.`;
            
            // Gönderim detayları ekleme
            if (data.city) {
                successMessage = `${data.city} şehrindeki ${data.sent} çalışana durum sorgulama mesajı gönderildi.`;
            } else if (data.region) {
                successMessage = `${data.region} bölgesindeki ${data.sent} çalışana durum sorgulama mesajı gönderildi.`;
            }
            
            successMessage += ` (Platform: ${platform === 'all' ? 'Tüm Platformlar' : platform})`;
            
            showAlert(successMessage, 'success');
            
            // Form resetleme
            document.getElementById('send-inquiry-form').reset();
            document.getElementById('employee-selection').style.display = 'none';
            document.getElementById('city-selection').style.display = 'none';
            document.getElementById('region-selection').style.display = 'block';
            document.querySelector('input[value="region"]').checked = true;
            updateMessagePreview();
            
            // Mesaj kaydı güncellemesi
            fetchMessages();
        } else {
            showAlert('Mesaj gönderilirken bir hata oluştu: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error sending inquiry:', error);
        showAlert('Mesaj gönderilirken bir hata oluştu', 'danger');
    })
    .finally(() => {
        // Her durumda buton durumunu normale çevir
        submitButton.disabled = false;
        submitButton.innerHTML = originalText;
    });
}

// Update the message preview
function updateMessagePreview() {
    const previewElement = document.getElementById('message-preview');
    if (!previewElement) {
        console.error("Message preview element not found");
        return;
    }
    
    const disasterTypeElement = document.getElementById('disaster-type');
    const disasterType = disasterTypeElement ? disasterTypeElement.value || 'afet' : 'afet';
    const disasterTypeName = disasterTypeElement && disasterTypeElement.options[disasterTypeElement.selectedIndex] ? 
        disasterTypeElement.options[disasterTypeElement.selectedIndex].text || 'Afet' : 'Afet';
    
    const platformSelectElement = document.getElementById('platform-select');
    const platform = platformSelectElement ? platformSelectElement.value || 'whatsapp' : 'whatsapp';
    
    // Alıcı türünü belirle
    const recipientRadio = document.querySelector('input[name="recipients"]:checked');
    const recipientType = recipientRadio ? recipientRadio.value || 'region' : 'region';
    
    let recipientInfo = "";
    if (recipientType === 'all') {
        recipientInfo = "Tüm çalışanlara gönderilecek";
    } else if (recipientType === 'region') {
        const regionSelectElement = document.getElementById('region-select');
        const selectedRegion = regionSelectElement ? regionSelectElement.value : '';
        recipientInfo = selectedRegion ? 
            `${selectedRegion} bölgesindeki çalışanlara gönderilecek` : 
            "Seçilen bölgedeki çalışanlara gönderilecek";
    } else if (recipientType === 'city') {
        const citySelectElement = document.getElementById('city-select');
        const selectedCity = citySelectElement ? citySelectElement.value : '';
        recipientInfo = selectedCity ? 
            `${selectedCity} şehrindeki çalışanlara gönderilecek` : 
            "Seçilen şehirdeki çalışanlara gönderilecek";
    } else if (recipientType === 'selected') {
        const checkboxes = document.querySelectorAll('#employee-checkboxes input[type="checkbox"]:checked');
        const selectedCount = checkboxes ? checkboxes.length : 0;
        recipientInfo = selectedCount > 0 ? 
            `${selectedCount} seçili çalışana gönderilecek` : 
            "Seçilen çalışanlara gönderilecek";
    }
    
    // Platform bilgisi
    const platformText = platform === 'whatsapp' ? 'WhatsApp üzerinden' :
                   platform === 'telegram' ? 'Telegram üzerinden' :
                   platform === 'sms' ? 'SMS yoluyla' : 'Tüm platformlar üzerinden';
    
    const previewMessage = `Merhaba [Çalışan Adı],
Acil Durum Hattı'ndan ulaşıyoruz. Yaşanan ${disasterTypeName.toLowerCase()} nedeniyle sana ulaşmak istiyoruz. Lütfen aşağıdaki butonlardan durumunu bildir:

[Butonlar burada görünecek]

------
${recipientInfo}
${platformText} gönderilecek`;

    previewElement.textContent = previewMessage;
}

// Show alert message
function showAlert(message, type = 'info') {
    // Create alert element
    const alertEl = document.createElement('div');
    alertEl.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    alertEl.style.zIndex = 9999;
    alertEl.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to document
    document.body.appendChild(alertEl);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alertEl);
        bsAlert.close();
    }, 5000);
}

// Load employee dropdown for custom message form
function loadEmployeeDropdownForCustomMessage() {
    fetch('/api/employee-status')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                const dropdown = document.getElementById('employee-select');
                dropdown.innerHTML = '<option value="">Çalışan seçin...</option>';
                
                // Sort employees by name
                const employees = data.data.sort((a, b) => 
                    a.name.localeCompare(b.name, 'tr')
                );
                
                employees.forEach(employee => {
                    const option = document.createElement('option');
                    option.value = employee.phone;
                    option.textContent = `${employee.name} (${employee.phone})`;
                    dropdown.appendChild(option);
                });
            } else {
                showAlert('Çalışan listesi alınamadı: ' + data.message, 'danger');
            }
        })
        .catch(error => {
            console.error('Error loading employee dropdown:', error);
            showAlert('Çalışan listesi alınırken bir hata oluştu', 'danger');
        });
}

// Send custom message to an employee
function sendCustomMessage() {
    const employeePhone = document.getElementById('employee-select').value;
    const platform = document.getElementById('message-platform').value;
    const messageContent = document.getElementById('message-content').value;
    
    if (!employeePhone || !messageContent) {
        showAlert('Lütfen bir çalışan seçin ve mesaj içeriği girin.', 'warning');
        return;
    }
    
    // Show loading state
    const submitButton = document.querySelector('#send-custom-message-form button[type="submit"]');
    const originalText = submitButton.innerHTML;
    submitButton.innerHTML = '<i class="spinner-border spinner-border-sm"></i> Gönderiliyor...';
    submitButton.disabled = true;
    
    // API request data
    const requestData = {
        phone: employeePhone,
        message: messageContent,
        platform: platform
    };
    
    // Send API request
    fetch('/api/send-message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(response => response.json())
    .then(data => {
        // Reset form
        submitButton.innerHTML = originalText;
        submitButton.disabled = false;
        
        if (data.status === 'success') {
            // Show success message
            showAlert(`Mesaj başarıyla gönderildi. Durum: ${data.details.status}`, 'success');
            document.getElementById('message-content').value = ''; // Clear message input
            
            // Refresh message history
            fetchMessages();
        } else {
            // Show error
            showAlert(`Hata: ${data.message}`, 'danger');
        }
    })
    .catch(error => {
        console.error('Error sending custom message:', error);
        submitButton.innerHTML = originalText;
        submitButton.disabled = false;
        showAlert('Mesaj gönderilirken bir hata oluştu. Lütfen tekrar deneyin.', 'danger');
    });
} 
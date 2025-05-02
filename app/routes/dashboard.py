from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from app.routes.auth import login_required, admin_required
from app.models.employee import Employee
from app.models.disaster import Disaster
from app.models.message import Message
from app.utils.message_sender import MessageSender
from app.utils.excel_importer import ExcelImporter
import os
import json
from werkzeug.utils import secure_filename
from datetime import datetime
import folium

dashboard = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard.route('/')
@login_required
def index():
    """Main dashboard page"""
    # Get counts for dashboard
    employee_count = len(Employee.get_all())
    active_disasters = Disaster.get_all(active_only=True)
    active_disasters_count = len(active_disasters)
    
    # Status counts
    employees = Employee.get_all()
    status_counts = {
        'safe': 0,
        'trapped': 0,
        'medical_help': 0,
        'support_needed': 0,
        'unknown': 0
    }
    
    for employee in employees:
        status = employee.get('status', 'unknown')
        if status in status_counts:
            status_counts[status] += 1
    
    # City distribution
    city_counts = {}
    for employee in employees:
        city = employee.get('city')
        if city:
            if city in city_counts:
                city_counts[city] += 1
            else:
                city_counts[city] = 1
    
    return render_template(
        'dashboard/index.html',
        employee_count=employee_count,
        active_disasters_count=active_disasters_count,
        status_counts=status_counts,
        city_counts=city_counts
    )

@dashboard.route('/employees')
@login_required
def employees():
    """Employee list page"""
    # Get search filters from request
    search_query = request.args.get('query', '')
    city_filter = request.args.get('city', '')
    status_filter = request.args.get('status', '')
    
    # Get employee data
    if search_query or city_filter or status_filter:
        employees = Employee.search(
            query=search_query if search_query else None,
            city=city_filter if city_filter else None,
            status=status_filter if status_filter else None
        )
    else:
        employees = Employee.get_all()
    
    # Get unique cities for filter dropdown
    all_employees = Employee.get_all()
    cities = set()
    for employee in all_employees:
        if 'city' in employee and employee['city']:
            cities.add(employee['city'])
    
    return render_template(
        'dashboard/employees.html',
        employees=employees,
        cities=sorted(cities),
        search_query=search_query,
        city_filter=city_filter,
        status_filter=status_filter
    )

@dashboard.route('/employees/add', methods=['GET', 'POST'])
@admin_required
def employee_add():
    """Add a new employee"""
    if request.method == 'POST':
        # Form verilerini al
        employee_data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'telegram_id': request.form.get('telegram_id'),
            'city': request.form.get('city'),
            'department': request.form.get('department'),
            'position': request.form.get('position'),
            'emergency_contact': request.form.get('emergency_contact'),
            'address': request.form.get('address'),
            'status': request.form.get('status', 'unknown')
        }
        
        # Boş değerleri temizle
        employee_data = {k: v for k, v in employee_data.items() if v}
        
        try:
            # E-posta kontrolü yap
            existing_employees = Employee.search(query=employee_data['email'])
            if existing_employees:
                flash('Bu e-posta adresiyle kayıtlı bir çalışan zaten var', 'danger')
                return redirect(request.url)
            
            # Çalışanı oluştur
            employee_id = Employee.create(employee_data)
            flash(f'Çalışan "{employee_data["name"]}" başarıyla eklendi', 'success')
            return redirect(url_for('dashboard.employee_detail', employee_id=employee_id))
            
        except Exception as e:
            flash(f'Çalışan eklenirken bir hata oluştu: {str(e)}', 'danger')
            return redirect(request.url)
    
    return render_template('dashboard/employee_add.html')

@dashboard.route('/employees/<employee_id>/edit', methods=['GET', 'POST'])
@admin_required
def employee_edit(employee_id):
    """Edit an employee"""
    # Çalışan bilgilerini getir
    employee = Employee.get(employee_id)
    
    if not employee:
        flash('Çalışan bulunamadı', 'danger')
        return redirect(url_for('dashboard.employees'))
    
    if request.method == 'POST':
        # Form verilerini al
        employee_data = {
            'name': request.form.get('name'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'telegram_id': request.form.get('telegram_id'),
            'city': request.form.get('city'),
            'department': request.form.get('department'),
            'position': request.form.get('position'),
            'emergency_contact': request.form.get('emergency_contact'),
            'address': request.form.get('address'),
            'status': request.form.get('status')
        }
        
        # Boş değerleri temizle
        employee_data = {k: v for k, v in employee_data.items() if v}
        
        try:
            # E-posta kontrolü yap (kendi e-postası hariç)
            if employee_data.get('email') != employee.get('email'):
                existing_employees = Employee.search(query=employee_data['email'])
                if existing_employees:
                    flash('Bu e-posta adresiyle kayıtlı başka bir çalışan zaten var', 'danger')
                    return redirect(request.url)
            
            # Çalışanı güncelle
            Employee.update(employee_id, employee_data)
            flash(f'Çalışan "{employee_data["name"]}" başarıyla güncellendi', 'success')
            return redirect(url_for('dashboard.employee_detail', employee_id=employee_id))
            
        except Exception as e:
            flash(f'Çalışan güncellenirken bir hata oluştu: {str(e)}', 'danger')
            return redirect(request.url)
    
    return render_template('dashboard/employee_edit.html', employee=employee)

@dashboard.route('/employees/delete', methods=['POST'])
@admin_required
def delete_employees():
    """Delete one or more employees"""
    employee_ids = request.form.getlist('employee_ids')
    
    if not employee_ids:
        flash('Silinecek çalışan seçilmedi', 'warning')
        return redirect(url_for('dashboard.employees'))
    
    try:
        # Toplu silme işlemini gerçekleştir
        result = Employee.delete_many(employee_ids)
        
        # Silinen çalışan sayısını doğrula
        deleted_count = result.deleted_count if result else 0
        
        if deleted_count == 1:
            flash('1 çalışan başarıyla silindi', 'success')
        else:
            flash(f'{deleted_count} çalışan başarıyla silindi', 'success')
            
    except Exception as e:
        flash(f'Çalışanlar silinirken bir hata oluştu: {str(e)}', 'danger')
    
    return redirect(url_for('dashboard.employees'))

@dashboard.route('/employees/import', methods=['GET', 'POST'])
@admin_required
def import_employees():
    """Import employees from Excel"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
            
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
            
        if file and file.filename.endswith(('.xlsx', '.xls')):
            # Create uploads directory if it doesn't exist
            uploads_dir = os.path.join(current_app.root_path, 'static', 'uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            
            # Save file
            filename = secure_filename(file.filename)
            file_path = os.path.join(uploads_dir, filename)
            file.save(file_path)
            
            # Process Excel
            result = ExcelImporter.import_employees(file_path)
            
            if result['success']:
                flash(f'Successfully imported {result["success_count"]} employees. {result["error_count"]} errors.', 'success')
            else:
                flash(f'Import failed: {result["message"]}', 'danger')
                
            # Delete temporary file
            os.remove(file_path)
            
            return redirect(url_for('dashboard.employees'))
        else:
            flash('Invalid file format. Please upload an Excel file (.xlsx or .xls)', 'danger')
            
    return render_template('dashboard/import_employees.html')

@dashboard.route('/employees/<employee_id>')
@login_required
def employee_detail(employee_id):
    """Employee detail page"""
    employee = Employee.get(employee_id)
    
    if not employee:
        flash('Employee not found', 'danger')
        return redirect(url_for('dashboard.employees'))
    
    # Get message history
    messages = Message.get_by_employee(employee_id)
    
    return render_template(
        'dashboard/employee_detail.html',
        employee=employee,
        messages=messages
    )

@dashboard.route('/disasters')
@login_required
def disasters():
    """Disasters list page"""
    active_only = request.args.get('active_only', 'false') == 'true'
    disasters = Disaster.get_all(active_only=active_only)
    
    return render_template(
        'dashboard/disasters.html',
        disasters=disasters,
        active_only=active_only
    )

@dashboard.route('/disasters/new', methods=['GET', 'POST'])
@admin_required
def new_disaster():
    """Create new disaster"""
    if request.method == 'POST':
        name = request.form.get('name')
        disaster_type = request.form.get('type')
        description = request.form.get('description')
        affected_cities = request.form.getlist('affected_cities')
        affected_regions = request.form.getlist('affected_regions')
        
        if not name or not disaster_type:
            flash('Name and type are required', 'danger')
            return redirect(request.url)
        
        disaster_data = {
            'name': name,
            'type': disaster_type,
            'description': description,
            'affected_cities': affected_cities,
            'affected_regions': affected_regions,
            'occurred_at': datetime.utcnow()
        }
        
        disaster_id = Disaster.create(disaster_data)
        
        flash(f'Disaster "{name}" has been created', 'success')
        return redirect(url_for('dashboard.disaster_detail', disaster_id=disaster_id))
    
    # Get unique cities for dropdown
    all_employees = Employee.get_all()
    cities = set()
    for employee in all_employees:
        if 'city' in employee and employee['city']:
            cities.add(employee['city'])
    
    return render_template(
        'dashboard/new_disaster.html',
        cities=sorted(cities),
        disaster_types=[
            Disaster.TYPE_EARTHQUAKE,
            Disaster.TYPE_FLOOD,
            Disaster.TYPE_FIRE,
            Disaster.TYPE_HURRICANE,
            Disaster.TYPE_OTHER
        ]
    )

@dashboard.route('/disasters/<disaster_id>')
@login_required
def disaster_detail(disaster_id):
    """Disaster detail page"""
    disaster = Disaster.get(disaster_id)
    
    if not disaster:
        flash('Disaster not found', 'danger')
        return redirect(url_for('dashboard.disasters'))
    
    # Get message statistics
    message_stats = Message.get_stats_by_disaster(disaster_id)
    
    # Get affected employees
    affected_employees = []
    for city in disaster.get('affected_cities', []):
        city_employees = Employee.get_by_city(city)
        affected_employees.extend(city_employees)
    
    # Count by status
    status_counts = {
        'safe': 0,
        'trapped': 0,
        'medical_help': 0,
        'support_needed': 0,
        'unknown': 0
    }
    
    for employee in affected_employees:
        status = employee.get('status', 'unknown')
        if status in status_counts:
            status_counts[status] += 1
    
    return render_template(
        'dashboard/disaster_detail.html',
        disaster=disaster,
        message_stats=message_stats,
        affected_employees=affected_employees,
        status_counts=status_counts
    )

@dashboard.route('/messages/send', methods=['GET', 'POST'])
@admin_required
def send_messages():
    """Send messages to employees"""
    if request.method == 'POST':
        message_text = request.form.get('message')
        disaster_id = request.form.get('disaster_id')
        city_filter = request.form.get('city')
        region_filter = request.form.get('region')
        channel = request.form.get('channel')
        
        if not message_text or not channel:
            flash('Message and channel are required', 'danger')
            return redirect(request.url)
        
        # Get employees to message based on filters
        if region_filter:
            # Bölgeye göre mesaj gönder
            result = MessageSender.send_messages_by_region(
                region_filter,
                message_text,
                channel,
                disaster_id if disaster_id else None
            )
        elif city_filter:
            # Şehre göre mesaj gönder
            result = MessageSender.send_messages_by_cities(
                city_filter,
                message_text,
                channel,
                disaster_id if disaster_id else None
            )
        else:
            # Tüm çalışanlara mesaj gönder
            employees = Employee.get_all()
            result = MessageSender.send_bulk_messages(
                employees,
                message_text,
                channel,
                disaster_id if disaster_id else None
            )
        
        flash(f'Sent {result["success"]} messages, {result["failed"]} failed', 'info')
        return redirect(url_for('dashboard.index'))
    
    # Get disasters for dropdown
    active_disasters = Disaster.get_all(active_only=True)
    
    # Get cities for dropdown
    all_employees = Employee.get_all()
    cities = set()
    for employee in all_employees:
        if 'city' in employee and employee['city']:
            cities.add(employee['city'])
    
    # Bölgeleri al
    regions = Employee.get_all_regions()
    
    return render_template(
        'dashboard/send_messages.html',
        disasters=active_disasters,
        cities=sorted(cities),
        regions=regions,
        channels=[
            Message.CHANNEL_SMS,
            Message.CHANNEL_WHATSAPP,
            Message.CHANNEL_TELEGRAM
        ]
    )

@dashboard.route('/map')
@login_required
def map_view():
    """Map view of employees"""
    employees = Employee.get_all()
    
    # Create a map centered on Turkey
    m = folium.Map(location=[39.9334, 32.8597], zoom_start=6)
    
    # Add markers for each employee with location
    for employee in employees:
        if 'latitude' in employee and 'longitude' in employee:
            # Set color based on status
            status = employee.get('status', 'unknown')
            color = 'gray'  # default for unknown
            
            if status == Employee.STATUS_SAFE:
                color = 'green'
            elif status == Employee.STATUS_TRAPPED:
                color = 'red'
            elif status == Employee.STATUS_MEDICAL_HELP:
                color = 'orange'
            elif status == Employee.STATUS_SUPPORT_NEEDED:
                color = 'blue'
            
            # Add marker
            folium.Marker(
                location=[employee['latitude'], employee['longitude']],
                popup=f"{employee['name']} - {status}",
                icon=folium.Icon(color=color)
            ).add_to(m)
    
    # Save map to HTML
    map_file = os.path.join(current_app.root_path, 'templates', 'dashboard', 'map_data.html')
    m.save(map_file)
    
    return render_template('dashboard/map.html')

@dashboard.route('/settings/api', methods=['GET', 'POST'])
@admin_required
def api_settings():
    """API ayarları sayfası"""
    from app.models.settings import Settings
    from app.config.config import Config
    
    if request.method == 'POST':
        # Form verilerini al
        settings_data = {
            # WhatsApp
            'whatsapp_api_key': request.form.get('whatsapp_api_key', ''),
            'whatsapp_phone_number': request.form.get('whatsapp_phone_number', ''),
            
            # Telegram
            'telegram_bot_token': request.form.get('telegram_bot_token', ''),
            
            # Twilio
            'twilio_account_sid': request.form.get('twilio_account_sid', ''),
            'twilio_auth_token': request.form.get('twilio_auth_token', ''),
            'twilio_phone_number': request.form.get('twilio_phone_number', '')
        }
        
        # Ayarları güncelle
        try:
            Settings.update_api_settings(settings_data)
            
            # Config'i güncelle
            with current_app.app_context():
                Config.load_db_settings()
            
            flash('API ayarları başarıyla güncellendi', 'success')
        except Exception as e:
            flash(f'API ayarlarını güncellerken hata oluştu: {str(e)}', 'danger')
            
        return redirect(url_for('dashboard.api_settings'))
    
    # Mevcut ayarları al
    current_settings = Settings.get_all() or {}
    
    return render_template(
        'dashboard/api_settings.html',
        whatsapp_settings=Settings.get_whatsapp_settings(),
        telegram_settings=Settings.get_telegram_settings(),
        twilio_settings=Settings.get_twilio_settings(),
        current_settings=current_settings
    ) 
from flask import Blueprint, jsonify, request, current_app
from app.models.employee import Employee
from app.models.disaster import Disaster
from app.models.message import Message
from datetime import datetime
import hmac
import hashlib

api = Blueprint('api', __name__, url_prefix='/api')

def verify_api_key():
    """Verify API key from request"""
    api_key = request.headers.get('X-API-Key')
    
    if not api_key:
        return False
        
    # In a real app, this would be stored securely and compared
    return api_key == 'your-secret-api-key'

@api.before_request
def before_request():
    """Check API key before all requests except for status update"""
    if request.endpoint != 'api.update_employee_status' and not verify_api_key():
        return jsonify({'error': 'Unauthorized'}), 401

@api.route('/employees', methods=['GET'])
def get_employees():
    """Get all employees or filtered list"""
    # Get filter parameters
    city = request.args.get('city')
    status = request.args.get('status')
    query = request.args.get('query')
    
    employees = Employee.search(
        query=query,
        city=city,
        status=status
    )
    
    # Convert ObjectId to string for JSON serialization
    for employee in employees:
        employee['_id'] = str(employee['_id'])
        
    return jsonify(employees)

@api.route('/employees/<employee_id>', methods=['GET'])
def get_employee(employee_id):
    """Get employee details"""
    employee = Employee.get(employee_id)
    
    if not employee:
        return jsonify({'error': 'Employee not found'}), 404
        
    # Convert ObjectId to string for JSON serialization
    employee['_id'] = str(employee['_id'])
    
    return jsonify(employee)

@api.route('/disasters/active', methods=['GET'])
def get_active_disasters():
    """Get active disasters"""
    disasters = Disaster.get_all(active_only=True)
    
    # Convert ObjectId to string for JSON serialization
    for disaster in disasters:
        disaster['_id'] = str(disaster['_id'])
        
    return jsonify(disasters)

@api.route('/employees/<employee_id>/status', methods=['POST'])
def update_employee_status(employee_id):
    """Update employee status - public API for messaging responses"""
    # For security, this endpoint uses a different authentication method
    # It uses a signature to validate the request
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400
        
    new_status = data.get('status')
    signature = data.get('signature')
    timestamp = data.get('timestamp')
    
    if not new_status or not signature or not timestamp:
        return jsonify({'error': 'Missing required parameters'}), 400
        
    # Verify request signature
    secret_key = current_app.config.get('SECRET_KEY')
    expected_signature = hmac.new(
        secret_key.encode(),
        f"{employee_id}:{new_status}:{timestamp}".encode(),
        hashlib.sha256
    ).hexdigest()
    
    if signature != expected_signature:
        return jsonify({'error': 'Invalid signature'}), 401
        
    # Update status
    valid_statuses = [
        Employee.STATUS_UNKNOWN,
        Employee.STATUS_SAFE,
        Employee.STATUS_TRAPPED,
        Employee.STATUS_MEDICAL_HELP,
        Employee.STATUS_SUPPORT_NEEDED
    ]
    
    if new_status not in valid_statuses:
        return jsonify({'error': 'Invalid status value'}), 400
        
    success = Employee.update_status(employee_id, new_status)
    
    if not success:
        return jsonify({'error': 'Employee not found'}), 404
        
    return jsonify({'status': 'success'})

@api.route('/analytics/status', methods=['GET'])
def get_status_analytics():
    """Get status analytics"""
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
            
    total = len(employees)
    
    return jsonify({
        'counts': status_counts,
        'total': total
    })

@api.route('/analytics/city', methods=['GET'])
def get_city_analytics():
    """Get city distribution analytics"""
    employees = Employee.get_all()
    
    city_counts = {}
    for employee in employees:
        city = employee.get('city')
        if city:
            if city in city_counts:
                city_counts[city] += 1
            else:
                city_counts[city] = 1
                
    return jsonify(city_counts)

@api.route('/analytics/disaster/<disaster_id>', methods=['GET'])
def get_disaster_analytics(disaster_id):
    """Get analytics for a specific disaster"""
    disaster = Disaster.get(disaster_id)
    
    if not disaster:
        return jsonify({'error': 'Disaster not found'}), 404
    
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
            
    return jsonify({
        'disaster_id': str(disaster['_id']),
        'disaster_name': disaster['name'],
        'affected_cities': disaster.get('affected_cities', []),
        'affected_employees_count': len(affected_employees),
        'status_counts': status_counts,
        'message_stats': message_stats
    }) 
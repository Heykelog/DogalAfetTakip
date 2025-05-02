from flask import Flask, request, jsonify, Blueprint
from datetime import datetime
from bson.objectid import ObjectId
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Create Blueprint for API routes
api = Blueprint('api', __name__)

# Reference to database collections (will be set in app.py)
employees_collection = None
messages_collection = None
status_collection = None

def init_api(empl_collection, msg_collection, status_coll):
    """Initialize API with database collections"""
    global employees_collection, messages_collection, status_collection
    employees_collection = empl_collection
    messages_collection = msg_collection
    status_collection = status_coll

# Employee endpoints
@api.route('/api/employees', methods=['GET'])
def get_employees():
    """Get all employees"""
    try:
        employees = list(employees_collection.find({}, {'_id': 0}))
        return jsonify({
            "status": "success",
            "data": employees
        })
    except Exception as e:
        logger.error(f"Error fetching employees: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@api.route('/api/employees', methods=['POST'])
def add_employee():
    """Add a new employee"""
    try:
        data = request.json
        
        # Validate required fields
        if not all(k in data for k in ['name', 'phone']):
            return jsonify({
                "status": "error",
                "message": "Missing required fields: name and phone are required"
            }), 400
        
        # Check if phone number already exists
        existing = employees_collection.find_one({"phone": data['phone']})
        if existing:
            return jsonify({
                "status": "error",
                "message": f"Employee with phone {data['phone']} already exists"
            }), 400
        
        # Add new employee
        new_employee = {
            "name": data['name'],
            "phone": data['phone'],
            "department": data.get('department', ''),
            "location": data.get('location', ''),
            "city": data.get('city', ''),
            "current_status": "unknown",
            "last_update": None,
            "created_at": datetime.now()
        }
        
        result = employees_collection.insert_one(new_employee)
        
        return jsonify({
            "status": "success",
            "message": "Employee added successfully",
            "employee_id": str(result.inserted_id)
        })
        
    except Exception as e:
        logger.error(f"Error adding employee: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@api.route('/api/employees/<phone>', methods=['DELETE'])
def delete_employee(phone):
    """Delete an employee by phone number"""
    try:
        result = employees_collection.delete_one({"phone": phone})
        
        if result.deleted_count == 0:
            return jsonify({
                "status": "error",
                "message": f"Employee with phone {phone} not found"
            }), 404
        
        return jsonify({
            "status": "success",
            "message": "Employee deleted successfully"
        })
        
    except Exception as e:
        logger.error(f"Error deleting employee: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Location based endpoints
@api.route('/api/employees/by-location/<city>', methods=['GET'])
def get_employees_by_location(city):
    """Get employees by city"""
    try:
        employees = list(employees_collection.find({"city": city}, {'_id': 0}))
        return jsonify({
            "status": "success",
            "data": employees,
            "count": len(employees)
        })
    except Exception as e:
        logger.error(f"Error fetching employees by location: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@api.route('/api/cities', methods=['GET'])
def get_cities():
    """Get list of all cities where employees are located"""
    try:
        cities = employees_collection.distinct("city")
        cities = [city for city in cities if city]  # Filter out empty values
        cities.sort()  # Sort alphabetically
        
        return jsonify({
            "status": "success",
            "data": cities
        })
    except Exception as e:
        logger.error(f"Error fetching cities: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Status endpoints
@api.route('/api/employee-status', methods=['GET'])
def get_employee_status():
    """Get status of all employees"""
    try:
        employees = list(employees_collection.find({}))
        
        # Convert ObjectId to string for JSON serialization
        for employee in employees:
            employee['_id'] = str(employee['_id'])
            if employee.get('last_update'):
                employee['last_update'] = employee['last_update'].isoformat()
            if employee.get('created_at'):
                employee['created_at'] = employee['created_at'].isoformat()
        
        return jsonify({
            "status": "success",
            "data": employees
        })
    except Exception as e:
        logger.error(f"Error fetching employee status: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@api.route('/api/status/<phone>', methods=['PUT'])
def update_status(phone):
    """Update employee status manually"""
    try:
        data = request.json
        
        # Validate status
        if 'status' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing required field: status"
            }), 400
        
        # Valid status values
        valid_statuses = ['urgent', 'safe', 'medical', 'support', 'unknown']
        if data['status'] not in valid_statuses:
            return jsonify({
                "status": "error",
                "message": f"Invalid status value. Must be one of: {', '.join(valid_statuses)}"
            }), 400
        
        # Find employee
        employee = employees_collection.find_one({"phone": phone})
        if not employee:
            return jsonify({
                "status": "error",
                "message": f"Employee with phone {phone} not found"
            }), 404
        
        # Update employee status
        employees_collection.update_one(
            {"phone": phone},
            {"$set": {
                "current_status": data['status'],
                "last_update": datetime.now()
            }}
        )
        
        # Log the status update
        status_update = {
            "employee_id": employee["_id"],
            "name": employee["name"],
            "phone": phone,
            "status": data['status'],
            "message": data.get('message', 'Manually updated by admin'),
            "timestamp": datetime.now(),
            "updated_by": "admin"
        }
        status_collection.insert_one(status_update)
        
        return jsonify({
            "status": "success",
            "message": "Status updated successfully"
        })
        
    except Exception as e:
        logger.error(f"Error updating status: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Message history endpoints
@api.route('/api/messages', methods=['GET'])
def get_messages():
    """Get message history"""
    try:
        messages = list(messages_collection.find({}))
        
        # Convert ObjectId to string for JSON serialization
        for message in messages:
            message['_id'] = str(message['_id'])
            if message.get('timestamp'):
                message['timestamp'] = message['timestamp'].isoformat()
        
        return jsonify({
            "status": "success",
            "data": messages
        })
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Import these endpoints in app.py and register the blueprint with:
# app.register_blueprint(api) 
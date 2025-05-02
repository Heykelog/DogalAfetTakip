from app.models.database import db
from datetime import datetime
from bson import ObjectId

class Message:
    COLLECTION = 'messages'
    
    # Message types
    TYPE_STATUS_CHECK = 'status_check'
    TYPE_ALERT = 'alert'
    TYPE_INFO = 'info'
    TYPE_RESPONSE = 'response'
    
    # Message channels
    CHANNEL_SMS = 'sms'
    CHANNEL_WHATSAPP = 'whatsapp'
    CHANNEL_TELEGRAM = 'telegram'
    CHANNEL_EMAIL = 'email'
    
    # Message statuses
    STATUS_PENDING = 'pending'
    STATUS_SENT = 'sent'
    STATUS_DELIVERED = 'delivered'
    STATUS_FAILED = 'failed'
    
    @staticmethod
    def create(message_data):
        """Create a new message record"""
        message_data['created_at'] = datetime.utcnow()
        message_data['updated_at'] = datetime.utcnow()
        message_data['status'] = Message.STATUS_PENDING
        
        if 'message_id' not in message_data:
            message_data['message_id'] = None
            
        result = db.connect()[Message.COLLECTION].insert_one(message_data)
        return str(result.inserted_id)
    
    @staticmethod
    def get(message_id):
        """Get message by ID"""
        return db.connect()[Message.COLLECTION].find_one({'_id': ObjectId(message_id)})
    
    @staticmethod
    def get_all():
        """Get all messages"""
        return list(db.connect()[Message.COLLECTION].find().sort('created_at', -1))
    
    @staticmethod
    def update_status(message_id, new_status, external_message_id=None):
        """Update message status"""
        update_data = {
            'status': new_status,
            'updated_at': datetime.utcnow()
        }
        
        if external_message_id:
            update_data['message_id'] = external_message_id
            
        return db.connect()[Message.COLLECTION].update_one(
            {'_id': ObjectId(message_id)},
            {'$set': update_data}
        )
    
    @staticmethod
    def get_by_employee(employee_id):
        """Get messages by employee ID"""
        return list(db.connect()[Message.COLLECTION].find({'employee_id': employee_id}).sort('created_at', -1))
    
    @staticmethod
    def get_by_disaster(disaster_id):
        """Get messages related to a specific disaster"""
        return list(db.connect()[Message.COLLECTION].find({'disaster_id': disaster_id}).sort('created_at', -1))
    
    @staticmethod
    def get_by_channel(channel):
        """Get messages by communication channel"""
        return list(db.connect()[Message.COLLECTION].find({'channel': channel}).sort('created_at', -1))
    
    @staticmethod
    def get_stats_by_disaster(disaster_id):
        """Get message statistics for a specific disaster"""
        messages = Message.get_by_disaster(disaster_id)
        
        stats = {
            'total': len(messages),
            'by_status': {},
            'by_channel': {}
        }
        
        for message in messages:
            # Count by status
            status = message.get('status')
            if status in stats['by_status']:
                stats['by_status'][status] += 1
            else:
                stats['by_status'][status] = 1
                
            # Count by channel
            channel = message.get('channel')
            if channel in stats['by_channel']:
                stats['by_channel'][channel] += 1
            else:
                stats['by_channel'][channel] = 1
                
        return stats 
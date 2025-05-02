from app.models.database import db
from datetime import datetime
from bson import ObjectId

class Disaster:
    COLLECTION = 'disasters'
    
    # Disaster types
    TYPE_EARTHQUAKE = 'earthquake'
    TYPE_FLOOD = 'flood'
    TYPE_FIRE = 'fire'
    TYPE_HURRICANE = 'hurricane'
    TYPE_OTHER = 'other'
    
    @staticmethod
    def create(disaster_data):
        """Create a new disaster record"""
        disaster_data['created_at'] = datetime.utcnow()
        disaster_data['updated_at'] = datetime.utcnow()
        disaster_data['is_active'] = True
        
        result = db.connect()[Disaster.COLLECTION].insert_one(disaster_data)
        return str(result.inserted_id)
    
    @staticmethod
    def get(disaster_id):
        """Get disaster by ID"""
        return db.connect()[Disaster.COLLECTION].find_one({'_id': ObjectId(disaster_id)})
    
    @staticmethod
    def get_all(active_only=False):
        """Get all disasters, optionally filtered by active status"""
        filter_query = {}
        if active_only:
            filter_query['is_active'] = True
            
        return list(db.connect()[Disaster.COLLECTION].find(filter_query).sort('created_at', -1))
    
    @staticmethod
    def update(disaster_id, update_data):
        """Update disaster data"""
        update_data['updated_at'] = datetime.utcnow()
        
        return db.connect()[Disaster.COLLECTION].update_one(
            {'_id': ObjectId(disaster_id)},
            {'$set': update_data}
        )
    
    @staticmethod
    def deactivate(disaster_id):
        """Mark disaster as inactive"""
        return Disaster.update(disaster_id, {'is_active': False})
    
    @staticmethod
    def get_by_location(city=None, region=None):
        """Get disasters by location"""
        query = {}
        
        if city:
            query['affected_cities'] = city
            
        if region:
            query['affected_regions'] = region
            
        return list(db.connect()[Disaster.COLLECTION].find(query).sort('created_at', -1))
    
    @staticmethod
    def get_active_by_type(disaster_type):
        """Get active disasters by type"""
        return list(db.connect()[Disaster.COLLECTION].find({
            'type': disaster_type,
            'is_active': True
        }).sort('created_at', -1)) 
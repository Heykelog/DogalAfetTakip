from app.models.database import db
from datetime import datetime
from bson import ObjectId

class Settings:
    COLLECTION = 'settings'
    
    @staticmethod
    def get_all():
        """Tüm ayarları getir"""
        return db.connect()[Settings.COLLECTION].find_one({"type": "api_settings"})
    
    @staticmethod
    def update_api_settings(settings_data):
        """API ayarlarını güncelle"""
        settings_data['updated_at'] = datetime.utcnow()
        settings_data['type'] = "api_settings"
        
        # Mevcut ayarları kontrol et
        existing = db.connect()[Settings.COLLECTION].find_one({"type": "api_settings"})
        
        if existing:
            # Mevcut ayarları güncelle
            return db.connect()[Settings.COLLECTION].update_one(
                {"type": "api_settings"},
                {"$set": settings_data}
            )
        else:
            # Yeni ayarlar oluştur
            settings_data['created_at'] = datetime.utcnow()
            return db.connect()[Settings.COLLECTION].insert_one(settings_data)
    
    @staticmethod
    def get_whatsapp_settings():
        """WhatsApp API ayarlarını getir"""
        settings = Settings.get_all()
        if settings:
            return {
                'api_key': settings.get('whatsapp_api_key', ''),
                'phone_number': settings.get('whatsapp_phone_number', '')
            }
        return {'api_key': '', 'phone_number': ''}
    
    @staticmethod
    def get_telegram_settings():
        """Telegram API ayarlarını getir"""
        settings = Settings.get_all()
        if settings:
            return {
                'bot_token': settings.get('telegram_bot_token', '')
            }
        return {'bot_token': ''}
    
    @staticmethod
    def get_twilio_settings():
        """Twilio API ayarlarını getir"""
        settings = Settings.get_all()
        if settings:
            return {
                'account_sid': settings.get('twilio_account_sid', ''),
                'auth_token': settings.get('twilio_auth_token', ''),
                'phone_number': settings.get('twilio_phone_number', '')
            }
        return {'account_sid': '', 'auth_token': '', 'phone_number': ''} 
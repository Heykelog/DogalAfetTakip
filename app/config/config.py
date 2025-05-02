import os
from dotenv import load_dotenv

# .env dosyasının yüklenmesini dene
try:
    load_dotenv()
    print(".env dosyası yüklendi")
except Exception as e:
    print(f".env dosyası yüklenirken hata oluştu: {e}")

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'default-secret-key-for-development'
    MONGODB_URI = os.environ.get('MONGODB_URI') or 'mongodb://localhost:27017/emergency_system'
    
    # WhatsApp API configuration - varsayılanlar
    WHATSAPP_API_KEY = os.environ.get('WHATSAPP_API_KEY') or 'development-whatsapp-key'
    WHATSAPP_PHONE_NUMBER = os.environ.get('WHATSAPP_PHONE_NUMBER') or '+9055555555'
    
    # Telegram API configuration - varsayılanlar
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN') or 'development-telegram-token'
    
    # SMS service configuration (Twilio) - varsayılanlar
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID') or 'development-twilio-sid'
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN') or 'development-twilio-token'
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER') or '+9055555555'
    
    # API ayarlarını veritabanından al
    @classmethod
    def load_db_settings(cls):
        try:
            # Döngüsel import'u önlemek için burada import ediyoruz
            from app.models.settings import Settings
            
            # WhatsApp ayarları
            whatsapp = Settings.get_whatsapp_settings()
            if whatsapp.get('api_key'):
                cls.WHATSAPP_API_KEY = whatsapp.get('api_key')
            if whatsapp.get('phone_number'):
                cls.WHATSAPP_PHONE_NUMBER = whatsapp.get('phone_number')
            
            # Telegram ayarları
            telegram = Settings.get_telegram_settings()
            if telegram.get('bot_token'):
                cls.TELEGRAM_BOT_TOKEN = telegram.get('bot_token')
            
            # Twilio ayarları
            twilio = Settings.get_twilio_settings()
            if twilio.get('account_sid'):
                cls.TWILIO_ACCOUNT_SID = twilio.get('account_sid')
            if twilio.get('auth_token'):
                cls.TWILIO_AUTH_TOKEN = twilio.get('auth_token')
            if twilio.get('phone_number'):
                cls.TWILIO_PHONE_NUMBER = twilio.get('phone_number')
                
            print("Veritabanından API ayarları güncellendi")
        except Exception as e:
            print(f"Veritabanından ayarları yüklerken hata: {e}")
    
    # Geliştirme sırasında değerleri yazdır
    @classmethod
    def print_config(cls):
        print("\nUygulama Yapılandırması:")
        print(f"MongoDB URI: {cls.MONGODB_URI}")
        print("WhatsApp yapılandırması:", "Yapılandırıldı" if cls.WHATSAPP_API_KEY else "Yapılandırılmadı")
        print("Telegram yapılandırması:", "Yapılandırıldı" if cls.TELEGRAM_BOT_TOKEN else "Yapılandırılmadı")
        print("Twilio yapılandırması:", "Yapılandırıldı" if cls.TWILIO_ACCOUNT_SID else "Yapılandırılmadı")
        print() 
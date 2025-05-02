from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash, send_from_directory, make_response
import os
import json
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pymongo import MongoClient
import requests
from flask_cors import CORS
from api_endpoints import api, init_api
import threading
import random
import pandas as pd
import io
import folium
import base64
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import urllib.parse
import time
from apscheduler.schedulers.background import BackgroundScheduler

# Sabit değerler - .env dosyası kullanılamadığında
MONGO_URI = 'mongodb://localhost:27017/afet_db'
SECRET_KEY = 'secure_secret_key_2025_TF'
WHATSAPP_API_TOKEN = ''
WHATSAPP_PHONE_NUMBER_ID = ''
COMPANY_NAME = 'TF Afet İletişim Sistemi'
WEBHOOK_VERIFICATION_TOKEN = 'afet_verification_token'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Admin credentials - Secured
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "TF2025"

# Initialize Flask application
app = Flask(__name__)
app.secret_key = SECRET_KEY
CORS(app)

# MongoDB connection
try:
    logger.info(f"Attempting to connect to MongoDB with URI: {MONGO_URI}")
    
    # Daha uzun bir timeout değeri kullanarak bağlantıyı dene
    mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
    
    # Bağlantıyı test et
    mongo_client.admin.command('ping')
    
    # Veritabanını al
    db = mongo_client.get_database()
    
    # Koleksiyonları ayarla
    employees_collection = db.employees if db is not None else None
    messages_collection = db.messages if db is not None else None
    status_collection = db.status_updates if db is not None else None
    
    logger.info("Connected to MongoDB successfully")
    
    # Veritabanı bağlantısı yapıldı
    db_connected = True
    
    # Initialize API endpoints with database collections
    init_api(employees_collection, messages_collection, status_collection)
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    logger.warning("Uygulama çalışmaya devam edecek, ancak veritabanı işlemleri yapılamayacak")
    
    # Veritabanı olmadan çalışmak için None değerleri ata
    db = None
    employees_collection = None
    messages_collection = None
    status_collection = None
    db_connected = False
    
    # API endpoints boş koleksiyonlarla başlat
    init_api(None, None, None)

# Register API blueprint
app.register_blueprint(api)

# WhatsApp Business API configuration
WHATSAPP_API_URL = f"https://graph.facebook.com/v16.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"

# Telegram Bot API configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

# Company information
COMPANY_NAME = COMPANY_NAME

# Status types and corresponding actions
STATUS_TYPES = {
    "enkaz": "urgent",
    "enkaz altındayım": "urgent",
    "enkaz altindayim": "urgent",
    "1": "urgent",
    "1️⃣": "urgent",
    "iyiyim": "safe",
    "2": "safe",
    "2️⃣": "safe",
    "tibbi": "medical",
    "tıbbi yardıma ihtiyacım var": "medical",
    "tibbi yardima ihtiyacim var": "medical",
    "3": "medical",
    "3️⃣": "medical",
    "destek": "support"
}

# Helper function to send WhatsApp message
def send_whatsapp_message(to_phone, message):
    """
    WhatsApp mesajı gönderme fonksiyonu
    API sağlayıcınıza göre değiştirilmelidir
    """
    if not to_phone or not message:
        logger.error("Phone number or message is missing")
        return False
    
    try:
        # Bu kısım API sağlayıcınıza göre değişecektir
        # Örnek: HTTP isteği gönderme
        headers = {
            'Authorization': f'Bearer {WHATSAPP_API_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'to': to_phone,
            'type': 'text',
            'text': {
                'body': message
            }
        }
        
        # API isteği gönder - burada gerçek API çağrısı yapılmalı
        # response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
        # Şimdilik simüle ediyoruz
        response_status = True
        
        # Mesajı veritabanına kaydet
        if db is not None:
            # Alıcı çalışan bilgilerini bul
            employee = employees_collection.find_one({"phone": to_phone})
            recipient_name = employee.get('name', '') if employee else ''
            
            message_doc = {
                "timestamp": datetime.now(),
                "to": to_phone,
                "recipient_name": recipient_name,
                "message": message,
                "status": "sent" if response_status else "failed"
            }
            
            messages_collection.insert_one(message_doc)
            
        return response_status
        
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}")
        return False

# Send WhatsApp message with interactive buttons
def send_whatsapp_interactive(to_phone, message, buttons=None):
    """
    WhatsApp etkileşimli mesaj gönderme fonksiyonu
    """
    if not to_phone or not message:
        logger.error("Phone number or message is missing")
        return False
    
    try:
        # API isteği için header
        headers = {
            'Authorization': f'Bearer {WHATSAPP_API_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        # Varsayılan butonlar (istenirse özelleştirilebilir)
        if buttons is None:
            buttons = [
                {
                    "type": "reply",
                    "reply": {
                        "id": "enkaz",
                        "title": "Enkaz Altı Bildirimi"
                    }
                },
                {
                    "type": "reply",
                    "reply": {
                        "id": "iyiyim",
                        "title": "İyiyim"
                    }
                },
                {
                    "type": "reply",
                    "reply": {
                        "id": "tibbi",
                        "title": "Tıbbi Yardım Talebi"
                    }
                }
            ]
        
        # Etkileşimli mesaj
        payload = {
            "to": to_phone,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": message
                },
                "action": {
                    "buttons": buttons
                }
            }
        }
        
        # API isteği gönder - burada gerçek API çağrısı yapılmalı
        # response = requests.post(WHATSAPP_API_URL, json=payload, headers=headers)
        # Şimdilik simüle ediyoruz
        response_status = True
        
        # Mesajı veritabanına kaydet
        if db is not None:
            employee = employees_collection.find_one({"phone": to_phone})
            recipient_name = employee.get('name', '') if employee else ''
            
            message_doc = {
                "timestamp": datetime.now(),
                "to": to_phone,
                "recipient_name": recipient_name,
                "message": f"{message} [Etkileşimli Butonlar]",
                "status": "sent" if response_status else "failed",
                "type": "interactive"
            }
            
            messages_collection.insert_one(message_doc)
        
        return response_status
        
    except Exception as e:
        logger.error(f"Error sending interactive WhatsApp message: {e}")
        return False

# Generate status inquiry message
def get_status_inquiry_message(username, disaster_type="afet"):
    return f"""Merhaba {username},
{COMPANY_NAME} Acil Durum Hattı'ndan ulaşıyoruz. Yaşanan {disaster_type} nedeniyle sana ulaşmak istiyoruz. Lütfen aşağıdaki seçeneklerden durumunu bildir:"""

# WhatsApp webhook (gelen mesajları işleme)
@app.route('/api/webhook', methods=['POST'])
def webhook():
    if db is None:
        return jsonify({"status": "error", "message": "Database connection not available"}), 500
    
    try:
        data = request.json
        
        # Webhook doğrulama (sadece örnek)
        if 'verification_token' in data:
            if data['verification_token'] == WEBHOOK_VERIFICATION_TOKEN:
                return jsonify({"status": "success", "message": "Webhook verified"}), 200
            else:
                return jsonify({"status": "error", "message": "Invalid verification token"}), 401
        
        # Gelen mesaj işleme
        if 'from' in data and ('body' in data or 'interactive' in data):
            sender = data['from']
            
            # Metin mesajı veya etkileşimli yanıt kontrolü
            message_body = ""
            is_interactive = False
            
            if 'interactive' in data:
                # Etkileşimli mesaj yanıtı
                is_interactive = True
                message_body = data['interactive'].get('button_reply', {}).get('id', '')
            elif 'body' in data:
                # Normal metin mesajı
                message_body = data['body'].strip().lower()
            
            # Destek talebi kontrolü
            if message_body.lower() == "destek":
                # Menuyu tekrar göster
                employee = employees_collection.find_one({"phone": sender})
                username = employee.get('name', '') if employee else ''
                
                inquiry_message = get_status_inquiry_message(username, "afet")
                send_whatsapp_interactive(sender, inquiry_message)
                
                return jsonify({"status": "success", "message": "Menu sent again"}), 200
            
            # Çalışan telefon numarasını kontrol et
            employee = employees_collection.find_one({"phone": sender})
            
            if not employee:
                # Tanınmayan numara
                return jsonify({"status": "error", "message": "Unknown phone number"}), 404
            
            # Gelen yanıtı işleme
            status_code = None
            
            # Yanıt formatını kontrol et
            if message_body.lower() in ["enkaz", "1", "enkaz altındayım", "enkaz altindayim"]:
                status_code = "urgent"
            elif message_body.lower() in ["iyiyim", "2"]:
                status_code = "safe"
            elif message_body.lower() in ["tibbi", "3", "tıbbi", "tıbbi yardım", "tibbi yardim"]:
                status_code = "medical"
            else:
                # Anlaşılmayan yanıt için tekrar bilgilendirme mesajı
                inquiry_message = get_status_inquiry_message(employee.get('name', ''), "afet")
                send_whatsapp_interactive(sender, inquiry_message + "\n\nYanıtınızı anlayamadık. Lütfen aşağıdaki butonlardan birini seçin.")
                
                return jsonify({
                    "status": "success", 
                    "message": "Clarification requested"
                }), 200
            
            # Çalışan durumunu güncelle
            now = datetime.now()
            
            # Güncelleme verileri
            update_data = {
                "$set": {
                    "current_status": status_code,
                    "last_update": now,
                    "location": data.get('location', employee.get('location')),
                }
            }
            
            # Durum güncellemesi yap
            employees_collection.update_one({"phone": sender}, update_data)
            
            # Durum mesajları
            status_messages = {
                "urgent": "Enkaz altında olduğunuzu bildirdiniz. En kısa sürede yardım ekipleri yönlendirilecek.",
                "safe": "İyi durumda olduğunuzu bildirdiğiniz için teşekkürler. Gelişmeleri takip ediniz.",
                "medical": "Tıbbi yardıma ihtiyacınız olduğunu bildirdiniz. Size en yakın sağlık ekibi bilgilendirilecek."
            }
            
            confirmation_message = status_messages.get(status_code, "Durumunuz güncellenmiştir.")
            confirmation_message += "\n\nDurumunuz değiştiyse 'destek' yazarak tekrar bildirimde bulunabilirsiniz."
            
            # Onay mesajını gönder
            send_whatsapp_message(sender, confirmation_message)
            
            # Durum güncellemesini veritabanında sakla
            status_update = {
                "employee_id": employee["_id"],
                "employee_name": employee["name"],
                "phone": sender,
                "status": status_code,
                "source": "interactive" if is_interactive else "text",
                "timestamp": now
            }
            
            status_collection.insert_one(status_update)
            
            # Başarılı yanıt
            return jsonify({
                "status": "success",
                "message": "Status updated",
                "employee_name": employee.get('name', ''),
                "new_status": status_code
            }), 200
        
        # Geçersiz mesaj formatı
        return jsonify({"status": "error", "message": "Invalid message format"}), 400
    
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# API endpoint to send status inquiry to all employees
@app.route('/api/send-inquiry', methods=['POST'])
def send_inquiry():
    if db is None:
        return jsonify({"status": "error", "message": "Database connection not available"}), 500
    
    try:
        data = request.json
        
        # Afet türü kontrolü
        if 'disaster_type' not in data or not data['disaster_type']:
            return jsonify({
                "status": "error",
                "message": "'disaster_type' alanı zorunludur"
            }), 400
        
        # Platform kontrolü
        platform = data.get('platform', 'whatsapp')
        if platform not in ['whatsapp', 'telegram', 'sms', 'all']:
            return jsonify({
                "status": "error",
                "message": "Geçersiz platform. Değerler: 'whatsapp', 'telegram', 'sms' veya 'all'"
            }), 400
        
        # Alıcı kontrolü (phones, city, veya region olmalı)
        if 'phones' not in data and 'city' not in data and 'region' not in data:
            return jsonify({
                "status": "error",
                "message": "Hedef belirtilmelidir: 'phones', 'city' veya 'region'"
            }), 400
        
        # İlgili çalışanları bulma
        if data.get('phones') and isinstance(data['phones'], list):
            # Belirli çalışanlara gönderme
            target_employees = list(employees_collection.find({"phone": {"$in": data['phones']}}, {"_id": 0, "name": 1, "phone": 1}))
        elif data.get('city'):
            # Şehre göre filtreleme
            city_name = data['city']
            
            # Belirtilen şehirdeki tüm çalışanları bulma
            target_employees = list(employees_collection.find({"city": city_name}, {"_id": 0, "name": 1, "phone": 1}))
                
            if not target_employees:
                return jsonify({
                    "status": "error",
                    "message": f"'{city_name}' şehrinde çalışan bulunamadı"
                }), 404
        elif data.get('region'):
            # Bölgeye göre filtreleme
            region_name = data['region']
            
            # Belirtilen bölgedeki tüm çalışanları bulma
            target_employees = list(employees_collection.find({"region": region_name}, {"_id": 0, "name": 1, "phone": 1}))
                
            if not target_employees:
                return jsonify({
                    "status": "error",
                    "message": f"'{region_name}' bölgesinde çalışan bulunamadı"
                }), 404
        else:
            # Hiçbir hedef belirtilmemişse tüm çalışanlara gönderme
            target_employees = list(employees_collection.find({}, {"_id": 0, "name": 1, "phone": 1}))
        
        # Mesaj işleme
        now = datetime.now()
        sent_count = 0
        failed_count = 0
        
        for employee in target_employees:
            phone = employee['phone']
            name = employee.get('name', '')
            
            # Mesaj oluşturma
            message_text = generate_inquiry_message(data['disaster_type'], name)
            message_sent = False
            
            # Platforma göre mesaj gönderme
            if platform in ['whatsapp', 'all']:
                # WhatsApp mesajı gönder
                try:
                    if send_whatsapp_interactive(phone, message_text):
                        message_sent = True
                        
                        # Mesajı kaydederken log
                        if messages_collection is not None:
                            message_log = {
                                "timestamp": now,
                                "to": phone,
                                "recipient_name": name,
                                "message": message_text,
                                "status": "sent",
                                "platform": "whatsapp",
                                "type": "inquiry",
                                "disaster_type": data['disaster_type']
                            }
                            messages_collection.insert_one(message_log)
                            
                except Exception as e:
                    logger.error(f"WhatsApp message sending error to {phone}: {e}")
            
            if platform in ['telegram', 'all'] and not message_sent:
                # Telegram mesajı gönder (gerçek implementasyon eklenecek)
                try:
                    # Şimdilik simüle ediyoruz, gerçek Telegram API entegrasyonu yapılmalı
                    # send_telegram_message(phone, message_text)
                    logger.info(f"Simulated Telegram message to {phone}: {message_text}")
                    
                    # Mesajı kaydederken log (simülasyon)
                    if messages_collection is not None:
                        message_log = {
                            "timestamp": now,
                            "to": phone,
                            "recipient_name": name,
                            "message": message_text,
                            "status": "simulated",
                            "platform": "telegram",
                            "type": "inquiry",
                            "disaster_type": data['disaster_type']
                        }
                        messages_collection.insert_one(message_log)
                        message_sent = True
                except Exception as e:
                    logger.error(f"Telegram message sending error to {phone}: {e}")
            
            if platform in ['sms', 'all'] and not message_sent:
                # SMS mesajı gönder (gerçek implementasyon eklenecek)
                try:
                    # Şimdilik simüle ediyoruz, gerçek SMS API entegrasyonu yapılmalı
                    # send_sms_message(phone, message_text)
                    logger.info(f"Simulated SMS to {phone}: {message_text}")
                    
                    # Mesajı kaydederken log (simülasyon)
                    if messages_collection is not None:
                        message_log = {
                            "timestamp": now,
                            "to": phone,
                            "recipient_name": name,
                            "message": message_text,
                            "status": "simulated",
                            "platform": "sms",
                            "type": "inquiry",
                            "disaster_type": data['disaster_type']
                        }
                        messages_collection.insert_one(message_log)
                        message_sent = True
                except Exception as e:
                    logger.error(f"SMS sending error to {phone}: {e}")
            
            # Başarı/hata sayısı güncelleme
            if message_sent:
                sent_count += 1
            else:
                failed_count += 1
        
        # Başarılı yanıt döndürme
        response_data = {
            "status": "success",
            "message": "Durum sorgulama mesajları gönderildi",
            "sent": sent_count,
            "failed": failed_count,
            "total": len(target_employees),
            "platform": platform
        }
        
        # Ekstra bilgi ekle
        if data.get('city'):
            response_data["city"] = data['city']
        elif data.get('region'):
            response_data["region"] = data['region']
        
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Error sending inquiry: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Sorgu mesajı oluşturma
def generate_inquiry_message(disaster_type, recipient_name=None):
    disaster_types = {
        "earthquake": "deprem",
        "flood": "sel",
        "fire": "yangın",
        "hurricane": "kasırga",
        "tsunami": "tsunami",
        "other": "afet"
    }
    
    # Afet türünü Türkçe'ye çevirme
    disaster_name = disaster_types.get(disaster_type, "afet")
    
    # Mesaj metni
    greeting = f"Merhaba {recipient_name}," if recipient_name else "Merhaba,"
    
    message = f"{greeting}\n{COMPANY_NAME} Acil Durum Hattı'ndan ulaşıyoruz. Yaşanan {disaster_name} nedeniyle sana ulaşmak istiyoruz. Lütfen aşağıdaki butonlardan durumunu bildir:"
    
    return message

# Admin login
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Geçersiz kullanıcı adı veya şifre', 'error')
    
    return render_template('login.html')

# Admin logout
@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))

# Admin dashboard
@app.route('/admin')
def admin_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    
    # Önbelleği devre dışı bırakmak için rastgele bir sorgu parametresi ekle
    response = make_response(render_template('dashboard.html', cache_buster=datetime.now().timestamp()))
    
    # Önbellek kontrolü başlıklarını ekle
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

# Analytics dashboard
@app.route('/analytics')
def analytics_dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    
    return render_template('analytics.html')

# Main route
@app.route('/')
def index():
    return redirect(url_for('admin_login'))

# Çalışan durum bilgilerini getirme
@app.route('/api/employee-status', methods=['GET'])
def get_employee_status():
    if db is None:
        return jsonify({
            "status": "error", 
            "message": "Veritabanı bağlantısı kurulamadı. MongoDB'nin yüklü ve çalışır durumda olduğundan emin olun."
        }), 500
    
    try:
        employees = list(employees_collection.find({}, {"_id": 0, "name": 1, "phone": 1, "city": 1, "current_status": 1, "last_update": 1}))
        return jsonify({
            "status": "success",
            "data": employees
        })
    except Exception as e:
        logger.error(f"Error retrieving employee status: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Şehirleri getirme (benzersiz şehirlerin listesi)
@app.route('/api/cities', methods=['GET'])
def get_cities():
    # Varsayılan şehirler
    default_cities = [
        "İstanbul", "Ankara", "İzmir", "Bursa", "Antalya", "Adana", "Konya", "Kayseri", 
        "Gaziantep", "Şanlıurfa", "Diyarbakır", "Samsun", "Mersin", "Malatya", "Erzurum", 
        "Trabzon", "Van", "Eskişehir", "Tekirdağ", "Balıkesir"
    ]
    
    if db is None:
        return jsonify({
            "status": "success",
            "data": default_cities
        })
    
    try:
        # Veritabanından benzersiz şehir listesini çek
        city_pipeline = [
            {"$group": {"_id": "$city"}},
            {"$match": {"_id": {"$ne": None, "$ne": ""}}},
            {"$sort": {"_id": 1}}
        ]
        city_results = list(employees_collection.aggregate(city_pipeline))
        
        # Sonuçları işle
        cities = [city["_id"] for city in city_results]
        
        # Hiç şehir bulunmazsa varsayılan listeyi kullan
        if not cities:
            cities = default_cities
        
        return jsonify({
            "status": "success",
            "data": cities
        })
    except Exception as e:
        logger.error(f"Error retrieving cities: {e}")
        # Hata durumunda varsayılan listeyi döndür
        return jsonify({
            "status": "success",
            "data": default_cities
        })

# Bölgeleri getirme (benzersiz bölgelerin listesi)
@app.route('/api/regions', methods=['GET'])
def get_regions():
    # Varsayılan Türkiye bölgeleri
    default_regions = [
        "Marmara", "Ege", "Akdeniz", "Karadeniz", "İç Anadolu", 
        "Doğu Anadolu", "Güneydoğu Anadolu"
    ]
    
    if db is None:
        return jsonify({
            "status": "success",
            "data": default_regions
        })
    
    try:
        # Veritabanından benzersiz bölge listesini çek
        region_pipeline = [
            {"$group": {"_id": "$region"}},
            {"$match": {"_id": {"$ne": None, "$ne": ""}}},
            {"$sort": {"_id": 1}}
        ]
        region_results = list(employees_collection.aggregate(region_pipeline))
        
        # Sonuçları işle
        regions = [region["_id"] for region in region_results]
        
        # Hiç bölge bulunmazsa varsayılan listeyi kullan
        if not regions:
            regions = default_regions
        
        return jsonify({
            "status": "success",
            "data": regions
        })
    except Exception as e:
        logger.error(f"Error retrieving regions: {e}")
        # Hata durumunda varsayılan listeyi döndür
        return jsonify({
            "status": "success",
            "data": default_regions
        })

# Çalışan ekleme
@app.route('/api/employees', methods=['POST'])
def add_employee():
    if db is None:
        return jsonify({"status": "error", "message": "Database connection not available"}), 500
    
    try:
        data = request.json
        
        # Gerekli alanları kontrol etme
        required_fields = ['name', 'phone', 'city']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    "status": "error",
                    "message": f"'{field}' alanı zorunludur"
                }), 400
        
        # Telefon numarası kontrol etme
        if not data['phone'].startswith('+'):
            return jsonify({
                "status": "error",
                "message": "Telefon numarası '+' işareti ile başlamalıdır"
            }), 400
        
        # Çalışanın zaten var olup olmadığını kontrol etme
        if employees_collection.find_one({"phone": data['phone']}):
            return jsonify({
                "status": "error",
                "message": "Bu telefon numarasına sahip bir çalışan zaten var"
            }), 400
        
        # Yeni çalışan oluşturma
        new_employee = {
            "name": data['name'],
            "phone": data['phone'],
            "department": data.get('department', ''),
            "city": data['city'],
            "region": data.get('region', ''),
            "current_status": None,
            "last_update": None,
            "created_at": datetime.now()
        }
        
        # Çalışanı veritabanına ekleme
        employees_collection.insert_one(new_employee)
        
        return jsonify({
            "status": "success",
            "message": "Çalışan başarıyla eklendi",
            "data": new_employee
        })
    except Exception as e:
        logger.error(f"Error adding employee: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Çalışan silme
@app.route('/api/employees/<phone>', methods=['DELETE'])
def delete_employee(phone):
    if db is None:
        return jsonify({"status": "error", "message": "Database connection not available"}), 500
    
    try:
        result = employees_collection.delete_one({"phone": phone})
        
        if result.deleted_count > 0:
            return jsonify({
                "status": "success",
                "message": "Çalışan başarıyla silindi"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Belirtilen telefon numarasına sahip çalışan bulunamadı"
            }), 404
    except Exception as e:
        logger.error(f"Error deleting employee: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Çalışan durumunu güncelleme
@app.route('/api/status/<phone>', methods=['PUT'])
def update_status(phone):
    if db is None:
        return jsonify({"status": "error", "message": "Database connection not available"}), 500
    
    try:
        data = request.json
        
        # Status kontrolü
        if 'status' not in data:
            return jsonify({
                "status": "error",
                "message": "'status' alanı zorunludur"
            }), 400
        
        # Geçerli durum kontrolü
        valid_statuses = ['safe', 'urgent', 'medical', 'support', None]
        if data['status'] not in valid_statuses:
            return jsonify({
                "status": "error",
                "message": "Geçersiz durum değeri"
            }), 400
        
        # Çalışanı bulma
        result = employees_collection.update_one(
            {"phone": phone},
            {"$set": {"current_status": data['status'], "last_update": datetime.now()}}
        )
        
        if result.modified_count > 0:
            return jsonify({
                "status": "success",
                "message": "Çalışan durumu başarıyla güncellendi"
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Belirtilen telefon numarasına sahip çalışan bulunamadı"
            }), 404
    except Exception as e:
        logger.error(f"Error updating employee status: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Mesaj geçmişini alma
@app.route('/api/messages', methods=['GET'])
def get_messages():
    if db is None:
        return jsonify({"status": "error", "message": "Database connection not available"}), 500
    
    try:
        messages = list(messages_collection.find({}, {"_id": 0, "timestamp": 1, "to": 1, "recipient_name": 1, "message": 1, "status": 1}))
        return jsonify({
            "status": "success",
            "data": messages
        })
    except Exception as e:
        logger.error(f"Error retrieving messages: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Statik dosyaları sunma
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

# Test endpoint for checking database and WhatsApp integration
@app.route('/api/test', methods=['GET'])
def test_integration():
    result = {
        "status": "success",
        "timestamp": datetime.now().isoformat(),
        "environment": os.getenv("FLASK_ENV", "development"),
        "database_connected": False,
        "whatsapp_configured": bool(WHATSAPP_API_URL and WHATSAPP_API_TOKEN)
    }
    
    # Test database collections
    try:
        if db is None:
            result["database_error"] = "Database connection not available"
        else:
            # Check if MongoDB is responding
            db.command('ping')
            result["database_connected"] = True
            result["database_ping"] = True
            
            # Check collections
            if employees_collection is not None:
                result["employees_count"] = employees_collection.count_documents({})
            
            if messages_collection is not None:
                result["messages_count"] = messages_collection.count_documents({})
    except Exception as e:
        result["database_connected"] = False
        result["database_error"] = str(e)
    
    return jsonify(result)

# Test endpoint for sending a WhatsApp message
@app.route('/api/test-whatsapp', methods=['POST'])
def test_whatsapp():
    if db is None:
        return jsonify({
            "status": "error", 
            "message": "Veritabanı bağlantısı kurulamadı. MongoDB'nin yüklü ve çalışır durumda olduğundan emin olun."
        }), 500
    
    data = request.json
    if not data or not data.get('phone'):
        return jsonify({
            "status": "error",
            "message": "Phone number is required in the request body"
        }), 400
    
    # Normalize phone number
    phone = data.get('phone')
    if not phone.startswith('+'):
        phone = '+' + phone
    
    # Create test message
    message = data.get('message', "Bu bir test mesajıdır. Bu mesaj, AfetTakip sisteminin düzgün çalıştığını doğrulamak için gönderilmiştir.")
    
    try:
        # Send test message
        response = send_whatsapp_message(phone, message)
        
        # Log the test message
        if messages_collection is not None:
            message_log = {
                "to": phone,
                "message": message,
                "timestamp": datetime.now(),
                "status": "sent",
                "type": "test",
                "response": response
            }
            messages_collection.insert_one(message_log)
        
        return jsonify({
            "status": "success",
            "message": "Test message sent successfully",
            "details": response
        })
        
    except Exception as e:
        logger.error(f"Error sending test WhatsApp message: {e}")
        return jsonify({
            "status": "error",
            "message": f"Failed to send test message: {str(e)}"
        }), 500

# Import employees from Excel file
@app.route('/api/import-employees', methods=['POST'])
def import_employees():
    if db is None:
        return jsonify({
            "status": "error", 
            "message": "Veritabanı bağlantısı kurulamadı. MongoDB'nin yüklü ve çalışır durumda olduğundan emin olun."
        }), 500
    
    if 'file' not in request.files:
        return jsonify({
            "status": "error",
            "message": "No file part in the request"
        }), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({
            "status": "error",
            "message": "No file selected"
        }), 400
    
    if not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        return jsonify({
            "status": "error",
            "message": "File must be an Excel file (.xlsx or .xls)"
        }), 400
    
    try:
        # Read Excel file
        df = pd.read_excel(file)
        
        # Check required columns
        required_columns = ['name', 'phone']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return jsonify({
                "status": "error",
                "message": f"Missing required columns: {', '.join(missing_columns)}"
            }), 400
        
        # Process employee data
        results = {
            "success": 0,
            "failed": 0,
            "errors": []
        }
        
        for index, row in df.iterrows():
            try:
                # Extract employee data
                employee_data = {
                    "name": row['name'],
                    "phone": row['phone'],
                    "email": row.get('email', ''),
                    "department": row.get('department', ''),
                    "position": row.get('position', ''),
                    "city": row.get('city', ''),
                    "region": row.get('region', ''),
                    "address": row.get('address', ''),
                    "emergency_contact": row.get('emergency_contact', ''),
                    "emergency_phone": row.get('emergency_phone', ''),
                    "current_status": row.get('current_status', 'unknown'),
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                }
                
                # Normalize phone number
                if not employee_data['phone'].startswith('+'):
                    employee_data['phone'] = '+' + employee_data['phone']
                
                # Check if employee already exists
                existing_employee = employees_collection.find_one({"phone": employee_data['phone']})
                
                if existing_employee:
                    # Update existing employee
                    employees_collection.update_one(
                        {"phone": employee_data['phone']},
                        {"$set": {**employee_data, "updated_at": datetime.now()}}
                    )
                else:
                    # Insert new employee
                    employees_collection.insert_one(employee_data)
                
                results["success"] += 1
                
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "row": index + 2,  # +2 because Excel is 1-indexed and header row
                    "error": str(e)
                })
        
        return jsonify({
            "status": "success",
            "message": f"Processed {results['success']} employees successfully, {results['failed']} failed",
            "details": results
        })
        
    except Exception as e:
        logger.error(f"Error importing employees: {e}")
        return jsonify({
            "status": "error",
            "message": f"Failed to process Excel file: {str(e)}"
        }), 500

# Harita görüntüleme endpoint'i
@app.route('/map')
def show_map():
    if not session.get('logged_in'):
        return redirect(url_for('admin_login'))
    
    return render_template('map.html')

# Çalışan konumlarını haritada gösterme API'si
@app.route('/api/map-data')
def get_map_data():
    if db is None:
        return jsonify({"status": "error", "message": "Database connection not available"}), 500
    
    try:
        # Türkiye'nin şehirlerine göre yaklaşık koordinatlar
        city_coordinates = {
            "İstanbul": [41.0082, 28.9784],
            "Ankara": [39.9334, 32.8597],
            "İzmir": [38.4237, 27.1428],
            "Antalya": [36.8969, 30.7133],
            "Adana": [37.0000, 35.3213],
            "Bursa": [40.1885, 29.0610],
            "Konya": [37.8719, 32.4844],
            "Gaziantep": [37.0662, 37.3833],
            "Şanlıurfa": [37.1674, 38.7955],
            "Kocaeli": [40.7654, 29.9408],
            "Mersin": [36.8000, 34.6333],
            "Diyarbakır": [37.9144, 40.2306],
            "Hatay": [36.2024, 36.1610],
            "Manisa": [38.6140, 27.4296],
            "Kayseri": [38.7205, 35.4826],
            "Samsun": [41.2928, 36.3313],
            "Balıkesir": [39.6484, 27.8826],
            "Kahramanmaraş": [37.5753, 36.9228],
            "Van": [38.4891, 43.4089],
            "Aydın": [37.8560, 27.8416]
        }
        
        # Varsayılan koordinatlar (Türkiye merkezi)
        default_coords = [39.1667, 35.6667]
        
        # Tüm çalışanları getir
        employees = list(employees_collection.find({}, {"_id": 0, "name": 1, "phone": 1, "city": 1, "current_status": 1, "last_update": 1}))
        
        # Harita verisi oluştur
        map_data = []
        
        for employee in employees:
            coords = city_coordinates.get(employee.get('city'), default_coords)
            status = employee.get('current_status')
            
            # Durum rengini belirle
            if status == 'urgent':
                color = 'red'
                status_text = 'Enkaz Altında'
            elif status == 'medical':
                color = 'orange'
                status_text = 'Tıbbi Yardım'
            elif status == 'safe':
                color = 'green'
                status_text = 'İyi Durumda'
            else:
                color = 'gray'
                status_text = 'Bilinmiyor'
            
            # Son güncelleme
            last_update = "Bilinmiyor"
            if employee.get('last_update'):
                last_update = employee['last_update'].strftime('%d.%m.%Y %H:%M:%S')
            
            map_data.append({
                'name': employee.get('name', 'İsimsiz'),
                'coords': coords,
                'status': status,
                'status_text': status_text,
                'color': color,
                'phone': employee.get('phone', ''),
                'city': employee.get('city', 'Bilinmiyor'),
                'last_update': last_update
            })
        
        return jsonify({
            "status": "success",
            "data": map_data
        })
    except Exception as e:
        logger.error(f"Error generating map data: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Analitik verileri getiren API
@app.route('/api/analytics')
def get_analytics():
    if db is None:
        return jsonify({
            "status": "error", 
            "message": "Veritabanı bağlantısı kurulamadı. MongoDB'nin yüklü ve çalışır durumda olduğundan emin olun."
        }), 500
    
    try:
        # Durum dağılımı
        total_employees = employees_collection.count_documents({}) if employees_collection is not None else 0
        urgent_count = employees_collection.count_documents({"current_status": "urgent"}) if employees_collection is not None else 0
        medical_count = employees_collection.count_documents({"current_status": "medical"}) if employees_collection is not None else 0
        safe_count = employees_collection.count_documents({"current_status": "safe"}) if employees_collection is not None else 0
        unknown_count = total_employees - urgent_count - medical_count - safe_count
        
        # Şehir bazlı dağılım
        city_pipeline = [
            {"$group": {"_id": "$city", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        city_distribution = list(employees_collection.aggregate(city_pipeline)) if employees_collection is not None else []
        
        # Bölge bazlı dağılım
        region_pipeline = [
            {"$group": {"_id": "$region", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        region_distribution = list(employees_collection.aggregate(region_pipeline)) if employees_collection is not None else []
        
        # Acil durum şehir dağılımı
        emergency_city_pipeline = [
            {"$match": {"current_status": {"$in": ["urgent", "medical"]}}},
            {"$group": {"_id": "$city", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        emergency_city_distribution = list(employees_collection.aggregate(emergency_city_pipeline)) if employees_collection is not None else []
        
        # Son 24 saat içinde güncellenen durumlar
        one_day_ago = datetime.now() - timedelta(days=1)
        recent_updates = employees_collection.count_documents({"last_update": {"$gte": one_day_ago}}) if employees_collection is not None else 0
        
        return jsonify({
            "status": "success",
            "data": {
                "total_employees": total_employees,
                "status_distribution": {
                    "urgent": urgent_count,
                    "medical": medical_count,
                    "safe": safe_count,
                    "unknown": unknown_count
                },
                "city_distribution": [{"city": item["_id"] or "Belirtilmemiş", "count": item["count"]} for item in city_distribution],
                "region_distribution": [{"region": item["_id"] or "Belirtilmemiş", "count": item["count"]} for item in region_distribution],
                "emergency_by_city": [{"city": item["_id"] or "Belirtilmemiş", "count": item["count"]} for item in emergency_city_distribution],
                "recent_updates": recent_updates
            }
        })
    except Exception as e:
        logger.error(f"Error generating analytics: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Analitik grafikler
@app.route('/api/analytics/charts/<chart_type>')
def get_analytics_chart(chart_type):
    if db is None:
        return jsonify({
            "status": "error", 
            "message": "Veritabanı bağlantısı kurulamadı. MongoDB'nin yüklü ve çalışır durumda olduğundan emin olun."
        }), 500
    
    try:
        plt.figure(figsize=(10, 6))
        
        if chart_type == 'status':
            # Durum dağılımı pasta grafiği
            total_employees = employees_collection.count_documents({}) if employees_collection is not None else 0
            urgent_count = employees_collection.count_documents({"current_status": "urgent"}) if employees_collection is not None else 0
            medical_count = employees_collection.count_documents({"current_status": "medical"}) if employees_collection is not None else 0
            safe_count = employees_collection.count_documents({"current_status": "safe"}) if employees_collection is not None else 0
            unknown_count = total_employees - urgent_count - medical_count - safe_count
            
            labels = ['Enkaz Altında', 'Tıbbi Yardım', 'İyi Durumda', 'Bilinmiyor']
            sizes = [urgent_count, medical_count, safe_count, unknown_count]
            colors = ['#ff4444', '#ffbb33', '#00C851', '#9e9e9e']
            explode = (0.1, 0.05, 0, 0)
            
            plt.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90, shadow=True)
            plt.axis('equal')
            plt.title('Çalışan Durum Dağılımı')
            
        elif chart_type == 'city':
            # Şehir bazlı durum grafiği
            city_pipeline = [
                {"$group": {"_id": "$city", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            city_distribution = list(employees_collection.aggregate(city_pipeline)) if employees_collection is not None else []
            
            cities = [item["_id"] or "Belirtilmemiş" for item in city_distribution]
            counts = [item["count"] for item in city_distribution]
            
            plt.barh(cities, counts, color='skyblue')
            plt.xlabel('Çalışan Sayısı')
            plt.ylabel('Şehirler')
            plt.title('Şehirlere Göre Çalışan Dağılımı')
            plt.tight_layout()
            
        elif chart_type == 'emergency':
            # Acil durum dağılımı
            emergency_city_pipeline = [
                {"$match": {"current_status": {"$in": ["urgent", "medical"]}}},
                {"$group": {"_id": "$city", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 10}
            ]
            emergency_distribution = list(employees_collection.aggregate(emergency_city_pipeline)) if employees_collection is not None else []
            
            cities = [item["_id"] or "Belirtilmemiş" for item in emergency_distribution]
            counts = [item["count"] for item in emergency_distribution]
            
            plt.barh(cities, counts, color='#ff4444')
            plt.xlabel('Acil Durum Sayısı')
            plt.ylabel('Şehirler')
            plt.title('Şehirlere Göre Acil Durum Dağılımı')
            plt.tight_layout()
        
        else:
            return jsonify({"status": "error", "message": "Invalid chart type"}), 400
        
        # Grafiği binary veri olarak dönüştür
        output = io.BytesIO()
        FigureCanvas(plt.gcf()).print_png(output)
        plt.close()
        
        # Base64 formatına çevir
        response = make_response(output.getvalue())
        response.mimetype = 'image/png'
        
        return response
    
    except Exception as e:
        logger.error(f"Error generating chart: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Geçmiş durum bilgilerini getirme
@app.route('/api/employee-history/<phone>')
def get_employee_history(phone):
    if db is None:
        return jsonify({"status": "error", "message": "Database connection not available"}), 500
    
    try:
        # Kullanıcı bilgisi
        employee = employees_collection.find_one({"phone": phone}, {"_id": 0})
        
        if not employee:
            return jsonify({"status": "error", "message": "Employee not found"}), 404
        
        # Durum güncellemeleri
        status_updates = list(status_collection.find(
            {"phone": phone}, 
            {"_id": 0, "status": 1, "timestamp": 1, "source": 1}
        ).sort("timestamp", -1))
        
        # Mesaj geçmişi
        messages = list(messages_collection.find(
            {"to": phone}, 
            {"_id": 0, "timestamp": 1, "message": 1, "status": 1, "type": 1}
        ).sort("timestamp", -1))
        
        # Timestamp'leri string'e çevir
        for update in status_updates:
            if update.get('timestamp'):
                update['timestamp'] = update['timestamp'].strftime('%d.%m.%Y %H:%M:%S')
                
        for msg in messages:
            if msg.get('timestamp'):
                msg['timestamp'] = msg['timestamp'].strftime('%d.%m.%Y %H:%M:%S')
        
        return jsonify({
            "status": "success",
            "data": {
                "employee": employee,
                "status_history": status_updates,
                "message_history": messages
            }
        })
    except Exception as e:
        logger.error(f"Error retrieving employee history: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# WhatsApp ile konum paylaşımı
@app.route('/api/location-update', methods=['POST'])
def update_location():
    if db is None:
        return jsonify({"status": "error", "message": "Database connection not available"}), 500
    
    try:
        data = request.json
        
        # Gerekli alanları kontrol et
        if not data.get('phone') or not (data.get('latitude') and data.get('longitude')):
            return jsonify({
                "status": "error",
                "message": "Phone number and location coordinates are required"
            }), 400
        
        phone = data['phone']
        latitude = float(data['latitude'])
        longitude = float(data['longitude'])
        
        # Çalışanı bul
        employee = employees_collection.find_one({"phone": phone})
        
        if not employee:
            return jsonify({
                "status": "error",
                "message": "Employee not found with the provided phone number"
            }), 404
        
        # Konum bilgisini güncelle
        employees_collection.update_one(
            {"phone": phone},
            {"$set": {
                "last_location": {
                    "type": "Point",
                    "coordinates": [longitude, latitude]
                },
                "location_updated_at": datetime.now()
            }}
        )
        
        # Konum güncellemesini loglama
        location_update = {
            "employee_id": employee["_id"],
            "phone": phone,
            "location": {
                "type": "Point",
                "coordinates": [longitude, latitude]
            },
            "timestamp": datetime.now(),
            "source": data.get('source', 'api')
        }
        
        # Konum güncellemelerini tutmak için yeni bir koleksiyon kullanılabilir
        db.location_updates.insert_one(location_update)
        
        return jsonify({
            "status": "success",
            "message": "Location updated successfully"
        })
        
    except Exception as e:
        logger.error(f"Error updating location: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# Çalışana özel mesaj gönderme
@app.route('/api/send-message', methods=['POST'])
def send_custom_message():
    if db is None:
        return jsonify({
            "status": "error", 
            "message": "Veritabanı bağlantısı kurulamadı. MongoDB'nin yüklü ve çalışır durumda olduğundan emin olun."
        }), 500
    
    try:
        data = request.json
        
        # Gerekli alanları kontrol et
        if not data.get('phone'):
            return jsonify({
                "status": "error",
                "message": "Telefon numarası zorunludur"
            }), 400
        
        if not data.get('message'):
            return jsonify({
                "status": "error",
                "message": "Mesaj içeriği zorunludur"
            }), 400
        
        # Platform kontrolü (varsayılan: whatsapp)
        platform = data.get('platform', 'whatsapp').lower()
        if platform not in ['whatsapp', 'telegram', 'sms']:
            return jsonify({
                "status": "error",
                "message": "Geçersiz platform. whatsapp, telegram veya sms olabilir."
            }), 400
        
        # Telefon numarasını normalleştir
        phone = data.get('phone')
        if not phone.startswith('+'):
            phone = '+' + phone
        
        # Çalışanı bul
        employee = employees_collection.find_one({"phone": phone})
        if not employee:
            return jsonify({
                "status": "error",
                "message": "Bu telefon numarasına sahip çalışan bulunamadı"
            }), 404
        
        message = data.get('message')
        now = datetime.now()
        status = "pending"
        response = None
        
        # Platforma göre mesaj gönderme
        if platform == 'whatsapp':
            # WhatsApp mesajı gönder
            try:
                response = send_whatsapp_message(phone, message)
                status = "sent" if response else "failed"
            except Exception as e:
                logger.error(f"WhatsApp message sending error: {e}")
                status = "failed"
                response = str(e)
        
        elif platform == 'telegram':
            # Telegram mesajı gönder
            try:
                response = send_telegram_message(phone, message)
                status = "sent" if response else "failed"
            except Exception as e:
                logger.error(f"Telegram message sending error: {e}")
                status = "failed"
                response = str(e)
        
        elif platform == 'sms':
            # SMS mesajı gönder (SMS fonksiyonu gerekir)
            try:
                # TODO: SMS entegrasyonu eklendiğinde burayı güncelle
                # response = send_sms_message(phone, message)
                response = {"status": "not_implemented", "message": "SMS integration pending"}
                status = "not_implemented"
            except Exception as e:
                logger.error(f"SMS message sending error: {e}")
                status = "failed"
                response = str(e)
        
        # Mesaj kaydını veritabanına ekle
        if messages_collection is not None:
            message_log = {
                "timestamp": now,
                "to": phone,
                "recipient_name": employee.get('name', ''),
                "message": message,
                "platform": platform,
                "status": status,
                "response": response,
                "type": "custom",
                "sender": data.get('sender', 'admin')
            }
            
            messages_collection.insert_one(message_log)
        
        return jsonify({
            "status": "success",
            "message": f"Mesaj gönderildi: {status}",
            "details": {
                "to": phone,
                "recipient": employee.get('name', ''),
                "platform": platform,
                "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                "status": status,
                "response": response
            }
        })
        
    except Exception as e:
        logger.error(f"Error sending custom message: {e}")
        return jsonify({
            "status": "error",
            "message": f"Mesaj gönderilirken hata oluştu: {str(e)}"
        }), 500

# Helper function to send Telegram message
def send_telegram_message(to_phone, message):
    """
    Telegram mesajı gönderme fonksiyonu
    """
    if not to_phone or not message:
        logger.error("Phone number or message is missing")
        return False
    
    try:
        # Telegram için telefon numarası arama (veritabanında kayıtlı olmalı)
        employee = None
        if db is not None:
            employee = employees_collection.find_one({"phone": to_phone})
        
        # Telegram Chat ID (gerçek uygulamada bu kaydedilmiş olmalı)
        # Simülasyon için telefon numarasının son 10 hanesini kullanıyoruz
        chat_id = to_phone.replace('+', '')[-10:]
        
        # Gerçek API çağrısı burada yapılmalı
        # Örnek: telegram_payload = {"chat_id": chat_id, "text": message}
        # response = requests.post(TELEGRAM_API_URL, json=telegram_payload)
        
        # Simülasyon için başarı dönüyoruz
        response_status = True
        logger.info(f"Simulated Telegram message to {to_phone} (chat_id: {chat_id}): {message}")
        
        # Mesajı veritabanına kaydet
        if db is not None:
            # Alıcı çalışan bilgilerini bul
            recipient_name = employee.get('name', '') if employee else ''
            
            message_doc = {
                "timestamp": datetime.now(),
                "to": to_phone,
                "recipient_name": recipient_name,
                "message": message,
                "platform": "telegram",
                "status": "simulated",
                "chat_id": chat_id
            }
            
            messages_collection.insert_one(message_doc)
            
        return response_status
        
    except Exception as e:
        logger.error(f"Error sending Telegram message: {e}")
        return False

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    host = os.getenv('HOST', '0.0.0.0')
    debug = os.getenv('DEBUG', 'true').lower() == 'true'
    
    logger.info(f"Starting application on {host}:{port} (debug: {debug})")
    app.run(host=host, port=port, debug=debug, load_dotenv=False) 
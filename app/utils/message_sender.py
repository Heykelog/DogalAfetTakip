import requests
from twilio.rest import Client
from flask import current_app
from app.models.message import Message
from app.models.employee import Employee

class MessageSender:
    @staticmethod
    def send_whatsapp(to_number, message_text, employee_id=None, disaster_id=None):
        """Send WhatsApp message using WhatsApp Business API"""
        try:
            # Güncel config değerlerini al
            api_key = current_app.config.get('WHATSAPP_API_KEY')
            from_number = current_app.config.get('WHATSAPP_PHONE_NUMBER')
            
            if not api_key or not from_number:
                raise ValueError("WhatsApp API ayarları yapılandırılmamış")
            
            # Create message record in database
            message_data = {
                'channel': Message.CHANNEL_WHATSAPP,
                'to': to_number,
                'from': from_number,
                'content': message_text,
                'type': Message.TYPE_STATUS_CHECK
            }
            
            if employee_id:
                message_data['employee_id'] = employee_id
                
            if disaster_id:
                message_data['disaster_id'] = disaster_id
                
            message_id = Message.create(message_data)
            
            # Send WhatsApp message via API
            url = "https://api.whatsapp.com/v1/messages"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to_number,
                "type": "text",
                "text": {
                    "body": message_text
                }
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                response_data = response.json()
                external_message_id = response_data.get('messages', [{}])[0].get('id')
                Message.update_status(message_id, Message.STATUS_SENT, external_message_id)
                return True, message_id
            else:
                Message.update_status(message_id, Message.STATUS_FAILED)
                return False, message_id
                
        except Exception as e:
            if 'message_id' in locals():
                Message.update_status(message_id, Message.STATUS_FAILED)
            return False, str(e)
    
    @staticmethod
    def send_telegram(chat_id, message_text, employee_id=None, disaster_id=None):
        """Send Telegram message using Telegram Bot API"""
        try:
            # Güncel config değerini al
            bot_token = current_app.config.get('TELEGRAM_BOT_TOKEN')
            
            # Config'den gelen token eğer yer tutucu ise gerçek token'ı kullan
            if not bot_token or bot_token == 'your-telegram-bot-token' or bot_token == 'development-telegram-token':
                # Geçici çözüm - gerçek token'ı doğrudan kullan
                bot_token = "BURAYA_BOT_TOKENI_GELECEK_TELEGRAM"
                print(f"UYARI: Yapılandırmadan Telegram token alınamadı, statik token kullanılıyor")
            
            print(f"DEBUG: Telegram mesajı gönderiliyor: chat_id={chat_id}, token={bot_token[:5]}...{bot_token[-5:]}")
            
            # Create message record in database
            message_data = {
                'channel': Message.CHANNEL_TELEGRAM,
                'to': chat_id,
                'from': 'TelegramBot',
                'content': message_text,
                'type': Message.TYPE_STATUS_CHECK
            }
            
            if employee_id:
                message_data['employee_id'] = employee_id
                
            if disaster_id:
                message_data['disaster_id'] = disaster_id
                
            message_id = Message.create(message_data)
            
            # Send Telegram message via API
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message_text,
                "parse_mode": "HTML"
            }
            
            print(f"DEBUG: Telegram API isteği gönderiliyor: {url}")
            response = requests.post(url, json=payload)
            
            if response.status_code == 200:
                response_data = response.json()
                external_message_id = response_data.get('result', {}).get('message_id')
                Message.update_status(message_id, Message.STATUS_SENT, external_message_id)
                print(f"DEBUG: Telegram API başarılı yanıt: {response_data}")
                return True, message_id
            else:
                Message.update_status(message_id, Message.STATUS_FAILED)
                print(f"HATA: Telegram API başarısız yanıt: {response.status_code} - {response.text}")
                return False, message_id
                
        except Exception as e:
            print(f"KRİTİK HATA: Telegram mesaj gönderirken istisna: {str(e)}")
            if 'message_id' in locals():
                Message.update_status(message_id, Message.STATUS_FAILED)
            return False, str(e)
    
    @staticmethod
    def send_sms(to_number, message_text, employee_id=None, disaster_id=None):
        """Send SMS using Twilio"""
        try:
            # Güncel config değerlerini al
            account_sid = current_app.config.get('TWILIO_ACCOUNT_SID')
            auth_token = current_app.config.get('TWILIO_AUTH_TOKEN')
            from_number = current_app.config.get('TWILIO_PHONE_NUMBER')
            
            if not account_sid or not auth_token or not from_number:
                raise ValueError("Twilio API ayarları yapılandırılmamış")
            
            # Create message record in database
            message_data = {
                'channel': Message.CHANNEL_SMS,
                'to': to_number,
                'from': from_number,
                'content': message_text,
                'type': Message.TYPE_STATUS_CHECK
            }
            
            if employee_id:
                message_data['employee_id'] = employee_id
                
            if disaster_id:
                message_data['disaster_id'] = disaster_id
                
            message_id = Message.create(message_data)
            
            # Send SMS via Twilio
            client = Client(account_sid, auth_token)
            
            message = client.messages.create(
                body=message_text,
                from_=from_number,
                to=to_number
            )
            
            Message.update_status(message_id, Message.STATUS_SENT, message.sid)
            return True, message_id
                
        except Exception as e:
            if 'message_id' in locals():
                Message.update_status(message_id, Message.STATUS_FAILED)
            return False, str(e)
    
    @staticmethod
    def send_bulk_messages(employee_list, message_text, channel, disaster_id=None):
        """Send messages to multiple employees"""
        results = {
            'success': 0,
            'failed': 0,
            'message_ids': []
        }
        
        for employee in employee_list:
            success = False
            message_id = None
            
            if channel == Message.CHANNEL_WHATSAPP and 'phone' in employee:
                success, message_id = MessageSender.send_whatsapp(
                    employee['phone'], 
                    message_text, 
                    employee_id=str(employee['_id']), 
                    disaster_id=disaster_id
                )
            
            elif channel == Message.CHANNEL_TELEGRAM and 'telegram_id' in employee:
                success, message_id = MessageSender.send_telegram(
                    employee['telegram_id'], 
                    message_text, 
                    employee_id=str(employee['_id']), 
                    disaster_id=disaster_id
                )
            
            elif channel == Message.CHANNEL_SMS and 'phone' in employee:
                success, message_id = MessageSender.send_sms(
                    employee['phone'], 
                    message_text, 
                    employee_id=str(employee['_id']), 
                    disaster_id=disaster_id
                )
            
            if success:
                results['success'] += 1
            else:
                results['failed'] += 1
                
            if message_id:
                results['message_ids'].append(message_id)
                
        return results
    
    @staticmethod
    def send_messages_by_region(regions, message_text, channel, disaster_id=None):
        """Belirli bölgelerdeki tüm çalışanlara mesaj gönder"""
        # Bölgedeki çalışanları bul
        if isinstance(regions, str):
            regions = [regions]  # Tek bölge gönderilmişse liste haline getir
            
        employees = Employee.get_by_regions(regions)
        
        # Çalışanlara mesaj gönder
        return MessageSender.send_bulk_messages(employees, message_text, channel, disaster_id)
    
    @staticmethod
    def send_messages_by_cities(cities, message_text, channel, disaster_id=None):
        """Belirli şehirlerdeki tüm çalışanlara mesaj gönder"""
        # Şehirlerdeki çalışanları bul
        if isinstance(cities, str):
            cities = [cities]  # Tek şehir gönderilmişse liste haline getir
            
        employees = Employee.get_by_cities(cities)
        
        # Çalışanlara mesaj gönder
        return MessageSender.send_bulk_messages(employees, message_text, channel, disaster_id)
    
    @staticmethod
    def send_messages_by_status(status, message_text, channel, disaster_id=None):
        """Belirli durumda olan tüm çalışanlara mesaj gönder"""
        # Duruma göre çalışanları bul
        employees = Employee.search(status=status)
        
        # Çalışanlara mesaj gönder
        return MessageSender.send_bulk_messages(employees, message_text, channel, disaster_id) 
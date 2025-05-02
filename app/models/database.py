from pymongo import MongoClient
from flask import current_app
import logging

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        
    def connect(self):
        if not self.client:
            try:
                mongo_uri = current_app.config['MONGODB_URI']
                print(f"MongoDB'ye bağlanılıyor: {mongo_uri}")
                self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
                # Bağlantıyı test et
                self.client.admin.command('ping')
                self.db = self.client.get_database()
                print("MongoDB bağlantısı başarılı!")
            except Exception as e:
                print(f"MongoDB bağlantı hatası: {e}")
                # Hata durumunda varsayılan olarak None döndürmek yerine bir hata fırlat
                # Bu, hatanın göz ardı edilmesini önler
                raise
        return self.db
    
    def close(self):
        if self.client:
            self.client.close()
            self.client = None
            self.db = None

# Singleton instance
db = Database() 
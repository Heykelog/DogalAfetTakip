from flask import Flask
from app.config.config import Config
from app.routes.main import main
from app.routes.auth import auth
from app.routes.dashboard import dashboard
from app.routes.api import api

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    with app.app_context():
        # Veritabanından API ayarlarını yükle
        try:
            config_class.load_db_settings()
        except Exception as e:
            print(f"Veritabanı ayarlarını yükleme hatası: {e}")
    
    # Geliştirme için yapılandırma bilgilerini yazdır
    config_class.print_config()
    
    # Register blueprints
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(dashboard)
    app.register_blueprint(api)
    
    print("Flask uygulaması hazır! Blueprints kaydedildi.")
    
    return app 
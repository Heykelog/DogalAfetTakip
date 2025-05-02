# Afet - Kurulum ve Kullanım Kılavuzu

Bu belge, Afet Anında Otomatik WhatsApp Durum Takip Sistemi'nin kurulumu ve kullanımı için adım adım talimatlar içerir.

## Gereksinimler

* Python 3.8 veya üstü
* MongoDB
* WhatsApp Business API erişimi
* Internet erişimi

## Kurulum

### 1. Kod Deposunu İndirin

```bash
git clone https://github.com/your-username/afet.git
cd afet
```

### 2. Sanal Ortam Oluşturun ve Etkinleştirin

Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

Linux/MacOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Bağımlılıkları Yükleyin

```bash
pip install -r requirements.txt
```

### 4. Çevre Değişkenlerini Yapılandırın

`.env.example` dosyasını `.env` olarak kopyalayın ve kendi ayarlarınızla düzenleyin:

```bash
cp .env.example .env
```

`.env` dosyasını düzenleyin ve aşağıdaki bilgileri girin:

```
# Flask Settings
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=kendi_gizli_anahtariniz
PORT=5000

# MongoDB Settings
MONGO_URI=mongodb://localhost:27017/afet_db

# WhatsApp Business API Settings
WHATSAPP_API_TOKEN=whatsapp_api_tokeniniz
WHATSAPP_PHONE_NUMBER_ID=telefon_numarasi_id
WHATSAPP_BUSINESS_ACCOUNT_ID=iş_hesabı_id
WHATSAPP_WEBHOOK_VERIFY_TOKEN=webhook_doğrulama_token

# Company Information
COMPANY_NAME=Şirket Adınız
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin_sifresi
```

### 5. MongoDB'yi Kurun ve Başlatın

MongoDB'yi [resmi belgelerinden](https://docs.mongodb.com/manual/installation/) indirin ve yükleyin.

MongoDB hizmetini başlatın:

Windows:
```bash
mongod
```

Linux/MacOS:
```bash
sudo systemctl start mongod
```

### 6. Uygulamayı Çalıştırın

```bash
python app.py
```

Uygulama şu adreste çalışacaktır: [http://localhost:5000](http://localhost:5000)

## WhatsApp Business API Entegrasyonu

WhatsApp Business API'yi kullanmak için:

1. [Facebook Developers Portal](https://developers.facebook.com/)'da bir hesap oluşturun
2. WhatsApp Business API kurulumunu yapın
3. Webhook'u kurun ve yapılandırın:
   - Webhook URL: `https://sizin-alan-adiniz.com/webhook`
   - Doğrulama Tokeni: `.env` dosyasında belirlediğiniz `WHATSAPP_WEBHOOK_VERIFY_TOKEN`
4. Gerekli izinleri etkinleştirin
5. API token ve diğer kimlik doğrulama bilgilerini `.env` dosyasına ekleyin

## Sistem Kullanımı

### Admin Paneline Giriş

1. Web tarayıcınızdan [http://localhost:5000](http://localhost:5000) adresine gidin
2. `.env` dosyasında belirlediğiniz `ADMIN_USERNAME` ve `ADMIN_PASSWORD` ile giriş yapın

### Çalışan Yönetimi

1. "Çalışanlar" sekmesine tıklayın
2. "Yeni Çalışan" düğmesine tıklayarak yeni çalışanlar ekleyin:
   - Ad Soyad
   - WhatsApp telefon numarası (uluslararası formatta: +905551234567)
   - Departman

### Durum Sorgulama Mesajı Gönderme

1. "Mesaj Gönder" sekmesine tıklayın
2. Afet türünü seçin (Deprem, Sel, Yangın vb.)
3. Alıcıları seçin: Tüm çalışanlar veya Seçilen çalışanlar
4. "Mesaj Gönder" düğmesine tıklayın

### Durum Takibi

Dashboard ekranında:
- Toplam çalışan sayısı
- Güvende olan çalışanlar
- Acil durumda olanlar
- Tıbbi yardım ihtiyacı olanlar

Acil durum listesinde enkaz altında veya tıbbi yardım ihtiyacı olan çalışanları görebilir ve durum güncellemelerini takip edebilirsiniz.

## Sorun Giderme

1. **MongoDB Bağlantı Hatası**: MongoDB'nin çalıştığından ve `.env` dosyasındaki bağlantı dizesinin doğru olduğundan emin olun.

2. **WhatsApp API Hatası**: WhatsApp Business API kimlik bilgilerinizi kontrol edin ve API erişiminizin etkin olduğundan emin olun.

3. **Webhook Sorunları**: Webhook URL'nizin internet üzerinden erişilebilir olduğundan emin olun. Yerel geliştirme için [ngrok](https://ngrok.com/) kullanabilirsiniz.

## Güvenlik Notları

- Üretim ortamında, güçlü bir SECRET_KEY kullanın
- ADMIN_PASSWORD'ü güçlü bir şifre olarak ayarlayın
- Hassas bilgileri .env dosyasında saklayın ve bu dosyayı asla kod deposuna dahil etmeyin
- Üretim ortamında HTTPS kullanın

## Sistem Mimarisi

```
+----------------+    +----------------+    +----------------+
|                |    |                |    |                |
| Çalışan Mobili |    |   Web Tarayıcı |    |  Admin Paneli  |
| (WhatsApp)     |    |                |    |                |
+-------+--------+    +--------+-------+    +-------+--------+
        |                      |                    |
        v                      v                    v
+-------+-----------------------------------------+--------+
|                                                          |
|                       Flask Uygulama                     |
|                                                          |
+---------+------------------------+---------------------+-+
          |                        |                     |
          v                        v                     v
  +-------+------+         +-------+-------+      +------+-------+
  |              |         |               |      |              |
  | WhatsApp API |         |   MongoDB     |      |  Frontend    |
  |              |         |               |      |              |
  +--------------+         +---------------+      +--------------+
```

## İleri Düzey Yapılandırma

### Nginx ile Dağıtım

Üretim ortamında Nginx ile dağıtım için örnek yapılandırma:

```nginx
server {
    listen 80;
    server_name sizin-alan-adiniz.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Gunicorn ile Çalıştırma

```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Sistem Servisi Olarak Yapılandırma

`/etc/systemd/system/afet.service` dosyası oluşturun:

```
[Unit]
Description=Afet WhatsApp Durum Takip Sistemi
After=network.target

[Service]
User=your-username
WorkingDirectory=/path/to/afet
ExecStart=/path/to/afet/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Servisi etkinleştirin ve başlatın:

```bash
sudo systemctl enable afet
sudo systemctl start afet
``` 
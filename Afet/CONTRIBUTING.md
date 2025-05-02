# Katkıda Bulunma Rehberi

Afet Anında Otomatik WhatsApp Durum Takip Sistemi'ne katkıda bulunmak istediğiniz için teşekkür ederiz. Bu belge, projeye nasıl katkıda bulunabileceğinizi açıklar.

## Katkıda Bulunma Süreci

1. Bu depoyu forklayın
2. Kendi dalınızı oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add some amazing feature'`)
4. Dalınızı push edin (`git push origin feature/amazing-feature`)
5. Bir Pull Request açın

## Geliştirme Ortamını Kurma

Bu projeyi yerel makinenizde çalıştırmak için [GETTING_STARTED.md](GETTING_STARTED.md) dosyasındaki adımları izleyin.

## Kod Stili

Bu projede aşağıdaki kod stillerine uyuyoruz:

- Python kodu için [PEP 8](https://www.python.org/dev/peps/pep-0008/) kuralları
- JavaScript için [StandardJS](https://standardjs.com/) kuralları
- HTML ve CSS için [W3C standartları](https://www.w3.org/standards/webdesign/htmlcss)

Kod formatlaması için şu araçları kullanabilirsiniz:
- Python: `black` ve `flake8`
- JavaScript: `eslint` ve `prettier`

## Özellik İstekleri

Yeni bir özellik önermek için:

1. Özelliğinizin mevcut bir issue ile ilgili olup olmadığını kontrol edin
2. Eğer yoksa, yeni bir issue oluşturun ve "enhancement" etiketi ekleyin

## Hata Raporları

Bir hata raporu oluştururken:

1. Hatayı net bir şekilde açıklayın
2. Hatayı nasıl yeniden oluşturabileceğimizi adım adım belirtin
3. Gerçek ve beklenen davranışı açıklayın
4. Mümkünse ekran görüntüleri veya kayıtlar ekleyin

## Dokümantasyon

Dokümantasyon güncellemeleri de önemli katkılardır:

- README.md veya GETTING_STARTED.md dosyalarındaki bilgileri güncelleyin
- API belgelerini güncel tutun
- Kod içi yorumlar ekleyin

## Test

Yeni özellikler veya hata düzeltmeleri eklerken:

- Birim testleri ekleyin
- Mevcut testlerin başarılı olduğundan emin olun
- Ek olarak entegrasyon testleri yazın (gerekirse)

## Branch Stratejisi

- `main`: Stabil, yayın sürümünü içerir
- `develop`: Ana geliştirme dalı
- `feature/*`: Yeni özellikler için
- `bugfix/*`: Hata düzeltmeleri için
- `release/*`: Yayın hazırlığı için

## İletişim

Sorularınız veya önerileriniz için:

- GitHub issues kullanın
- [example@email.com](mailto:example@email.com) adresine e-posta gönderin

## Lisans

Bu projeye katkıda bulunarak, katkılarınızın projenin lisansı altında yayınlanacağını kabul etmiş olursunuz. 
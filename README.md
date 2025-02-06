# HepsiEmlak Scraper

Modern web teknolojileri kullanılarak geliştirilmiş, HepsiEmlak üzerinden emlak ilanlarını toplayan ve yöneten bir web uygulaması.

## 🚀 Özellikler

- **Otomatik Veri Toplama**
  - HepsiEmlak üzerinden emlak ilanlarını otomatik toplama
  - Akıllı sayfalama ve filtreleme sistemi
  - Anti-bot korumalı scraping altyapısı

- **Modern Web Arayüzü**
  - React ve Material-UI ile geliştirilmiş kullanıcı dostu arayüz
  - Responsive tasarım
  - Gelişmiş filtreleme ve arama özellikleri

- **Güçlü Backend**
  - FastAPI ile yüksek performanslı REST API
  - SQLAlchemy ORM ile veritabanı yönetimi
  - PostgreSQL veritabanı desteği

## 🛠️ Teknolojiler

### Backend
- Python 3.x
- FastAPI
- SQLAlchemy
- PostgreSQL
- BeautifulSoup4
- Selenium/Undetected Chromedriver

### Frontend
- React
- TypeScript
- Material-UI
- React Query
- Axios

## 📋 Gereksinimler

- Python 3.8+
- Node.js 14+
- PostgreSQL
- Chrome Browser

## 🔧 Kurulum

### Backend Kurulumu

```bash
# Repo'yu klonlayın
git clone https://github.com/ogulcanodemis/hepsi-emlak-scraper.git
cd hepsi-emlak-scraper

# Virtual environment oluşturun
python -m venv venv
source venv/bin/activate  # Linux/Mac için
.\venv\Scripts\activate   # Windows için

# Bağımlılıkları yükleyin
pip install -r requirements.txt

# Veritabanını oluşturun
alembic upgrade head

# Backend'i başlatın
uvicorn src.main:app --reload
```

### Frontend Kurulumu

```bash
# Frontend dizinine gidin
cd frontend

# Bağımlılıkları yükleyin
npm install

# Uygulamayı başlatın
npm start
```

### Ortam Değişkenleri

`.env` dosyası oluşturun ve aşağıdaki değişkenleri ekleyin:

```env
DATABASE_URL=postgresql://postgres:1234@localhost:5432/hepsiemlak_db
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000
```

## 📱 Kullanım

1. Backend ve Frontend uygulamalarını başlatın
2. Tarayıcıda `http://localhost:3000` adresine gidin
3. HepsiEmlak arama URL'sini girin
4. Veri toplama işlemini başlatın
5. Toplanan ilanları görüntüleyin ve filtreleyin

## 🔍 API Endpoints

- `GET /properties`: İlanları listeler
- `GET /properties/{id}`: İlan detaylarını getirir
- `POST /scrape`: Yeni veri toplama işlemi başlatır
- `GET /search-history`: Arama geçmişini listeler

## 🎯 Özellikler

### Veri Toplama
- İlan başlığı ve açıklaması
- Fiyat bilgisi
- Konum bilgisi
- İlan özellikleri
- Emlak ofisi bilgileri
- İlan görselleri

### Filtreleme
- Anahtar kelime araması
- Fiyat aralığı
- Konum bazlı filtreleme
- Özellik bazlı filtreleme

## 🤝 Katkıda Bulunma

1. Bu repo'yu fork edin
2. Yeni bir branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add some amazing feature'`)
4. Branch'inizi push edin (`git push origin feature/amazing-feature`)
5. Pull Request oluşturun

## 📝 Lisans

Bu proje MIT lisansı altında lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına bakın.

## 👥 Yazarlar

- **Oğulcan Ödemiş** - [GitHub](https://github.com/ogulcanodemis)

## 🙏 Teşekkürler

- HepsiEmlak'a veri kaynağı olduğu için
- Tüm açık kaynak kütüphanelerin geliştiricilerine 
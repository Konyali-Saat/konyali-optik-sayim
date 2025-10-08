# 📦 Konyalı Optik Sayım Sistemi

Envanter sayım sistemi - Barkod okutarak ürün eşleştirme ve kayıt.

## 🎯 Özellikler

- ✅ Barkod okutma ve otomatik eşleştirme
- ✅ Direkt / Belirsiz / Bulunamadı akışları
- ✅ Manuel ürün arama
- ✅ Marka/Kategori bağlamı (context)
- ✅ Fuzzy matching (benzer barkodlar)
- ✅ Günlük istatistikler
- ✅ Responsive design (tablet optimized)
- ✅ Airtable entegrasyonu
- ✅ RESTful API
- ✅ Cloud Run ready

## 🏗️ Teknoloji Stack

**Backend:**
- Python 3.11
- Flask 3.1
- pyairtable 3.2
- fuzzywuzzy (barkod matching)

**Frontend:**
- Vanilla JavaScript (no framework)
- Modern CSS3
- Responsive design

**Database:**
- Airtable

**Deployment:**
- Google Cloud Run
- Docker

## 📁 Proje Yapısı

```
konyali-optik-sayim/
├── backend/
│   ├── app.py                 # Flask API
│   ├── airtable_client.py     # Airtable işlemleri
│   ├── matcher.py             # Barkod eşleştirme
│   ├── requirements.txt       # Python bağımlılıklar
│   ├── Dockerfile             # Docker config
│   └── .env                   # Environment variables
│
├── frontend/
│   ├── index.html             # Ana sayfa
│   ├── styles.css             # Stil
│   └── app.js                 # JavaScript
│
├── docs/
│   └── ...                    # Dokümanlar
│
├── README.md                  # Bu dosya
└── DEPLOYMENT.md              # Deploy rehberi
```

## 🚀 Hızlı Başlangıç

### 1. Gereksinimler

- Python 3.11+
- pip
- Airtable hesabı ve token

### 2. Backend Kurulum

```bash
cd backend

# Sanal ortam oluştur
python -m venv venv

# Aktifleştir (Windows)
venv\Scripts\activate

# Aktifleştir (macOS/Linux)
source venv/bin/activate

# Bağımlılıkları yükle
pip install -r requirements.txt

# .env dosyasını düzenle
# AIRTABLE_TOKEN ve AIRTABLE_BASE_ID'yi ekle
```

### 3. Çalıştır

```bash
cd backend
python app.py
```

Tarayıcıda aç: **http://localhost:5000**

## 🔧 Environment Variables

Backend klasöründe `.env` dosyası oluştur:

```env
AIRTABLE_TOKEN=patXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
AIRTABLE_BASE_ID=appXXXXXXXXXXXXXX
FLASK_ENV=development
FLASK_DEBUG=True
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## 📊 Airtable Yapısı

### Tablolar

1. **Master_SKU** - Ana ürün kataloğu
2. **Tedarikci_Urun_Listesi** - Tedarikçi barkodları
3. **Sayim_Kayitlari** - Sayım kayıtları
4. **Markalar** - Marka listesi
5. **Stok_Kalemleri** - Stok takip

### Gerekli Field'lar

**Master_SKU:**
- SKU (primary)
- Kategori (OF/GN/CM/LN)
- Marka (link)
- Model_Kodu
- Model_Adi
- Renk_Kodu, Renk_Adi
- Ekartman

**Tedarikci_Urun_Listesi:**
- Tedarikci_Barkodu (arama için)
- Master_SKU (link)
- Tedarikci (link)

**Sayim_Kayitlari:**
- Okutulan_Barkod
- SKU (link)
- Eslesme_Durumu (Direkt/Belirsiz/Bulunamadı)
- Durum (Tamamlandı/İnceleme Gerekli)
- Timestamp (auto)

## 🔍 API Endpoints

### Health Check
```
GET /api/health
```

### Barkod Arama
```
POST /api/search-barcode
Body: {
  "barkod": "8056597412261",
  "context_brand": "recXXXXXX" (optional),
  "context_category": "OF" (optional)
}
```

### Manuel Arama
```
POST /api/search-manual
Body: {
  "term": "2140",
  "context_brand": "recXXXXXX" (optional),
  "context_category": "OF" (optional)
}
```

### Sayım Kaydet
```
POST /api/save-count
Body: {
  "barkod": "8056597412261",
  "sku_id": "recXXXXXX",
  "eslesme_durumu": "Direkt",
  "tedarikci_kaydi_id": "recXXXXXX",
  "context_brand": "recXXXXXX" (optional),
  "context_category": "OF" (optional)
}
```

### Markalar
```
GET /api/brands
```

### İstatistikler
```
GET /api/stats
```

## 🎯 Kullanım

1. **Bağlam Seç (Opsiyonel):**
   - Marka ve/veya kategori seç
   - Arama sonuçlarını filtreler

2. **Barkod Okut:**
   - Barkod okuyucu ile okut veya manuel gir
   - "ARA" tıkla

3. **Sonuç:**
   - **Direkt:** Tek eşleşme bulundu → Onayla ve kaydet
   - **Belirsiz:** Çoklu eşleşme → Doğru olanı seç
   - **Bulunamadı:** → Manuel ara veya atla

4. **İstatistikler:**
   - Altta günlük sayım özeti görünür

## 🧪 Test

### Backend Test
```bash
cd backend
python airtable_client.py  # Airtable bağlantısı test
python matcher.py          # Matcher test (interaktif)
```

### API Test
```bash
# Health check
curl http://localhost:5000/api/health

# Brands
curl http://localhost:5000/api/brands

# Stats
curl http://localhost:5000/api/stats
```

## 🚢 Deployment

**ÖNEMLİ:** Deployment komutunu projenin ana dizininde (`konyali-optik-sayim` klasöründe) çalıştırdığınızdan emin olun. `backend` klasörüne girmeyin.

```bash
# Projenin ana dizininde olduğunuzdan emin olun.
# Make sure you are in the main directory of the project.

# Cloud Run'a deploy
gcloud run deploy konyali-optik-sayim \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated \
  --project <PROJE_ID> \
  --set-env-vars AIRTABLE_TOKEN=<AIRTABLE_TOKEN>,AIRTABLE_BASE_ID=<AIRTABLE_BASE_ID>
```

**Not:** `DEPLOYMENT.md` dosyası güncel değildir. Lütfen bu bölümdeki komutları kullanın.

## 🔒 Güvenlik

- `.env` dosyasını git'e commit etmeyin
- Airtable token'ları güvende tutun
- Production'da CORS ayarlarını daraltın
- HTTPS kullanın (Cloud Run otomatik sağlar)

## 📝 Notlar

- Barkod eşleştirme %85+ benzerlikte fuzzy match yapar
- Context seçimi çoklu sonuçları azaltır
- Günlük istatistikler Airtable CREATED_TIME'a göre hesaplanır
- Offline çalışma şu an desteklenmiyor (gelecek sürüm)

## 🐛 Sorun Giderme

**Airtable bağlantı hatası:**
- Token'ı kontrol et
- Base ID'yi kontrol et
- API limitlerini kontrol et

**Port hatası:**
- Port 5000 kullanımda mı kontrol et
- Başka port dene: `PORT=8000 python app.py`

**Frontend açılmıyor:**
- Backend çalışıyor mu kontrol et
- CORS ayarlarını kontrol et

## 📄 Lisans

Bu proje Konyalı Optik için özel olarak geliştirilmiştir.

## 👤 İletişim

Teknik destek için: Claude Code ile geliştirme yapıldı.

---

**Versiyon:** 1.0.0
**Son Güncelleme:** 2025-10-07

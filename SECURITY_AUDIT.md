# 🔒 Security Audit - Konyalı Optik Sayım Sistemi

**Tarih:** 31 Ekim 2025  
**Versiyon:** 2.0.0  
**Audit Türü:** Kapsamlı Güvenlik İncelemesi

---

## 📊 Genel Güvenlik Skoru: 7/10

**Durum:** ⚠️ Orta Seviye Güvenlik (Production için iyileştirme gerekli)

---

## ✅ Güvenli Alanlar

### 1. ✅ SQL Injection Riski Yok
**Sebep:** Airtable kullanılıyor (NoSQL)  
**Risk Seviyesi:** 🟢 Düşük

### 2. ✅ Şifre Yönetimi Yok
**Sebep:** Airtable token ile authentication  
**Risk Seviyesi:** 🟢 Düşük

### 3. ✅ HTTPS Desteği
**Sebep:** Cloud Run otomatik HTTPS sağlıyor  
**Risk Seviyesi:** 🟢 Düşük

---

## ⚠️ Güvenlik Riskleri

### 🔴 KRİTİK RİSKLER

#### 1. CORS Wildcard (Production)

**Sorun:**
```python
# app.py:29-30
allowed_origins = os.getenv('ALLOWED_ORIGINS', '*').split(',')
CORS(app, origins=allowed_origins)
```

**Risk:**
- CSRF saldırıları
- Unauthorized access
- Data leakage

**Çözüm:**
```python
# Production .env
ALLOWED_ORIGINS=https://sayim.konyalioptik.com,https://admin.konyalioptik.com

# app.py - Validation ekle
if os.getenv('FLASK_ENV') == 'production':
    if '*' in allowed_origins:
        raise ValueError("❌ Production'da ALLOWED_ORIGINS=* kullanılamaz!")
```

**Öncelik:** 🔴 YÜKSEK  
**CVSS Score:** 7.5 (High)

---

#### 2. Rate Limiting Yok

**Sorun:** API abuse koruması yok

**Risk:**
- DDoS saldırıları
- Brute force attacks
- API quota tüketimi

**Çözüm:**
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

@app.route('/api/search-barcode', methods=['POST'])
@limiter.limit("10 per minute")
def search_barcode():
    # ...
```

**Öncelik:** 🔴 YÜKSEK  
**CVSS Score:** 6.5 (Medium)

---

#### 3. Input Validation Eksik

**Sorun:** User input sanitization yetersiz

**Örnek:**
```python
# app.py:146
barkod = data.get('barkod', '').strip()
# Sadece strip() yapılıyor, validation yok
```

**Risk:**
- Formula injection (Airtable)
- XSS (frontend'de)
- Data corruption

**Çözüm:**
```python
import re

def validate_barcode(barkod: str) -> bool:
    """Barkod formatını validate et"""
    # Sadece rakam ve harf, 8-20 karakter
    if not re.match(r'^[A-Za-z0-9]{8,20}$', barkod):
        return False
    return True

# Kullanım
barkod = data.get('barkod', '').strip()
if not validate_barcode(barkod):
    return jsonify({'error': 'Geçersiz barkod formatı'}), 400
```

**Öncelik:** 🟡 ORTA  
**CVSS Score:** 5.5 (Medium)

---

### 🟡 ORTA RİSKLER

#### 4. Airtable Token Exposure

**Sorun:** Token `.env` dosyasında plain text

**Risk:**
- Token leak (git commit)
- Unauthorized database access

**Çözüm:**
```bash
# 1. .gitignore'a ekle (zaten var ✅)
.env

# 2. Secret Manager kullan (Production)
# Google Cloud Secret Manager
gcloud secrets create airtable-token --data-file=token.txt

# 3. Environment'tan yükle
export AIRTABLE_TOKEN=$(gcloud secrets versions access latest --secret="airtable-token")
```

**Öncelik:** 🟡 ORTA  
**CVSS Score:** 5.0 (Medium)

---

#### 5. Error Message Information Disclosure

**Sorun:** Detaylı error mesajları döndürülüyor

**Örnek:**
```python
# app.py:166
return jsonify({'error': f'Arama hatası: {str(e)}'}), 500
```

**Risk:**
- Stack trace leak
- Internal structure exposure

**Çözüm:**
```python
# Production'da generic error
if os.getenv('FLASK_DEBUG') == 'True':
    return jsonify({'error': f'Arama hatası: {str(e)}'}), 500
else:
    logger.error(f"Arama hatası: {e}")
    return jsonify({'error': 'Bir hata oluştu'}), 500
```

**Öncelik:** 🟡 ORTA  
**CVSS Score:** 4.5 (Medium)

---

#### 6. No Request Logging

**Sorun:** API request'leri loglanmıyor

**Risk:**
- Audit trail yok
- Security incident investigation zor

**Çözüm:**
```python
from flask import request
import logging

@app.before_request
def log_request():
    """Her request'i logla"""
    logger.info(f"Request: {request.method} {request.path}", extra={
        'ip': request.remote_addr,
        'user_agent': request.user_agent.string,
        'category': request.json.get('category') if request.json else None
    })
```

**Öncelik:** 🟡 ORTA  
**CVSS Score:** 4.0 (Medium)

---

### 🟢 DÜŞÜK RİSKLER

#### 7. No Authentication

**Sorun:** API endpoint'leri public

**Risk:**
- Anyone can access
- No user tracking

**Not:** Şu an internal use için sorun değil, ama production'da authentication eklenebilir.

**Çözüm (Gelecek):**
```python
from functools import wraps
from flask import request

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or api_key != os.getenv('API_KEY'):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/search-barcode', methods=['POST'])
@require_api_key
def search_barcode():
    # ...
```

**Öncelik:** 🟢 DÜŞÜK  
**CVSS Score:** 3.0 (Low)

---

## 🛡️ Güvenlik Best Practices

### 1. Environment Variables

**✅ Yapılması Gerekenler:**
- [ ] `.env` dosyası `.gitignore`'da (✅ zaten var)
- [ ] Production'da Secret Manager kullan
- [ ] Token rotation policy (3 ayda bir)
- [ ] Minimum privilege principle

---

### 2. HTTPS/TLS

**✅ Yapılması Gerekenler:**
- [ ] HTTPS zorunlu (Cloud Run otomatik ✅)
- [ ] HTTP → HTTPS redirect
- [ ] HSTS header ekle
- [ ] TLS 1.2+ zorunlu

**Çözüm:**
```python
from flask_talisman import Talisman

# HTTPS enforcement
Talisman(app, force_https=True)
```

---

### 3. Input Sanitization

**✅ Yapılması Gerekenler:**
- [ ] Barcode validation
- [ ] SKU format validation
- [ ] Category whitelist
- [ ] Max length checks

**Çözüm:**
```python
VALID_CATEGORIES = ['OF', 'GN', 'LN']

def validate_category(category: str) -> bool:
    return category in VALID_CATEGORIES

def validate_barcode(barkod: str) -> bool:
    # 8-20 karakter, sadece alphanumeric
    return bool(re.match(r'^[A-Za-z0-9]{8,20}$', barkod))
```

---

### 4. Security Headers

**✅ Yapılması Gerekenler:**
- [ ] X-Content-Type-Options
- [ ] X-Frame-Options
- [ ] X-XSS-Protection
- [ ] Content-Security-Policy

**Çözüm:**
```python
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response
```

---

## 🔍 Penetration Testing Checklist

### API Endpoints

- [ ] **SQL Injection** - N/A (Airtable)
- [ ] **XSS** - Test frontend inputs
- [ ] **CSRF** - Test CORS config
- [ ] **Rate Limiting** - Test API abuse
- [ ] **Authentication** - Test unauthorized access
- [ ] **Authorization** - Test category isolation
- [ ] **Input Validation** - Test malformed inputs
- [ ] **Error Handling** - Test information disclosure

---

## 📊 OWASP Top 10 (2021) Compliance

| Risk | Status | Notes |
|------|--------|-------|
| A01:2021 - Broken Access Control | ⚠️ | No authentication |
| A02:2021 - Cryptographic Failures | ✅ | HTTPS enforced |
| A03:2021 - Injection | ⚠️ | Formula injection risk |
| A04:2021 - Insecure Design | ✅ | Good architecture |
| A05:2021 - Security Misconfiguration | ⚠️ | CORS wildcard |
| A06:2021 - Vulnerable Components | ✅ | Dependencies up-to-date |
| A07:2021 - Authentication Failures | ⚠️ | No authentication |
| A08:2021 - Software and Data Integrity | ✅ | No CI/CD issues |
| A09:2021 - Logging Failures | ⚠️ | Insufficient logging |
| A10:2021 - SSRF | ✅ | No external requests |

**Compliance Score:** 6/10 ⚠️

---

## 🎯 Öncelikli Aksiyonlar

### Sprint 1 (1 hafta) - KRİTİK

1. **CORS Configuration**
   ```python
   # Production'da wildcard kaldır
   ALLOWED_ORIGINS=https://sayim.konyalioptik.com
   ```

2. **Rate Limiting**
   ```bash
   pip install Flask-Limiter
   ```

3. **Input Validation**
   ```python
   def validate_barcode(barkod: str) -> bool:
       return bool(re.match(r'^[A-Za-z0-9]{8,20}$', barkod))
   ```

### Sprint 2 (1 hafta) - YÜKSEK

4. **Logging Enhancement**
5. **Security Headers**
6. **Error Message Sanitization**

### Sprint 3 (2 hafta) - ORTA

7. **Authentication (Optional)**
8. **Secret Manager Integration**
9. **Penetration Testing**

---

## 📝 Sonuç

**Mevcut Durum:** ⚠️ Orta Seviye Güvenlik (7/10)

**Production Hazırlığı:** Sprint 1 ve 2 tamamlandıktan sonra ✅

**Tavsiye:**
- Sprint 1 aksiyonlarını hemen uygula
- Penetration testing yaptır
- Security monitoring kur (Sentry)

---

**Hazırlayan:** Security Audit System  
**Tarih:** 31 Ekim 2025  
**Sonraki Audit:** 3 ay sonra


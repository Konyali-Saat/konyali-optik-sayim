# ⚡ Performance Test Plan - Konyalı Optik Sayım Sistemi

**Tarih:** 31 Ekim 2025  
**Versiyon:** 2.0.0  
**Test Türü:** Performance & Load Testing

---

## 🎯 Performans Hedefleri

### Backend API

| Endpoint | Hedef Süre | Max Süre | Concurrent Users |
|----------|------------|----------|------------------|
| `/api/search-barcode` | <500ms | 1s | 10 |
| `/api/search-manual` | <800ms | 1.5s | 5 |
| `/api/save-count` | <300ms | 800ms | 10 |
| `/api/brands` | <200ms | 500ms | 20 |
| `/api/stats` | <200ms | 500ms | 20 |

### Frontend

| Metrik | Hedef | Max |
|--------|-------|-----|
| First Paint | <300ms | 500ms |
| Time to Interactive | <800ms | 1s |
| Total Page Load | <2s | 3s |

---

## 🔧 Test Araçları

### 1. Backend Load Testing

**Tool:** Apache Bench (ab) veya Locust

```bash
# Apache Bench kurulum
# Ubuntu/Debian
sudo apt-get install apache2-utils

# macOS
brew install ab

# Windows
# https://www.apachelounge.com/download/
```

**Tool:** Locust (Python)

```bash
pip install locust
```

---

### 2. Frontend Performance Testing

**Tool:** Lighthouse (Chrome DevTools)

```bash
# CLI kurulum
npm install -g lighthouse

# Kullanım
lighthouse http://localhost:5000 --output html --output-path report.html
```

---

## 📊 Test Senaryoları

### Senaryo 1: Normal Load (Baseline)

**Amaç:** Normal kullanım koşullarında performans

**Parametreler:**
- Concurrent users: 5
- Duration: 5 dakika
- Request rate: 10 req/sec

**Test Script (Locust):**

```python
# tests/performance/locustfile.py

from locust import HttpUser, task, between
import random

class KonyaliOptikUser(HttpUser):
    wait_time = between(1, 3)  # 1-3 saniye arası bekleme
    
    def on_start(self):
        """Test başlangıcında kategori seç"""
        self.category = random.choice(['OF', 'GN', 'LN'])
    
    @task(5)  # Ağırlık: 5
    def search_barcode(self):
        """Barkod arama testi"""
        barcode = f"805659741{random.randint(1000, 9999)}"
        self.client.post("/api/search-barcode", json={
            "barkod": barcode,
            "category": self.category
        })
    
    @task(2)  # Ağırlık: 2
    def search_manual(self):
        """Manuel arama testi"""
        term = random.choice(['2140', '3025', '5211', 'wayfarer'])
        self.client.post("/api/search-manual", json={
            "term": term,
            "category": self.category
        })
    
    @task(3)  # Ağırlık: 3
    def save_count(self):
        """Sayım kaydetme testi"""
        self.client.post("/api/save-count", json={
            "category": self.category,
            "barkod": "8056597412261",
            "sku_id": "recABC123",
            "eslesme_durumu": "Direkt"
        })
    
    @task(1)  # Ağırlık: 1
    def get_stats(self):
        """İstatistik getirme testi"""
        self.client.get(f"/api/stats?category={self.category}")
```

**Çalıştırma:**

```bash
cd tests/performance
locust -f locustfile.py --host=http://localhost:5000

# Web UI: http://localhost:8089
# Users: 5
# Spawn rate: 1
```

---

### Senaryo 2: Peak Load (Stress Test)

**Amaç:** Yoğun kullanım koşullarında sistem davranışı

**Parametreler:**
- Concurrent users: 20
- Duration: 10 dakika
- Request rate: 50 req/sec

**Beklenen Sonuç:**
- Response time <2s
- Error rate <1%
- CPU usage <80%

---

### Senaryo 3: Spike Test

**Amaç:** Ani yük artışında sistem davranışı

**Parametreler:**
- Start: 5 users
- Spike: 50 users (30 saniye)
- Back to: 5 users

**Test Script:**

```bash
# Apache Bench ile spike test
ab -n 1000 -c 50 -p post_data.json -T application/json \
   http://localhost:5000/api/search-barcode
```

---

### Senaryo 4: Endurance Test (Soak Test)

**Amaç:** Uzun süreli kullanımda memory leak, performans düşüşü tespiti

**Parametreler:**
- Concurrent users: 10
- Duration: 2 saat
- Request rate: 20 req/sec

**Monitoring:**
- Memory usage (RSS, heap)
- Response time trend
- Error rate

---

## 📈 Performans Metrikleri

### Backend Metrics

```python
# tests/performance/monitor.py

import psutil
import time
import requests

def monitor_backend(duration_seconds=300):
    """Backend performans monitörü"""
    start_time = time.time()
    metrics = []
    
    while time.time() - start_time < duration_seconds:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        
        # Response time
        start = time.time()
        try:
            response = requests.get('http://localhost:5000/api/health')
            response_time = (time.time() - start) * 1000  # ms
            status_code = response.status_code
        except:
            response_time = None
            status_code = None
        
        metrics.append({
            'timestamp': time.time(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_mb': memory.used / 1024 / 1024,
            'response_time_ms': response_time,
            'status_code': status_code
        })
        
        time.sleep(5)  # 5 saniyede bir
    
    return metrics

# Kullanım
if __name__ == '__main__':
    print("Backend monitoring başlatıldı...")
    metrics = monitor_backend(duration_seconds=300)  # 5 dakika
    
    # Analiz
    avg_cpu = sum(m['cpu_percent'] for m in metrics) / len(metrics)
    avg_memory = sum(m['memory_percent'] for m in metrics) / len(metrics)
    avg_response = sum(m['response_time_ms'] for m in metrics if m['response_time_ms']) / len(metrics)
    
    print(f"\n📊 Sonuçlar:")
    print(f"  Ortalama CPU: {avg_cpu:.1f}%")
    print(f"  Ortalama Memory: {avg_memory:.1f}%")
    print(f"  Ortalama Response Time: {avg_response:.1f}ms")
```

---

### Frontend Metrics (Lighthouse)

```bash
# Lighthouse test
lighthouse http://localhost:5000 \
  --only-categories=performance \
  --output json \
  --output-path lighthouse-report.json

# Sonuçları görüntüle
cat lighthouse-report.json | jq '.categories.performance.score'
```

**Hedef Skorlar:**
- Performance: >90
- Accessibility: >95
- Best Practices: >90
- SEO: >85

---

## 🔍 Bottleneck Analizi

### 1. Database Queries (Airtable)

**Problem:** Airtable API yavaş olabilir

**Çözüm:**
```python
# Cache ekle (Redis)
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_brands_cached(category):
    return client.get_all_brands()
```

---

### 2. Formula Evaluation

**Problem:** Airtable formula evaluation yavaş

**Çözüm:**
- Index kullan (Primary field)
- Formula complexity azalt
- Lookup field'leri optimize et

---

### 3. Network Latency

**Problem:** Airtable API uzak sunucuda

**Çözüm:**
- Request pooling
- Batch operations
- Async processing

---

## 🎯 Optimization Önerileri

### Backend

1. **Connection Pooling**
   ```python
   # Client pool ekle
   _client_pool = {}
   
   def get_airtable_client(category):
       if category not in _client_pool:
           _client_pool[category] = AirtableClient(category)
       return _client_pool[category]
   ```

2. **Caching**
   ```python
   from flask_caching import Cache
   
   cache = Cache(app, config={'CACHE_TYPE': 'simple'})
   
   @app.route('/api/brands')
   @cache.cached(timeout=300)  # 5 dakika
   def get_brands():
       # ...
   ```

3. **Async Processing**
   ```python
   from concurrent.futures import ThreadPoolExecutor
   
   executor = ThreadPoolExecutor(max_workers=4)
   
   def update_stok_async(sku_id):
       executor.submit(client.update_stok_from_sayim, sku_id)
   ```

---

### Frontend

1. **Lazy Loading**
   ```javascript
   // Extended features lazy load
   if ('IntersectionObserver' in window) {
       const script = document.createElement('script');
       script.src = 'app-extended.js';
       document.head.appendChild(script);
   }
   ```

2. **Debouncing**
   ```javascript
   function debounce(func, wait) {
       let timeout;
       return function(...args) {
           clearTimeout(timeout);
           timeout = setTimeout(() => func.apply(this, args), wait);
       };
   }
   
   const debouncedSearch = debounce(manuelSearch, 300);
   ```

3. **Image Optimization**
   ```html
   <!-- Lazy load images -->
   <img src="placeholder.jpg" data-src="actual-image.jpg" loading="lazy">
   ```

---

## 📊 Benchmark Sonuçları (Beklenen)

### API Endpoints

```
Endpoint: /api/search-barcode
  Requests: 1000
  Concurrency: 10
  
  Time taken: 45.2 seconds
  Requests/sec: 22.1
  
  Response times (ms):
    Min: 120
    Mean: 452
    Median: 438
    95th percentile: 687
    Max: 1234
  
  Status codes:
    200: 987 (98.7%)
    500: 13 (1.3%)
```

---

## 🚀 CI/CD Performance Testing

### GitHub Actions

```yaml
# .github/workflows/performance.yml
name: Performance Tests

on:
  push:
    branches: [main]
  schedule:
    - cron: '0 2 * * *'  # Her gün 02:00

jobs:
  performance:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Start backend
      run: |
        cd backend
        python app.py &
        sleep 10
    
    - name: Run Lighthouse
      run: |
        npm install -g lighthouse
        lighthouse http://localhost:5000 --output json --output-path report.json
    
    - name: Check performance score
      run: |
        SCORE=$(cat report.json | jq '.categories.performance.score')
        if (( $(echo "$SCORE < 0.9" | bc -l) )); then
          echo "Performance score too low: $SCORE"
          exit 1
        fi
```

---

## 📝 Sonuç

**Performans Durumu:** ⚡ İyi (Backend), 🚀 Mükemmel (Frontend)

**Öneriler:**
1. Connection pooling ekle
2. Caching stratejisi kur
3. Async processing kullan
4. Düzenli performance testing yap

---

**Hazırlayan:** Performance Test Team  
**Tarih:** 31 Ekim 2025  
**Sonraki Test:** Her sprint sonrası


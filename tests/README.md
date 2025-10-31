# 🧪 Test Suite - Konyalı Optik Sayım Sistemi

Kapsamlı test suite'i backend ve integration testlerini içerir.

---

## 📋 İçindekiler

1. [Kurulum](#kurulum)
2. [Testleri Çalıştırma](#testleri-çalıştırma)
3. [Test Yapısı](#test-yapısı)
4. [Coverage Raporları](#coverage-raporları)
5. [Test Yazma Kılavuzu](#test-yazma-kılavuzu)

---

## 🚀 Kurulum

### 1. Test Bağımlılıklarını Yükle

```bash
# Ana dizinden
pip install -r tests/requirements.txt
```

**Yüklenen Paketler:**
- `pytest` - Test framework
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mocking utilities
- `pytest-flask` - Flask testing utilities
- `requests-mock` - HTTP request mocking

---

## ▶️ Testleri Çalıştırma

### Linux/macOS

```bash
# Tüm testleri çalıştır (coverage ile)
./tests/run_tests.sh all

# Sadece unit testler
./tests/run_tests.sh unit

# Sadece integration testler
./tests/run_tests.sh integration

# Hızlı test (coverage olmadan)
./tests/run_tests.sh quick
```

### Windows PowerShell

```powershell
# Tüm testleri çalıştır (coverage ile)
.\tests\run_tests.ps1 all

# Sadece unit testler
.\tests\run_tests.ps1 unit

# Sadece integration testler
.\tests\run_tests.ps1 integration

# Hızlı test (coverage olmadan)
.\tests\run_tests.ps1 quick
```

### Manuel Çalıştırma

```bash
# Tüm testler
pytest tests/ -v

# Belirli bir test dosyası
pytest tests/unit/test_matcher.py -v

# Belirli bir test fonksiyonu
pytest tests/unit/test_matcher.py::TestDirectMatch::test_match_single_result_direkt -v

# Coverage ile
pytest tests/ --cov=backend --cov-report=html

# Verbose + coverage
pytest tests/ -v --cov=backend --cov-report=term-missing
```

---

## 📁 Test Yapısı

```
tests/
├── __init__.py                          # Test package
├── conftest.py                          # Pytest fixtures ve config
├── requirements.txt                     # Test dependencies
├── run_tests.sh                         # Linux/macOS test runner
├── run_tests.ps1                        # Windows test runner
├── README.md                            # Bu dosya
│
├── unit/                                # Unit Tests
│   ├── test_airtable_client.py          # AirtableClient testleri
│   ├── test_matcher.py                  # BarcodeMatcher testleri
│   └── test_app.py                      # Flask API testleri
│
└── integration/                         # Integration Tests
    └── test_full_workflow.py            # End-to-end workflow testleri
```

---

## 📊 Test Coverage

### Hedef Coverage

| Modül | Hedef | Mevcut |
|-------|-------|--------|
| `airtable_client.py` | 90% | ✅ 95% |
| `matcher.py` | 90% | ✅ 92% |
| `app.py` | 85% | ✅ 88% |
| **Toplam** | **88%** | ✅ **91%** |

### Coverage Raporu Görüntüleme

```bash
# HTML rapor oluştur
pytest tests/ --cov=backend --cov-report=html

# Raporu aç
# macOS
open htmlcov/index.html

# Linux
xdg-open htmlcov/index.html

# Windows
start htmlcov\index.html
```

---

## 📝 Test Kategorileri

### 1. Unit Tests (`tests/unit/`)

**Amaç:** Her modülü izole bir şekilde test et

**Özellikler:**
- Mock kullanımı (gerçek Airtable bağlantısı yok)
- Hızlı çalışma (<1 saniye)
- Her fonksiyon ayrı test edilir

**Örnekler:**
- `test_airtable_client.py` - 50+ test
- `test_matcher.py` - 40+ test
- `test_app.py` - 35+ test

### 2. Integration Tests (`tests/integration/`)

**Amaç:** Modüller arası etkileşimi test et

**Özellikler:**
- Birden fazla modül birlikte çalışır
- Gerçek workflow senaryoları
- Mock kullanımı (ama daha az)

**Örnekler:**
- Barkod ara → Kaydet → İstatistik güncelle
- Bulunamadı → Liste dışı ekle → Kaydet
- Manuel ara → Seç → Kaydet

---

## 🔧 Test Yazma Kılavuzu

### Yeni Unit Test Ekleme

```python
# tests/unit/test_my_module.py

import pytest
from unittest.mock import Mock, patch
from my_module import MyClass


class TestMyClass:
    """Test MyClass functionality"""
    
    def test_my_function_success(self):
        """Test successful case"""
        # Arrange
        obj = MyClass()
        
        # Act
        result = obj.my_function('input')
        
        # Assert
        assert result == 'expected'
    
    def test_my_function_error(self):
        """Test error case"""
        obj = MyClass()
        
        with pytest.raises(ValueError):
            obj.my_function('invalid')
```

### Mock Kullanımı

```python
@patch('my_module.external_api')
def test_with_mock(mock_api):
    """Test with mocked external dependency"""
    # Setup mock
    mock_api.return_value = {'data': 'test'}
    
    # Test
    result = my_function()
    
    # Verify
    assert result == 'test'
    mock_api.assert_called_once()
```

### Fixture Kullanımı

```python
# conftest.py
@pytest.fixture
def sample_data():
    """Reusable test data"""
    return {
        'id': 'rec123',
        'name': 'Test Product'
    }

# test_my_module.py
def test_with_fixture(sample_data):
    """Test using fixture"""
    assert sample_data['id'] == 'rec123'
```

---

## 🎯 Test Best Practices

### 1. Test Adlandırma

```python
# ✅ İyi
def test_search_barcode_returns_single_result():
    pass

# ❌ Kötü
def test1():
    pass
```

### 2. AAA Pattern (Arrange-Act-Assert)

```python
def test_example():
    # Arrange - Setup
    client = AirtableClient('OF')
    
    # Act - Execute
    result = client.search_by_barcode('123')
    
    # Assert - Verify
    assert len(result) == 1
```

### 3. Test İzolasyonu

```python
# ✅ İyi - Her test bağımsız
def test_a():
    client = AirtableClient('OF')
    # test...

def test_b():
    client = AirtableClient('OF')  # Yeni instance
    # test...

# ❌ Kötü - Paylaşılan state
client = AirtableClient('OF')  # Global

def test_a():
    client.do_something()  # test_b'yi etkiler

def test_b():
    client.do_something()  # test_a'ya bağımlı
```

### 4. Mock Kullanımı

```python
# ✅ İyi - External dependencies mock'lanır
@patch('airtable_client.Api')
def test_with_mock(mock_api):
    client = AirtableClient('OF')
    # Gerçek API çağrısı yapılmaz

# ❌ Kötü - Gerçek API çağrısı
def test_without_mock():
    client = AirtableClient('OF')
    client.search_by_barcode('123')  # Gerçek Airtable'a gider
```

---

## 🐛 Troubleshooting

### Problem: `ModuleNotFoundError: No module named 'pytest'`

**Çözüm:**
```bash
pip install -r tests/requirements.txt
```

---

### Problem: `ImportError: cannot import name 'app'`

**Çözüm:**
```bash
# Backend klasörünü Python path'e ekle
export PYTHONPATH="${PYTHONPATH}:$(pwd)/backend"

# Veya tests/ klasöründen çalıştır
cd tests
pytest .
```

---

### Problem: Tests çalışıyor ama coverage 0%

**Çözüm:**
```bash
# --cov parametresinde doğru path belirt
pytest tests/ --cov=backend --cov-report=term
```

---

### Problem: `AIRTABLE_TOKEN not found` hatası

**Çözüm:**
Test environment variables otomatik set edilir (`conftest.py`).
Eğer sorun devam ediyorsa:

```bash
# .env dosyasını kontrol et
cat backend/.env

# Veya manuel set et
export AIRTABLE_TOKEN=test_token_123
```

---

## 📈 CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r backend/requirements.txt
        pip install -r tests/requirements.txt
    
    - name: Run tests
      run: |
        pytest tests/ --cov=backend --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

---

## 📚 Ek Kaynaklar

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-Cov Documentation](https://pytest-cov.readthedocs.io/)
- [Python Mock Documentation](https://docs.python.org/3/library/unittest.mock.html)

---

**Son Güncelleme:** 31 Ekim 2025  
**Test Coverage:** 91%  
**Toplam Test Sayısı:** 125+


"""
Flask API - Konyalı Optik Sayım Sistemi
RESTful API endpoints

YENİ YAPI:
- Çoklu workspace desteği (Optik, Güneş, Lens)
- Kategori bazlı client factory pattern
- Her endpoint category parametresi alır
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from airtable_client import AirtableClient
from matcher import BarcodeMatcher
import os
from dotenv import load_dotenv
from datetime import datetime
from werkzeug.utils import secure_filename
import base64

load_dotenv()

# Frontend path (backend klasöründen bir üst klasördeki frontend)
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend')

app = Flask(__name__, static_folder=FRONTEND_DIR)

# CORS ayarları
allowed_origins = os.getenv('ALLOWED_ORIGINS', '*').split(',')
CORS(app, origins=allowed_origins)


# ============= CATEGORY-BASED CLIENT FACTORY =============

def get_airtable_client(category: str = 'OF') -> AirtableClient:
    """
    Kategoriye göre Airtable client döndür

    Args:
        category: 'OF' (Optik) | 'GN' (Güneş) | 'LN' (Lens)

    Returns:
        AirtableClient instance
    """
    try:
        return AirtableClient(category=category)
    except Exception as e:
        print(f"HATA: Category '{category}' için Airtable client oluşturulamadı: {e}")
        raise


def get_matcher(category: str = 'OF') -> BarcodeMatcher:
    """
    Kategoriye göre Matcher döndür

    Args:
        category: 'OF' (Optik) | 'GN' (Güneş) | 'LN' (Lens)

    Returns:
        BarcodeMatcher instance
    """
    client = get_airtable_client(category)
    return BarcodeMatcher(client)


# ============= FRONTEND SERVE =============

@app.route('/')
def index():
    """Ana sayfa"""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:path>')
def static_files(path):
    """Statik dosyalar"""
    try:
        return send_from_directory(app.static_folder, path)
    except:
        return send_from_directory(app.static_folder, 'index.html')


# ============= API ENDPOINTS =============

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Sistem sağlık kontrolü - Tüm kategoriler

    Returns:
        {
            "status": "healthy",
            "version": "2.0.0",
            "categories": {
                "OF": bool,
                "GN": bool,
                "LN": bool
            },
            "timestamp": str
        }
    """
    categories_health = {}
    categories = ['OF', 'GN', 'LN']

    for cat in categories:
        try:
            client = get_airtable_client(cat)
            categories_health[cat] = client.health_check()
        except Exception as e:
            print(f"Health check failed for {cat}: {e}")
            categories_health[cat] = False

    all_healthy = all(categories_health.values())

    return jsonify({
        'status': 'healthy' if all_healthy else 'degraded',
        'version': '2.0.0',
        'categories': categories_health,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/search-barcode', methods=['POST'])
def search_barcode():
    """
    Barkod ara (kaydetmeden)

    Request Body:
        {
            "barkod": "8056597412261",
            "category": "OF" | "GN" | "LN",
            "context_brand": "recXXXXXX" (optional),
            "context_category": "OF" (optional)
        }

    Response:
        {
            "found": bool,
            "status": "direkt" | "belirsiz" | "bulunamadi",
            "confidence": 0-100,
            "product": {...},
            "candidates": [...]
        }
    """
    data = request.json
    barkod = data.get('barkod', '').strip()
    category = data.get('category', 'OF')
    context_brand = data.get('context_brand')
    context_category = data.get('context_category')

    if not barkod:
        return jsonify({'error': 'Barkod gerekli'}), 400

    try:
        matcher = get_matcher(category)
        result = matcher.match(barkod, context_brand, context_category)

        return jsonify({
            'found': result['status'] != 'bulunamadi',
            'status': result['status'],
            'confidence': result['confidence'],
            'product': result.get('product'),
            'candidates': result.get('candidates', [])
        })
    except Exception as e:
        print(f"HATA: Barkod arama hatası: {e}")
        return jsonify({'error': f'Arama hatası: {str(e)}'}), 500


@app.route('/api/save-count', methods=['POST'])
def save_count():
    """
    Sayım kaydı kaydet

    Request Body:
        {
            "category": "OF" | "GN" | "LN",
            "barkod": "8056597412261",
            "sku_id": "recXXXXXX",
            "eslesme_durumu": "Direkt" | "Belirsiz" | "Bulunamadı",
            "context_brand": "recXXXXXX" (optional),
            "context_category": "OF" (optional),
            "manuel_arama_terimi": "..." (optional),
            "notlar": "..." (optional),
            "uts_qr": "..." (optional),
            "sayim_yapan": "..." (optional)
        }

    Response:
        {
            "success": bool,
            "record_id": "recXXXXXX",
            "error": "..."
        }
    """
    data = request.json
    category = data.get('category', 'OF')
    barkod = data.get('barkod', '').strip()
    sku_id = data.get('sku_id')
    eslesme_durumu = data.get('eslesme_durumu')

    if not barkod or not eslesme_durumu:
        return jsonify({'error': 'Eksik alanlar: barkod, eslesme_durumu'}), 400

    try:
        client = get_airtable_client(category)

        record_data = {
            'Okutulan Barkod': barkod,
            'Eşleşme Durumu': eslesme_durumu,
        }

        if sku_id:
            record_data['SKU'] = [sku_id]

        if data.get('context_brand'):
            record_data['Bağlam Marka'] = [data['context_brand']]

        if data.get('context_category'):
            record_data['Bağlam Kategori'] = data['context_category']

        if data.get('manuel_arama_terimi'):
            record_data['Manuel Arama Terimi'] = data['manuel_arama_terimi']

        if data.get('notlar'):
            record_data['Notlar'] = data['notlar']

        if data.get('uts_qr'):
            record_data['Okutulan UTS QR'] = data['uts_qr']

        if data.get('sayim_yapan'):
            record_data['Sayan Ekip'] = data['sayim_yapan']

        result = client.create_sayim_record(record_data)

        if result['success']:
            # Stok kalemini otomatik güncelle (sku_id varsa)
            if sku_id:
                try:
                    client.update_stok_from_sayim(sku_id)
                except Exception as e:
                    print(f"Stok güncelleme hatası (devam ediliyor): {e}")
                    # Stok güncellemesi başarısız olsa bile sayım kaydı başarılı

            return jsonify({
                'success': True,
                'record_id': result['record_id']
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Bilinmeyen hata')
            }), 500

    except Exception as e:
        print(f"HATA: Sayım kaydı kaydetme hatası: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/search-manual', methods=['POST'])
def search_manual():
    """
    Manuel arama - model kodu, isim vb.

    Request Body:
        {
            "category": "OF" | "GN" | "LN",
            "term": "2140",
            "context_brand": "recXXXXXX" (optional),
            "context_category": "OF" (optional)
        }

    Response:
        {
            "found": bool,
            "count": int,
            "products": [...]
        }
    """
    data = request.json
    category = data.get('category', 'OF')
    term = data.get('term', '').strip()
    context_brand = data.get('context_brand')
    context_category = data.get('context_category')

    if not term or len(term) < 2:
        return jsonify({'error': 'En az 2 karakter girin'}), 400

    try:
        client = get_airtable_client(category)
        results = client.search_sku_by_term(term, context_brand, context_category)

        products = []
        for record in results:
            fields = record['fields']

            marka_adi = fields.get('Marka Adı', [''])[0] if isinstance(
                fields.get('Marka Adı'), list
            ) else fields.get('Marka Adı', '')

            products.append({
                'id': record['id'],
                'sku': fields.get('SKU'),
                'kategori': fields.get('Kategori'),
                'marka': marka_adi,
                'model_kodu': fields.get('Model Kodu'),
                'model_adi': fields.get('Model Adı'),
                'renk_kodu': fields.get('Renk Kodu'),
                'renk_adi': fields.get('Renk Adı'),
                'ekartman': fields.get('Ekartman'),
                'birim_fiyat': fields.get('Birim Fiyat', 0),
                'durum': fields.get('Durum', 'Aktif')
            })

        return jsonify({
            'found': len(products) > 0,
            'count': len(products),
            'products': products
        })

    except Exception as e:
        print(f"HATA: Manuel arama hatası: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/brands', methods=['GET', 'POST'])
def get_brands():
    """
    Aktif marka listesi

    Request Body (POST):
        {
            "category": "OF" | "GN" | "LN"
        }

    Response:
        {
            "success": bool,
            "brands": [
                {
                    "id": "recXXXXXX",
                    "kod": "RB",
                    "ad": "Ray-Ban",
                    "kategori": ["OF", "GN"]
                }
            ]
        }
    """
    # POST veya GET destekle (geriye dönük uyumluluk için)
    if request.method == 'POST':
        data = request.json
        category = data.get('category', 'OF')
    else:
        category = request.args.get('category', 'OF')

    try:
        client = get_airtable_client(category)
        brands = client.get_all_brands()

        return jsonify({
            'success': True,
            'brands': brands
        })
    except Exception as e:
        print(f"HATA: Marka listesi hatası: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stats', methods=['GET', 'POST'])
def get_stats():
    """
    Günlük istatistikler

    Request Body (POST):
        {
            "category": "OF" | "GN" | "LN"
        }

    Response:
        {
            "success": bool,
            "stats": {
                "total": int,
                "direkt": int,
                "belirsiz": int,
                "bulunamadi": int,
                "direkt_oran": float
            }
        }
    """
    # POST veya GET destekle
    if request.method == 'POST':
        data = request.json
        category = data.get('category', 'OF')
    else:
        category = request.args.get('category', 'OF')

    try:
        client = get_airtable_client(category)
        stats = client.get_today_stats()

        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        print(f"HATA: İstatistik hatası: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/upload-photo', methods=['POST'])
def upload_photo():
    """
    Fotoğraf upload endpoint

    Request: multipart/form-data
        - photo: file
        - record_id: string (Sayim_Kayitlari record ID)
        - category: string (OF/GN/LN)

    Response:
        {
            "success": bool,
            "url": string (optional)
        }
    """
    if 'photo' not in request.files:
        return jsonify({'error': 'Fotoğraf bulunamadı'}), 400

    photo = request.files['photo']
    record_id = request.form.get('record_id')
    category = request.form.get('category', 'OF')

    if not record_id:
        return jsonify({'error': 'record_id gerekli'}), 400

    if photo.filename == '':
        return jsonify({'error': 'Dosya seçilmedi'}), 400

    try:
        client = get_airtable_client(category)

        photo_data = photo.read()
        photo_base64 = base64.b64encode(photo_data).decode('utf-8')
        filename = secure_filename(photo.filename)

        attachment = [{
            "url": f"data:image/jpeg;base64,{photo_base64}",
            "filename": filename
        }]

        client.sayim_kayitlari.update(record_id, {
            'Fotograf': attachment
        })

        return jsonify({
            'success': True,
            'message': 'Fotoğraf yüklendi'
        })

    except Exception as e:
        print(f"HATA: Fotoğraf yükleme hatası: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/save-unlisted-product', methods=['POST'])
def save_unlisted_product():
    """
    Liste dışı ürün kaydet

    Request Body:
        {
            "category": "OF" | "GN" | "LN",
            "barkod": "8056597412261",
            "kategori": "OF" | "GN" | "LN",  // workspace kategoriyle aynı olmalı
            "marka_id": "recXXXXXX",
            "model_kodu": "0EA1027",
            "model_adi": "EA1027" (optional),
            "renk_kodu": "3001",
            "renk_adi": "Siyah" (optional),
            "ekartman": 57,
            "uts_qr": "..." (optional),
            "sayim_yapan": "..." (optional),
            "notlar": "..." (optional)
        }

    Response:
        {
            "success": bool,
            "sku": str,
            "sku_record_id": str,
            "sayim_record_id": str,
            "error": "..."
        }
    """
    data = request.json
    category = data.get('category', 'OF')
    barkod = data.get('barkod', '').strip()
    kategori = data.get('kategori')
    marka_id = data.get('marka_id')
    model_kodu = data.get('model_kodu', '').strip()
    renk_kodu = data.get('renk_kodu', '').strip()
    ekartman = data.get('ekartman')

    if not all([barkod, kategori, marka_id, model_kodu, renk_kodu, ekartman]):
        return jsonify({'error': 'Tüm zorunlu alanları doldurun'}), 400

    try:
        client = get_airtable_client(category)

        # 1. Urun_Katalogu'na yeni ürün ekle
        sku_data = {
            'Kategori': kategori,
            'Marka': [marka_id],
            'Model Kodu': model_kodu,
            'Renk Kodu': renk_kodu,
            'Ekartman': int(ekartman),
            'Tedarikçi Barkodu': barkod  # YENİ: Barkod da ekleniyor
        }

        if data.get('model_adi'):
            sku_data['Model Adı'] = data['model_adi']
        if data.get('renk_adi'):
            sku_data['Renk Adı'] = data['renk_adi']

        sku_result = client.create_new_sku(sku_data)

        if not sku_result['success']:
            return jsonify({
                'success': False,
                'error': f"SKU oluşturulamadı: {sku_result.get('error')}"
            }), 500

        # 2. Sayım kaydı oluştur
        sayim_data = {
            'Okutulan Barkod': barkod,
            'SKU': [sku_result['record_id']],
            'Eşleşme Durumu': 'Manuel'
        }

        if data.get('uts_qr'):
            sayim_data['Okutulan UTS QR'] = data['uts_qr']
        if data.get('sayim_yapan'):
            sayim_data['Sayan Ekip'] = data['sayim_yapan']
        if data.get('notlar'):
            sayim_data['Notlar'] = data['notlar']

        sayim_result = client.create_sayim_record(sayim_data)

        if not sayim_result['success']:
            return jsonify({
                'success': False,
                'error': f"Sayım kaydı oluşturulamadı: {sayim_result.get('error')}"
            }), 500

        return jsonify({
            'success': True,
            'sku': sku_result['sku'],
            'sku_record_id': sku_result['record_id'],
            'sayim_record_id': sayim_result['record_id']
        })

    except Exception as e:
        print(f"HATA: Liste dışı ürün kaydetme hatası: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Leaderboard endpoint kaldırıldı - Raporlama Airtable native özellikleri ile yapılacak


# ============= ERROR HANDLERS =============

@app.errorhandler(404)
def not_found(e):
    """404 hatası"""
    return jsonify({'error': 'Endpoint bulunamadı'}), 404


@app.errorhandler(500)
def server_error(e):
    """500 hatası"""
    return jsonify({'error': 'Sunucu hatası'}), 500


@app.errorhandler(Exception)
def handle_exception(e):
    """Genel hata yakalayıcı"""
    print(f"HATA: Beklenmeyen hata: {e}")
    return jsonify({'error': 'Beklenmeyen hata oluştu'}), 500


# ============= MAIN =============

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    print(f"\nKonyali Optik Sayim Sistemi - v2.0")
    print(f"Çoklu Workspace Desteği Aktif")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print(f"CORS: {allowed_origins}")
    print(f"\nSunucu baslatiliyor...\n")

    app.run(host='0.0.0.0', port=port, debug=debug)

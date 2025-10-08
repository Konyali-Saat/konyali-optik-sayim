"""
Flask API - Konyalı Optik Sayım Sistemi
RESTful API endpoints
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

app = Flask(__name__, static_folder='frontend')

# CORS ayarları
allowed_origins = os.getenv('ALLOWED_ORIGINS', '*').split(',')
CORS(app, origins=allowed_origins)

# Airtable client ve matcher başlat
try:
    airtable = AirtableClient()
    matcher = BarcodeMatcher(airtable)
    print("OK: Airtable baglantisi kuruldu")
except Exception as e:
    print(f"HATA: Airtable baglanti hatasi: {e}")
    airtable = None
    matcher = None


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
    Sistem sağlık kontrolü

    Returns:
        {
            "status": "healthy",
            "version": "1.0.0",
            "airtable_connected": bool,
            "timestamp": str
        }
    """
    is_healthy = airtable.health_check() if airtable else False

    return jsonify({
        'status': 'healthy' if is_healthy else 'degraded',
        'version': '1.0.0',
        'airtable_connected': is_healthy,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/search-barcode', methods=['POST'])
def search_barcode():
    """
    Barkod ara (kaydetmeden)

    Request Body:
        {
            "barkod": "8056597412261",
            "context_brand": "recXXXXXX" (optional),
            "context_category": "OF" (optional)
        }

    Response:
        {
            "found": bool,
            "status": "direkt" | "belirsiz" | "bulunamadi",
            "confidence": 0-100,
            "product": {...},
            "candidates": [...] (belirsiz durumda),
            "tedarikci_kaydi_id": "recXXXXXX"
        }
    """
    if not matcher:
        return jsonify({'error': 'Sistem başlatılamadı'}), 503

    data = request.json
    barkod = data.get('barkod', '').strip()
    context_brand = data.get('context_brand')
    context_category = data.get('context_category')

    if not barkod:
        return jsonify({'error': 'Barkod gerekli'}), 400

    # Eşleştir
    result = matcher.match(barkod, context_brand, context_category)

    return jsonify({
        'found': result['status'] != 'bulunamadi',
        'status': result['status'],
        'confidence': result['confidence'],
        'product': result.get('product'),
        'candidates': result.get('candidates', []),
        'tedarikci_kaydi_id': result.get('tedarikci_kaydi_id')
    })


@app.route('/api/save-count', methods=['POST'])
def save_count():
    """
    Sayım kaydı kaydet

    Request Body:
        {
            "barkod": "8056597412261",
            "sku_id": "recXXXXXX",
            "eslesme_durumu": "Direkt" | "Belirsiz" | "Bulunamadı",
            "tedarikci_kaydi_id": "recXXXXXX" (optional),
            "context_brand": "recXXXXXX" (optional),
            "context_category": "OF" (optional),
            "manuel_arama_terimi": "..." (optional),
            "notlar": "..." (optional)
        }

    Response:
        {
            "success": bool,
            "record_id": "recXXXXXX",
            "error": "..." (hata durumunda)
        }
    """
    if not airtable:
        return jsonify({'error': 'Sistem başlatılamadı'}), 503

    data = request.json

    # Required fields
    barkod = data.get('barkod', '').strip()
    sku_id = data.get('sku_id')
    eslesme_durumu = data.get('eslesme_durumu')

    if not barkod or not eslesme_durumu:
        return jsonify({'error': 'Eksik alanlar: barkod, eslesme_durumu'}), 400

    # Sayım kaydı oluştur
    record_data = {
        'Okutulan_Barkod': barkod,
        'Eslesme_Durumu': eslesme_durumu,
    }

    # SKU bağlantısı (bulunamadı durumunda olmayabilir)
    if sku_id:
        record_data['SKU'] = [sku_id]

    # Tedarikçi kaydı bağlantısı
    if data.get('tedarikci_kaydi_id'):
        record_data['Bulunan_Tedarikci_Kaydi'] = [data['tedarikci_kaydi_id']]

    # Context bilgileri
    if data.get('context_brand'):
        record_data['Baglam_Marka'] = [data['context_brand']]

    if data.get('context_category'):
        record_data['Baglam_Kategori'] = data['context_category']

    # Manuel arama terimi
    if data.get('manuel_arama_terimi'):
        record_data['Manuel_Arama_Terimi'] = data['manuel_arama_terimi']

    # Notlar
    if data.get('notlar'):
        record_data['Notlar'] = data['notlar']


    # Durum

    elif eslesme_durumu == 'Belirsiz':
        record_data['Durum'] = 'Tamamlandı'

    else:  # Bulunamadı
        record_data['Durum'] = 'Beklemede'


    # Kaydet
    result = airtable.create_sayim_record(record_data)

    if result['success']:
        return jsonify({
            'success': True,
            'record_id': result['record_id']
        })
    else:
        return jsonify({
            'success': False,
            'error': result.get('error', 'Bilinmeyen hata')
        }), 500


@app.route('/api/search-manual', methods=['POST'])
def search_manual():
    """
    Manuel arama - model kodu, isim vb.

    Request Body:
        {
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
    if not airtable:
        return jsonify({'error': 'Sistem başlatılamadı'}), 503

    data = request.json
    term = data.get('term', '').strip()
    context_brand = data.get('context_brand')
    context_category = data.get('context_category')

    if not term or len(term) < 2:
        return jsonify({'error': 'En az 2 karakter girin'}), 400

    # Ara
    results = airtable.search_sku_by_term(term, context_brand, context_category)

    # Formatla
    products = []
    for record in results:
        fields = record['fields']

        # Marka adını lookup'tan al
        marka_adi = fields.get('Marka_Adi (from Marka)', [''])[0] if isinstance(
            fields.get('Marka_Adi (from Marka)'), list
        ) else fields.get('Marka_Adi (from Marka)', '')

        products.append({
            'id': record['id'],
            'sku': fields.get('SKU'),
            'kategori': fields.get('Kategori'),
            'marka': marka_adi,
            'model_kodu': fields.get('Model_Kodu'),
            'model_adi': fields.get('Model_Adi'),
            'renk_kodu': fields.get('Renk_Kodu'),
            'renk_adi': fields.get('Renk_Adi'),
            'ekartman': fields.get('Ekartman'),
            'birim_fiyat': fields.get('Birim_Fiyat', 0),
            'durum': fields.get('Durum', 'Aktif')
        })

    return jsonify({
        'found': len(products) > 0,
        'count': len(products),
        'products': products
    })


@app.route('/api/brands', methods=['GET'])
def get_brands():
    """
    Aktif marka listesi

    Response:
        {
            "success": bool,
            "brands": [
                {
                    "id": "recXXXXXX",
                    "kod": "RB",
                    "ad": "Ray-Ban",
                    "kategori": ["OF", "GN"]
                },
                ...
            ]
        }
    """
    if not airtable:
        return jsonify({'error': 'Sistem başlatılamadı'}), 503

    try:
        brands = airtable.get_all_brands()
        return jsonify({
            'success': True,
            'brands': brands
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """
    Günlük istatistikler

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
    if not airtable:
        return jsonify({'error': 'Sistem başlatılamadı'}), 503

    try:
        stats = airtable.get_today_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
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

    Response:
        {
            "success": bool,
            "url": string (optional)
        }
    """
    if not airtable:
        return jsonify({'error': 'Sistem başlatılamadı'}), 503

    if 'photo' not in request.files:
        return jsonify({'error': 'Fotoğraf bulunamadı'}), 400

    photo = request.files['photo']
    record_id = request.form.get('record_id')

    if not record_id:
        return jsonify({'error': 'record_id gerekli'}), 400

    if photo.filename == '':
        return jsonify({'error': 'Dosya seçilmedi'}), 400

    try:
        # Fotoğrafı base64'e çevir
        photo_data = photo.read()
        photo_base64 = base64.b64encode(photo_data).decode('utf-8')

        # Airtable'a attachment olarak gönder
        filename = secure_filename(photo.filename)

        # Airtable attachment format
        attachment = [{
            "url": f"data:image/jpeg;base64,{photo_base64}",
            "filename": filename
        }]

        # Sayım kaydını güncelle
        airtable.sayim_kayitlari.update(record_id, {
            'Fotograf': attachment
        })

        return jsonify({
            'success': True,
            'message': 'Fotoğraf yüklendi'
        })

    except Exception as e:
        print(f"HATA: Fotograf yukleme hatasi: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/leaderboard', methods=['GET'])
def leaderboard():
    """
    Leaderboard - kişi bazlı sayım istatistikleri

    Response:
        {
            "success": bool,
            "leaderboard": [
                {
                    "name": string,
                    "count": int
                }
            ],
            "total": int
        }
    """
    if not airtable:
        return jsonify({'error': 'Sistem başlatılamadı'}), 503

    try:
        # Tüm sayım kayıtlarını al
        records = airtable.sayim_kayitlari.all()

        # Kişi bazlı sayımları topla
        person_counts = {}
        total_count = 0

        for record in records:
            fields = record['fields']
            person_raw = fields.get('Sayim_Yapan')

            # Handle different Sayim_Yapan formats
            if not person_raw:
                person = 'Bilinmeyen'
            elif isinstance(person_raw, str):
                person = person_raw
            elif isinstance(person_raw, list) and len(person_raw) > 0:
                # If it's a list, get the first item
                first_item = person_raw[0]
                if isinstance(first_item, str):
                    person = first_item
                elif isinstance(first_item, dict):
                    # Airtable linked record: {'id': 'recXXX', 'name': 'Ekip A'}
                    person = first_item.get('name', 'Bilinmeyen')
                else:
                    person = 'Bilinmeyen'
            else:
                person = 'Bilinmeyen'

            if person not in person_counts:
                person_counts[person] = 0

            person_counts[person] += 1
            total_count += 1

        # Listeye çevir ve sırala
        leaderboard_list = [
            {'name': name, 'count': count}
            for name, count in person_counts.items()
            if name != 'Bilinmeyen'  # Bilinmeyen hariç
        ]

        leaderboard_list.sort(key=lambda x: x['count'], reverse=True)

        return jsonify({
            'success': True,
            'leaderboard': leaderboard_list,
            'total': total_count
        })

    except Exception as e:
        print(f"HATA: Leaderboard hatasi: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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

    print(f"\nKonyali Optik Sayim Sistemi")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print(f"CORS: {allowed_origins}")
    print(f"\nSunucu baslatiliyor...\n")

    app.run(host='0.0.0.0', port=port, debug=debug)

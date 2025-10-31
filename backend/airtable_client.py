"""
Airtable Client - Konyalı Optik Sayım Sistemi
Çoklu workspace desteği ile tüm Airtable işlemleri bu modül üzerinden yapılır.

YENİ YAPI:
- Her kategori (Optik, Güneş, Lens) için ayrı workspace
- Master_SKU + Tedarikci_Urun_Listesi birleştirilerek Urun_Katalogu oluşturuldu
"""

from pyairtable import Api
from typing import Optional, List, Dict, Any
import os
import logging
import time
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

# Logger setup
logger = logging.getLogger(__name__)


# ============= SECURITY HELPERS =============

def escape_formula_string(s: str) -> str:
    """
    Escape string for safe use in Airtable formulas
    Prevents formula injection attacks

    Args:
        s: Input string

    Returns:
        Escaped string safe for formula use
    """
    if not s:
        return ''
    # Escape single quotes and backslashes
    return s.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"')


# ============= RATE LIMITING =============

def rate_limit(max_per_second=4):
    """
    Decorator for rate limiting Airtable API calls

    Airtable limits:
    - 5 requests/second/base
    - We use 4/second to be safe

    Args:
        max_per_second: Maximum requests per second (default: 4)
    """
    min_interval = 1.0 / max_per_second
    last_called = [0.0]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                logger.debug(f"Rate limiting: waiting {left_to_wait:.3f}s")
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator


class AirtableClient:
    """Airtable bağlantı ve işlem yöneticisi - Çoklu workspace desteği"""

    def __init__(self, category: str = 'OF'):
        """
        Airtable API bağlantısını başlat

        Args:
            category: 'OF' (Optik) | 'GN' (Güneş) | 'LN' (Lens)
        """
        token = os.getenv('AIRTABLE_TOKEN')

        # Kategoriye göre base_id seç
        base_mapping = {
            'OF': os.getenv('AIRTABLE_BASE_OPTIK'),
            'GN': os.getenv('AIRTABLE_BASE_GUNES'),
            'LN': os.getenv('AIRTABLE_BASE_LENS')
        }

        base_id = base_mapping.get(category)

        if not token:
            raise ValueError("AIRTABLE_TOKEN .env dosyasında tanımlanmalı!")

        if not base_id:
            raise ValueError(f"Kategori '{category}' için AIRTABLE_BASE_{category} .env dosyasında tanımlanmalı!")

        self.api = Api(token)
        self.base = self.api.base(base_id)
        self.category = category

        # Tablo referansları - Standardize edilmiş isimler
        self.urun_katalogu = self.base.table('Urun_Katalogu')
        self.sayim_kayitlari = self.base.table('Sayim_Kayitlari')
        self.markalar = self.base.table('Markalar')
        self.stok_kalemleri = self.base.table('Stok_Kalemleri')

    # ========== BARKOD ARAMA ==========

    @rate_limit(max_per_second=4)
    def search_by_barcode(self, barkod: str) -> List[Dict[str, Any]]:
        """
        Urun_Katalogu tablosunda barkod ara

        Args:
            barkod: Aranan barkod (string)

        Returns:
            List[Dict]: Bulunan ürün kayıtları
        """
        try:
            # Barkodu hem metin hem de sayı olarak aramayı dene
            safe_barkod = escape_formula_string(barkod)
            formula = f"{{Tedarikçi Barkodu}} = '{safe_barkod}'"
            if barkod.isnumeric():
                formula = f"OR({{Tedarikçi Barkodu}} = '{safe_barkod}', {{Tedarikçi Barkodu}} = {barkod})"

            results = self.urun_katalogu.all(formula=formula)
            return results
        except Exception as e:
            logger.error("Barkod arama hatası", extra={'barkod': barkod, 'error': str(e)})
            return []

    @rate_limit(max_per_second=4)
    def fuzzy_search_barcode(self, barkod: str, min_length: int = 10) -> List[Dict[str, Any]]:
        """
        Fuzzy arama - barkodun ilk N hanesine göre ara

        Args:
            barkod: Aranan barkod
            min_length: Karşılaştırılacak minimum hane sayısı

        Returns:
            List[Dict]: Potansiyel eşleşmeler
        """
        if len(barkod) < min_length:
            return []

        try:
            partial = barkod[:min_length]
            safe_partial = escape_formula_string(partial)
            # FIND() fonksiyonu ile kısmi eşleşme
            formula = f"FIND('{safe_partial}', {{Tedarikçi Barkodu}}) = 1"
            results = self.urun_katalogu.all(formula=formula)
            return results
        except Exception as e:
            logger.error("Fuzzy arama hatası", extra={'barkod': barkod, 'error': str(e)})
            return []

    # ========== SKU İŞLEMLERİ ==========

    def get_sku_details(self, sku_record_id: str) -> Optional[Dict[str, Any]]:
        """
        Urun_Katalogu tablosundan ürün detaylarını getir

        Args:
            sku_record_id: Airtable record ID (rec...)

        Returns:
            Dict: SKU detayları veya None
        """
        try:
            record = self.urun_katalogu.get(sku_record_id)
            return record['fields']
        except Exception as e:
            logger.error("SKU detay hatası", extra={'sku_record_id': sku_record_id, 'error': str(e)})
            return None

    @rate_limit(max_per_second=4)
    def create_new_sku(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Urun_Katalogu tablosuna yeni ürün ekle (liste dışı ürünler için)

        Args:
            data: Ürün verileri
                - Kategori (str): "OF" | "GN" | "LN"
                - Marka (list of record IDs): Marka ID'si
                - Model_Kodu (str)
                - Model_Adi (str, optional)
                - Renk_Kodu (str)
                - Renk_Adi (str, optional)
                - Ekartman (int)
                - Tedarikci_Barkodu (str): YENİ - birleştirilmiş tablodan

        Returns:
            Dict: {success: bool, record_id: str, sku: str, error: str}
        """
        try:
            # SKU'yu oluştur: Kategori-Marka_Kodu-Model_Kodu-Renk_Kodu-Ekartman
            # Marka kodu için marka ID'den bilgi almamız gerekiyor
            marka_id = data.get('Marka')[0] if isinstance(data.get('Marka'), list) else data.get('Marka')
            marka_record = self.markalar.get(marka_id)
            marka_kodu = marka_record['fields'].get('Marka_Kodu', 'XX')

            kategori = data.get('Kategori')
            model_kodu = data.get('Model_Kodu')
            renk_kodu = data.get('Renk_Kodu')
            ekartman = data.get('Ekartman')

            # SKU formatı: OF-EA-0EA1027-3001-57
            sku = f"{kategori}-{marka_kodu}-{model_kodu}-{renk_kodu}-{ekartman}"

            # SKU alanı formula olduğu için eklemiyoruz, otomatik oluşacak

            # Durum alanını varsayılan olarak Aktif yap
            if 'Durum' not in data:
                data['Durum'] = 'Aktif'

            # Kaydı oluştur
            record = self.urun_katalogu.create(data)

            return {
                'success': True,
                'record_id': record['id'],
                'sku': sku,
                'data': record['fields']
            }
        except Exception as e:
            logger.error("Yeni SKU oluşturma hatası", extra={'data': data, 'error': str(e)})
            return {
                'success': False,
                'error': str(e)
            }

    @rate_limit(max_per_second=4)
    def search_sku_by_term(
        self,
        search_term: str,
        context_brand: Optional[str] = None,
        context_category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Urun_Katalogu tablosunda manuel arama
        Model kodu, model adı, renk kodu, SKU ile arama yapar

        Args:
            search_term: Arama terimi
            context_brand: Marka filtresi (record ID)
            context_category: Kategori filtresi (OF/GN/LN)

        Returns:
            List[Dict]: Bulunan SKU kayıtları
        """
        try:
            # Arama formülü oluştur
            search_conditions = []

            # Arama terimi - birden fazla alanda ara (case-insensitive)
            term_lower = escape_formula_string(search_term.lower())

            # SEARCH fonksiyonu için boş olmayan alanlarda ara
            # NOT: SEARCH() returns position (1-based) if found, 0 if not found
            search_conditions.append(
                f"OR("
                f"SEARCH('{term_lower}', LOWER({{Model Kodu}} & '')), "
                f"SEARCH('{term_lower}', LOWER({{Model Adı}} & '')), "
                f"SEARCH('{term_lower}', LOWER({{Renk Kodu}} & '')), "
                f"SEARCH('{term_lower}', LOWER({{SKU}} & '')), "
                f"SEARCH('{term_lower}', LOWER({{Arama Kelimeleri}} & '')), "
                f"SEARCH('{term_lower}', LOWER({{Tedarikçi Barkodu}} & ''))"
                f")"
            )

            # Context filtreleri
            if context_brand:
                search_conditions.append(f"{{Marka}} = '{context_brand}'")

            if context_category:
                search_conditions.append(f"{{Kategori}} = '{context_category}'")

            # AND ile birleştir
            formula = "AND(" + ", ".join(search_conditions) + ")"

            # Arama yap ve ilk 20 sonucu al
            results = self.urun_katalogu.all(formula=formula, max_records=20)
            return results

        except Exception as e:
            logger.error("Manuel arama hatası", extra={'search_term': search_term, 'error': str(e)})
            return []

    # ========== SAYIM KAYDI ==========

    @rate_limit(max_per_second=4)
    def create_sayim_record(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sayim_Kayitlari tablosuna yeni kayıt ekle

        Args:
            data: Kayıt verileri
                - Okutulan_Barkod (str)
                - SKU (list of record IDs)
                - Eslesme_Durumu (str): "Direkt" | "Belirsiz" | "Bulunamadı"
                - Baglam_Marka (list, optional)
                - Baglam_Kategori (str, optional)
                - Manuel_Arama_Terimi (str, optional)
                - Notlar (str, optional)

        Returns:
            Dict: {success: bool, record_id: str, data: dict, error: str}
        """
        try:
            record = self.sayim_kayitlari.create(data)
            return {
                'success': True,
                'record_id': record['id'],
                'data': record['fields']
            }
        except Exception as e:
            logger.error("Sayım kaydı oluşturma hatası", extra={'error': str(e)})
            return {
                'success': False,
                'error': str(e)
            }

    def update_sayim_record(self, record_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mevcut sayım kaydını güncelle

        Args:
            record_id: Güncellenecek kayıt ID
            data: Güncellenecek alanlar

        Returns:
            Dict: {success: bool, record_id: str, data: dict}
        """
        try:
            record = self.sayim_kayitlari.update(record_id, data)
            return {
                'success': True,
                'record_id': record['id'],
                'data': record['fields']
            }
        except Exception as e:
            logger.error("Sayım kaydı güncelleme hatası", extra={'record_id': record_id, 'error': str(e)})
            return {
                'success': False,
                'error': str(e)
            }

    # ========== STOK YÖNETİMİ ==========

    def update_stok_from_sayim(self, sku_id: str, konum: str = None) -> bool:
        """
        Sayım sonrası stok kalemini otomatik güncelle

        Args:
            sku_id: SKU record ID
            konum: Ürün konumu (opsiyonel)

        Returns:
            bool: Başarılı mı?
        """
        try:
            from datetime import datetime
            today = datetime.now().strftime('%Y-%m-%d')

            # Bugün bu SKU için kaç adet sayıldı?
            formula = f"AND(IS_SAME({{Timestamp}}, '{today}', 'day'), SEARCH('{sku_id}', ARRAYJOIN({{SKU}})))"
            records = self.sayim_kayitlari.all(formula=formula)
            count = len(records)

            # Stok_Kalemleri tablosunda bu SKU var mı?
            stok_formula = f"SEARCH('{sku_id}', ARRAYJOIN({{SKU}}))"
            stok_records = self.stok_kalemleri.all(formula=stok_formula)

            if stok_records:
                # Güncelle (ilk kaydı)
                record_id = stok_records[0]['id']
                update_data = {
                    'Son_Sayim_Tarihi': today,
                    'Son_Sayim_Miktari': count
                }
                # Konum belirtilmişse güncelle
                if konum:
                    update_data['Konum'] = konum

                self.stok_kalemleri.update(record_id, update_data)
                logger.info(f"Stok güncellendi: {sku_id} → {count} adet")
            else:
                # Yeni oluştur
                create_data = {
                    'SKU': [sku_id],
                    'Konum': konum or 'Genel',
                    'Son_Sayim_Tarihi': today,
                    'Son_Sayim_Miktari': count,
                    'Mevcut_Miktar': count  # İlk sayımda mevcut = sayılan
                }
                self.stok_kalemleri.create(create_data)
                logger.info(f"Yeni stok kalemi oluşturuldu: {sku_id} → {count} adet")

            return True

        except Exception as e:
            logger.error("Stok güncelleme hatası", extra={'sku_id': sku_id, 'error': str(e)})
            return False

    # ========== İSTATİSTİKLER ==========

    def get_today_stats(self) -> Dict[str, Any]:
        """
        Bugünün sayım istatistiklerini getir

        Returns:
            Dict: {
                total: int,
                direkt: int,
                belirsiz: int,
                bulunamadi: int,
                direkt_oran: float
            }
        """
        try:
            # Bugünün kayıtlarını çek
            from datetime import datetime
            today = datetime.now().strftime('%Y-%m-%d')

            formula = f"IS_SAME({{Timestamp}}, '{today}', 'day')"
            records = self.sayim_kayitlari.all(formula=formula)

            total = len(records)
            direkt = sum(1 for r in records if r['fields'].get('Eslesme_Durumu') == 'Direkt')
            belirsiz = sum(1 for r in records if r['fields'].get('Eslesme_Durumu') == 'Belirsiz')
            bulunamadi = sum(1 for r in records if r['fields'].get('Eslesme_Durumu') == 'Bulunamadı')

            direkt_oran = round(direkt / total * 100, 1) if total > 0 else 0

            return {
                'total': total,
                'direkt': direkt,
                'belirsiz': belirsiz,
                'bulunamadi': bulunamadi,
                'direkt_oran': direkt_oran
            }

        except Exception as e:
            logger.error("İstatistik hatası", extra={'error': str(e)})
            return {
                'total': 0,
                'direkt': 0,
                'belirsiz': 0,
                'bulunamadi': 0,
                'direkt_oran': 0
            }

    # ========== MARKALAR ==========

    def get_all_brands(self) -> List[Dict[str, Any]]:
        """
        Tüm markaları listele

        Returns:
            List[Dict]: {id, kod, ad, kategori}
        """
        try:
            # Tüm markaları çek (formül olmadan)
            records = self.markalar.all()

            brands = []
            for record in records:
                fields = record['fields']
                # Sadece Marka Adı olan kayıtları al
                if fields.get('Marka Adı'):
                    brands.append({
                        'id': record['id'],
                        'kod': fields.get('Marka Kodu', ''),
                        'ad': fields.get('Marka Adı', ''),
                        'kategori': fields.get('Kategori', [])
                    })

            # Marka adına göre sırala
            brands.sort(key=lambda x: x['ad'])
            return brands

        except Exception as e:
            logger.error("Marka listesi hatası", extra={'error': str(e)})
            return []

    # ========== YARDIMCI FONKSİYONLAR ==========

    def health_check(self) -> bool:
        """
        Airtable bağlantısını test et

        Returns:
            bool: Bağlantı sağlıklı mı?
        """
        try:
            # Basit bir sorgu yap
            self.markalar.first()
            return True
        except Exception as e:
            logger.error("Health check başarısız", extra={'error': str(e)})
            return False


# Test için
if __name__ == "__main__":
    print("[TEST] Airtable Client Test - Çoklu Workspace\n")

    categories = ['OF', 'GN', 'LN']

    for cat in categories:
        print(f"\n{'='*50}")
        print(f"Kategori: {cat}")
        print('='*50)

        try:
            client = AirtableClient(category=cat)
            print("OK: Baglanti basarili!")

            # Health check
            if client.health_check():
                print("OK: Health check OK")

            # Markalar
            brands = client.get_all_brands()
            print(f"OK: {len(brands)} marka bulundu")
            if brands:
                print(f"  Ornek: {brands[0]['ad']}")

            # İstatistikler
            stats = client.get_today_stats()
            print(f"OK: Bugun {stats['total']} urun sayildi")

        except Exception as e:
            print(f"HATA: Test basarisiz: {e}")

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
from dotenv import load_dotenv

load_dotenv()


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
            formula = f"{{Tedarikçi Barkodu}} = '{barkod}'"
            if barkod.isnumeric():
                formula = f"OR({{Tedarikçi Barkodu}} = '{barkod}', {{Tedarikçi Barkodu}} = {barkod})"

            results = self.urun_katalogu.all(formula=formula)
            return results
        except Exception as e:
            print(f"HATA: Barkod arama hatası: {e}")
            return []

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
            # FIND() fonksiyonu ile kısmi eşleşme
            formula = f"FIND('{partial}', {{Tedarikçi Barkodu}}) = 1"
            results = self.urun_katalogu.all(formula=formula)
            return results
        except Exception as e:
            print(f"HATA: Fuzzy arama hatası: {e}")
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
            print(f"HATA: SKU detay hatası: {e}")
            return None

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
            print(f"HATA: Yeni SKU oluşturma hatası: {e}")
            return {
                'success': False,
                'error': str(e)
            }

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
            term_lower = search_term.lower().replace("'", "\\'")

            # SEARCH fonksiyonu için boş olmayan alanlarda ara
            search_conditions.append(
                f"OR("
                f"IF({{Model Kodu}}, SEARCH('{term_lower}', LOWER({{Model Kodu}})), 0), "
                f"IF({{Model Adı}}, SEARCH('{term_lower}', LOWER({{Model Adı}})), 0), "
                f"IF({{Renk Kodu}}, SEARCH('{term_lower}', LOWER({{Renk Kodu}})), 0), "
                f"IF({{SKU}}, SEARCH('{term_lower}', LOWER({{SKU}})), 0), "
                f"IF({{Arama Kelimeleri}}, SEARCH('{term_lower}', LOWER({{Arama Kelimeleri}})), 0)"
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
            print(f"HATA: Manuel arama hatası: {e}")
            return []

    # ========== SAYIM KAYDI ==========

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
            print(f"HATA: Sayım kaydı oluşturma hatası: {e}")
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
            print(f"HATA: Sayım kaydı güncelleme hatası: {e}")
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
                print(f"Stok güncellendi: {sku_id} → {count} adet")
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
                print(f"Yeni stok kalemi oluşturuldu: {sku_id} → {count} adet")

            return True

        except Exception as e:
            print(f"HATA: Stok güncelleme hatası: {e}")
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
            print(f"HATA: İstatistik hatası: {e}")
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
            print(f"HATA: Marka listesi hatası: {e}")
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
            print(f"HATA: Health check başarısız: {e}")
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

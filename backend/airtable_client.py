"""
Airtable Client - Konyalı Optik Sayım Sistemi
Tüm Airtable işlemleri bu modül üzerinden yapılır.
"""

from pyairtable import Api
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()


class AirtableClient:
    """Airtable bağlantı ve işlem yöneticisi"""

    def __init__(self):
        """Airtable API bağlantısını başlat"""
        token = os.getenv('AIRTABLE_TOKEN')
        base_id = os.getenv('AIRTABLE_BASE_ID')

        if not token or not base_id:
            raise ValueError("AIRTABLE_TOKEN ve AIRTABLE_BASE_ID .env dosyasında tanımlanmalı!")

        self.api = Api(token)
        self.base = self.api.base(base_id)

        # Tablo referansları
        self.master_sku = self.base.table('Master_SKU')
        self.tedarikci_liste = self.base.table('Tedarikci_Urun_Listesi')
        self.sayim_kayitlari = self.base.table('Sayim_Kayitlari')
        self.markalar = self.base.table('Markalar')
        self.stok_kalemleri = self.base.table('Stok_Kalemleri')

    # ========== BARKOD ARAMA ==========

    def search_by_barcode(self, barkod: str) -> List[Dict[str, Any]]:
        """
        Tedarikci_Urun_Listesi tablosunda barkod ara

        Args:
            barkod: Aranan barkod (string)

        Returns:
            List[Dict]: Bulunan tedarikçi kayıtları
        """
        try:
            # Barkodu hem metin hem de sayı olarak aramayı dene
            # Bu, Airtable'daki alanın formatı (Metin veya Sayı) ne olursa olsun eşleşmeyi sağlar
            formula = f"{{Tedarikci_Barkodu}} = '{barkod}'"
            if barkod.isnumeric():
                formula = f"OR({{Tedarikci_Barkodu}} = '{barkod}', {{Tedarikci_Barkodu}} = {barkod})"

            results = self.tedarikci_liste.all(formula=formula)
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
            formula = f"FIND('{partial}', {{Tedarikci_Barkodu}}) = 1"
            results = self.tedarikci_liste.all(formula=formula)
            return results
        except Exception as e:
            print(f"HATA: Fuzzy arama hatası: {e}")
            return []

    # ========== SKU İŞLEMLERİ ==========

    def get_sku_details(self, sku_record_id: str) -> Optional[Dict[str, Any]]:
        """
        Master_SKU tablosundan ürün detaylarını getir

        Args:
            sku_record_id: Airtable record ID (rec...)

        Returns:
            Dict: SKU detayları veya None
        """
        try:
            record = self.master_sku.get(sku_record_id)
            return record['fields']
        except Exception as e:
            print(f"HATA: SKU detay hatası: {e}")
            return None

    def create_new_sku(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Master_SKU tablosuna yeni ürün ekle (liste dışı ürünler için)

        Args:
            data: Ürün verileri
                - Kategori (str): "OF" | "GN" | "CM" | "LN"
                - Marka (list of record IDs): Marka ID'si
                - Model_Kodu (str)
                - Model_Adi (str, optional)
                - Renk_Kodu (str)
                - Renk_Adi (str, optional)
                - Ekartman (int)

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

            # SKU alanını ekle
            data['SKU'] = sku

            # Durum alanını varsayılan olarak Aktif yap
            if 'Durum' not in data:
                data['Durum'] = 'Aktif'

            # Kaydı oluştur
            record = self.master_sku.create(data)

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
        Master_SKU tablosunda manuel arama
        Model kodu, model adı, renk kodu, SKU ile arama yapar

        Args:
            search_term: Arama terimi
            context_brand: Marka filtresi (record ID)
            context_category: Kategori filtresi (OF/GN/CM/LN)

        Returns:
            List[Dict]: Bulunan SKU kayıtları
        """
        try:
            # Arama formülü oluştur
            search_conditions = []

            # Arama terimi - birden fazla alanda ara (case-insensitive)
            # Arama_Kelimeleri alanını da dahil et
            term_lower = search_term.lower().replace("'", "\\'")

            # SEARCH fonksiyonu için boş olmayan alanlarda ara
            # IF kullanarak boş alanları atla
            search_conditions.append(
                f"OR("
                f"IF({{Model_Kodu}}, SEARCH('{term_lower}', LOWER({{Model_Kodu}})), 0), "
                f"IF({{Model_Adi}}, SEARCH('{term_lower}', LOWER({{Model_Adi}})), 0), "
                f"IF({{Renk_Kodu}}, SEARCH('{term_lower}', LOWER({{Renk_Kodu}})), 0), "
                f"IF({{SKU}}, SEARCH('{term_lower}', LOWER({{SKU}})), 0), "
                f"IF({{Arama_Kelimeleri}}, SEARCH('{term_lower}', LOWER({{Arama_Kelimeleri}})), 0)"
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
            results = self.master_sku.all(formula=formula, max_records=20)
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
                - Durum (str): "Tamamlandı" | "Beklemede" | "İnceleme Gerekli"
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
                # Sadece Marka_Adi olan kayıtları al
                if fields.get('Marka_Adi'):
                    brands.append({
                        'id': record['id'],
                        'kod': fields.get('Marka_Kodu', ''),
                        'ad': fields.get('Marka_Adi', ''),
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
    print("[TEST] Airtable Client Test\n")

    try:
        client = AirtableClient()
        print("OK: Bağlantı başarılı!")

        # Health check
        if client.health_check():
            print("OK: Health check OK")

        # Markalar
        brands = client.get_all_brands()
        print(f"OK: {len(brands)} marka bulundu")
        if brands:
            print(f"   Örnek: {brands[0]['ad']}")

        # İstatistikler
        stats = client.get_today_stats()
        print(f"OK: Bugün {stats['total']} ürün sayıldı")

    except Exception as e:
        print(f"HATA: Test başarısız: {e}")

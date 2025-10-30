"""
Barkod Matcher - Konyalı Optik Sayım Sistemi
Akıllı barkod eşleştirme algoritması

YENİ YAPI:
- Artık tek tablo (Urun_Katalogu) - barkod ve ürün bilgileri birlikte
"""

from typing import Dict, Optional, List, Any
from fuzzywuzzy import fuzz
from airtable_client import AirtableClient


class BarcodeMatcher:
    """Barkod eşleştirme ve SKU bulma motoru"""

    def __init__(self, airtable_client: AirtableClient):
        """
        Args:
            airtable_client: Airtable bağlantı nesnesi
        """
        self.client = airtable_client

    def match(
        self,
        barkod: str,
        context_brand: Optional[str] = None,
        context_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Ana eşleştirme fonksiyonu

        Algoritma:
        1. Direkt barkod eşleşmesi (exact match)
        2. Fuzzy search (ilk 10 hane)
        3. Bulunamadı durumu

        Args:
            barkod: Okutulan barkod
            context_brand: Marka bağlamı (record ID, optional)
            context_category: Kategori bağlamı (OF/GN/LN, optional)

        Returns:
            {
                'status': 'direkt' | 'belirsiz' | 'bulunamadi',
                'confidence': 0-100,
                'sku_id': str or None,
                'product': dict or None,
                'candidates': list (belirsiz durumda)
            }
        """

        # 1. Direkt arama - YENİ: Artık direkt Urun_Katalogu'nda ara
        urun_records = self.client.search_by_barcode(barkod)

        if len(urun_records) == 0:
            # 2. Fuzzy search dene
            fuzzy_results = self._fuzzy_search(barkod, context_brand, context_category)
            if fuzzy_results:
                return fuzzy_results

            # Bulunamadı
            return {
                'status': 'bulunamadi',
                'confidence': 0,
                'sku_id': None,
                'product': None
            }

        elif len(urun_records) == 1:
            # Tek sonuç - Direkt eşleşme (context filtresi uygula)
            return self._process_single_match(urun_records[0], context_brand, context_category)

        else:
            # Çoklu sonuç - Belirsiz (context ile filtrelemeyi dene)
            return self._process_multiple_matches(
                urun_records,
                context_brand,
                context_category
            )

    def _process_single_match(
        self,
        urun_record: Dict,
        context_brand: Optional[str] = None,
        context_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Tek ürün kaydını işle

        Args:
            urun_record: Urun_Katalogu kaydı (YENİ: artık tedarikçi kaydı değil)
            context_brand: Marka filtresi
            context_category: Kategori filtresi

        Returns:
            Eşleştirme sonucu
        """
        fields = urun_record['fields']
        sku_id = urun_record['id']

        # Context filtresi uygula
        if context_brand:
            marka_links = fields.get('Marka', [])
            if not marka_links or marka_links[0] != context_brand:
                return {
                    'status': 'bulunamadi',
                    'confidence': 0,
                    'sku_id': None,
                    'product': None
                }

        if context_category:
            kategori = fields.get('Kategori')
            if kategori != context_category:
                return {
                    'status': 'bulunamadi',
                    'confidence': 0,
                    'sku_id': None,
                    'product': None
                }

        return {
            'status': 'direkt',
            'confidence': 100,
            'sku_id': sku_id,
            'product': self._format_product(fields, sku_id)
        }

    def _process_multiple_matches(
        self,
        urun_records: List[Dict],
        context_brand: Optional[str] = None,
        context_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Çoklu ürün kaydını işle
        Context varsa filtrele, yoksa tüm adayları döndür

        Args:
            urun_records: Bulunan ürün kayıtları
            context_brand: Marka filtresi
            context_category: Kategori filtresi

        Returns:
            Eşleştirme sonucu (belirsiz)
        """
        candidates = []

        for record in urun_records[:10]:  # İlk 10 aday
            fields = record['fields']
            sku_id = record['id']

            # Context filtresi uygula
            if context_brand:
                marka_links = fields.get('Marka', [])
                if not marka_links or marka_links[0] != context_brand:
                    continue

            if context_category:
                kategori = fields.get('Kategori')
                if kategori != context_category:
                    continue

            candidates.append({
                'sku_id': sku_id,
                'product': self._format_product(fields, sku_id)
            })

        if not candidates:
            return {
                'status': 'bulunamadi',
                'confidence': 0,
                'sku_id': None,
                'product': None
            }

        if len(candidates) == 1:
            # Filtreleme sonucu tek aday kaldı
            candidate = candidates[0]
            return {
                'status': 'direkt',
                'confidence': 95,
                'sku_id': candidate['sku_id'],
                'product': candidate['product']
            }

        # Hala çoklu aday var - belirsiz
        first_candidate = candidates[0]
        return {
            'status': 'belirsiz',
            'confidence': 80,
            'sku_id': first_candidate['sku_id'],
            'product': first_candidate['product'],
            'candidates': candidates
        }

    def _fuzzy_search(
        self,
        barkod: str,
        context_brand: Optional[str] = None,
        context_category: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fuzzy matching - barkodun ilk 10 hanesine göre ara

        Args:
            barkod: Aranan barkod
            context_brand: Marka filtresi
            context_category: Kategori filtresi

        Returns:
            Eşleştirme sonucu veya None
        """
        if len(barkod) < 10:
            return None

        # İlk 10 haneye göre ara
        fuzzy_results = self.client.fuzzy_search_barcode(barkod, min_length=10)

        if not fuzzy_results:
            return None

        # Benzerlik skorlarını hesapla
        matches = []
        for record in fuzzy_results:
            fields = record['fields']
            stored_barcode = fields.get('Tedarikçi Barkodu', '')

            if len(stored_barcode) < 10:
                continue

            # İlk 10 haneyi karşılaştır
            score = fuzz.ratio(barkod[:10], stored_barcode[:10])

            if score >= 85:  # %85 ve üzeri benzerlik
                matches.append({
                    'record': record,
                    'score': score
                })

        if not matches:
            return None

        # En yüksek skora göre sırala
        matches.sort(key=lambda x: x['score'], reverse=True)

        # Context filtresi uygula
        filtered_matches = []
        for match in matches:
            record = match['record']
            fields = record['fields']
            sku_id = record['id']

            # Context kontrolü
            if context_brand:
                marka_links = fields.get('Marka', [])
                if not marka_links or marka_links[0] != context_brand:
                    continue

            if context_category:
                kategori = fields.get('Kategori')
                if kategori != context_category:
                    continue

            filtered_matches.append({
                'sku_id': sku_id,
                'product': self._format_product(fields, sku_id),
                'score': match['score']
            })

        if not filtered_matches:
            return None

        if len(filtered_matches) == 1:
            # Tek sonuç
            result = filtered_matches[0]
            return {
                'status': 'direkt',
                'confidence': result['score'],
                'sku_id': result['sku_id'],
                'product': result['product']
            }

        # Çoklu sonuç
        return {
            'status': 'belirsiz',
            'confidence': filtered_matches[0]['score'],
            'sku_id': filtered_matches[0]['sku_id'],
            'product': filtered_matches[0]['product'],
            'candidates': filtered_matches
        }

    def _format_product(self, product_fields: Dict, sku_id: str) -> Dict[str, Any]:
        """
        Ürün bilgilerini frontend için formatla

        Args:
            product_fields: Urun_Katalogu fields
            sku_id: SKU record ID

        Returns:
            Formatlanmış ürün bilgisi
        """
        # Marka adını lookup'tan al (YENİ: Lookup field adı değişmiş olabilir)
        # Marka Adı artık lookup field olarak tanımlı
        marka_adi = product_fields.get('Marka Adı', [''])[0] if isinstance(
            product_fields.get('Marka Adı'), list
        ) else product_fields.get('Marka Adı', '')

        return {
            'id': sku_id,
            'sku': product_fields.get('SKU', ''),
            'kategori': product_fields.get('Kategori', ''),
            'marka': marka_adi,
            'model_kodu': product_fields.get('Model Kodu', ''),
            'model_adi': product_fields.get('Model Adı', ''),
            'renk_kodu': product_fields.get('Renk Kodu', ''),
            'renk_adi': product_fields.get('Renk Adı', ''),
            'ekartman': product_fields.get('Ekartman', ''),
            'birim_fiyat': product_fields.get('Birim Fiyat', 0),
            'durum': product_fields.get('Durum', 'Aktif')
        }


# Test için
if __name__ == "__main__":
    print("[TEST] Barkod Matcher Test\n")

    try:
        from airtable_client import AirtableClient

        # Kategori seç
        print("Kategori seçin:")
        print("1. OF - Optik Çerçeve")
        print("2. GN - Güneş Gözlüğü")
        print("3. LN - Lens")

        choice = input("Seçim (1/2/3): ").strip()
        category_map = {'1': 'OF', '2': 'GN', '3': 'LN'}
        category = category_map.get(choice, 'OF')

        client = AirtableClient(category=category)
        matcher = BarcodeMatcher(client)

        print(f"\nOK: Matcher başlatıldı! (Kategori: {category})")
        print("\n📝 Test barkodu girin (veya 'q' ile çık):")

        while True:
            barkod = input("\nBarkod: ").strip()

            if barkod.lower() == 'q':
                break

            if not barkod:
                continue

            print(f"\n🔍 Arıyor: {barkod}")
            result = matcher.match(barkod)

            print(f"\n📊 Sonuç:")
            print(f"   Status: {result['status']}")
            print(f"   Güven: {result['confidence']}%")

            if result['product']:
                p = result['product']
                print(f"   SKU: {p['sku']}")
                print(f"   Model: {p['model_kodu']} - {p['model_adi']}")
                print(f"   Renk: {p['renk_adi']} ({p['renk_kodu']})")
                print(f"   Ekartman: {p['ekartman']}")

            if result.get('candidates'):
                print(f"\nUYARI: {len(result['candidates'])} aday bulundu")

    except Exception as e:
        print(f"HATA: Test başarısız: {e}")

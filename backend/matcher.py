"""
Barkod Matcher - Konyalı Optik Sayım Sistemi
Akıllı barkod eşleştirme algoritması
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
            context_category: Kategori bağlamı (OF/GN/CM/LN, optional)

        Returns:
            {
                'status': 'direkt' | 'belirsiz' | 'bulunamadi',
                'confidence': 0-100,
                'sku_id': str or None,
                'product': dict or None,
                'candidates': list (belirsiz durumda),
                'tedarikci_kaydi_id': str or None
            }
        """

        # 1. Direkt arama
        tedarikci_records = self.client.search_by_barcode(barkod)

        if len(tedarikci_records) == 0:
            # 2. Fuzzy search dene
            fuzzy_results = self._fuzzy_search(barkod, context_brand, context_category)
            if fuzzy_results:
                return fuzzy_results

            # Bulunamadı
            return {
                'status': 'bulunamadi',
                'confidence': 0,
                'sku_id': None,
                'product': None,
                'tedarikci_kaydi_id': None
            }

        elif len(tedarikci_records) == 1:
            # Tek sonuç - Direkt eşleşme (context filtresi uygula)
            return self._process_single_match(tedarikci_records[0], context_brand, context_category)

        else:
            # Çoklu sonuç - Belirsiz (context ile filtrelemeyi dene)
            return self._process_multiple_matches(
                tedarikci_records,
                context_brand,
                context_category
            )

    def _process_single_match(
        self,
        tedarikci_record: Dict,
        context_brand: Optional[str] = None,
        context_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Tek tedarikçi kaydını işle ve SKU detaylarını getir

        Args:
            tedarikci_record: Tedarikçi ürün listesi kaydı
            context_brand: Marka filtresi
            context_category: Kategori filtresi

        Returns:
            Eşleştirme sonucu
        """
        fields = tedarikci_record['fields']
        tedarikci_kaydi_id = tedarikci_record['id']

        # Master_SKU bağlantısını bul
        sku_links = fields.get('Master_SKU', [])

        if not sku_links:
            return {
                'status': 'bulunamadi',
                'confidence': 0,
                'sku_id': None,
                'product': None,
                'tedarikci_kaydi_id': tedarikci_kaydi_id
            }

        # İlk SKU'yu al (genelde 1 tane olur)
        sku_id = sku_links[0]
        product = self.client.get_sku_details(sku_id)

        if not product:
            return {
                'status': 'bulunamadi',
                'confidence': 0,
                'sku_id': sku_id,
                'product': None,
                'tedarikci_kaydi_id': tedarikci_kaydi_id
            }

        # Context filtresi uygula
        if context_brand:
            marka_links = product.get('Marka', [])
            if not marka_links or marka_links[0] != context_brand:
                return {
                    'status': 'bulunamadi',
                    'confidence': 0,
                    'sku_id': None,
                    'product': None,
                    'tedarikci_kaydi_id': None
                }

        if context_category:
            kategori = product.get('Kategori')
            if kategori != context_category:
                return {
                    'status': 'bulunamadi',
                    'confidence': 0,
                    'sku_id': None,
                    'product': None,
                    'tedarikci_kaydi_id': None
                }

        return {
            'status': 'direkt',
            'confidence': 100,
            'sku_id': sku_id,
            'product': self._format_product(product, sku_id),
            'tedarikci_kaydi_id': tedarikci_kaydi_id
        }

    def _process_multiple_matches(
        self,
        tedarikci_records: List[Dict],
        context_brand: Optional[str] = None,
        context_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Çoklu tedarikçi kaydını işle
        Context varsa filtrele, yoksa tüm adayları döndür

        Args:
            tedarikci_records: Bulunan tedarikçi kayıtları
            context_brand: Marka filtresi
            context_category: Kategori filtresi

        Returns:
            Eşleştirme sonucu (belirsiz)
        """
        candidates = []

        for record in tedarikci_records[:10]:  # İlk 10 aday
            fields = record['fields']
            sku_links = fields.get('Master_SKU', [])

            if not sku_links:
                continue

            sku_id = sku_links[0]
            product = self.client.get_sku_details(sku_id)

            if not product:
                continue

            # Context filtresi uygula
            if context_brand:
                marka_links = product.get('Marka', [])
                if not marka_links or marka_links[0] != context_brand:
                    continue

            if context_category:
                kategori = product.get('Kategori')
                if kategori != context_category:
                    continue

            candidates.append({
                'sku_id': sku_id,
                'product': self._format_product(product, sku_id),
                'tedarikci_kaydi_id': record['id']
            })

        if not candidates:
            return {
                'status': 'bulunamadi',
                'confidence': 0,
                'sku_id': None,
                'product': None,
                'tedarikci_kaydi_id': None
            }

        if len(candidates) == 1:
            # Filtreleme sonucu tek aday kaldı
            candidate = candidates[0]
            return {
                'status': 'direkt',
                'confidence': 95,
                'sku_id': candidate['sku_id'],
                'product': candidate['product'],
                'tedarikci_kaydi_id': candidate['tedarikci_kaydi_id']
            }

        # Hala çoklu aday var - belirsiz
        first_candidate = candidates[0]
        return {
            'status': 'belirsiz',
            'confidence': 80,
            'sku_id': first_candidate['sku_id'],
            'product': first_candidate['product'],
            'candidates': candidates,
            'tedarikci_kaydi_id': first_candidate['tedarikci_kaydi_id']
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
            stored_barcode = fields.get('Tedarikci_Barkodu', '')

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
            sku_links = fields.get('Master_SKU', [])

            if not sku_links:
                continue

            sku_id = sku_links[0]
            product = self.client.get_sku_details(sku_id)

            if not product:
                continue

            # Context kontrolü
            if context_brand:
                marka_links = product.get('Marka', [])
                if not marka_links or marka_links[0] != context_brand:
                    continue

            if context_category:
                kategori = product.get('Kategori')
                if kategori != context_category:
                    continue

            filtered_matches.append({
                'sku_id': sku_id,
                'product': self._format_product(product, sku_id),
                'tedarikci_kaydi_id': record['id'],
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
                'product': result['product'],
                'tedarikci_kaydi_id': result['tedarikci_kaydi_id']
            }

        # Çoklu sonuç
        return {
            'status': 'belirsiz',
            'confidence': filtered_matches[0]['score'],
            'sku_id': filtered_matches[0]['sku_id'],
            'product': filtered_matches[0]['product'],
            'candidates': filtered_matches,
            'tedarikci_kaydi_id': filtered_matches[0]['tedarikci_kaydi_id']
        }

    def _format_product(self, product_fields: Dict, sku_id: str) -> Dict[str, Any]:
        """
        Ürün bilgilerini frontend için formatla

        Args:
            product_fields: Master_SKU fields
            sku_id: SKU record ID

        Returns:
            Formatlanmış ürün bilgisi
        """
        # Marka adını lookup'tan al
        marka_adi = product_fields.get('Marka_Adi (from Marka)', [''])[0] if isinstance(
            product_fields.get('Marka_Adi (from Marka)'), list
        ) else product_fields.get('Marka_Adi (from Marka)', '')

        return {
            'id': sku_id,
            'sku': product_fields.get('SKU', ''),
            'kategori': product_fields.get('Kategori', ''),
            'marka': marka_adi,
            'model_kodu': product_fields.get('Model_Kodu', ''),
            'model_adi': product_fields.get('Model_Adi', ''),
            'renk_kodu': product_fields.get('Renk_Kodu', ''),
            'renk_adi': product_fields.get('Renk_Adi', ''),
            'ekartman': product_fields.get('Ekartman', ''),
            'birim_fiyat': product_fields.get('Birim_Fiyat', 0),
            'durum': product_fields.get('Durum', 'Aktif')
        }


# Test için
if __name__ == "__main__":
    print("[TEST] Barkod Matcher Test\n")

    try:
        from airtable_client import AirtableClient

        client = AirtableClient()
        matcher = BarcodeMatcher(client)

        print("OK: Matcher başlatıldı!")
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

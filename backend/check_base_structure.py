"""
Base yapilarini kontrol et - tablo isimlerini ve alanlarini listele
"""

from pyairtable import Api
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('AIRTABLE_TOKEN')
bases = {
    'Optik': os.getenv('AIRTABLE_BASE_OPTIK'),
    'Gunes': os.getenv('AIRTABLE_BASE_GUNES'),
    'Lens': os.getenv('AIRTABLE_BASE_LENS')
}

api = Api(token)

for category_name, base_id in bases.items():
    print(f"\n{'='*60}")
    print(f"BASE: {category_name} ({base_id})")
    print('='*60)

    try:
        base = api.base(base_id)

        # Bilinen tablo isimlerini dene
        known_tables = [
            'Urun_Katalogu',
            'Sayim_Kayitlari',
            'Markalar',
            'Stok_Kalemleri',
            # Alternatif isimler (boşluksuz)
            'UrunKatalogu',
            'SayimKayitlari',
            # İngilizce versiyonlar
            'Products',
            'Counts',
            'Brands',
            'Stock'
        ]

        found_tables = []

        for table_name in known_tables:
            try:
                table = base.table(table_name)
                # İlk kaydı almaya çalış (tablo varsa, boş bile olsa çalışır)
                table.first()
                found_tables.append(table_name)
                print(f"  [OK] Tablo bulundu: {table_name}")
            except Exception as e:
                if '404' in str(e) or 'not found' in str(e).lower():
                    # Tablo yok
                    pass
                elif '403' in str(e):
                    # İzin yok ama tablo var
                    found_tables.append(f"{table_name} (izin hatasi)")
                    print(f"  [IZIN] Tablo var ama erisim yok: {table_name}")
                else:
                    # Başka hata
                    pass

        if not found_tables:
            print("  [UYARI] Hic tablo bulunamadi!")
            print("  Base bos olabilir veya tablo isimleri farkli olabilir")
        else:
            print(f"\n  Toplam {len(found_tables)} tablo bulundu")

    except Exception as e:
        print(f"  [HATA] Base erisim hatasi: {e}")

print("\n" + "="*60)
print("KONTROL TAMAMLANDI")
print("="*60)

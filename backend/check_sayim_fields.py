"""
Sayim_Kayitlari tablosundaki field adlarını kontrol et
"""
from airtable_client import AirtableClient
from dotenv import load_dotenv

load_dotenv()

def check_fields():
    """Sayim_Kayitlari field adlarını listele"""
    
    categories = ['OF', 'GN', 'LN']
    
    for cat in categories:
        print(f"\n{'='*60}")
        print(f"Kategori: {cat}")
        print('='*60)
        
        try:
            client = AirtableClient(category=cat)
            
            # İlk kaydı al (varsa)
            records = client.sayim_kayitlari.all(max_records=1)
            
            if records:
                fields = records[0]['fields']
                print(f"\n✅ Bulunan Field'ler:")
                for field_name in sorted(fields.keys()):
                    value = fields[field_name]
                    print(f"  - {field_name}: {type(value).__name__}")
            else:
                print("\n⚠️  Tabloda kayıt yok, schema kontrol edilemiyor")
                
                # Boş kayıt oluşturup field'leri görelim
                print("\n📝 Beklenen field'ler:")
                expected_fields = [
                    'Okutulan Barkod',
                    'SKU',
                    'Eşleşme Durumu',
                    'Bağlam Marka',
                    'Bağlam Kategori',
                    'Manuel Arama Terimi',
                    'Okutulan UTS QR',
                    'Notlar',
                    'Sayan Ekip',
                    'Timestamp',
                    'Sayım Günü'
                ]
                for field in expected_fields:
                    print(f"  - {field}")
                
        except Exception as e:
            print(f"❌ HATA: {e}")

if __name__ == "__main__":
    print("Sayim_Kayitlari Field Kontrolü")
    check_fields()


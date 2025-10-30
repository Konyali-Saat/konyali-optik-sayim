# Airtable Workspace Kurulum Promptları

Bu promptları her workspace için Airtable AI'ye sırayla verin.

---

## WORKSPACE 1: Konyalı Optik - Optik Çerçeveler

### Prompt:

```
Bu workspace'te optik çerçeve ürünleri için sayım sistemi kurulacak. Aşağıdaki 4 tabloyu oluştur:

## 1. Tablo: Urun_Katalogu

Bu tablo hem master ürün bilgilerini hem de tedarikçi bilgilerini içeriyor.

Alanlar:
- SKU (Formula): {Kategori} & "-" & {Marka_Kodu} & "-" & {Model_Kodu} & "-" & {Renk_Kodu} & "-" & STR({Ekartman})
- Kategori (Single select): Varsayılan "OF", opsiyonlar: "OF"
- Marka (Link to Markalar table)
- Marka_Kodu (Lookup from Marka): Marka tablosundan Marka_Kodu alanını çek
- Marka_Adi (Lookup from Marka): Marka tablosundan Marka_Adi alanını çek
- Model_Kodu (Single line text): Zorunlu
- Model_Adi (Single line text)
- Renk_Kodu (Single line text): Zorunlu
- Renk_Adi (Single line text)
- Ekartman (Number): Integer, zorunlu
- Birim_Fiyat (Currency): TRY, varsayılan 0
- Tedarikci_Barkodu (Single line text): Zorunlu, benzersiz olmalı
- Tedarikci_Adi (Single select): Opsiyonlar: "Safilo", "Luxottica", "Bausch & Lomb", "Diğer"
- Tedarikci_SKU (Single line text)
- Tedarikci_Fiyat (Currency): TRY
- Durum (Single select): Varsayılan "Aktif", opsiyonlar: "Aktif", "Pasif", "Sonlandırıldı"
- Arama_Kelimeleri (Long text): Elle eklenen arama terimleri
- Kayit_Tarihi (Created time)
- Son_Guncelleme (Last modified time)

Views:
1. "Tüm Ürünler" (default): Tüm kayıtlar
2. "Aktif Ürünler": Durum = Aktif filtresi
3. "Marka Bazlı": Marka'ya göre grupla
4. "Tedarikçi Bazlı": Tedarikci_Adi'ye göre grupla
5. "Barkod Arama": Tedarikci_Barkodu, Model_Kodu, SKU görünür

## 2. Tablo: Sayim_Kayitlari

Alanlar:
- Okutulan_Barkod (Single line text): Zorunlu
- SKU (Link to Urun_Katalogu table)
- Eslesme_Durumu (Single select): Opsiyonlar: "Direkt", "Belirsiz", "Bulunamadı", "Manuel"
- Sayan_Ekip (Single line text): Kimin sayım yaptığı
- Timestamp (Created time)
- Baglam_Marka (Link to Markalar table)
- Baglam_Kategori (Single select): "OF"
- Manuel_Arama_Terimi (Single line text)
- Okutulan_UTS_QR (Single line text)
- Notlar (Long text)
- Fotograf (Attachment)

Views:
1. "Tüm Sayımlar" (default)
2. "Bugün": Timestamp = Today filtresi
3. "Bu Hafta": Timestamp = This Week filtresi
4. "Direkt Eşleşmeler": Eslesme_Durumu = Direkt
5. "Bulunamayanlar": Eslesme_Durumu = Bulunamadı
6. "Kişi Bazlı": Sayan_Ekip'e göre grupla

## 3. Tablo: Markalar

Alanlar:
- Marka_Adi (Single line text): Primary field, zorunlu
- Marka_Kodu (Single line text): Zorunlu, 2-3 karakter
- Kategori (Multiple select): Opsiyonlar: "OF"
- Logo (Attachment)
- Durum (Single select): Varsayılan "Aktif", opsiyonlar: "Aktif", "Pasif"
- Kayit_Tarihi (Created time)

Views:
1. "Aktif Markalar" (default): Durum = Aktif filtresi
2. "Tüm Markalar"

## 4. Tablo: Stok_Kalemleri

Alanlar:
- SKU (Link to Urun_Katalogu table): Zorunlu
- Konum (Single line text): Örn: "Raf A12", "Vitrin 3"
- Mevcut_Miktar (Number): Integer, varsayılan 0
- Hedef_Miktar (Number): Integer
- Son_Sayim_Tarihi (Date)
- Son_Sayim_Miktari (Number): Integer
- Fark (Formula): {Mevcut_Miktar} - {Son_Sayim_Miktari}
- Notlar (Long text)

Views:
1. "Tüm Stok" (default)
2. "Konum Bazlı": Konum'a göre grupla
3. "Eksik Stok": Mevcut_Miktar < Hedef_Miktar filtresi
4. "Fark Var": Fark != 0 filtresi
```

---

## WORKSPACE 2: Konyalı Optik - Güneş Gözlükleri

### Prompt:

```
Bu workspace'te güneş gözlüğü ürünleri için sayım sistemi kurulacak. Aşağıdaki 4 tabloyu oluştur:

## 1. Tablo: Urun_Katalogu

Alanlar:
- SKU (Formula): {Kategori} & "-" & {Marka_Kodu} & "-" & {Model_Kodu} & "-" & {Renk_Kodu} & "-" & STR({Ekartman})
- Kategori (Single select): Varsayılan "GN", opsiyonlar: "GN"
- Marka (Link to Markalar table)
- Marka_Kodu (Lookup from Marka): Marka tablosundan Marka_Kodu alanını çek
- Marka_Adi (Lookup from Marka): Marka tablosundan Marka_Adi alanını çek
- Model_Kodu (Single line text): Zorunlu
- Model_Adi (Single line text)
- Renk_Kodu (Single line text): Zorunlu
- Renk_Adi (Single line text)
- Ekartman (Number): Integer, zorunlu
- Birim_Fiyat (Currency): TRY, varsayılan 0
- Tedarikci_Barkodu (Single line text): Zorunlu, benzersiz olmalı
- Tedarikci_Adi (Single select): Opsiyonlar: "Safilo", "Luxottica", "Bausch & Lomb", "Diğer"
- Tedarikci_SKU (Single line text)
- Tedarikci_Fiyat (Currency): TRY
- Durum (Single select): Varsayılan "Aktif", opsiyonlar: "Aktif", "Pasif", "Sonlandırıldı"
- Arama_Kelimeleri (Long text)
- Kayit_Tarihi (Created time)
- Son_Guncelleme (Last modified time)

Views:
1. "Tüm Ürünler" (default)
2. "Aktif Ürünler": Durum = Aktif
3. "Marka Bazlı": Marka'ya göre grupla
4. "Tedarikçi Bazlı": Tedarikci_Adi'ye göre grupla
5. "Barkod Arama": Tedarikci_Barkodu, Model_Kodu, SKU görünür

## 2. Tablo: Sayim_Kayitlari

Alanlar:
- Okutulan_Barkod (Single line text): Zorunlu
- SKU (Link to Urun_Katalogu table)
- Eslesme_Durumu (Single select): Opsiyonlar: "Direkt", "Belirsiz", "Bulunamadı", "Manuel"
- Sayan_Ekip (Single line text)
- Timestamp (Created time)
- Baglam_Marka (Link to Markalar table)
- Baglam_Kategori (Single select): "GN"
- Manuel_Arama_Terimi (Single line text)
- Notlar (Long text)
- Fotograf (Attachment)

Views:
1. "Tüm Sayımlar" (default)
2. "Bugün": Timestamp = Today
3. "Bu Hafta": Timestamp = This Week
4. "Direkt Eşleşmeler": Eslesme_Durumu = Direkt
5. "Bulunamayanlar": Eslesme_Durumu = Bulunamadı
6. "Kişi Bazlı": Sayan_Ekip'e göre grupla

## 3. Tablo: Markalar

Alanlar:
- Marka_Adi (Single line text): Primary field, zorunlu
- Marka_Kodu (Single line text): Zorunlu, 2-3 karakter
- Kategori (Multiple select): Opsiyonlar: "GN"
- Logo (Attachment)
- Durum (Single select): Varsayılan "Aktif", opsiyonlar: "Aktif", "Pasif"
- Kayit_Tarihi (Created time)

Views:
1. "Aktif Markalar" (default): Durum = Aktif
2. "Tüm Markalar"

## 4. Tablo: Stok_Kalemleri

Alanlar:
- SKU (Link to Urun_Katalogu table): Zorunlu
- Konum (Single line text)
- Mevcut_Miktar (Number): Integer, varsayılan 0
- Hedef_Miktar (Number): Integer
- Son_Sayim_Tarihi (Date)
- Son_Sayim_Miktari (Number): Integer
- Fark (Formula): {Mevcut_Miktar} - {Son_Sayim_Miktari}
- Notlar (Long text)

Views:
1. "Tüm Stok" (default)
2. "Konum Bazlı": Konum'a göre grupla
3. "Eksik Stok": Mevcut_Miktar < Hedef_Miktar
4. "Fark Var": Fark != 0
```

---

## WORKSPACE 3: Konyalı Optik - Lens

### Prompt:

```
Bu workspace'te lens ürünleri için sayım sistemi kurulacak. Aşağıdaki 4 tabloyu oluştur:

## 1. Tablo: Urun_Katalogu

Alanlar:
- SKU (Formula): {Kategori} & "-" & {Marka_Kodu} & "-" & {Model_Kodu} & "-" & {Renk_Kodu} & "-" & STR({Ekartman})
- Kategori (Single select): Varsayılan "LN", opsiyonlar: "LN"
- Marka (Link to Markalar table)
- Marka_Kodu (Lookup from Marka): Marka tablosundan Marka_Kodu alanını çek
- Marka_Adi (Lookup from Marka): Marka tablosundan Marka_Adi alanını çek
- Model_Kodu (Single line text): Zorunlu
- Model_Adi (Single line text)
- Renk_Kodu (Single line text): Zorunlu (lens için genelde renk kodu yok, "00" kullanılabilir)
- Renk_Adi (Single line text)
- Ekartman (Number): Integer, zorunlu (lens için 0 olabilir)
- Birim_Fiyat (Currency): TRY, varsayılan 0
- Tedarikci_Barkodu (Single line text): Zorunlu, benzersiz olmalı
- Tedarikci_Adi (Single select): Opsiyonlar: "Essilor", "Hoya", "Zeiss", "Diğer"
- Tedarikci_SKU (Single line text)
- Tedarikci_Fiyat (Currency): TRY
- Durum (Single select): Varsayılan "Aktif", opsiyonlar: "Aktif", "Pasif", "Sonlandırıldı"
- Arama_Kelimeleri (Long text)
- Kayit_Tarihi (Created time)
- Son_Guncelleme (Last modified time)

Views:
1. "Tüm Ürünler" (default)
2. "Aktif Ürünler": Durum = Aktif
3. "Marka Bazlı": Marka'ya göre grupla
4. "Tedarikçi Bazlı": Tedarikci_Adi'ye göre grupla
5. "Barkod Arama": Tedarikci_Barkodu, Model_Kodu, SKU görünür

## 2. Tablo: Sayim_Kayitlari

Alanlar:
- Okutulan_Barkod (Single line text): Zorunlu
- SKU (Link to Urun_Katalogu table)
- Eslesme_Durumu (Single select): Opsiyonlar: "Direkt", "Belirsiz", "Bulunamadı", "Manuel"
- Sayan_Ekip (Single line text)
- Timestamp (Created time)
- Baglam_Marka (Link to Markalar table)
- Baglam_Kategori (Single select): "LN"
- Manuel_Arama_Terimi (Single line text)
- Okutulan_UTS_QR (Single line text)
- Notlar (Long text)
- Fotograf (Attachment)

Views:
1. "Tüm Sayımlar" (default)
2. "Bugün": Timestamp = Today
3. "Bu Hafta": Timestamp = This Week
4. "Direkt Eşleşmeler": Eslesme_Durumu = Direkt
5. "Bulunamayanlar": Eslesme_Durumu = Bulunamadı
6. "Kişi Bazlı": Sayan_Ekip'e göre grupla

## 3. Tablo: Markalar

Alanlar:
- Marka_Adi (Single line text): Primary field, zorunlu
- Marka_Kodu (Single line text): Zorunlu, 2-3 karakter
- Kategori (Multiple select): Opsiyonlar: "LN"
- Logo (Attachment)
- Durum (Single select): Varsayılan "Aktif", opsiyonlar: "Aktif", "Pasif"
- Kayit_Tarihi (Created time)

Views:
1. "Aktif Markalar" (default): Durum = Aktif
2. "Tüm Markalar"

## 4. Tablo: Stok_Kalemleri

Alanlar:
- SKU (Link to Urun_Katalogu table): Zorunlu
- Konum (Single line text)
- Mevcut_Miktar (Number): Integer, varsayılan 0
- Hedef_Miktar (Number): Integer
- Son_Sayim_Tarihi (Date)
- Son_Sayim_Miktari (Number): Integer
- Fark (Formula): {Mevcut_Miktar} - {Son_Sayim_Miktari}
- Notlar (Long text)

Views:
1. "Tüm Stok" (default)
2. "Konum Bazlı": Konum'a göre grupla
3. "Eksik Stok": Mevcut_Miktar < Hedef_Miktar
4. "Fark Var": Fark != 0
```

---

## Kurulum Sonrası

Her workspace'i kurduktan sonra:

1. Her workspace'in **Base ID**'sini alın (Settings > API > Base ID)
2. `.env` dosyasına ekleyin:
   ```
   AIRTABLE_BASE_OPTIK=appXXXXXXXXXXXXXX
   AIRTABLE_BASE_GUNES=appYYYYYYYYYYYYYY
   AIRTABLE_BASE_LENS=appZZZZZZZZZZZZZZ
   ```
3. Backend kodunu güncelleyin (aşağıdaki güncellenmiş dosyaları kullanın)

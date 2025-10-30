#!/usr/bin/env python3
"""
PDF to Excel Converter - Luxottica Tedarikçi Dosyaları
Tabula-py kullanarak PDF'deki tabloları Excel'e çevirir
"""

import tabula
import pandas as pd
from pathlib import Path
import sys

def convert_pdf_to_excel(pdf_path, output_path, skip_first_page=True):
    """
    PDF'deki tabloları Excel'e çevir

    Args:
        pdf_path: Kaynak PDF dosyası
        output_path: Hedef Excel dosyası
        skip_first_page: İlk sayfayı atla (True/False)
    """
    print(f"\n{'='*60}")
    print(f"PDF İşleniyor: {pdf_path}")
    print(f"{'='*60}\n")

    try:
        # PDF'deki tüm tabloları oku
        # pages='all' tüm sayfaları okur
        # multiple_tables=True her sayfadaki birden fazla tabloyu algılar
        # lattice=True ızgara çizgileri olan tabloları algılar
        # stream=True ızgara çizgisi olmayan tabloları algılar

        start_page = 2 if skip_first_page else 1

        print(f"[INFO] Sayfalar okunuyor (sayfa {start_page}'den itibaren)...")

        # Önce lattice modu dene (çizgili tablolar için)
        dfs_lattice = tabula.read_pdf(
            pdf_path,
            pages=f'{start_page}-end',
            multiple_tables=True,
            lattice=True,
            pandas_options={'header': None}  # İlk satırı header olarak kullanma
        )

        print(f"[OK] Lattice modu: {len(dfs_lattice)} tablo bulundu")

        # Stream modu da dene (çizgisiz tablolar için)
        dfs_stream = tabula.read_pdf(
            pdf_path,
            pages=f'{start_page}-end',
            multiple_tables=True,
            stream=True,
            pandas_options={'header': None}
        )

        print(f"[OK] Stream modu: {len(dfs_stream)} tablo bulundu")

        # Daha fazla tablo bulan metodu kullan
        dfs = dfs_lattice if len(dfs_lattice) >= len(dfs_stream) else dfs_stream

        if not dfs:
            print("[ERROR] HATA: Hic tablo bulunamadi!")
            return False

        print(f"\n[INFO] Toplam {len(dfs)} tablo islenecek\n")

        # Excel dosyasına yaz
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for idx, df in enumerate(dfs, 1):
                if df is not None and not df.empty:
                    sheet_name = f'Sayfa_{idx}'
                    df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
                    print(f"  [OK] {sheet_name}: {len(df)} satir, {len(df.columns)} sutun")

        print(f"\n[SUCCESS] BASARILI: {output_path}")
        print(f"[INFO] Dosya boyutu: {Path(output_path).stat().st_size / 1024:.1f} KB")
        return True

    except Exception as e:
        print(f"[ERROR] HATA: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Ana fonksiyon"""
    base_dir = Path(__file__).parent
    pdf_dir = base_dir / "Tedarikçi Dosyaları"

    # İşlenecek PDF'ler
    pdfs = [
        ("luxottica-gunes.pdf", "luxottica-gunes-CONVERTED.xlsx"),
        ("luxottica-optik.pdf", "luxottica-optik-CONVERTED.xlsx")
    ]

    print("\n" + "="*60)
    print("PDF to EXCEL Converter - Luxottica")
    print("="*60)
    print(f"Kaynak dizin: {pdf_dir}")
    print(f"Islenecek dosya sayisi: {len(pdfs)}")

    results = []

    for pdf_file, excel_file in pdfs:
        pdf_path = pdf_dir / pdf_file
        output_path = pdf_dir / excel_file

        if not pdf_path.exists():
            print(f"\n[ERROR] Dosya bulunamadi: {pdf_path}")
            results.append(False)
            continue

        success = convert_pdf_to_excel(
            str(pdf_path),
            str(output_path),
            skip_first_page=True  # İlk sayfayı atla
        )
        results.append(success)

    # Özet
    print("\n" + "="*60)
    print("ISLEM OZETI")
    print("="*60)

    for (pdf_file, excel_file), success in zip(pdfs, results):
        status = "[SUCCESS] BASARILI" if success else "[ERROR] BASARISIZ"
        print(f"{status}: {pdf_file} -> {excel_file}")

    success_count = sum(results)
    print(f"\n[INFO] {success_count}/{len(pdfs)} dosya basariyla cevrildi")
    print("="*60 + "\n")

    if success_count == len(pdfs):
        print("[SUCCESS] Tum dosyalar basariyla cevrildi!")
        print("[INFO] Excel dosyalarini 'Tedarikci Dosyalari' klasorunde bulabilirsiniz.")
    else:
        print("[WARNING] Bazi dosyalar cevrilemedi. Hata mesajlarini kontrol edin.")


if __name__ == "__main__":
    main()

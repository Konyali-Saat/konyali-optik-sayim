#!/usr/bin/env python3
"""
PDF to Excel Converter v2 - Luxottica Tedarikçi Dosyaları
pdfplumber kullanarak PDF'deki tabloları Excel'e çevirir (Java gerektirmez!)
"""

import pdfplumber
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
    print(f"PDF Isleniyor: {pdf_path}")
    print(f"{'='*60}\n")

    try:
        all_tables = []

        # PDF'i aç
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            start_page = 1 if skip_first_page else 0

            print(f"[INFO] Toplam {total_pages} sayfa")
            print(f"[INFO] Sayfa {start_page + 1}'den itibaren islenecek\n")

            # Her sayfayı işle
            for page_num, page in enumerate(pdf.pages[start_page:], start=start_page + 1):
                print(f"[INFO] Sayfa {page_num} isleniyor...")

                # Sayfadaki tabloları çıkar
                tables = page.extract_tables()

                if tables:
                    print(f"  [OK] {len(tables)} tablo bulundu")

                    for table_idx, table in enumerate(tables, 1):
                        if table:
                            # Tabloya sayfa ve tablo numarası ekle
                            all_tables.append({
                                'page': page_num,
                                'table_num': table_idx,
                                'data': table
                            })
                else:
                    print(f"  [WARNING] Tablo bulunamadi")

        if not all_tables:
            print("\n[ERROR] Hic tablo bulunamadi!")
            return False

        print(f"\n[INFO] Toplam {len(all_tables)} tablo bulundu")
        print(f"[INFO] Excel dosyasina yaziliyor...\n")

        # Excel dosyasına yaz
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            for idx, table_info in enumerate(all_tables, 1):
                page = table_info['page']
                table_num = table_info['table_num']
                data = table_info['data']

                # DataFrame oluştur
                df = pd.DataFrame(data)

                # Sheet ismi: Sayfa_X_Tablo_Y
                sheet_name = f'Sayfa_{page}'
                if table_num > 1:
                    sheet_name += f'_T{table_num}'

                # Excel'e yaz
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
    print("PDF to EXCEL Converter v2 - Luxottica")
    print("(pdfplumber - Java gerektirmez)")
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

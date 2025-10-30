"""
Airtable Base Schema Sorgulama
Tum tabloları, sütunları ve ilişkileri detaylı olarak listeler
"""

import requests
import os
from dotenv import load_dotenv
import json

load_dotenv()

token = os.getenv('AIRTABLE_TOKEN')
bases = {
    'Optik': os.getenv('AIRTABLE_BASE_OPTIK'),
    'Gunes': os.getenv('AIRTABLE_BASE_GUNES'),
    'Lens': os.getenv('AIRTABLE_BASE_LENS')
}

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
}


def get_base_schema(base_id):
    """Base schema'sını Airtable Meta API'den çek"""
    url = f'https://api.airtable.com/v0/meta/bases/{base_id}/tables'

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"    HATA: Schema alinamadi: {e}")
        return None


def format_field_info(field):
    """Field bilgilerini formatla"""
    field_type = field.get('type', 'unknown')
    field_name = field.get('name', 'unnamed')

    info = f"    - {field_name} ({field_type})"

    # Özel field type bilgileri
    options = field.get('options', {})

    if field_type == 'singleSelect' or field_type == 'multipleSelects':
        choices = options.get('choices', [])
        if choices:
            choice_names = [c.get('name') for c in choices]
            info += f"\n      Secenekler: {', '.join(choice_names)}"

    elif field_type == 'number' or field_type == 'currency':
        precision = options.get('precision', 0)
        info += f" (Precision: {precision})"
        if field_type == 'currency':
            symbol = options.get('symbol', 'TRY')
            info += f" [{symbol}]"

    elif field_type == 'formula':
        formula = options.get('formula', '')
        if formula:
            info += f"\n      Formula: {formula}"

    elif field_type == 'multipleRecordLinks':
        linked_table_id = options.get('linkedTableId', '')
        info += f"\n      Linked to table ID: {linked_table_id}"

    elif field_type == 'multipleLookupValues':
        result_type = options.get('result', {}).get('type', '')
        info += f"\n      Lookup result type: {result_type}"

    elif field_type == 'date' or field_type == 'dateTime':
        date_format = options.get('dateFormat', {}).get('name', '')
        info += f" (Format: {date_format})"

    return info


print("\n" + "="*70)
print("AIRTABLE BASE SCHEMA ANALIZI")
print("="*70)

for category_name, base_id in bases.items():
    print(f"\n{'='*70}")
    print(f"BASE: {category_name}")
    print(f"Base ID: {base_id}")
    print('='*70)

    schema = get_base_schema(base_id)

    if not schema:
        print("  Schema alinamadi!")
        continue

    tables = schema.get('tables', [])

    if not tables:
        print("  Hic tablo bulunamadi!")
        continue

    print(f"\n  Toplam {len(tables)} tablo bulundu:\n")

    for table in tables:
        table_name = table.get('name', 'unnamed')
        table_id = table.get('id', '')
        fields = table.get('fields', [])

        print(f"  [{len(fields)} alan] {table_name}")
        print(f"  Table ID: {table_id}")
        print()

        # Primary field'ı özel olarak göster
        primary_field_id = table.get('primaryFieldId', '')

        for field in fields:
            field_info = format_field_info(field)

            # Primary field'ı işaretle
            if field.get('id') == primary_field_id:
                field_info += " [PRIMARY]"

            print(field_info)

        print()
        print("  " + "-"*60)
        print()

print("\n" + "="*70)
print("ANALIZ TAMAMLANDI")
print("="*70)
print("\nNOT: Bu bilgileri 'airtable-structure-query.md' dosyasindaki")
print("     prompt ile Airtable AI'den aldiginiz bilgilerle karsilastirin.")
print("="*70 + "\n")

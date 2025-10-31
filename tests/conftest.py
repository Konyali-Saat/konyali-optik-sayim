"""
Pytest Configuration and Fixtures
"""

import pytest
import os
import sys
from unittest.mock import Mock, MagicMock

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


@pytest.fixture
def mock_airtable_api():
    """Mock Airtable API"""
    mock_api = Mock()
    mock_base = Mock()
    mock_table = Mock()
    
    mock_api.base.return_value = mock_base
    mock_base.table.return_value = mock_table
    
    return {
        'api': mock_api,
        'base': mock_base,
        'table': mock_table
    }


@pytest.fixture
def sample_product_record():
    """Sample product record from Airtable"""
    return {
        'id': 'recABC123',
        'fields': {
            'SKU': 'OF-RB-2140-901-50',
            'Kategori': 'OF',
            'Marka': ['recMARKA1'],
            'Marka Adı': ['Ray-Ban'],
            'Marka Kodu': ['RB'],
            'Model Kodu': '2140',
            'Model Adı': 'Wayfarer',
            'Renk Kodu': '901',
            'Renk Adı': 'Shiny Black',
            'Ekartman': 50,
            'Birim Fiyat': 350.00,
            'Tedarikçi Barkodu': '8056597412261',
            'Durum': 'Aktif'
        }
    }


@pytest.fixture
def sample_barcode():
    """Sample barcode"""
    return '8056597412261'


@pytest.fixture
def flask_app():
    """Flask app instance for testing"""
    from app import app
    app.config['TESTING'] = True
    return app


@pytest.fixture
def flask_client(flask_app):
    """Flask test client"""
    return flask_app.test_client()


@pytest.fixture(autouse=True)
def setup_env_vars():
    """Setup environment variables for tests"""
    os.environ['AIRTABLE_TOKEN'] = 'test_token_123'
    os.environ['AIRTABLE_BASE_OPTIK'] = 'appTEST_OPTIK'
    os.environ['AIRTABLE_BASE_GUNES'] = 'appTEST_GUNES'
    os.environ['AIRTABLE_BASE_LENS'] = 'appTEST_LENS'
    os.environ['FLASK_DEBUG'] = 'False'
    os.environ['ALLOWED_ORIGINS'] = '*'
    
    yield
    
    # Cleanup
    for key in ['AIRTABLE_TOKEN', 'AIRTABLE_BASE_OPTIK', 'AIRTABLE_BASE_GUNES', 
                'AIRTABLE_BASE_LENS', 'FLASK_DEBUG', 'ALLOWED_ORIGINS']:
        os.environ.pop(key, None)


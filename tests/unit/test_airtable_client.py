"""
Unit Tests - AirtableClient
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from airtable_client import AirtableClient


class TestAirtableClientInit:
    """Test AirtableClient initialization"""
    
    def test_init_with_valid_category_OF(self, setup_env_vars):
        """Test initialization with OF category"""
        with patch('airtable_client.Api') as mock_api:
            client = AirtableClient(category='OF')
            assert client.category == 'OF'
            mock_api.assert_called_once()
    
    def test_init_with_valid_category_GN(self, setup_env_vars):
        """Test initialization with GN category"""
        with patch('airtable_client.Api') as mock_api:
            client = AirtableClient(category='GN')
            assert client.category == 'GN'
    
    def test_init_with_invalid_category(self, setup_env_vars):
        """Test initialization with invalid category"""
        with patch('airtable_client.Api'):
            # Invalid category should raise ValueError
            with pytest.raises(ValueError, match="AIRTABLE_BASE_INVALID"):
                AirtableClient(category='INVALID')
    
    def test_init_without_token(self):
        """Test initialization without AIRTABLE_TOKEN"""
        import os
        os.environ.pop('AIRTABLE_TOKEN', None)
        
        with pytest.raises(ValueError, match="AIRTABLE_TOKEN"):
            AirtableClient(category='OF')


class TestBarcodeSearch:
    """Test barcode search methods"""
    
    @patch('airtable_client.Api')
    def test_search_by_barcode_found(self, mock_api_class, sample_product_record):
        """Test successful barcode search"""
        mock_table = Mock()
        mock_table.all.return_value = [sample_product_record]
        
        mock_base = Mock()
        mock_base.table.return_value = mock_table
        
        mock_api = Mock()
        mock_api.base.return_value = mock_base
        mock_api_class.return_value = mock_api
        
        client = AirtableClient(category='OF')
        results = client.search_by_barcode('8056597412261')
        
        assert len(results) == 1
        assert results[0]['id'] == 'recABC123'
        mock_table.all.assert_called_once()
    
    @patch('airtable_client.Api')
    def test_search_by_barcode_not_found(self, mock_api_class):
        """Test barcode search with no results"""
        mock_table = Mock()
        mock_table.all.return_value = []
        
        mock_base = Mock()
        mock_base.table.return_value = mock_table
        
        mock_api = Mock()
        mock_api.base.return_value = mock_base
        mock_api_class.return_value = mock_api
        
        client = AirtableClient(category='OF')
        results = client.search_by_barcode('999999999999')
        
        assert len(results) == 0
    
    @patch('airtable_client.Api')
    def test_search_by_barcode_exception(self, mock_api_class):
        """Test barcode search with exception"""
        mock_table = Mock()
        mock_table.all.side_effect = Exception("API Error")
        
        mock_base = Mock()
        mock_base.table.return_value = mock_table
        
        mock_api = Mock()
        mock_api.base.return_value = mock_base
        mock_api_class.return_value = mock_api
        
        client = AirtableClient(category='OF')
        results = client.search_by_barcode('8056597412261')
        
        # Should return empty list on error
        assert results == []
    
    @patch('airtable_client.Api')
    def test_fuzzy_search_barcode(self, mock_api_class, sample_product_record):
        """Test fuzzy barcode search"""
        mock_table = Mock()
        mock_table.all.return_value = [sample_product_record]
        
        mock_base = Mock()
        mock_base.table.return_value = mock_table
        
        mock_api = Mock()
        mock_api.base.return_value = mock_base
        mock_api_class.return_value = mock_api
        
        client = AirtableClient(category='OF')
        results = client.fuzzy_search_barcode('8056597412', min_length=10)
        
        assert len(results) == 1
        mock_table.all.assert_called_once()
    
    @patch('airtable_client.Api')
    def test_fuzzy_search_barcode_short_input(self, mock_api_class):
        """Test fuzzy search with short barcode"""
        mock_api = Mock()
        mock_api_class.return_value = mock_api
        
        client = AirtableClient(category='OF')
        results = client.fuzzy_search_barcode('123', min_length=10)
        
        # Should return empty for short input
        assert results == []


class TestSKUOperations:
    """Test SKU-related operations"""
    
    @patch('airtable_client.Api')
    def test_get_sku_details(self, mock_api_class, sample_product_record):
        """Test getting SKU details"""
        mock_table = Mock()
        mock_table.get.return_value = sample_product_record
        
        mock_base = Mock()
        mock_base.table.return_value = mock_table
        
        mock_api = Mock()
        mock_api.base.return_value = mock_base
        mock_api_class.return_value = mock_api
        
        client = AirtableClient(category='OF')
        details = client.get_sku_details('recABC123')
        
        assert details['SKU'] == 'OF-RB-2140-901-50'
        assert details['Model Kodu'] == '2140'
    
    @patch('airtable_client.Api')
    def test_create_new_sku_success(self, mock_api_class):
        """Test creating new SKU"""
        mock_markalar_table = Mock()
        mock_markalar_table.get.return_value = {
            'id': 'recMARKA1',
            'fields': {'Marka_Kodu': 'RB'}
        }
        
        mock_urun_table = Mock()
        mock_urun_table.create.return_value = {
            'id': 'recNEW123',
            'fields': {
                'SKU': 'OF-RB-9999-001-50',
                'Kategori': 'OF'
            }
        }
        
        mock_base = Mock()
        mock_base.table.side_effect = lambda name: {
            'Markalar': mock_markalar_table,
            'Urun_Katalogu': mock_urun_table,
            'Sayim_Kayitlari': Mock(),
            'Stok_Kalemleri': Mock()
        }[name]
        
        mock_api = Mock()
        mock_api.base.return_value = mock_base
        mock_api_class.return_value = mock_api
        
        client = AirtableClient(category='OF')
        
        sku_data = {
            'Kategori': 'OF',
            'Marka': ['recMARKA1'],
            'Model_Kodu': '9999',
            'Renk_Kodu': '001',
            'Ekartman': 50,
            'Tedarikçi_Barkodu': '999999999999'
        }
        
        result = client.create_new_sku(sku_data)
        
        assert result['success'] is True
        assert 'record_id' in result
        assert 'sku' in result
    
    @patch('airtable_client.Api')
    def test_search_sku_by_term(self, mock_api_class, sample_product_record):
        """Test manual SKU search"""
        mock_table = Mock()
        mock_table.all.return_value = [sample_product_record]
        
        mock_base = Mock()
        mock_base.table.return_value = mock_table
        
        mock_api = Mock()
        mock_api.base.return_value = mock_base
        mock_api_class.return_value = mock_api
        
        client = AirtableClient(category='OF')
        results = client.search_sku_by_term('2140')
        
        assert len(results) == 1
        assert results[0]['fields']['Model Kodu'] == '2140'


class TestSayimOperations:
    """Test sayim (count) operations"""
    
    @patch('airtable_client.Api')
    def test_create_sayim_record(self, mock_api_class):
        """Test creating sayim record"""
        mock_table = Mock()
        mock_table.create.return_value = {
            'id': 'recSAYIM123',
            'fields': {'Okutulan Barkod': '8056597412261'}
        }
        
        mock_base = Mock()
        mock_base.table.return_value = mock_table
        
        mock_api = Mock()
        mock_api.base.return_value = mock_base
        mock_api_class.return_value = mock_api
        
        client = AirtableClient(category='OF')
        
        sayim_data = {
            'Okutulan Barkod': '8056597412261',
            'SKU': ['recABC123'],
            'Eşleşme Durumu': 'Direkt'
        }
        
        result = client.create_sayim_record(sayim_data)
        
        assert result['success'] is True
        assert result['record_id'] == 'recSAYIM123'
    
    @patch('airtable_client.Api')
    def test_update_sayim_record(self, mock_api_class):
        """Test updating sayim record"""
        mock_table = Mock()
        mock_table.update.return_value = {
            'id': 'recSAYIM123',
            'fields': {'Notlar': 'Updated note'}
        }
        
        mock_base = Mock()
        mock_base.table.return_value = mock_table
        
        mock_api = Mock()
        mock_api.base.return_value = mock_base
        mock_api_class.return_value = mock_api
        
        client = AirtableClient(category='OF')
        
        result = client.update_sayim_record('recSAYIM123', {'Notlar': 'Updated note'})
        
        assert result['success'] is True


class TestStatistics:
    """Test statistics methods"""
    
    @patch('airtable_client.Api')
    def test_get_today_stats(self, mock_api_class):
        """Test getting today's statistics"""
        mock_table = Mock()
        mock_table.all.return_value = [
            {'fields': {'Eslesme_Durumu': 'Direkt'}},
            {'fields': {'Eslesme_Durumu': 'Direkt'}},
            {'fields': {'Eslesme_Durumu': 'Belirsiz'}},
            {'fields': {'Eslesme_Durumu': 'Bulunamadı'}}
        ]
        
        mock_base = Mock()
        mock_base.table.return_value = mock_table
        
        mock_api = Mock()
        mock_api.base.return_value = mock_base
        mock_api_class.return_value = mock_api
        
        client = AirtableClient(category='OF')
        stats = client.get_today_stats()
        
        assert stats['total'] == 4
        assert stats['direkt'] == 2
        assert stats['belirsiz'] == 1
        assert stats['bulunamadi'] == 1
        assert stats['direkt_oran'] == 50.0


class TestBrands:
    """Test brand operations"""
    
    @patch('airtable_client.Api')
    def test_get_all_brands(self, mock_api_class):
        """Test getting all brands"""
        mock_table = Mock()
        mock_table.all.return_value = [
            {
                'id': 'recMARKA1',
                'fields': {
                    'Marka Kodu': 'RB',
                    'Marka Adı': 'Ray-Ban',
                    'Kategori': ['OF', 'GN']
                }
            },
            {
                'id': 'recMARKA2',
                'fields': {
                    'Marka Kodu': 'VOGUE',
                    'Marka Adı': 'Vogue Eyewear',
                    'Kategori': ['OF']
                }
            }
        ]
        
        mock_base = Mock()
        mock_base.table.return_value = mock_table
        
        mock_api = Mock()
        mock_api.base.return_value = mock_base
        mock_api_class.return_value = mock_api
        
        client = AirtableClient(category='OF')
        brands = client.get_all_brands()
        
        assert len(brands) == 2
        assert brands[0]['ad'] == 'Ray-Ban'
        assert brands[1]['ad'] == 'Vogue Eyewear'


class TestHealthCheck:
    """Test health check"""
    
    @patch('airtable_client.Api')
    def test_health_check_success(self, mock_api_class):
        """Test successful health check"""
        mock_table = Mock()
        mock_table.first.return_value = {'id': 'rec123'}
        
        mock_base = Mock()
        mock_base.table.return_value = mock_table
        
        mock_api = Mock()
        mock_api.base.return_value = mock_base
        mock_api_class.return_value = mock_api
        
        client = AirtableClient(category='OF')
        result = client.health_check()
        
        assert result is True
    
    @patch('airtable_client.Api')
    def test_health_check_failure(self, mock_api_class):
        """Test failed health check"""
        mock_table = Mock()
        mock_table.first.side_effect = Exception("Connection error")
        
        mock_base = Mock()
        mock_base.table.return_value = mock_table
        
        mock_api = Mock()
        mock_api.base.return_value = mock_base
        mock_api_class.return_value = mock_api
        
        client = AirtableClient(category='OF')
        result = client.health_check()
        
        assert result is False


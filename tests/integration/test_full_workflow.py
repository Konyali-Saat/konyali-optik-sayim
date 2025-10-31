"""
Integration Tests - Full Workflow
Testler gerçek Airtable bağlantısı gerektirmez (mock kullanılır)
"""

import pytest
import json
from unittest.mock import Mock, patch


class TestBarcodeSearchToSaveWorkflow:
    """Test complete workflow from barcode search to save"""
    
    @patch('app.get_airtable_client')
    @patch('app.get_matcher')
    def test_complete_workflow_direkt_match(self, mock_get_matcher, mock_get_client, flask_client):
        """Test complete workflow with direct match"""
        # Setup mocks
        mock_matcher = Mock()
        mock_matcher.match.return_value = {
            'status': 'direkt',
            'confidence': 100,
            'product': {
                'id': 'recABC123',
                'sku': 'OF-RB-2140-901-50',
                'marka': 'Ray-Ban'
            }
        }
        mock_get_matcher.return_value = mock_matcher
        
        mock_client = Mock()
        mock_client.create_sayim_record.return_value = {
            'success': True,
            'record_id': 'recSAYIM123'
        }
        mock_client.update_stok_from_sayim.return_value = True
        mock_get_client.return_value = mock_client
        
        # Step 1: Search barcode
        search_response = flask_client.post('/api/search-barcode',
            data=json.dumps({
                'barkod': '8056597412261',
                'category': 'OF'
            }),
            content_type='application/json'
        )
        
        search_data = json.loads(search_response.data)
        assert search_data['found'] is True
        assert search_data['status'] == 'direkt'
        
        # Step 2: Save count
        save_response = flask_client.post('/api/save-count',
            data=json.dumps({
                'category': 'OF',
                'barkod': '8056597412261',
                'sku_id': search_data['product']['id'],
                'eslesme_durumu': 'Direkt',
                'sayim_yapan': 'Ekip 1'
            }),
            content_type='application/json'
        )
        
        save_data = json.loads(save_response.data)
        assert save_data['success'] is True
        assert 'record_id' in save_data
        
        # Verify stok update was called
        mock_client.update_stok_from_sayim.assert_called_once()
    
    @patch('app.get_airtable_client')
    @patch('app.get_matcher')
    def test_workflow_bulunamadi_then_unlisted(self, mock_get_matcher, mock_get_client, flask_client):
        """Test workflow when product not found, then add as unlisted"""
        # Setup mocks
        mock_matcher = Mock()
        mock_matcher.match.return_value = {
            'status': 'bulunamadi',
            'confidence': 0,
            'product': None
        }
        mock_get_matcher.return_value = mock_matcher
        
        mock_client = Mock()
        mock_client.get_all_brands.return_value = [
            {'id': 'recMARKA1', 'kod': 'RB', 'ad': 'Ray-Ban'}
        ]
        mock_client.create_new_sku.return_value = {
            'success': True,
            'record_id': 'recNEW123',
            'sku': 'OF-RB-9999-001-50'
        }
        mock_client.create_sayim_record.return_value = {
            'success': True,
            'record_id': 'recSAYIM123'
        }
        mock_get_client.return_value = mock_client
        
        # Step 1: Search barcode (not found)
        search_response = flask_client.post('/api/search-barcode',
            data=json.dumps({
                'barkod': '999999999999',
                'category': 'OF'
            }),
            content_type='application/json'
        )
        
        search_data = json.loads(search_response.data)
        assert search_data['found'] is False
        
        # Step 2: Get brands for form
        brands_response = flask_client.get('/api/brands?category=OF')
        brands_data = json.loads(brands_response.data)
        assert len(brands_data['brands']) > 0
        
        # Step 3: Save as unlisted product
        unlisted_response = flask_client.post('/api/save-unlisted-product',
            data=json.dumps({
                'category': 'OF',
                'barkod': '999999999999',
                'kategori': 'OF',
                'marka_id': 'recMARKA1',
                'model_kodu': '9999',
                'renk_kodu': '001',
                'ekartman': 50
            }),
            content_type='application/json'
        )
        
        unlisted_data = json.loads(unlisted_response.data)
        assert unlisted_data['success'] is True
        assert 'sku_record_id' in unlisted_data
        assert 'sayim_record_id' in unlisted_data


class TestManualSearchWorkflow:
    """Test manual search workflow"""
    
    @patch('app.get_airtable_client')
    def test_manual_search_then_save(self, mock_get_client, flask_client):
        """Test manual search followed by save"""
        mock_client = Mock()
        mock_client.search_sku_by_term.return_value = [
            {
                'id': 'recABC123',
                'fields': {
                    'SKU': 'OF-RB-2140-901-50',
                    'Model Kodu': '2140',
                    'Marka Adı': ['Ray-Ban'],
                    'Kategori': 'OF'
                }
            }
        ]
        mock_client.create_sayim_record.return_value = {
            'success': True,
            'record_id': 'recSAYIM123'
        }
        mock_get_client.return_value = mock_client
        
        # Step 1: Manual search
        search_response = flask_client.post('/api/search-manual',
            data=json.dumps({
                'category': 'OF',
                'term': '2140'
            }),
            content_type='application/json'
        )
        
        search_data = json.loads(search_response.data)
        assert search_data['found'] is True
        assert len(search_data['products']) > 0
        
        # Step 2: Save count with manual search term
        save_response = flask_client.post('/api/save-count',
            data=json.dumps({
                'category': 'OF',
                'barkod': '8056597412261',
                'sku_id': search_data['products'][0]['id'],
                'eslesme_durumu': 'Manuel',
                'manuel_arama_terimi': '2140',
                'sayim_yapan': 'Ekip 1'
            }),
            content_type='application/json'
        )
        
        save_data = json.loads(save_response.data)
        assert save_data['success'] is True


class TestMultipleCategoriesWorkflow:
    """Test workflow across multiple categories"""
    
    @patch('app.get_airtable_client')
    @patch('app.get_matcher')
    def test_switch_categories(self, mock_get_matcher, mock_get_client, flask_client):
        """Test switching between categories"""
        # Mock for OF category
        mock_matcher_of = Mock()
        mock_matcher_of.match.return_value = {
            'status': 'direkt',
            'confidence': 100,
            'product': {'id': 'recOF123', 'sku': 'OF-RB-2140-901-50'}
        }
        
        # Mock for GN category
        mock_matcher_gn = Mock()
        mock_matcher_gn.match.return_value = {
            'status': 'direkt',
            'confidence': 100,
            'product': {'id': 'recGN123', 'sku': 'GN-RB-3025-001-58'}
        }
        
        def matcher_side_effect(category):
            return mock_matcher_of if category == 'OF' else mock_matcher_gn
        
        mock_get_matcher.side_effect = matcher_side_effect
        
        mock_client = Mock()
        mock_client.create_sayim_record.return_value = {
            'success': True,
            'record_id': 'recSAYIM123'
        }
        mock_get_client.return_value = mock_client
        
        # Search in OF category
        response_of = flask_client.post('/api/search-barcode',
            data=json.dumps({
                'barkod': '8056597412261',
                'category': 'OF'
            }),
            content_type='application/json'
        )
        
        data_of = json.loads(response_of.data)
        assert data_of['product']['sku'].startswith('OF-')
        
        # Search in GN category
        response_gn = flask_client.post('/api/search-barcode',
            data=json.dumps({
                'barkod': '8056597123456',
                'category': 'GN'
            }),
            content_type='application/json'
        )
        
        data_gn = json.loads(response_gn.data)
        assert data_gn['product']['sku'].startswith('GN-')


class TestStatsUpdateWorkflow:
    """Test statistics update workflow"""
    
    @patch('app.get_airtable_client')
    def test_stats_after_multiple_saves(self, mock_get_client, flask_client):
        """Test that stats update after multiple saves"""
        mock_client = Mock()
        
        # Initial stats
        mock_client.get_today_stats.return_value = {
            'total': 0,
            'direkt': 0,
            'belirsiz': 0,
            'bulunamadi': 0,
            'direkt_oran': 0
        }
        
        mock_client.create_sayim_record.return_value = {
            'success': True,
            'record_id': 'recSAYIM123'
        }
        
        mock_get_client.return_value = mock_client
        
        # Get initial stats
        stats_response_1 = flask_client.get('/api/stats?category=OF')
        stats_data_1 = json.loads(stats_response_1.data)
        assert stats_data_1['stats']['total'] == 0
        
        # Save a count
        flask_client.post('/api/save-count',
            data=json.dumps({
                'category': 'OF',
                'barkod': '8056597412261',
                'sku_id': 'recABC123',
                'eslesme_durumu': 'Direkt'
            }),
            content_type='application/json'
        )
        
        # Update mock to return new stats
        mock_client.get_today_stats.return_value = {
            'total': 1,
            'direkt': 1,
            'belirsiz': 0,
            'bulunamadi': 0,
            'direkt_oran': 100.0
        }
        
        # Get updated stats
        stats_response_2 = flask_client.get('/api/stats?category=OF')
        stats_data_2 = json.loads(stats_response_2.data)
        assert stats_data_2['stats']['total'] == 1
        assert stats_data_2['stats']['direkt'] == 1


class TestContextFilteringWorkflow:
    """Test context filtering workflow"""
    
    @patch('app.get_airtable_client')
    @patch('app.get_matcher')
    def test_brand_context_filtering(self, mock_get_matcher, mock_get_client, flask_client):
        """Test search with brand context filter"""
        mock_matcher = Mock()
        mock_matcher.match.return_value = {
            'status': 'direkt',
            'confidence': 100,
            'product': {
                'id': 'recABC123',
                'sku': 'OF-RB-2140-901-50',
                'marka': 'Ray-Ban'
            }
        }
        mock_get_matcher.return_value = mock_matcher
        
        mock_client = Mock()
        mock_client.get_all_brands.return_value = [
            {'id': 'recMARKA1', 'kod': 'RB', 'ad': 'Ray-Ban'}
        ]
        mock_get_client.return_value = mock_client
        
        # Step 1: Get brands
        brands_response = flask_client.get('/api/brands?category=OF')
        brands_data = json.loads(brands_response.data)
        ray_ban_id = brands_data['brands'][0]['id']
        
        # Step 2: Search with brand context
        search_response = flask_client.post('/api/search-barcode',
            data=json.dumps({
                'barkod': '8056597412261',
                'category': 'OF',
                'context_brand': ray_ban_id
            }),
            content_type='application/json'
        )
        
        search_data = json.loads(search_response.data)
        assert search_data['found'] is True
        
        # Verify matcher was called with context
        mock_matcher.match.assert_called_with(
            '8056597412261',
            ray_ban_id,
            None
        )


class TestErrorRecoveryWorkflow:
    """Test error recovery scenarios"""
    
    @patch('app.get_airtable_client')
    def test_save_failure_recovery(self, mock_get_client, flask_client):
        """Test recovery from save failure"""
        mock_client = Mock()
        
        # First attempt fails
        mock_client.create_sayim_record.return_value = {
            'success': False,
            'error': 'Network error'
        }
        
        mock_get_client.return_value = mock_client
        
        # Try to save
        response_1 = flask_client.post('/api/save-count',
            data=json.dumps({
                'category': 'OF',
                'barkod': '8056597412261',
                'sku_id': 'recABC123',
                'eslesme_durumu': 'Direkt'
            }),
            content_type='application/json'
        )
        
        data_1 = json.loads(response_1.data)
        assert data_1['success'] is False
        
        # Second attempt succeeds
        mock_client.create_sayim_record.return_value = {
            'success': True,
            'record_id': 'recSAYIM123'
        }
        
        response_2 = flask_client.post('/api/save-count',
            data=json.dumps({
                'category': 'OF',
                'barkod': '8056597412261',
                'sku_id': 'recABC123',
                'eslesme_durumu': 'Direkt'
            }),
            content_type='application/json'
        )
        
        data_2 = json.loads(response_2.data)
        assert data_2['success'] is True


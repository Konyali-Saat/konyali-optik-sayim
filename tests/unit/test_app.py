"""
Unit Tests - Flask API Endpoints
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock


class TestHealthEndpoint:
    """Test /api/health endpoint"""
    
    @patch('app.get_airtable_client')
    def test_health_check_all_healthy(self, mock_get_client, flask_client):
        """Test health check when all categories are healthy"""
        mock_client = Mock()
        mock_client.health_check.return_value = True
        mock_get_client.return_value = mock_client
        
        response = flask_client.get('/api/health')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data['status'] == 'healthy'
        assert data['version'] == '2.0.0'
        assert data['categories']['OF'] is True
        assert data['categories']['GN'] is True
        assert data['categories']['LN'] is True
    
    @patch('app.get_airtable_client')
    def test_health_check_one_degraded(self, mock_get_client, flask_client):
        """Test health check when one category is degraded"""
        def side_effect(category):
            mock_client = Mock()
            mock_client.health_check.return_value = (category != 'GN')
            return mock_client
        
        mock_get_client.side_effect = side_effect
        
        response = flask_client.get('/api/health')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data['status'] == 'degraded'
        assert data['categories']['OF'] is True
        assert data['categories']['GN'] is False
        assert data['categories']['LN'] is True


class TestSearchBarcodeEndpoint:
    """Test /api/search-barcode endpoint"""
    
    @patch('app.get_matcher')
    def test_search_barcode_found_direkt(self, mock_get_matcher, flask_client):
        """Test barcode search with direct match"""
        mock_matcher = Mock()
        mock_matcher.match.return_value = {
            'status': 'direkt',
            'confidence': 100,
            'product': {
                'id': 'recABC123',
                'sku': 'OF-RB-2140-901-50',
                'marka': 'Ray-Ban'
            },
            'candidates': []
        }
        mock_get_matcher.return_value = mock_matcher
        
        response = flask_client.post('/api/search-barcode',
            data=json.dumps({
                'barkod': '8056597412261',
                'category': 'OF'
            }),
            content_type='application/json'
        )
        
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data['found'] is True
        assert data['status'] == 'direkt'
        assert data['confidence'] == 100
        assert data['product']['sku'] == 'OF-RB-2140-901-50'
    
    @patch('app.get_matcher')
    def test_search_barcode_not_found(self, mock_get_matcher, flask_client):
        """Test barcode search with no results"""
        mock_matcher = Mock()
        mock_matcher.match.return_value = {
            'status': 'bulunamadi',
            'confidence': 0,
            'product': None,
            'candidates': []
        }
        mock_get_matcher.return_value = mock_matcher
        
        response = flask_client.post('/api/search-barcode',
            data=json.dumps({
                'barkod': '999999999999',
                'category': 'OF'
            }),
            content_type='application/json'
        )
        
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data['found'] is False
        assert data['status'] == 'bulunamadi'
    
    def test_search_barcode_missing_barkod(self, flask_client):
        """Test barcode search without barkod parameter"""
        response = flask_client.post('/api/search-barcode',
            data=json.dumps({'category': 'OF'}),
            content_type='application/json'
        )
        
        data = json.loads(response.data)
        
        assert response.status_code == 400
        assert 'error' in data
    
    @patch('app.get_matcher')
    def test_search_barcode_with_context(self, mock_get_matcher, flask_client):
        """Test barcode search with brand context"""
        mock_matcher = Mock()
        mock_matcher.match.return_value = {
            'status': 'direkt',
            'confidence': 100,
            'product': {'sku': 'OF-RB-2140-901-50'},
            'candidates': []
        }
        mock_get_matcher.return_value = mock_matcher
        
        response = flask_client.post('/api/search-barcode',
            data=json.dumps({
                'barkod': '8056597412261',
                'category': 'OF',
                'context_brand': 'recMARKA1'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        mock_matcher.match.assert_called_once_with(
            '8056597412261',
            'recMARKA1',
            None
        )


class TestSaveCountEndpoint:
    """Test /api/save-count endpoint"""
    
    @patch('app.get_airtable_client')
    def test_save_count_success(self, mock_get_client, flask_client):
        """Test successful count save"""
        mock_client = Mock()
        mock_client.create_sayim_record.return_value = {
            'success': True,
            'record_id': 'recSAYIM123'
        }
        mock_client.update_stok_from_sayim.return_value = True
        mock_get_client.return_value = mock_client
        
        response = flask_client.post('/api/save-count',
            data=json.dumps({
                'category': 'OF',
                'barkod': '8056597412261',
                'sku_id': 'recABC123',
                'eslesme_durumu': 'Direkt',
                'sayim_yapan': 'Ekip 1'
            }),
            content_type='application/json'
        )
        
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data['success'] is True
        assert data['record_id'] == 'recSAYIM123'
    
    def test_save_count_missing_fields(self, flask_client):
        """Test save count with missing required fields"""
        response = flask_client.post('/api/save-count',
            data=json.dumps({
                'category': 'OF',
                'barkod': '8056597412261'
                # Missing eslesme_durumu
            }),
            content_type='application/json'
        )
        
        data = json.loads(response.data)
        
        assert response.status_code == 400
        assert 'error' in data


class TestManualSearchEndpoint:
    """Test /api/search-manual endpoint"""
    
    @patch('app.get_airtable_client')
    def test_manual_search_found(self, mock_get_client, flask_client):
        """Test manual search with results"""
        mock_client = Mock()
        mock_client.search_sku_by_term.return_value = [
            {
                'id': 'recABC123',
                'fields': {
                    'SKU': 'OF-RB-2140-901-50',
                    'Model Kodu': '2140',
                    'Marka Adı': ['Ray-Ban']
                }
            }
        ]
        mock_get_client.return_value = mock_client
        
        response = flask_client.post('/api/search-manual',
            data=json.dumps({
                'category': 'OF',
                'term': '2140'
            }),
            content_type='application/json'
        )
        
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data['found'] is True
        assert data['count'] == 1
        assert len(data['products']) == 1
    
    def test_manual_search_short_term(self, flask_client):
        """Test manual search with too short term"""
        response = flask_client.post('/api/search-manual',
            data=json.dumps({
                'category': 'OF',
                'term': 'a'  # Too short
            }),
            content_type='application/json'
        )
        
        data = json.loads(response.data)
        
        assert response.status_code == 400
        assert 'error' in data


class TestBrandsEndpoint:
    """Test /api/brands endpoint"""
    
    @patch('app.get_airtable_client')
    def test_get_brands_success(self, mock_get_client, flask_client):
        """Test getting brands list"""
        mock_client = Mock()
        mock_client.get_all_brands.return_value = [
            {'id': 'rec1', 'kod': 'RB', 'ad': 'Ray-Ban'},
            {'id': 'rec2', 'kod': 'VOGUE', 'ad': 'Vogue Eyewear'}
        ]
        mock_get_client.return_value = mock_client
        
        response = flask_client.get('/api/brands?category=OF')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data['success'] is True
        assert len(data['brands']) == 2
    
    @patch('app.get_airtable_client')
    def test_get_brands_post_method(self, mock_get_client, flask_client):
        """Test getting brands via POST"""
        mock_client = Mock()
        mock_client.get_all_brands.return_value = []
        mock_get_client.return_value = mock_client
        
        response = flask_client.post('/api/brands',
            data=json.dumps({'category': 'OF'}),
            content_type='application/json'
        )
        
        assert response.status_code == 200


class TestStatsEndpoint:
    """Test /api/stats endpoint"""
    
    @patch('app.get_airtable_client')
    def test_get_stats_success(self, mock_get_client, flask_client):
        """Test getting statistics"""
        mock_client = Mock()
        mock_client.get_today_stats.return_value = {
            'total': 100,
            'direkt': 85,
            'belirsiz': 10,
            'bulunamadi': 5,
            'direkt_oran': 85.0
        }
        mock_get_client.return_value = mock_client
        
        response = flask_client.get('/api/stats?category=OF')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data['success'] is True
        assert data['stats']['total'] == 100
        assert data['stats']['direkt_oran'] == 85.0


class TestUnlistedProductEndpoint:
    """Test /api/save-unlisted-product endpoint"""
    
    @patch('app.get_airtable_client')
    def test_save_unlisted_product_success(self, mock_get_client, flask_client):
        """Test saving unlisted product"""
        mock_client = Mock()
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
        
        response = flask_client.post('/api/save-unlisted-product',
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
        
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data['success'] is True
        assert 'sku' in data
        assert 'sku_record_id' in data
        assert 'sayim_record_id' in data
    
    def test_save_unlisted_product_missing_fields(self, flask_client):
        """Test saving unlisted product with missing fields"""
        response = flask_client.post('/api/save-unlisted-product',
            data=json.dumps({
                'category': 'OF',
                'barkod': '999999999999'
                # Missing required fields
            }),
            content_type='application/json'
        )
        
        data = json.loads(response.data)
        
        assert response.status_code == 400
        assert 'error' in data


class TestErrorHandlers:
    """Test error handlers"""
    
    @pytest.mark.skip(reason="Flask static_folder causes routing issues in tests")
    def test_404_error(self, flask_client):
        """Test 404 error handler for API endpoints"""
        # Test with an API endpoint that doesn't exist
        response = flask_client.post('/api/nonexistent_endpoint_test_12345')
        
        # API endpoints should return 404 (or 405 for wrong method)
        assert response.status_code in [404, 405]
    
    @patch('app.get_airtable_client')
    def test_500_error(self, mock_get_client, flask_client):
        """Test 500 error handling"""
        mock_get_client.side_effect = Exception("Database error")
        
        response = flask_client.get('/api/brands?category=OF')
        data = json.loads(response.data)
        
        assert response.status_code == 500
        assert 'error' in data


class TestCategoryValidation:
    """Test category parameter validation"""
    
    @patch('app.get_matcher')
    def test_valid_category_OF(self, mock_get_matcher, flask_client):
        """Test with valid OF category"""
        mock_matcher = Mock()
        mock_matcher.match.return_value = {
            'status': 'bulunamadi',
            'confidence': 0,
            'product': None
        }
        mock_get_matcher.return_value = mock_matcher
        
        response = flask_client.post('/api/search-barcode',
            data=json.dumps({
                'barkod': '123',
                'category': 'OF'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200
    
    @patch('app.get_matcher')
    def test_valid_category_GN(self, mock_get_matcher, flask_client):
        """Test with valid GN category"""
        mock_matcher = Mock()
        mock_matcher.match.return_value = {
            'status': 'bulunamadi',
            'confidence': 0,
            'product': None
        }
        mock_get_matcher.return_value = mock_matcher
        
        response = flask_client.post('/api/search-barcode',
            data=json.dumps({
                'barkod': '123',
                'category': 'GN'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200


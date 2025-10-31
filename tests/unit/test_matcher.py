"""
Unit Tests - BarcodeMatcher
"""

import pytest
from unittest.mock import Mock, MagicMock
from matcher import BarcodeMatcher


class TestMatcherInit:
    """Test BarcodeMatcher initialization"""
    
    def test_init_with_client(self):
        """Test matcher initialization"""
        mock_client = Mock()
        matcher = BarcodeMatcher(mock_client)
        
        assert matcher.client == mock_client


class TestDirectMatch:
    """Test direct barcode matching"""
    
    def test_match_single_result_direkt(self, sample_product_record):
        """Test direct match with single result"""
        mock_client = Mock()
        mock_client.search_by_barcode.return_value = [sample_product_record]
        
        matcher = BarcodeMatcher(mock_client)
        result = matcher.match('8056597412261')
        
        assert result['status'] == 'direkt'
        assert result['confidence'] == 100
        assert result['product'] is not None
        assert result['product']['sku'] == 'OF-RB-2140-901-50'
    
    def test_match_no_result_bulunamadi(self):
        """Test match with no results"""
        mock_client = Mock()
        mock_client.search_by_barcode.return_value = []
        mock_client.fuzzy_search_barcode.return_value = []
        
        matcher = BarcodeMatcher(mock_client)
        result = matcher.match('999999999999')
        
        assert result['status'] == 'bulunamadi'
        assert result['confidence'] == 0
        assert result['product'] is None
    
    def test_match_multiple_results_belirsiz(self, sample_product_record):
        """Test match with multiple results"""
        product1 = sample_product_record.copy()
        product2 = sample_product_record.copy()
        product2['id'] = 'recABC456'
        product2['fields']['Ekartman'] = 52
        
        mock_client = Mock()
        mock_client.search_by_barcode.return_value = [product1, product2]
        
        matcher = BarcodeMatcher(mock_client)
        result = matcher.match('8056597412261')
        
        assert result['status'] == 'belirsiz'
        assert result['confidence'] == 80
        assert 'candidates' in result
        assert len(result['candidates']) == 2


class TestContextFiltering:
    """Test context-based filtering"""
    
    def test_match_with_brand_context_match(self, sample_product_record):
        """Test match with matching brand context"""
        mock_client = Mock()
        mock_client.search_by_barcode.return_value = [sample_product_record]
        
        matcher = BarcodeMatcher(mock_client)
        result = matcher.match('8056597412261', context_brand='recMARKA1')
        
        assert result['status'] == 'direkt'
        assert result['confidence'] == 100
    
    def test_match_with_brand_context_no_match(self, sample_product_record):
        """Test match with non-matching brand context"""
        mock_client = Mock()
        mock_client.search_by_barcode.return_value = [sample_product_record]
        
        matcher = BarcodeMatcher(mock_client)
        result = matcher.match('8056597412261', context_brand='recMARKA_WRONG')
        
        assert result['status'] == 'bulunamadi'
        assert result['confidence'] == 0
    
    def test_match_with_category_context_match(self, sample_product_record):
        """Test match with matching category context"""
        mock_client = Mock()
        mock_client.search_by_barcode.return_value = [sample_product_record]
        
        matcher = BarcodeMatcher(mock_client)
        result = matcher.match('8056597412261', context_category='OF')
        
        assert result['status'] == 'direkt'
    
    def test_match_with_category_context_no_match(self, sample_product_record):
        """Test match with non-matching category context"""
        mock_client = Mock()
        mock_client.search_by_barcode.return_value = [sample_product_record]
        
        matcher = BarcodeMatcher(mock_client)
        result = matcher.match('8056597412261', context_category='GN')
        
        assert result['status'] == 'bulunamadi'


class TestFuzzyMatching:
    """Test fuzzy matching algorithm"""
    
    def test_fuzzy_match_success(self, sample_product_record):
        """Test successful fuzzy match"""
        mock_client = Mock()
        mock_client.search_by_barcode.return_value = []
        mock_client.fuzzy_search_barcode.return_value = [sample_product_record]
        
        matcher = BarcodeMatcher(mock_client)
        result = matcher.match('8056597412999')  # Similar but not exact
        
        # Should find via fuzzy match
        assert result['status'] in ['direkt', 'belirsiz']
        assert result['confidence'] >= 85
    
    def test_fuzzy_match_short_barcode(self):
        """Test fuzzy match with short barcode"""
        mock_client = Mock()
        mock_client.search_by_barcode.return_value = []
        
        matcher = BarcodeMatcher(mock_client)
        result = matcher.match('123')  # Too short for fuzzy
        
        assert result['status'] == 'bulunamadi'
    
    def test_fuzzy_match_low_similarity(self, sample_product_record):
        """Test fuzzy match with low similarity score"""
        # Create a product with very different barcode
        different_product = sample_product_record.copy()
        different_product['fields']['Tedarikçi Barkodu'] = '1234567890123'
        
        mock_client = Mock()
        mock_client.search_by_barcode.return_value = []
        mock_client.fuzzy_search_barcode.return_value = [different_product]
        
        matcher = BarcodeMatcher(mock_client)
        result = matcher.match('9999999999999')
        
        # Should not match due to low similarity
        assert result['status'] == 'bulunamadi'


class TestMultipleMatchesWithContext:
    """Test handling multiple matches with context filtering"""
    
    def test_multiple_matches_filtered_to_one(self, sample_product_record):
        """Test multiple matches filtered down to one by context"""
        import copy
        product1 = copy.deepcopy(sample_product_record)
        product2 = copy.deepcopy(sample_product_record)
        product2['id'] = 'recABC456'
        product2['fields']['Marka'] = ['recMARKA2']
        
        mock_client = Mock()
        mock_client.search_by_barcode.return_value = [product1, product2]
        
        matcher = BarcodeMatcher(mock_client)
        result = matcher.match('8056597412261', context_brand='recMARKA1')
        
        # Should filter to single match
        assert result['status'] == 'direkt'
        assert result['confidence'] == 95
    
    def test_multiple_matches_all_filtered_out(self, sample_product_record):
        """Test multiple matches all filtered out by context"""
        product1 = sample_product_record.copy()
        product2 = sample_product_record.copy()
        product2['id'] = 'recABC456'
        
        mock_client = Mock()
        mock_client.search_by_barcode.return_value = [product1, product2]
        
        matcher = BarcodeMatcher(mock_client)
        result = matcher.match('8056597412261', context_brand='recMARKA_NONE')
        
        # Should filter out all matches
        assert result['status'] == 'bulunamadi'


class TestProductFormatting:
    """Test product data formatting"""
    
    def test_format_product_with_all_fields(self, sample_product_record):
        """Test formatting product with all fields"""
        mock_client = Mock()
        mock_client.search_by_barcode.return_value = [sample_product_record]
        
        matcher = BarcodeMatcher(mock_client)
        result = matcher.match('8056597412261')
        
        product = result['product']
        assert product['id'] == 'recABC123'
        assert product['sku'] == 'OF-RB-2140-901-50'
        assert product['kategori'] == 'OF'
        assert product['marka'] == 'Ray-Ban'
        assert product['model_kodu'] == '2140'
        assert product['model_adi'] == 'Wayfarer'
        assert product['renk_kodu'] == '901'
        assert product['renk_adi'] == 'Shiny Black'
        assert product['ekartman'] == 50
        assert product['birim_fiyat'] == 350.00
        assert product['durum'] == 'Aktif'
    
    def test_format_product_with_missing_fields(self):
        """Test formatting product with missing optional fields"""
        incomplete_record = {
            'id': 'recABC123',
            'fields': {
                'SKU': 'OF-RB-2140-901-50',
                'Kategori': 'OF',
                'Model Kodu': '2140',
                'Tedarikçi Barkodu': '8056597412261'
                # Missing many optional fields
            }
        }
        
        mock_client = Mock()
        mock_client.search_by_barcode.return_value = [incomplete_record]
        
        matcher = BarcodeMatcher(mock_client)
        result = matcher.match('8056597412261')
        
        product = result['product']
        assert product['sku'] == 'OF-RB-2140-901-50'
        assert product['model_kodu'] == '2140'
        # Missing fields should have default values
        assert product['model_adi'] == ''
        assert product['birim_fiyat'] == 0


class TestEdgeCases:
    """Test edge cases and error scenarios"""
    
    def test_match_with_empty_barcode(self):
        """Test match with empty barcode"""
        mock_client = Mock()
        mock_client.search_by_barcode.return_value = []
        mock_client.fuzzy_search_barcode.return_value = []
        
        matcher = BarcodeMatcher(mock_client)
        
        result = matcher.match('')
        
        # Should handle gracefully
        assert result['status'] == 'bulunamadi'
    
    def test_match_with_special_characters(self):
        """Test match with special characters in barcode"""
        mock_client = Mock()
        mock_client.search_by_barcode.return_value = []
        mock_client.fuzzy_search_barcode.return_value = []
        
        matcher = BarcodeMatcher(mock_client)
        result = matcher.match("123'456\"789")
        
        # Should handle special characters
        assert result['status'] == 'bulunamadi'
    
    def test_match_with_very_long_barcode(self):
        """Test match with very long barcode"""
        mock_client = Mock()
        mock_client.search_by_barcode.return_value = []
        mock_client.fuzzy_search_barcode.return_value = []
        
        matcher = BarcodeMatcher(mock_client)
        result = matcher.match('1' * 100)
        
        # Should handle long input
        assert result['status'] == 'bulunamadi'


class TestCandidatesOrdering:
    """Test candidates ordering in belirsiz status"""
    
    def test_candidates_ordered_by_score(self, sample_product_record):
        """Test that candidates are ordered by similarity score"""
        product1 = sample_product_record.copy()
        product1['id'] = 'rec1'
        product1['fields']['Tedarikçi Barkodu'] = '8056597412261'
        
        product2 = sample_product_record.copy()
        product2['id'] = 'rec2'
        product2['fields']['Tedarikçi Barkodu'] = '8056597412269'
        
        product3 = sample_product_record.copy()
        product3['id'] = 'rec3'
        product3['fields']['Tedarikçi Barkodu'] = '8056597412277'
        
        mock_client = Mock()
        mock_client.search_by_barcode.return_value = []
        mock_client.fuzzy_search_barcode.return_value = [product1, product2, product3]
        
        matcher = BarcodeMatcher(mock_client)
        result = matcher.match('8056597412261')
        
        if result['status'] == 'belirsiz':
            # First candidate should have highest score
            assert result['candidates'][0]['sku_id'] == 'rec1'


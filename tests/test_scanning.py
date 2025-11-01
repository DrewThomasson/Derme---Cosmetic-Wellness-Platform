"""
Unit tests for Product Scanning (Use Case 4)
Tests corresponding to TC-SCAN-001, TC-SCAN-002, TC-SCAN-003
"""
import pytest
import io
from PIL import Image
from app import db


class TestProductScanning:
    """Test cases for product scanning and OCR functionality"""
    
    def test_scan_page_requires_authentication(self, client):
        """
        Verify that scan page requires user to be logged in
        """
        response = client.get('/scan', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_scan_with_no_image_uploaded(self, authenticated_client):
        """
        TC-SCAN-002: Scan with No Image Uploaded
        Verify that scan fails gracefully when no image is provided
        """
        # Attempt to scan without uploading an image
        response = authenticated_client.post('/scan', data={}, follow_redirects=True)
        
        # Should show error message
        assert response.status_code == 200
        assert b'No image' in response.data or b'required' in response.data
    
    def test_scan_with_empty_filename(self, authenticated_client):
        """
        Test scan with empty filename
        """
        # Create empty file upload
        data = {
            'image': (io.BytesIO(b''), '')
        }
        
        response = authenticated_client.post(
            '/scan',
            data=data,
            content_type='multipart/form-data',
            follow_redirects=True
        )
        
        # Should show error
        assert b'No image selected' in response.data or b'No image' in response.data
    
    def test_scan_results_without_scanning(self, authenticated_client):
        """
        Verify that scan results page requires scan to be performed first
        """
        response = authenticated_client.get('/scan/results', follow_redirects=True)
        
        # Should redirect or show message about no results
        assert b'No scan results' in response.data or b'scan' in response.data.lower()
    
    def test_save_product_without_scan_results(self, authenticated_client):
        """
        Verify that saving product requires scan results in session
        """
        response = authenticated_client.post('/scan/save', data={
            'product_name': 'Test Product',
            'product_type': 'safe'
        }, follow_redirects=True)
        
        # Should return error since no scan results in session
        assert response.status_code == 400 or b'error' in response.data.lower()
    
    def test_scan_with_valid_image_structure(self, authenticated_client, app):
        """
        TC-SCAN-001 (partial): Test scan endpoint accepts valid image
        Note: Full OCR testing requires Tesseract installation
        """
        # Create a simple test image
        img = Image.new('RGB', (100, 100), color='white')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        data = {
            'image': (img_bytes, 'test_image.png')
        }
        
        try:
            response = authenticated_client.post(
                '/scan',
                data=data,
                content_type='multipart/form-data',
                follow_redirects=True
            )
            
            # Response should be successful (200) even if OCR fails
            assert response.status_code == 200
        except Exception as e:
            # If Tesseract is not installed, expect specific error
            if 'tesseract' in str(e).lower():
                pytest.skip("Tesseract OCR not installed")
            else:
                raise
    
    def test_parse_ingredients_function(self):
        """
        Test the parse_ingredients helper function
        """
        from app import parse_ingredients
        
        # Test with comma-separated ingredients
        text = "Water, Glycerin, Methylisothiazolinone, Fragrance"
        ingredients = parse_ingredients(text)
        assert len(ingredients) == 4
        assert 'Water' in ingredients
        assert 'Glycerin' in ingredients
        
        # Test with semicolon-separated ingredients
        text = "Water; Glycerin; Vitamin E"
        ingredients = parse_ingredients(text)
        assert len(ingredients) == 3
        
        # Test with newlines
        text = "Water\nGlycerin\nVitamin E"
        ingredients = parse_ingredients(text)
        assert len(ingredients) >= 2  # Should handle newlines
        
        # Test with empty text
        text = ""
        ingredients = parse_ingredients(text)
        assert len(ingredients) == 0
    
    def test_save_safe_product(self, authenticated_client, app, test_user):
        """
        Test saving a product as safe
        """
        from app import SafeProduct
        
        # Set up scan results in session
        with authenticated_client.session_transaction() as sess:
            sess['scan_results'] = {
                'ocr_text': 'Water, Glycerin, Vitamin E',
                'ingredients': ['Water', 'Glycerin', 'Vitamin E'],
                'analysis': {
                    'allergens_found': [],
                    'warnings': [],
                    'safe_ingredients': ['Water', 'Glycerin', 'Vitamin E']
                }
            }
        
        # Save product as safe
        response = authenticated_client.post('/scan/save', data={
            'product_name': 'Test Safe Product',
            'product_type': 'safe'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify product was saved
        with app.app_context():
            user = test_user
            product = SafeProduct.query.filter_by(
                user_id=user.id,
                product_name='Test Safe Product'
            ).first()
            assert product is not None
            assert 'Water' in product.ingredients
    
    def test_save_allergic_product(self, authenticated_client, app, test_user):
        """
        Test saving a product as allergic
        """
        from app import AllergicProduct
        
        # Set up scan results in session
        with authenticated_client.session_transaction() as sess:
            sess['scan_results'] = {
                'ocr_text': 'Water, Fragrance, Methylisothiazolinone',
                'ingredients': ['Water', 'Fragrance', 'Methylisothiazolinone'],
                'analysis': {
                    'allergens_found': [{'name': 'Fragrance', 'severity': 'severe'}],
                    'warnings': [],
                    'safe_ingredients': ['Water']
                }
            }
        
        # Save product as allergic with severity
        response = authenticated_client.post('/scan/save', data={
            'product_name': 'Test Allergic Product',
            'product_type': 'allergic',
            'reaction_severity': 'severe'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Verify product was saved
        with app.app_context():
            user = test_user
            product = AllergicProduct.query.filter_by(
                user_id=user.id,
                product_name='Test Allergic Product'
            ).first()
            assert product is not None
            assert 'Fragrance' in product.ingredients
            assert product.reaction_severity == 'severe'
    
    def test_view_allergic_products(self, authenticated_client, app, test_user):
        """
        Test viewing list of allergic products
        """
        from app import AllergicProduct
        
        # Create an allergic product
        with app.app_context():
            user = test_user
            product = AllergicProduct(
                user_id=user.id,
                product_name='Test Allergic Product',
                ingredients='Fragrance, Water',
                reaction_severity='moderate'
            )
            db.session.add(product)
            db.session.commit()
        
        # View allergic products page
        response = authenticated_client.get('/products/allergic', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Test Allergic Product' in response.data
    
    def test_delete_allergic_product(self, authenticated_client, app, test_user):
        """
        Test deleting an allergic product
        """
        from app import AllergicProduct
        
        # Create an allergic product
        with app.app_context():
            user = test_user
            product = AllergicProduct(
                user_id=user.id,
                product_name='Product To Delete',
                ingredients='Fragrance, Water',
                reaction_severity='mild'
            )
            db.session.add(product)
            db.session.commit()
            product_id = product.id
        
        # Delete the product
        response = authenticated_client.post(
            f'/products/allergic/delete/{product_id}',
            follow_redirects=True
        )
        
        assert response.status_code == 200
        
        # Verify product was deleted
        with app.app_context():
            product = AllergicProduct.query.get(product_id)
            assert product is None

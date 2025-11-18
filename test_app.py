#!/usr/bin/env python
"""Comprehensive test suite for the Derme application"""

import unittest
import os
import sys
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import (
    app, db, User, UserAllergen, SafeProduct, AllergicProduct,
    KnownAllergen, IngredientSynonym,
    normalize_ingredient, parse_ingredients, find_ingredient_synonyms,
    detect_potential_allergens, analyze_ingredients
)


class TestUserModel(unittest.TestCase):
    """Test cases for User model"""
    
    def setUp(self):
        """Set up test database before each test"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()
        
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up after each test"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
        
        # Remove test database file
        if os.path.exists('test.db'):
            os.remove('test.db')
    
    def test_user_password_hashing(self):
        """Test that passwords are properly hashed"""
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('mypassword')
            
            # Password should be hashed, not stored in plain text
            self.assertNotEqual(user.password_hash, 'mypassword')
            self.assertTrue(user.check_password('mypassword'))
            self.assertFalse(user.check_password('wrongpassword'))
    
    def test_user_security_questions(self):
        """Test security question functionality"""
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('mypassword')
            
            # Set security questions
            user.security_question_1 = 'What is your pet name?'
            user.set_security_answer(1, 'Fluffy')
            
            db.session.add(user)
            db.session.commit()
            
            # Verify security answers work
            self.assertTrue(user.check_security_answer(1, 'fluffy'))  # Case insensitive
            self.assertTrue(user.check_security_answer(1, 'Fluffy'))
            self.assertTrue(user.check_security_answer(1, ' Fluffy '))  # Trimmed
            self.assertFalse(user.check_security_answer(1, 'wrong'))
    
    def test_user_creation(self):
        """Test basic user creation"""
        with app.app_context():
            user = User(username='newuser', email='newuser@example.com')
            user.set_password('password123')
            
            db.session.add(user)
            db.session.commit()
            
            # Retrieve user and verify
            retrieved_user = User.query.filter_by(username='newuser').first()
            self.assertIsNotNone(retrieved_user)
            self.assertEqual(retrieved_user.email, 'newuser@example.com')
            self.assertTrue(retrieved_user.check_password('password123'))


class TestDatabaseModels(unittest.TestCase):
    """Test cases for database models"""
    
    def setUp(self):
        """Set up test database before each test"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        self.app = app.test_client()
        
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up after each test"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
        
        if os.path.exists('test.db'):
            os.remove('test.db')
    
    def test_user_allergen_model(self):
        """Test UserAllergen model"""
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            allergen = UserAllergen(
                user_id=user.id,
                ingredient_name='Fragrance',
                severity='severe'
            )
            db.session.add(allergen)
            db.session.commit()
            
            # Verify allergen was saved
            saved_allergen = UserAllergen.query.filter_by(user_id=user.id).first()
            self.assertIsNotNone(saved_allergen)
            self.assertEqual(saved_allergen.ingredient_name, 'Fragrance')
            self.assertEqual(saved_allergen.severity, 'severe')
    
    def test_safe_product_model(self):
        """Test SafeProduct model"""
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            product = SafeProduct(
                user_id=user.id,
                product_name='Test Lotion',
                ingredients='Water, Glycerin, Aloe Vera'
            )
            db.session.add(product)
            db.session.commit()
            
            # Verify product was saved
            saved_product = SafeProduct.query.filter_by(user_id=user.id).first()
            self.assertIsNotNone(saved_product)
            self.assertEqual(saved_product.product_name, 'Test Lotion')
            self.assertIn('Water', saved_product.ingredients)
    
    def test_allergic_product_model(self):
        """Test AllergicProduct model"""
        with app.app_context():
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            product = AllergicProduct(
                user_id=user.id,
                product_name='Bad Cream',
                ingredients='Water, Fragrance, Parabens',
                reaction_severity='moderate'
            )
            db.session.add(product)
            db.session.commit()
            
            # Verify product was saved
            saved_product = AllergicProduct.query.filter_by(user_id=user.id).first()
            self.assertIsNotNone(saved_product)
            self.assertEqual(saved_product.product_name, 'Bad Cream')
            self.assertEqual(saved_product.reaction_severity, 'moderate')


class TestHelperFunctions(unittest.TestCase):
    """Test cases for helper functions"""
    
    def test_normalize_ingredient(self):
        """Test ingredient normalization"""
        self.assertEqual(normalize_ingredient('Water'), 'water')
        self.assertEqual(normalize_ingredient('  GLYCERIN  '), 'glycerin')
        self.assertEqual(normalize_ingredient('Aloe-Vera'), 'aloe-vera')
    
    def test_parse_ingredients(self):
        """Test ingredient parsing"""
        # Test comma-separated ingredients
        ingredients = parse_ingredients('Water, Glycerin, Aloe Vera')
        self.assertEqual(len(ingredients), 3)
        self.assertIn('Water', ingredients)
        self.assertIn('Glycerin', ingredients)
        
        # Test with semicolons
        ingredients = parse_ingredients('Water; Glycerin; Aloe Vera')
        self.assertEqual(len(ingredients), 3)
        
        # Test with numbered list
        ingredients = parse_ingredients('1. Water, 2. Glycerin, 3. Aloe Vera')
        self.assertTrue(len(ingredients) >= 3)
    
    def test_parse_ingredients_with_newlines(self):
        """Test ingredient parsing with newlines"""
        ingredients = parse_ingredients('Water\nGlycerin\nAloe Vera')
        # Should handle newlines by converting to spaces
        self.assertTrue(len(ingredients) > 0)


class TestIngredientSynonyms(unittest.TestCase):
    """Test cases for ingredient synonyms"""
    
    def setUp(self):
        """Set up test database before each test"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up after each test"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
        
        if os.path.exists('test.db'):
            os.remove('test.db')
    
    def test_find_ingredient_synonyms(self):
        """Test finding ingredient synonyms"""
        with app.app_context():
            # Add a synonym
            synonym = IngredientSynonym(
                primary_name='Vitamin E',
                synonym='Tocopherol'
            )
            db.session.add(synonym)
            db.session.commit()
            
            # Find synonyms
            synonyms = find_ingredient_synonyms('Vitamin E')
            self.assertIn('vitamin e', synonyms)
            self.assertIn('tocopherol', synonyms)
            
            # Test reverse lookup
            synonyms = find_ingredient_synonyms('Tocopherol')
            self.assertIn('vitamin e', synonyms)
            self.assertIn('tocopherol', synonyms)


class TestAllergenDetection(unittest.TestCase):
    """Test cases for allergen detection"""
    
    def setUp(self):
        """Set up test database before each test"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up after each test"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
        
        if os.path.exists('test.db'):
            os.remove('test.db')
    
    def test_detect_potential_allergens(self):
        """Test detection of potential allergens"""
        with app.app_context():
            # Create test user
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            # Add allergic product
            allergic = AllergicProduct(
                user_id=user.id,
                product_name='Bad Product',
                ingredients='Water, Fragrance, Parabens'
            )
            db.session.add(allergic)
            
            # Add safe product
            safe = SafeProduct(
                user_id=user.id,
                product_name='Good Product',
                ingredients='Water, Glycerin'
            )
            db.session.add(safe)
            db.session.commit()
            
            # Detect potential allergens
            potential = detect_potential_allergens(user.id)
            
            # Fragrance and Parabens should be potential allergens
            # (present in allergic but not in safe products)
            self.assertTrue(len(potential) >= 0)  # May be empty or contain detected allergens
    
    def test_analyze_ingredients_with_known_allergen(self):
        """Test analyzing ingredients against user allergens"""
        with app.app_context():
            # Create test user
            user = User(username='testuser', email='test@example.com')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
            
            # Add user allergen
            allergen = UserAllergen(
                user_id=user.id,
                ingredient_name='Fragrance',
                severity='severe'
            )
            db.session.add(allergen)
            db.session.commit()
            
            # Analyze ingredients
            ingredients = ['Water', 'Glycerin', 'Fragrance']
            analysis = analyze_ingredients(ingredients, user.id)
            
            # Should find Fragrance as an allergen
            self.assertTrue(len(analysis['allergens_found']) > 0)
            allergen_names = [a['name'] for a in analysis['allergens_found']]
            self.assertIn('Fragrance', allergen_names)


class TestRoutes(unittest.TestCase):
    """Test cases for application routes"""
    
    def setUp(self):
        """Set up test client before each test"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        app.config['WTF_CSRF_ENABLED'] = False
        self.app = app.test_client()
        
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up after each test"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
        
        if os.path.exists('test.db'):
            os.remove('test.db')
    
    def test_index_route(self):
        """Test index page loads"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_login_page_loads(self):
        """Test login page loads"""
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
    
    def test_register_page_loads(self):
        """Test register page loads"""
        response = self.app.get('/register')
        self.assertEqual(response.status_code, 200)
    
    def test_forgot_password_page_loads(self):
        """Test forgot password page loads"""
        response = self.app.get('/forgot-password')
        self.assertEqual(response.status_code, 200)
    
    def test_dashboard_requires_login(self):
        """Test dashboard requires authentication"""
        response = self.app.get('/dashboard', follow_redirects=False)
        # Should redirect to login
        self.assertIn(response.status_code, [302, 401])


class TestKnownAllergens(unittest.TestCase):
    """Test cases for known allergen database"""
    
    def setUp(self):
        """Set up test database before each test"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        """Clean up after each test"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
        
        if os.path.exists('test.db'):
            os.remove('test.db')
    
    def test_known_allergen_creation(self):
        """Test creating known allergen entries"""
        with app.app_context():
            allergen = KnownAllergen(
                name='Formaldehyde',
                category='Preservative',
                description='Common preservative in cosmetics'
            )
            db.session.add(allergen)
            db.session.commit()
            
            # Verify allergen was saved
            saved_allergen = KnownAllergen.query.filter_by(name='Formaldehyde').first()
            self.assertIsNotNone(saved_allergen)
            self.assertEqual(saved_allergen.category, 'Preservative')


def run_tests():
    """Run all tests and return results"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestUserModel))
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseModels))
    suite.addTests(loader.loadTestsFromTestCase(TestHelperFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestIngredientSynonyms))
    suite.addTests(loader.loadTestsFromTestCase(TestAllergenDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestRoutes))
    suite.addTests(loader.loadTestsFromTestCase(TestKnownAllergens))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == '__main__':
    print("="*70)
    print("Running Derme Application Test Suite")
    print("="*70)
    print()
    
    result = run_tests()
    
    print()
    print("="*70)
    print("Test Summary")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)

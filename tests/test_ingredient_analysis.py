"""
Unit tests for Ingredient Analysis & Allergen Detection (Use Case 5)
Tests corresponding to TC-ANALYSIS-001, TC-ANALYSIS-002, TC-ANALYSIS-003, TC-ANALYSIS-004, TC-ANALYSIS-005
"""
import pytest
from app import analyze_ingredients, normalize_ingredient, find_ingredient_synonyms, detect_potential_allergens, db


class TestIngredientAnalysis:
    """Test cases for ingredient analysis and allergen detection functionality"""
    
    def test_analyze_with_user_allergen_match(self, app, test_user_with_allergen, known_allergen_db):
        """
        TC-ANALYSIS-001: Analyze Ingredients with User Allergen Match
        Verify that analysis correctly identifies user's personal allergens
        """
        with app.app_context():
            user = test_user_with_allergen
            # User has "Fragrance" allergen with severity "severe"
            
            # Test ingredients containing user's allergen
            ingredients = ["Water", "Glycerin", "Fragrance", "Vitamin E"]
            
            # Perform analysis
            results = analyze_ingredients(ingredients, user.id)
            
            # Verify allergen was found
            assert len(results['allergens_found']) > 0
            
            # Find the Fragrance allergen in results
            found_fragrance = False
            for allergen in results['allergens_found']:
                if allergen['name'].lower() == 'fragrance':
                    found_fragrance = True
                    assert allergen['severity'] == 'severe'
            
            assert found_fragrance, "User's personal allergen (Fragrance) should be detected"
    
    def test_analyze_with_known_database_allergen(self, app, test_user, known_allergen_db):
        """
        TC-ANALYSIS-002: Analyze Ingredients with Known Database Allergen
        Verify that analysis identifies known allergens from database
        """
        with app.app_context():
            user = test_user
            # User has no personal allergens
            
            # Test ingredients with known allergen from database
            ingredients = ["Water", "Methylisothiazolinone", "Glycerin"]
            
            # Perform analysis
            results = analyze_ingredients(ingredients, user.id)
            
            # Verify warning was generated for known allergen
            assert len(results['warnings']) > 0
            
            # Find Methylisothiazolinone in warnings
            found_mit = False
            for warning in results['warnings']:
                if 'methylisothiazolinone' in warning['name'].lower():
                    found_mit = True
                    # Should have database information
                    assert 'where_found' in warning or 'description' in warning
            
            assert found_mit, "Known allergen from database should be detected"
    
    def test_analyze_safe_ingredients(self, app, test_user, known_allergen_db):
        """
        TC-ANALYSIS-003: Analyze Safe Ingredients (No Allergens)
        Verify that analysis correctly identifies all ingredients as safe
        """
        with app.app_context():
            user = test_user
            
            # Test safe ingredients
            ingredients = ["Water", "Glycerin", "Vitamin E", "Shea Butter"]
            
            # Perform analysis
            results = analyze_ingredients(ingredients, user.id)
            
            # Verify no allergens found
            assert len(results['allergens_found']) == 0
            
            # Verify no warnings (assuming these aren't in allergen database)
            # Note: Some might be in database, so check safe ingredients exist
            assert len(results['safe_ingredients']) > 0
    
    def test_analyze_with_synonym_matching(self, app, test_user_with_allergen, known_allergen_db):
        """
        TC-ANALYSIS-004: Analyze with Synonym Matching
        Verify that analysis matches allergens using synonyms
        """
        with app.app_context():
            user = test_user_with_allergen
            # User has "Fragrance" allergen
            
            # Test with synonym "Parfum" (synonym for Fragrance)
            ingredients = ["Water", "Parfum", "Glycerin"]
            
            # Perform analysis
            results = analyze_ingredients(ingredients, user.id)
            
            # Verify synonym was matched to user allergen
            assert len(results['allergens_found']) > 0
            
            # Should find allergen (either as Parfum or mapped to Fragrance)
            found_allergen = False
            for allergen in results['allergens_found']:
                if allergen['severity'] == 'severe':  # User's fragrance allergen
                    found_allergen = True
            
            assert found_allergen, "Synonym (Parfum) should match user allergen (Fragrance)"
    
    def test_analyze_empty_ingredient_list(self, app, test_user):
        """
        TC-ANALYSIS-005: Analyze Empty Ingredient List
        Verify handling of empty ingredient list
        """
        with app.app_context():
            user = test_user
            
            # Test with empty ingredient list
            ingredients = []
            
            # Perform analysis
            results = analyze_ingredients(ingredients, user.id)
            
            # Verify results structure is correct
            assert 'allergens_found' in results
            assert 'safe_ingredients' in results
            assert 'warnings' in results
            
            # All lists should be empty
            assert len(results['allergens_found']) == 0
            assert len(results['safe_ingredients']) == 0
            assert len(results['warnings']) == 0
    
    def test_normalize_ingredient_function(self):
        """
        Test the normalize_ingredient helper function
        """
        # Test case insensitivity
        assert normalize_ingredient("FRAGRANCE") == normalize_ingredient("fragrance")
        assert normalize_ingredient("Fragrance") == normalize_ingredient("fragrance")
        
        # Test whitespace handling
        assert normalize_ingredient("  Water  ") == "water"
        assert normalize_ingredient("Vitamin E") == "vitamin e"
    
    def test_find_ingredient_synonyms_function(self, app, known_allergen_db):
        """
        Test the find_ingredient_synonyms helper function
        """
        with app.app_context():
            # Test finding synonyms for Fragrance
            synonyms = find_ingredient_synonyms("Fragrance")
            
            assert len(synonyms) > 0
            assert "fragrance" in synonyms
            # Should include Parfum and Perfume from our test data
            assert "parfum" in synonyms or "perfume" in synonyms
    
    def test_analyze_multiple_allergens(self, app, test_user, known_allergen_db):
        """
        Test analysis with multiple different allergens
        """
        from app import UserAllergen
        
        with app.app_context():
            user = test_user
            
            # Add multiple allergens for user
            allergen1 = UserAllergen(
                user_id=user.id,
                ingredient_name='Fragrance',
                severity='severe'
            )
            allergen2 = UserAllergen(
                user_id=user.id,
                ingredient_name='Formaldehyde',
                severity='moderate'
            )
            db.session.add(allergen1)
            db.session.add(allergen2)
            db.session.commit()
            
            # Test with ingredients containing both allergens
            ingredients = ["Water", "Fragrance", "Glycerin", "Formaldehyde", "Vitamin E"]
            
            # Perform analysis
            results = analyze_ingredients(ingredients, user.id)
            
            # Should find both allergens
            assert len(results['allergens_found']) >= 2
    
    def test_analyze_case_insensitive_matching(self, app, test_user_with_allergen, known_allergen_db):
        """
        Test that allergen matching is case-insensitive
        """
        with app.app_context():
            user = test_user_with_allergen
            
            # Test with different case variations
            test_cases = [
                ["water", "FRAGRANCE", "glycerin"],
                ["Water", "fragrance", "Glycerin"],
                ["WATER", "Fragrance", "GLYCERIN"]
            ]
            
            for ingredients in test_cases:
                results = analyze_ingredients(ingredients, user.id)
                # Should find fragrance allergen regardless of case
                assert len(results['allergens_found']) > 0
    
    def test_detect_potential_allergens_function(self, app, test_user):
        """
        Test the detect_potential_allergens cross-referencing function
        """
        from app import SafeProduct, AllergicProduct
        
        with app.app_context():
            user = test_user
            
            # Add a safe product
            safe = SafeProduct(
                user_id=user.id,
                product_name='Safe Product',
                ingredients='Water, Glycerin, Vitamin E'
            )
            db.session.add(safe)
            
            # Add an allergic product with some unique ingredients
            allergic = AllergicProduct(
                user_id=user.id,
                product_name='Allergic Product',
                ingredients='Water, Glycerin, Fragrance',
                reaction_severity='severe'
            )
            db.session.add(allergic)
            db.session.commit()
            
            # Detect potential allergens
            potential = detect_potential_allergens(user.id)
            
            # Fragrance should be detected as potential allergen
            # (in allergic but not in safe product)
            potential_names = [p['name'].lower() for p in potential]
            assert 'fragrance' in potential_names
    
    def test_analyze_with_special_characters(self, app, test_user):
        """
        Test analysis with ingredients containing special characters
        """
        with app.app_context():
            user = test_user
            
            # Test ingredients with parentheses, dashes, etc.
            ingredients = [
                "Water (Aqua)",
                "Vitamin E (Tocopherol)",
                "Alpha-Hydroxy Acid",
                "Sodium Laureth Sulfate (SLS)"
            ]
            
            # Should not crash and should return valid results
            results = analyze_ingredients(ingredients, user.id)
            
            assert 'allergens_found' in results
            assert 'safe_ingredients' in results
            assert 'warnings' in results
    
    def test_analyze_ingredients_with_numbers(self, app, test_user):
        """
        Test analysis with ingredients containing numbers (chemical formulas)
        """
        with app.app_context():
            user = test_user
            
            ingredients = [
                "Butylene Glycol",
                "PEG-40 Hydrogenated Castor Oil",
                "CI 77891",
                "FD&C Red No. 40"
            ]
            
            # Should handle ingredients with numbers
            results = analyze_ingredients(ingredients, user.id)
            
            assert 'allergens_found' in results
            assert isinstance(results['allergens_found'], list)

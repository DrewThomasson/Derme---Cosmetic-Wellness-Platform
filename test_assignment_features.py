import unittest
from app import app, db, User, UserAllergen, KnownAllergen, IngredientSynonym, analyze_ingredients

class TestAssignmentFeatures(unittest.TestCase):
    def setUp(self):
        """Set up test database and context"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create a test user
        self.user = User(username='testuser', email='test@example.com')
        self.user.set_password('password123')
        db.session.add(self.user)
        db.session.commit()

    def tearDown(self):
        """Clean up after tests"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

class TestAnalyzeIngredients(TestAssignmentFeatures):
    """Tests for Feature 1: Analyze Product Ingredients"""

    def setUp(self):
        super().setUp()
        # Add user allergens
        self.allergen = UserAllergen(user_id=self.user.id, ingredient_name='Peanut', severity='severe')
        db.session.add(self.allergen)
        
        # Add ingredient synonym
        self.synonym = IngredientSynonym(primary_name='Peanut', synonym='Arachis hypogaea')
        db.session.add(self.synonym)
        
        # Add known allergen
        self.known = KnownAllergen(name='Parabens', where_found='Preservatives', category='Preservative')
        db.session.add(self.known)
        
        db.session.commit()

    def test_analyze_empty_list(self):
        """TC-01: Analyze Empty List"""
        print("\n" + "-"*50)
        print("Running TC-01: Analyze Empty List")
        print("Input: []")
        result = analyze_ingredients([], self.user.id)
        print(f"Output: {result}")
        self.assertEqual(result['allergens_found'], [])
        self.assertEqual(result['safe_ingredients'], [])
        self.assertEqual(result['warnings'], [])

    def test_analyze_safe_ingredients(self):
        """TC-02: Analyze Safe Ingredients"""
        print("\n" + "-"*50)
        print("Running TC-02: Analyze Safe Ingredients")
        ingredients = ['Water', 'Glycerin']
        print(f"Input: {ingredients}")
        result = analyze_ingredients(ingredients, self.user.id)
        print(f"Output: {result}")
        self.assertEqual(result['safe_ingredients'], ['Water', 'Glycerin'])
        self.assertEqual(result['allergens_found'], [])

    def test_analyze_user_allergen_direct(self):
        """TC-03: Analyze User Allergen (Direct)"""
        print("\n" + "-"*50)
        print("Running TC-03: Analyze User Allergen (Direct)")
        ingredients = ['Peanut']
        print(f"Input: {ingredients}")
        print("Context: User is allergic to 'Peanut'")
        result = analyze_ingredients(ingredients, self.user.id)
        print(f"Output: {result}")
        self.assertEqual(len(result['allergens_found']), 1)
        self.assertEqual(result['allergens_found'][0]['name'], 'Peanut')
        self.assertEqual(result['allergens_found'][0]['severity'], 'severe')

    def test_analyze_user_allergen_synonym(self):
        """TC-04: Analyze User Allergen (Synonym)"""
        print("\n" + "-"*50)
        print("Running TC-04: Analyze User Allergen (Synonym)")
        ingredients = ['Arachis hypogaea']
        print(f"Input: {ingredients}")
        print("Context: 'Arachis hypogaea' is a synonym for 'Peanut'")
        result = analyze_ingredients(ingredients, self.user.id)
        print(f"Output: {result}")
        self.assertEqual(len(result['allergens_found']), 1)
        self.assertEqual(result['allergens_found'][0]['name'], 'Arachis hypogaea')
        # Should still detect severity from the primary allergen 'Peanut'
        self.assertEqual(result['allergens_found'][0]['severity'], 'severe')

    def test_analyze_known_allergen(self):
        """TC-05: Analyze Known Allergen"""
        print("\n" + "-"*50)
        print("Running TC-05: Analyze Known Allergen")
        ingredients = ['Parabens']
        print(f"Input: {ingredients}")
        print("Context: 'Parabens' is in the KnownAllergen database")
        result = analyze_ingredients(ingredients, self.user.id)
        print(f"Output: {result}")
        self.assertEqual(len(result['warnings']), 1)
        self.assertEqual(result['warnings'][0]['name'], 'Parabens')
        self.assertEqual(result['warnings'][0]['category'], 'Preservative')

    def test_analyze_mixed_list(self):
        """TC-06: Analyze Mixed List"""
        print("\n" + "-"*50)
        print("Running TC-06: Analyze Mixed List")
        ingredients = ['Water', 'Peanut']
        print(f"Input: {ingredients}")
        result = analyze_ingredients(ingredients, self.user.id)
        print(f"Output: {result}")
        self.assertEqual(result['safe_ingredients'], ['Water'])
        self.assertEqual(len(result['allergens_found']), 1)
        self.assertEqual(result['allergens_found'][0]['name'], 'Peanut')

class TestSecurityAnswer(TestAssignmentFeatures):
    """Tests for Feature 2: Verify Security Answer"""

    def setUp(self):
        super().setUp()
        # Set up security questions for the user
        self.user.security_question_1 = "What is your pet's name?"
        self.user.set_security_answer(1, "Fido")
        db.session.commit()

    def test_verify_correct_answer(self):
        """TC-07: Verify Correct Answer"""
        print("\n" + "-"*50)
        print("Running TC-07: Verify Correct Answer")
        print("Question: 1, Answer: 'Fido'")
        print("Input: 'Fido'")
        result = self.user.check_security_answer(1, "Fido")
        print(f"Output: {result}")
        self.assertTrue(result)

    def test_verify_correct_answer_case_space(self):
        """TC-08: Verify Correct Answer (Case/Whitespace)"""
        print("\n" + "-"*50)
        print("Running TC-08: Verify Correct Answer (Case/Whitespace)")
        print("Question: 1, Answer: 'Fido'")
        print("Input: '  fido  '")
        result = self.user.check_security_answer(1, "  fido  ")
        print(f"Output: {result}")
        self.assertTrue(result)

    def test_verify_incorrect_answer(self):
        """TC-09: Verify Incorrect Answer"""
        print("\n" + "-"*50)
        print("Running TC-09: Verify Incorrect Answer")
        print("Question: 1, Answer: 'Fido'")
        print("Input: 'Rex'")
        result = self.user.check_security_answer(1, "Rex")
        print(f"Output: {result}")
        self.assertFalse(result)

    def test_verify_empty_answer(self):
        """TC-10: Verify Empty Answer"""
        print("\n" + "-"*50)
        print("Running TC-10: Verify Empty Answer")
        print("Question: 1, Answer: 'Fido'")
        print("Input: ''")
        result = self.user.check_security_answer(1, "")
        print(f"Output: {result}")
        self.assertFalse(result)

    def test_verify_unset_question(self):
        """TC-11: Verify Unset Question"""
        print("\n" + "-"*50)
        print("Running TC-11: Verify Unset Question")
        print("Question: 2 (Not set)")
        print("Input: 'Anything'")
        result = self.user.check_security_answer(2, "Anything")
        print(f"Output: {result}")
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()

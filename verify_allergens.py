from app import app, db, analyze_ingredients, User, UserAllergen, KnownAllergen, IngredientSynonym, load_allergens_from_json
import os

def run_test():
    print("=== TC-002: Allergen Detection Verification ===")
    
    # Use a fresh test database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///verify_allergens.db'
    app.config['TESTING'] = True
    
    if os.path.exists('instance/verify_allergens.db'):
        os.remove('instance/verify_allergens.db')
        
    with app.app_context():
        db.create_all()
        
        # 1. Setup Data
        # Create a user
        user = User(username='test_allergen_user', email='test_allergen@example.com')
        user.set_password('password')
        db.session.add(user)
        db.session.commit()
        
        # Add "Fragrance" as a known allergen in the system (simulating loaded data)
        # We need to ensure synonyms are loaded. 
        # Instead of loading the huge JSON, let's manually add the relevant entries for this test.
        
        # Add Known Allergen
        ka = KnownAllergen(
            name='Fragrance',
            category='Fragrance',
            description='Common allergen',
            where_found='Perfumes, lotions',
            product_categories='["Cosmetics"]'
        )
        db.session.add(ka)
        
        # Add Synonym: Parfum -> Fragrance
        syn = IngredientSynonym(primary_name='Fragrance', synonym='Parfum')
        db.session.add(syn)
        
        db.session.commit()
        
        # 2. Test Case: User is NOT allergic yet, but we want to see if it's flagged as a "Warning" (Known Allergen)
        print("Testing detection of 'Parfum' as a Known Allergen (Warning)...")
        ingredients = ['Aqua', 'Parfum', 'Glycerin']
        results = analyze_ingredients(ingredients, user.id)
        
        # Check Warnings
        warnings = results['warnings']
        found_parfum = False
        for w in warnings:
            if w['name'] == 'Parfum' and w['allergen_name'] == 'Fragrance':
                found_parfum = True
                break
        
        if found_parfum:
            print("SUCCESS: 'Parfum' correctly identified as 'Fragrance' warning.")
        else:
            print("FAILED: 'Parfum' was not identified as a warning.")
            print(f"Results: {results}")
            exit(1)
            
        # 3. Test Case: User IS allergic to Fragrance
        print("Testing detection of 'Parfum' for a user allergic to 'Fragrance'...")
        ua = UserAllergen(user_id=user.id, ingredient_name='Fragrance', severity='severe')
        db.session.add(ua)
        db.session.commit()
        
        results = analyze_ingredients(ingredients, user.id)
        
        # Check Allergens Found
        found_personal = False
        for a in results['allergens_found']:
            if a['name'] == 'Parfum':
                found_personal = True
                break
                
        if found_personal:
            print("SUCCESS: 'Parfum' correctly identified as personal allergen.")
            print("TC-002 PASSED")
        else:
            print("FAILED: 'Parfum' was not identified as personal allergen.")
            print(f"Results: {results}")
            exit(1)

if __name__ == "__main__":
    run_test()

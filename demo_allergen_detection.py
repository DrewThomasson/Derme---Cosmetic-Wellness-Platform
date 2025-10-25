#!/usr/bin/env python3
"""
Demonstration script for the Contact Dermatitis Institute allergen database integration.
This script shows how the allergen detection system works with real cosmetic ingredients.
"""

from app import app, db, User, UserAllergen, KnownAllergen, IngredientSynonym
from app import init_db, analyze_ingredients
import json

def print_header(text):
    print('\n' + '=' * 80)
    print(f'  {text}')
    print('=' * 80)

def print_section(text):
    print('\n' + '-' * 80)
    print(f'  {text}')
    print('-' * 80)

def main():
    # Initialize database
    init_db()
    
    with app.app_context():
        # Get database statistics
        allergen_count = KnownAllergen.query.count()
        synonym_count = IngredientSynonym.query.count()
        
        print_header('DERME - CONTACT DERMATITIS ALLERGEN DATABASE DEMO')
        
        print('\n📊 Database Statistics:')
        print(f'   • Total Allergens: {allergen_count}')
        print(f'   • Total Synonyms: {synonym_count}')
        print(f'   • Data Source: Contact Dermatitis Institute')
        
        # Create a demo user
        demo_user = User.query.filter_by(username='demo_user').first()
        if not demo_user:
            demo_user = User(username='demo_user', email='demo@example.com')
            demo_user.set_password('demo123')
            db.session.add(demo_user)
            db.session.commit()
            
            # Add a personal allergen
            allergen = UserAllergen(
                user_id=demo_user.id,
                ingredient_name='Fragrance',
                severity='severe'
            )
            db.session.add(allergen)
            db.session.commit()
        
        print_section('EXAMPLE 1: Analyzing a Shampoo Product')
        
        print('\n🧴 Product: Daily Moisturizing Shampoo')
        print('📝 Ingredients:')
        
        shampoo_ingredients = [
            'Water',
            'Sodium Laureth Sulfate',
            'Cocamidopropyl Betaine',
            'Methylisothiazolinone',
            'Methylchloroisothiazolinone',
            'Fragrance',
            'Citric Acid',
            'Sodium Chloride',
            'Glycerin'
        ]
        
        for i, ing in enumerate(shampoo_ingredients, 1):
            print(f'     {i}. {ing}')
        
        # Analyze ingredients
        results = analyze_ingredients(shampoo_ingredients, demo_user.id)
        
        print('\n📊 Analysis Results:')
        print(f'   🚨 User Allergens Found: {len(results["allergens_found"])}')
        print(f'   ⚠️  Known Database Allergens: {len(results["warnings"])}')
        print(f'   ✅ Safe Ingredients: {len(results["safe_ingredients"])}')
        
        if results['allergens_found']:
            print('\n🚨 WARNING: YOUR PERSONAL ALLERGENS DETECTED!')
            for allergen in results['allergens_found']:
                print(f'\n   • {allergen["name"]}')
                print(f'     Severity: {allergen["severity"].upper()}')
                print(f'     Recommendation: AVOID this product')
        
        if results['warnings']:
            print('\n⚠️  KNOWN CONTACT DERMATITIS ALLERGENS DETECTED:')
            for warning in results['warnings'][:3]:  # Show first 3
                print(f'\n   • {warning["name"]}')
                if warning.get('allergen_name') and warning['allergen_name'] != warning['name']:
                    print(f'     Also known as: {warning["allergen_name"]}')
                if warning.get('where_found'):
                    desc = warning['where_found'].replace('\n', ' ')[:120]
                    print(f'     Where found: {desc}...')
                if warning.get('product_categories'):
                    cats = ', '.join(warning['product_categories'][:3])
                    print(f'     Common in: {cats}')
        
        print_section('EXAMPLE 2: Analyzing a Safe Moisturizer')
        
        print('\n🧴 Product: Gentle Face Moisturizer')
        print('📝 Ingredients:')
        
        moisturizer_ingredients = [
            'Water',
            'Glycerin',
            'Cetyl Alcohol',
            'Shea Butter',
            'Vitamin E',
            'Aloe Vera Extract'
        ]
        
        for i, ing in enumerate(moisturizer_ingredients, 1):
            print(f'     {i}. {ing}')
        
        # Analyze ingredients
        results = analyze_ingredients(moisturizer_ingredients, demo_user.id)
        
        print('\n📊 Analysis Results:')
        print(f'   🚨 User Allergens Found: {len(results["allergens_found"])}')
        print(f'   ⚠️  Known Database Allergens: {len(results["warnings"])}')
        print(f'   ✅ Safe Ingredients: {len(results["safe_ingredients"])}')
        
        if len(results['allergens_found']) == 0 and len(results['warnings']) == 0:
            print('\n✅ SAFE TO USE!')
            print('   No allergens detected in this product.')
            print('   All ingredients appear safe based on the allergen database.')
        
        print_section('EXAMPLE 3: Synonym Detection')
        
        print('\n🔍 Testing ingredient name variations...')
        print('📝 Ingredients using alternative names:')
        
        synonym_test = [
            'Parfum',           # Alternative name for Fragrance
            'MIT',              # Abbreviation for Methylisothiazolinone
            'Kathon CG',        # Trade name for preservative blend
        ]
        
        for i, ing in enumerate(synonym_test, 1):
            print(f'     {i}. {ing}')
        
        results = analyze_ingredients(synonym_test, demo_user.id)
        
        print('\n📊 Synonym Matching Results:')
        if results['allergens_found']:
            print(f'   ✅ User allergen matched via synonym!')
            for allergen in results['allergens_found']:
                print(f'      "{allergen["name"]}" → User allergen detected')
        
        if results['warnings']:
            print(f'   ✅ Database allergen matched via synonym!')
            for warning in results['warnings']:
                print(f'      "{warning["name"]}" → Known allergen: {warning.get("allergen_name", "N/A")}')
        
        print_section('Sample Allergen Information')
        
        # Show detailed info for one allergen
        mit = KnownAllergen.query.filter(
            db.func.lower(KnownAllergen.name).like('%methylisothiazolinone%')
        ).first()
        
        if mit:
            print(f'\n📋 Allergen: {mit.name}')
            print(f'   Category: {mit.category}')
            if mit.where_found:
                print(f'   Where Found: {mit.where_found[:150]}...')
            if mit.product_categories:
                cats = json.loads(mit.product_categories)
                print(f'   Product Categories: {", ".join(cats[:5])}')
            if mit.url:
                print(f'   More Info: {mit.url}')
        
        print_header('DEMO COMPLETE')
        
        print('\n✨ Key Features Demonstrated:')
        print('   ✅ Comprehensive allergen database (496 allergens, 14K+ synonyms)')
        print('   ✅ Personal allergen tracking')
        print('   ✅ Synonym and alternative name matching')
        print('   ✅ Detailed allergen information')
        print('   ✅ Clear safety recommendations')
        
        print('\n📚 Data Source:')
        print('   Contact Dermatitis Institute')
        print('   https://www.contactdermatitisinstitute.com')
        
        print('\n⚠️  Disclaimer:')
        print('   This information is for educational purposes only.')
        print('   Always consult a healthcare professional for medical advice.')
        print()

if __name__ == '__main__':
    main()

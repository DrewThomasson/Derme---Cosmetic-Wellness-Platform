#!/usr/bin/env python3
"""Quick script to check users while app is running"""

from app import app, db, User, UserAllergen, SafeProduct, AllergicProduct

with app.app_context():
    # Count users
    user_count = User.query.count()
    print(f"\n{'='*60}")
    print(f"DERME DATABASE STATUS")
    print(f"{'='*60}")
    print(f"Total Users: {user_count}\n")
    
    # List all users
    users = User.query.all()
    for user in users:
        print(f"User ID: {user.id}")
        print(f"  Username: {user.username}")
        print(f"  Email: {user.email}")
        
        # Count their data
        allergen_count = UserAllergen.query.filter_by(user_id=user.id).count()
        safe_count = SafeProduct.query.filter_by(user_id=user.id).count()
        allergic_count = AllergicProduct.query.filter_by(user_id=user.id).count()
        
        print(f"  Allergens: {allergen_count}")
        print(f"  Safe Products: {safe_count}")
        print(f"  Allergic Products: {allergic_count}")
        print()
    
    print(f"{'='*60}\n")

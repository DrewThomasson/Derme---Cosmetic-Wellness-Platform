#!/usr/bin/env python
"""Test script to verify the EpiPen functionality"""

from datetime import date, timedelta
from app import app, db, User, EpiPen

def test_epipen_feature():
    """Test the EpiPen feature"""
    with app.app_context():
        # Initialize database
        db.create_all()
        
        # Check if test user already exists
        test_user = User.query.filter_by(email='epipen_test@example.com').first()
        
        if not test_user:
            # Create a test user
            test_user = User(username='epipen_testuser', email='epipen_test@example.com')
            test_user.set_password('testpass123')
            db.session.add(test_user)
            db.session.commit()
            print("✓ Test user created successfully")
        else:
            print("✓ Test user already exists")
        
        print(f"  Username: {test_user.username}")
        print(f"  Email: {test_user.email}")
        
        # Test 1: Create an expired EpiPen
        expired_date = date.today() - timedelta(days=30)
        expired_epipen = EpiPen(
            user_id=test_user.id,
            name='EpiPen Jr - Expired',
            location='Test Location',
            expiration_date=expired_date,
            lot_number='TEST001'
        )
        db.session.add(expired_epipen)
        db.session.commit()
        
        assert expired_epipen.is_expired() == True, "Expired EpiPen should be marked as expired"
        assert expired_epipen.days_until_expiration() < 0, "Expired EpiPen should have negative days"
        print("\n✓ Expired EpiPen detection works")
        
        # Test 2: Create an EpiPen expiring soon
        expiring_soon_date = date.today() + timedelta(days=15)
        expiring_soon_epipen = EpiPen(
            user_id=test_user.id,
            name='EpiPen - Expiring Soon',
            location='Purse',
            expiration_date=expiring_soon_date,
            lot_number='TEST002'
        )
        db.session.add(expiring_soon_epipen)
        db.session.commit()
        
        assert expiring_soon_epipen.is_expired() == False, "Expiring soon EpiPen should not be expired"
        assert expiring_soon_epipen.needs_reminder(30) == True, "EpiPen expiring in 15 days should need reminder"
        assert expiring_soon_epipen.days_until_expiration() == 15, "EpiPen should have 15 days remaining"
        print("✓ Expiring soon EpiPen detection works")
        
        # Test 3: Create a current EpiPen (not expiring soon)
        current_date = date.today() + timedelta(days=180)
        current_epipen = EpiPen(
            user_id=test_user.id,
            name='EpiPen - Current',
            location='Home',
            expiration_date=current_date,
            lot_number='TEST003',
            notes='Test notes'
        )
        db.session.add(current_epipen)
        db.session.commit()
        
        assert current_epipen.is_expired() == False, "Current EpiPen should not be expired"
        assert current_epipen.needs_reminder(30) == False, "Current EpiPen should not need reminder"
        assert current_epipen.days_until_expiration() == 180, "EpiPen should have 180 days remaining"
        print("✓ Current EpiPen detection works")
        
        # Test 4: Query all EpiPens for the user
        user_epipens = EpiPen.query.filter_by(user_id=test_user.id).all()
        assert len(user_epipens) >= 3, "Should have at least 3 EpiPens"
        print(f"✓ User has {len(user_epipens)} EpiPens tracked")
        
        # Test 5: Filter expired EpiPens
        expired_epipens = [e for e in user_epipens if e.is_expired()]
        assert len(expired_epipens) >= 1, "Should have at least 1 expired EpiPen"
        print(f"✓ Found {len(expired_epipens)} expired EpiPen(s)")
        
        # Test 6: Filter expiring soon EpiPens
        expiring_soon_epipens = [e for e in user_epipens if e.needs_reminder(30) and not e.is_expired()]
        assert len(expiring_soon_epipens) >= 1, "Should have at least 1 EpiPen expiring soon"
        print(f"✓ Found {len(expiring_soon_epipens)} EpiPen(s) expiring soon")
        
        # Test 7: Update an EpiPen
        current_epipen.location = 'Updated Location'
        current_epipen.notes = 'Updated notes'
        db.session.commit()
        
        updated_epipen = EpiPen.query.get(current_epipen.id)
        assert updated_epipen.location == 'Updated Location', "Location should be updated"
        assert updated_epipen.notes == 'Updated notes', "Notes should be updated"
        print("✓ EpiPen update works correctly")
        
        # Test 8: Delete an EpiPen
        epipen_id_to_delete = expired_epipen.id
        db.session.delete(expired_epipen)
        db.session.commit()
        
        deleted_epipen = EpiPen.query.get(epipen_id_to_delete)
        assert deleted_epipen is None, "EpiPen should be deleted"
        print("✓ EpiPen deletion works correctly")
        
        print("\n" + "="*60)
        print("ALL EPIPEN TESTS PASSED!")
        print("="*60)
        print("\nEpiPen feature is working correctly with:")
        print("  - Expiration date tracking")
        print("  - Expired detection")
        print("  - Expiring soon reminders (30-day threshold)")
        print("  - Location and lot number tracking")
        print("  - Notes support")
        print("  - CRUD operations (Create, Read, Update, Delete)")

if __name__ == '__main__':
    test_epipen_feature()

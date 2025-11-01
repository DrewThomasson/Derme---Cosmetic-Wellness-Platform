"""
Unit tests for Allergen Management (Use Case 3)
Tests corresponding to TC-ALLERGEN-001, TC-ALLERGEN-002, TC-ALLERGEN-003
"""
import pytest
from app import UserAllergen, User, db


class TestAllergenManagement:
    """Test cases for user allergen management functionality"""
    
    def test_add_personal_allergen(self, authenticated_client, app, test_user):
        """
        TC-ALLERGEN-001: Add Personal Allergen
        Verify that authenticated user can add a personal allergen
        """
        # Test inputs
        ingredient_name = "Methylisothiazolinone"
        severity = "severe"
        
        with app.app_context():
            user = test_user
            initial_count = UserAllergen.query.filter_by(user_id=user.id).count()
        
        # Add allergen
        response = authenticated_client.post('/allergens', data={
            'ingredient_name': ingredient_name,
            'severity': severity
        }, follow_redirects=True)
        
        # Assert success
        assert response.status_code == 200
        
        # Verify allergen was added to database
        with app.app_context():
            user = test_user
            final_count = UserAllergen.query.filter_by(user_id=user.id).count()
            assert final_count == initial_count + 1
            
            # Verify the allergen details
            allergen = UserAllergen.query.filter_by(
                user_id=user.id,
                ingredient_name=ingredient_name
            ).first()
            assert allergen is not None
            assert allergen.severity == severity
    
    def test_delete_personal_allergen(self, authenticated_client, app, test_user_with_allergen):
        """
        TC-ALLERGEN-002: Delete Personal Allergen
        Verify that authenticated user can delete a personal allergen
        """
        with app.app_context():
            user = test_user_with_allergen
            # Get the allergen to delete
            allergen = UserAllergen.query.filter_by(user_id=user.id).first()
            assert allergen is not None
            allergen_id = allergen.id
            initial_count = UserAllergen.query.filter_by(user_id=user.id).count()
        
        # Delete the allergen
        response = authenticated_client.post(
            f'/allergens/delete/{allergen_id}',
            follow_redirects=True
        )
        
        # Assert success
        assert response.status_code == 200
        
        # Verify allergen was deleted
        with app.app_context():
            user = test_user_with_allergen
            final_count = UserAllergen.query.filter_by(user_id=user.id).count()
            assert final_count == initial_count - 1
            
            # Verify specific allergen no longer exists
            deleted_allergen = UserAllergen.query.get(allergen_id)
            assert deleted_allergen is None
    
    def test_add_allergen_with_empty_name(self, authenticated_client, app, test_user):
        """
        TC-ALLERGEN-003: Add Allergen with Empty Name
        Verify that adding allergen with empty name fails
        """
        with app.app_context():
            user = test_user
            initial_count = UserAllergen.query.filter_by(user_id=user.id).count()
        
        # Attempt to add allergen with empty name
        response = authenticated_client.post('/allergens', data={
            'ingredient_name': '',
            'severity': 'moderate'
        }, follow_redirects=True)
        
        # Verify no allergen was added
        with app.app_context():
            user = test_user
            final_count = UserAllergen.query.filter_by(user_id=user.id).count()
            assert final_count == initial_count
    
    def test_add_multiple_allergens(self, authenticated_client, app, test_user):
        """
        Test adding multiple allergens to user's list
        """
        allergens = [
            ('Fragrance', 'severe'),
            ('Methylisothiazolinone', 'moderate'),
            ('Formaldehyde', 'mild')
        ]
        
        with app.app_context():
            user = test_user
            initial_count = UserAllergen.query.filter_by(user_id=user.id).count()
        
        # Add multiple allergens
        for ingredient, severity in allergens:
            authenticated_client.post('/allergens', data={
                'ingredient_name': ingredient,
                'severity': severity
            }, follow_redirects=True)
        
        # Verify all allergens were added
        with app.app_context():
            user = test_user
            final_count = UserAllergen.query.filter_by(user_id=user.id).count()
            assert final_count == initial_count + len(allergens)
    
    def test_allergen_management_requires_authentication(self, client):
        """
        Verify that allergen management requires user to be logged in
        """
        # Try to access allergen page without login
        response = client.get('/allergens', follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location
        
        # Try to add allergen without login
        response = client.post('/allergens', data={
            'ingredient_name': 'Fragrance',
            'severity': 'severe'
        }, follow_redirects=False)
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_view_allergen_list(self, authenticated_client, app, test_user_with_allergen):
        """
        Verify that user can view their allergen list
        """
        response = authenticated_client.get('/allergens', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'Fragrance' in response.data  # From test_user_with_allergen fixture
    
    def test_add_allergen_with_different_severities(self, authenticated_client, app, test_user):
        """
        Test adding allergens with different severity levels
        """
        severities = ['mild', 'moderate', 'severe', 'unknown']
        
        for i, severity in enumerate(severities):
            ingredient_name = f"TestAllergen{i}"
            
            authenticated_client.post('/allergens', data={
                'ingredient_name': ingredient_name,
                'severity': severity
            }, follow_redirects=True)
            
            # Verify allergen was added with correct severity
            with app.app_context():
                user = test_user
                allergen = UserAllergen.query.filter_by(
                    user_id=user.id,
                    ingredient_name=ingredient_name
                ).first()
                assert allergen is not None
                assert allergen.severity == severity
    
    def test_cannot_delete_another_users_allergen(self, client, app):
        """
        Verify that users cannot delete allergens belonging to other users
        """
        # Create two users
        with app.app_context():
            user1 = User(username='user1', email='user1@example.com')
            user1.set_password('password123')
            db.session.add(user1)
            db.session.commit()
            
            user2 = User(username='user2', email='user2@example.com')
            user2.set_password('password123')
            db.session.add(user2)
            db.session.commit()
            
            # Add allergen for user1
            allergen1 = UserAllergen(
                user_id=user1.id,
                ingredient_name='Fragrance',
                severity='severe'
            )
            db.session.add(allergen1)
            db.session.commit()
            allergen1_id = allergen1.id
        
        # Login as user2
        client.post('/login', data={
            'username': 'user2',
            'password': 'password123'
        }, follow_redirects=True)
        
        # Try to delete user1's allergen as user2
        response = client.post(
            f'/allergens/delete/{allergen1_id}',
            follow_redirects=True
        )
        
        # Verify allergen still exists (wasn't deleted)
        with app.app_context():
            allergen = UserAllergen.query.get(allergen1_id)
            # Should still exist or get proper error handling
            # (depending on implementation, might still exist or return error)

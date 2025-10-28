"""
Unit tests for User Registration (Use Case 1)
Tests corresponding to TC-REG-001, TC-REG-002, TC-REG-003
"""
import pytest
from app import User, db


class TestUserRegistration:
    """Test cases for user registration functionality"""
    
    def test_successful_registration(self, client, app):
        """
        TC-REG-001: Successful User Registration
        Verify that a user can successfully register with valid credentials
        """
        # Test inputs
        username = "testuser123"
        email = "testuser@example.com"
        password = "SecurePass123"
        
        # Perform registration
        response = client.post('/register', data={
            'username': username,
            'email': email,
            'password': password,
            'confirm_password': password
        }, follow_redirects=True)
        
        # Assert response
        assert response.status_code == 200
        assert b'Registration successful' in response.data or b'Please log in' in response.data
        
        # Verify user exists in database
        with app.app_context():
            user = User.query.filter_by(username=username).first()
            assert user is not None
            assert user.email == email
            assert user.username == username
            # Verify password is hashed (not stored as plaintext)
            assert user.password_hash != password
            assert len(user.password_hash) > 50  # Hashed passwords are long
    
    def test_registration_with_duplicate_username(self, client, app, test_user):
        """
        TC-REG-002: Registration with Duplicate Username
        Verify that registration fails when username already exists
        """
        # Test inputs - using existing username from test_user fixture
        username = "testuser"  # This already exists
        email = "newemail@example.com"
        password = "SecurePass123"
        
        # Get initial user count
        with app.app_context():
            initial_count = User.query.count()
        
        # Attempt registration with duplicate username
        response = client.post('/register', data={
            'username': username,
            'email': email,
            'password': password,
            'confirm_password': password
        }, follow_redirects=True)
        
        # Assert error message displayed
        assert b'Username already exists' in response.data
        
        # Verify no new user was created
        with app.app_context():
            final_count = User.query.count()
            assert final_count == initial_count
    
    def test_registration_with_duplicate_email(self, client, app, test_user):
        """
        TC-REG-002 (variant): Registration with Duplicate Email
        Verify that registration fails when email already exists
        """
        # Test inputs - using existing email from test_user fixture
        username = "newuser"
        email = "test@example.com"  # This already exists
        password = "SecurePass123"
        
        # Get initial user count
        with app.app_context():
            initial_count = User.query.count()
        
        # Attempt registration with duplicate email
        response = client.post('/register', data={
            'username': username,
            'email': email,
            'password': password,
            'confirm_password': password
        }, follow_redirects=True)
        
        # Assert error message displayed
        assert b'Email already registered' in response.data
        
        # Verify no new user was created
        with app.app_context():
            final_count = User.query.count()
            assert final_count == initial_count
    
    def test_registration_with_mismatched_passwords(self, client, app):
        """
        TC-REG-003: Registration with Mismatched Passwords
        Verify that registration fails when passwords don't match
        """
        # Test inputs
        username = "newuser"
        email = "newuser@example.com"
        password = "SecurePass123"
        confirm_password = "DifferentPass456"
        
        # Get initial user count
        with app.app_context():
            initial_count = User.query.count()
        
        # Attempt registration with mismatched passwords
        response = client.post('/register', data={
            'username': username,
            'email': email,
            'password': password,
            'confirm_password': confirm_password
        }, follow_redirects=True)
        
        # Assert error message displayed
        assert b'Passwords do not match' in response.data
        
        # Verify no new user was created
        with app.app_context():
            final_count = User.query.count()
            assert final_count == initial_count
    
    def test_registration_with_empty_username(self, client, app):
        """
        Test registration with empty username (boundary condition)
        """
        response = client.post('/register', data={
            'username': '',
            'email': 'test@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        
        assert b'All fields are required' in response.data
        
        with app.app_context():
            assert User.query.filter_by(email='test@example.com').first() is None
    
    def test_registration_with_empty_email(self, client, app):
        """
        Test registration with empty email (boundary condition)
        """
        response = client.post('/register', data={
            'username': 'testuser',
            'email': '',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        
        assert b'All fields are required' in response.data
        
        with app.app_context():
            assert User.query.filter_by(username='testuser').first() is None
    
    def test_registration_with_empty_password(self, client, app):
        """
        Test registration with empty password (boundary condition)
        """
        response = client.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': '',
            'confirm_password': ''
        }, follow_redirects=True)
        
        assert b'All fields are required' in response.data
        
        with app.app_context():
            assert User.query.filter_by(username='testuser').first() is None

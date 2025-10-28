"""
Unit tests for User Login/Authentication (Use Case 2)
Tests corresponding to TC-LOGIN-001, TC-LOGIN-002, TC-LOGIN-003
"""
import pytest
from flask_login import current_user


class TestUserLogin:
    """Test cases for user authentication and login functionality"""
    
    def test_successful_login(self, client, app, test_user):
        """
        TC-LOGIN-001: Successful Login
        Verify that a registered user can successfully log in with correct credentials
        """
        # Test inputs
        username = "testuser"
        password = "testpassword123"
        
        # Perform login
        response = client.post('/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)
        
        # Assert successful login
        assert response.status_code == 200
        # Should be redirected to dashboard
        assert b'dashboard' in response.data or b'Dashboard' in response.data
        
        # Verify session is active
        with client.session_transaction() as sess:
            assert '_user_id' in sess
    
    def test_login_with_incorrect_password(self, client, app, test_user):
        """
        TC-LOGIN-002: Login with Incorrect Password
        Verify that login fails with incorrect password
        """
        # Test inputs
        username = "testuser"
        password = "wrongpassword"
        
        # Attempt login with wrong password
        response = client.post('/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)
        
        # Assert login failed
        assert b'Invalid username or password' in response.data
        
        # Verify no session created
        with client.session_transaction() as sess:
            assert '_user_id' not in sess
    
    def test_login_with_nonexistent_user(self, client, app):
        """
        TC-LOGIN-003: Login with Non-existent User
        Verify that login fails for non-existent user
        """
        # Test inputs
        username = "nonexistentuser"
        password = "anypassword"
        
        # Attempt login with non-existent username
        response = client.post('/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)
        
        # Assert login failed
        assert b'Invalid username or password' in response.data
        
        # Verify no session created
        with client.session_transaction() as sess:
            assert '_user_id' not in sess
    
    def test_login_with_empty_username(self, client, app):
        """
        Test login with empty username (boundary condition)
        """
        response = client.post('/login', data={
            'username': '',
            'password': 'password123'
        }, follow_redirects=True)
        
        # Should fail - either show error or stay on login page
        with client.session_transaction() as sess:
            assert '_user_id' not in sess
    
    def test_login_with_empty_password(self, client, app, test_user):
        """
        Test login with empty password (boundary condition)
        """
        response = client.post('/login', data={
            'username': 'testuser',
            'password': ''
        }, follow_redirects=True)
        
        # Should fail
        with client.session_transaction() as sess:
            assert '_user_id' not in sess
    
    def test_logout(self, authenticated_client, app):
        """
        Test that logout properly clears the session
        """
        # Verify user is logged in first
        with authenticated_client.session_transaction() as sess:
            assert '_user_id' in sess
        
        # Perform logout
        response = authenticated_client.get('/logout', follow_redirects=True)
        
        assert response.status_code == 200
        assert b'logged out' in response.data
        
        # Verify session is cleared
        with authenticated_client.session_transaction() as sess:
            assert '_user_id' not in sess
    
    def test_login_redirect_to_dashboard(self, client, test_user):
        """
        Verify that successful login redirects to dashboard
        """
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'testpassword123'
        }, follow_redirects=False)
        
        # Should redirect to dashboard
        assert response.status_code == 302
        assert '/dashboard' in response.location or response.location.endswith('/')
    
    def test_login_protects_dashboard(self, client):
        """
        Verify that dashboard requires authentication
        """
        # Try to access dashboard without logging in
        response = client.get('/dashboard', follow_redirects=False)
        
        # Should redirect to login
        assert response.status_code == 302
        assert '/login' in response.location
    
    def test_authenticated_user_cannot_access_login(self, authenticated_client):
        """
        Verify that authenticated users are redirected from login page
        """
        response = authenticated_client.get('/login', follow_redirects=False)
        
        # Should redirect to dashboard (already logged in)
        assert response.status_code == 302
        assert '/dashboard' in response.location or response.location.endswith('/')
    
    def test_authenticated_user_cannot_access_register(self, authenticated_client):
        """
        Verify that authenticated users are redirected from register page
        """
        response = authenticated_client.get('/register', follow_redirects=False)
        
        # Should redirect to dashboard (already logged in)
        assert response.status_code == 302
        assert '/dashboard' in response.location or response.location.endswith('/')

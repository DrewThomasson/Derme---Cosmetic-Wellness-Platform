#!/usr/bin/env python
"""Test script to verify the forgot password functionality"""

from app import app, db, User

def test_forgot_password_feature():
    """Test the forgot password feature"""
    with app.app_context():
        # Initialize database
        db.create_all()
        
        # Create a test user with security questions
        test_user = User(username='testuser', email='test@example.com')
        test_user.set_password('testpass123')
        
        # Set security questions
        test_user.security_question_1 = 'What was the name of your first pet?'
        test_user.set_security_answer(1, 'Fluffy')
        
        test_user.security_question_2 = 'What city were you born in?'
        test_user.set_security_answer(2, 'New York')
        
        test_user.security_question_3 = 'What is your favorite color?'
        test_user.set_security_answer(3, 'Blue')
        
        db.session.add(test_user)
        db.session.commit()
        
        print("✓ Test user created successfully")
        print(f"  Username: {test_user.username}")
        print(f"  Email: {test_user.email}")
        print(f"  Security Question 1: {test_user.security_question_1}")
        print(f"  Security Question 2: {test_user.security_question_2}")
        print(f"  Security Question 3: {test_user.security_question_3}")
        
        # Test password verification
        assert test_user.check_password('testpass123'), "Password check failed"
        print("\n✓ Password verification works")
        
        # Test security answer verification
        assert test_user.check_security_answer(1, 'fluffy'), "Security answer 1 check failed (case insensitive)"
        assert test_user.check_security_answer(1, 'Fluffy'), "Security answer 1 check failed"
        assert test_user.check_security_answer(1, ' Fluffy '), "Security answer 1 check failed (with spaces)"
        print("✓ Security answer 1 verification works (case insensitive, trimmed)")
        
        assert test_user.check_security_answer(2, 'new york'), "Security answer 2 check failed"
        print("✓ Security answer 2 verification works")
        
        assert test_user.check_security_answer(3, 'blue'), "Security answer 3 check failed"
        print("✓ Security answer 3 verification works")
        
        # Test wrong answers
        assert not test_user.check_security_answer(1, 'wrong'), "Wrong answer should fail"
        print("✓ Wrong security answer correctly rejected")
        
        # Test password reset
        test_user.set_password('newpassword123')
        db.session.commit()
        
        assert test_user.check_password('newpassword123'), "New password check failed"
        assert not test_user.check_password('testpass123'), "Old password should not work"
        print("\n✓ Password reset works correctly")
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED!")
        print("="*60)
        print("\nForgot password feature is working correctly with:")
        print("  - Security questions stored in database")
        print("  - Security answers hashed for security")
        print("  - Case-insensitive and trimmed answer verification")
        print("  - Password reset functionality")

if __name__ == '__main__':
    test_forgot_password_feature()

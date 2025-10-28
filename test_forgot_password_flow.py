#!/usr/bin/env python
"""Test the complete forgot password flow"""

import requests
from bs4 import BeautifulSoup

BASE_URL = "http://localhost:7860"

def test_forgot_password_flow():
    # Create a session to maintain cookies
    session = requests.Session()
    
    print("="*60)
    print("TESTING FORGOT PASSWORD FLOW")
    print("="*60)
    
    # Step 1: Submit username/email
    print("\n1. Submitting username to forgot password page...")
    response = session.post(f"{BASE_URL}/forgot-password", data={
        "identifier": "testuser123"
    }, allow_redirects=False)
    
    if response.status_code == 302:
        print("   ✓ Redirected to security questions page")
        print(f"   Location: {response.headers.get('Location')}")
    else:
        print(f"   ✗ Unexpected status code: {response.status_code}")
        return
    
    # Step 2: Get security questions page
    print("\n2. Loading security questions page...")
    response = session.get(f"{BASE_URL}/verify-security-questions")
    
    if response.status_code == 200:
        print("   ✓ Security questions page loaded")
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract security questions
        labels = soup.find_all('label')
        questions = [label.get_text().strip() for label in labels if '?' in label.get_text()]
        print(f"   Found {len(questions)} security question(s):")
        for i, q in enumerate(questions, 1):
            print(f"     {i}. {q}")
    else:
        print(f"   ✗ Failed to load page: {response.status_code}")
        return
    
    # Step 3: Submit security answers
    print("\n3. Submitting security answers...")
    response = session.post(f"{BASE_URL}/verify-security-questions", data={
        "answer_1": "Fluffy",
        "answer_2": "Harry Potter",
        "answer_3": "Pizza"
    }, allow_redirects=False)
    
    if response.status_code == 302:
        print("   ✓ Security answers verified successfully")
        print(f"   Location: {response.headers.get('Location')}")
    else:
        print(f"   ✗ Unexpected status code: {response.status_code}")
        return
    
    # Step 4: Get password reset page
    print("\n4. Loading password reset page...")
    response = session.get(f"{BASE_URL}/reset-password")
    
    if response.status_code == 200:
        print("   ✓ Password reset page loaded")
    else:
        print(f"   ✗ Failed to load page: {response.status_code}")
        return
    
    # Step 5: Submit new password
    print("\n5. Submitting new password...")
    response = session.post(f"{BASE_URL}/reset-password", data={
        "new_password": "newpassword123",
        "confirm_password": "newpassword123"
    }, allow_redirects=False)
    
    if response.status_code == 302:
        print("   ✓ Password reset successfully")
        print(f"   Location: {response.headers.get('Location')}")
    else:
        print(f"   ✗ Unexpected status code: {response.status_code}")
        return
    
    # Step 6: Test login with new password
    print("\n6. Testing login with new password...")
    response = session.post(f"{BASE_URL}/login", data={
        "username": "testuser123",
        "password": "newpassword123"
    }, allow_redirects=False)
    
    if response.status_code == 302 and '/dashboard' in response.headers.get('Location', ''):
        print("   ✓ Successfully logged in with new password!")
    else:
        print(f"   ✗ Login failed: {response.status_code}")
        return
    
    print("\n" + "="*60)
    print("FORGOT PASSWORD FLOW TEST: PASSED ✓")
    print("="*60)
    print("\nAll steps completed successfully:")
    print("  1. ✓ User identified by username/email")
    print("  2. ✓ Security questions displayed")
    print("  3. ✓ Security answers verified")
    print("  4. ✓ New password set")
    print("  5. ✓ Login with new password successful")

if __name__ == '__main__':
    test_forgot_password_flow()

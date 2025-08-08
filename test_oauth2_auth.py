#!/usr/bin/env python3
"""
Test script to verify the new OAuth2 authentication works.
This simulates what FastAPI docs will do.
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_oauth2_login():
    """Test the OAuth2 token endpoint (what FastAPI docs uses)"""
    
    print("Testing OAuth2 Login (FastAPI Docs style)...")
    
    # This is how FastAPI docs sends the login request
    login_data = {
        "username": "test@example.com",  # Use email as username
        "password": "testpassword"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/token",
            data=login_data,  # OAuth2 uses form data, not JSON
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data["access_token"]
            print(f"✅ Login successful!")
            print(f"Access Token: {access_token[:50]}...")
            
            # Test using the token
            test_protected_endpoint(access_token)
            
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during login: {e}")

def test_protected_endpoint(token):
    """Test a protected endpoint with the token"""
    
    print(f"\nTesting protected endpoint...")
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test a protected endpoint (you can change this to any protected route)
        response = requests.get(f"{BASE_URL}/teachers/classrooms", headers=headers)
        
        if response.status_code == 200:
            print("✅ Protected endpoint access successful!")
        elif response.status_code == 401:
            print("❌ Unauthorized - token might be invalid")
        else:
            print(f"ℹ️  Endpoint returned: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing protected endpoint: {e}")

def test_regular_login():
    """Test the regular JSON login endpoint"""
    
    print("\nTesting Regular JSON Login...")
    
    login_data = {
        "email": "test@example.com",
        "password": "testpassword"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            token_data = response.json()
            print("✅ Regular login also works!")
        else:
            print(f"❌ Regular login failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error during regular login: {e}")

if __name__ == "__main__":
    print("FastAPI OAuth2 Authentication Test")
    print("=" * 40)
    print("Make sure your server is running on localhost:8000")
    print("And you have a user with email: test@example.com")
    print()
    
    test_oauth2_login()
    test_regular_login()
    
    print("\n" + "=" * 40)
    print("How to use in FastAPI Docs:")
    print("1. Go to http://localhost:8000/docs")
    print("2. Click the 'Authorize' button (🔒)")
    print("3. Enter your email in the 'username' field")
    print("4. Enter your password in the 'password' field")
    print("5. Click 'Authorize'")
    print("6. Now you can test protected endpoints!")

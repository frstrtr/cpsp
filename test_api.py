#!/usr/bin/env python3
"""
Simple test script for TRON USDT Payment Monitor API
"""

import requests
import json
import time
import sys

API_BASE = "http://localhost:5000"

def test_health():
    """Test health endpoint"""
    print("🏥 Testing health endpoint...")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health test failed: {e}")
        return False

def test_stats():
    """Test statistics endpoint"""
    print("\n📊 Testing statistics endpoint...")
    try:
        response = requests.get(f"{API_BASE}/stats", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Stats test failed: {e}")
        return False

def test_create_payment():
    """Test payment creation"""
    print("\n💰 Testing payment creation...")
    payment_data = {
        "wallet_address": "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
        "expected_amount_usdt": 12.34,
        "callback_url": "https://webhook.site/test-python-script",
        "order_id": f"PYTHON_TEST_{int(time.time())}"
    }
    
    try:
        response = requests.post(f"{API_BASE}/create_payment", 
                               json=payment_data, timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 201:
            return response.json().get('payment_id')
        return None
    except Exception as e:
        print(f"❌ Payment creation test failed: {e}")
        return None

def test_payment_status(payment_id):
    """Test payment status check"""
    print(f"\n🔍 Testing payment status for {payment_id}...")
    try:
        response = requests.get(f"{API_BASE}/payment_status/{payment_id}", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Payment status test failed: {e}")
        return False

def test_invalid_payment():
    """Test invalid payment data"""
    print("\n⚠️ Testing invalid payment creation...")
    invalid_data = {
        "wallet_address": "invalid_address",
        "expected_amount_usdt": 10.0,
        "callback_url": "invalid_url",
        "order_id": "INVALID_TEST"
    }
    
    try:
        response = requests.post(f"{API_BASE}/create_payment", 
                               json=invalid_data, timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 400
    except Exception as e:
        print(f"❌ Invalid payment test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 TRON USDT Payment Monitor API Tests")
    print("=" * 50)
    
    # Test health
    if not test_health():
        print("❌ Health test failed, exiting...")
        sys.exit(1)
    
    # Test stats
    if not test_stats():
        print("❌ Stats test failed")
    
    # Test payment creation
    payment_id = test_create_payment()
    if not payment_id:
        print("❌ Payment creation failed")
    else:
        print(f"✅ Payment created with ID: {payment_id}")
        
        # Test payment status
        if test_payment_status(payment_id):
            print("✅ Payment status check successful")
        else:
            print("❌ Payment status check failed")
    
    # Test invalid payment
    if test_invalid_payment():
        print("✅ Invalid payment validation working")
    else:
        print("❌ Invalid payment validation failed")
    
    print("\n" + "=" * 50)
    print("✅ API tests completed!")

if __name__ == "__main__":
    main()

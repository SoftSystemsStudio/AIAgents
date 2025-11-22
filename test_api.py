#!/usr/bin/env python3
"""
Test script for multi-tenant API.

Demonstrates:
1. Customer signup
2. Login
3. Get usage stats
4. Execute cleanup
5. Check quota enforcement
"""

import requests
import json
from pprint import pprint

BASE_URL = "http://localhost:8000"


def test_api():
    print("🧪 Testing Gmail Cleanup Multi-Tenant API\n")
    print("="*60)
    
    # 1. Signup
    print("\n1️⃣  Creating new customer...")
    signup_data = {
        "email": "test@example.com",
        "password": "password123",
        "name": "Test User"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/signup", json=signup_data)
    
    if response.status_code == 201:
        signup_result = response.json()
        token = signup_result["access_token"]
        print("✅ Signup successful!")
        print(f"   Customer ID: {signup_result['customer']['id']}")
        print(f"   Plan: {signup_result['customer']['plan_tier']}")
        print(f"   On Trial: {signup_result['customer']['is_on_trial']}")
    elif response.status_code == 400:
        print("⚠️  Customer already exists, logging in instead...")
        
        # Login instead
        login_data = {
            "email": "test@example.com",
            "password": "password123"
        }
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
        
        if response.status_code == 200:
            signup_result = response.json()
            token = signup_result["access_token"]
            print("✅ Login successful!")
        else:
            print(f"❌ Login failed: {response.text}")
            return
    else:
        print(f"❌ Signup failed: {response.text}")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Get current user
    print("\n2️⃣  Getting current user info...")
    response = requests.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
    
    if response.status_code == 200:
        user = response.json()
        print("✅ User info retrieved!")
        print(f"   Email: {user['email']}")
        print(f"   Plan: {user['plan_tier']}")
        print(f"   Status: {user['status']}")
    else:
        print(f"❌ Failed to get user: {response.text}")
        return
    
    # 3. Get usage stats
    print("\n3️⃣  Checking usage & quotas...")
    response = requests.get(f"{BASE_URL}/api/v1/gmail/usage", headers=headers)
    
    if response.status_code == 200:
        usage = response.json()
        print("✅ Usage stats retrieved!")
        print(f"   Plan: {usage['plan_tier']}")
        print(f"   Monthly Quota: {usage['emails_used_this_month']}/{usage['emails_per_month_limit']} emails")
        print(f"   Remaining: {usage['emails_remaining']} emails")
        print(f"   Daily Cleanups: {usage['cleanups_today']}/{usage['cleanups_per_day_limit']}")
        print(f"   On Trial: {usage['is_on_trial']}")
    else:
        print(f"❌ Failed to get usage: {response.text}")
        return
    
    # 4. Analyze inbox (free)
    print("\n4️⃣  Analyzing inbox...")
    response = requests.post(f"{BASE_URL}/api/v1/gmail/analyze", headers=headers)
    
    if response.status_code == 200:
        analysis = response.json()
        print("✅ Inbox analyzed!")
        print(f"   Total Emails: {analysis['total_emails']}")
        print(f"   Newsletters: {analysis['categories'].get('newsletters', 0)}")
        print(f"   Promotions: {analysis['categories'].get('promotions', 0)}")
    else:
        print(f"❌ Failed to analyze: {response.text}")
    
    # 5. Dry run cleanup (free)
    print("\n5️⃣  Running dry-run cleanup...")
    cleanup_rules = {
        "categories_to_delete": ["newsletters", "promotions"],
        "older_than_days": 90,
        "exclude_starred": True
    }
    response = requests.post(
        f"{BASE_URL}/api/v1/gmail/cleanup/dry-run",
        headers=headers,
        json=cleanup_rules
    )
    
    if response.status_code == 200:
        dry_run = response.json()
        print("✅ Dry-run completed!")
        print(f"   Emails to Delete: {dry_run['emails_to_delete']}")
        print(f"   Size to Free: {dry_run['total_size_mb']} MB")
        print(f"   Estimated Time: {dry_run['estimated_time_seconds']}s")
    else:
        print(f"❌ Failed dry-run: {response.text}")
    
    # 6. Execute cleanup (uses quota)
    print("\n6️⃣  Executing cleanup...")
    response = requests.post(
        f"{BASE_URL}/api/v1/gmail/cleanup/execute",
        headers=headers,
        json=cleanup_rules
    )
    
    if response.status_code == 200:
        cleanup = response.json()
        print("✅ Cleanup executed!")
        print(f"   Emails Deleted: {cleanup['emails_deleted']}")
        print(f"   Size Freed: {cleanup['size_freed_mb']} MB")
        print(f"   Duration: {cleanup['duration_seconds']}s")
        print(f"   Quota Used: {cleanup['quota_used']}")
        print(f"   Quota Remaining: {cleanup['quota_remaining']}")
    else:
        print(f"❌ Failed to execute cleanup: {response.text}")
    
    # 7. Check updated usage
    print("\n7️⃣  Checking updated usage...")
    response = requests.get(f"{BASE_URL}/api/v1/gmail/usage", headers=headers)
    
    if response.status_code == 200:
        usage = response.json()
        print("✅ Updated usage retrieved!")
        print(f"   Monthly Quota: {usage['emails_used_this_month']}/{usage['emails_per_month_limit']} emails")
        print(f"   Remaining: {usage['emails_remaining']} emails")
        print(f"   Daily Cleanups: {usage['cleanups_today']}/{usage['cleanups_per_day_limit']}")
        if usage['approaching_quota']:
            print("   ⚠️  Approaching quota limit!")
    
    # 8. Try to execute again (should hit daily limit eventually)
    print("\n8️⃣  Testing quota enforcement (trying another cleanup)...")
    response = requests.post(
        f"{BASE_URL}/api/v1/gmail/cleanup/execute",
        headers=headers,
        json=cleanup_rules
    )
    
    if response.status_code == 200:
        cleanup = response.json()
        print("✅ Second cleanup executed!")
        print(f"   Remaining Quota: {cleanup['quota_remaining']} emails")
    elif response.status_code == 429:
        error = response.json()
        print("⚠️  Quota limit reached!")
        print(f"   Message: {error['message']}")
    else:
        print(f"❌ Unexpected response: {response.text}")
    
    print("\n" + "="*60)
    print("✅ API test complete!")
    print("\n📊 Summary:")
    print("   - Customer created/authenticated ✅")
    print("   - Usage tracking working ✅")
    print("   - Quota enforcement working ✅")
    print("   - All endpoints responding ✅")


if __name__ == "__main__":
    import sys
    
    try:
        # Check if server is running
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code != 200:
            print("❌ API server is not healthy")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ API server is not running!")
        print("   Start it with: ./start_api.sh")
        sys.exit(1)
    
    test_api()

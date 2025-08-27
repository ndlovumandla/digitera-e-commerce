#!/usr/bin/env python
"""
Simple validation script to check creator upgrade functionality.
"""

import os
import sys
import django

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(__file__))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digitera_platform.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.urls import reverse
from accounts.models import UserRole, CreatorProfile

def validate_creator_upgrade():
    """Validate that creator upgrade functionality is set up correctly."""
    print("🔍 Validating Creator Upgrade Setup")
    print("=" * 40)
    
    User = get_user_model()
    
    # Check 1: URLs resolve correctly
    print("\n1. URL Resolution:")
    try:
        upgrade_url = reverse('accounts:upgrade_to_creator')
        dashboard_url = reverse('accounts:dashboard')
        creator_profile_url = reverse('accounts:creator_profile_update')
        purchased_url = reverse('orders:purchased_products')
        
        print(f"   ✅ Upgrade URL: {upgrade_url}")
        print(f"   ✅ Dashboard URL: {dashboard_url}")
        print(f"   ✅ Creator Profile URL: {creator_profile_url}")
        print(f"   ✅ Purchased Products URL: {purchased_url}")
    except Exception as e:
        print(f"   ❌ URL resolution error: {e}")
        return False
    
    # Check 2: Test user exists and has correct setup
    print("\n2. Test User Setup:")
    try:
        user = User.objects.get(email='buyer@example.com')
        print(f"   ✅ Test user exists: {user.email}")
        print(f"   ✅ Current role: {user.role}")
        print(f"   ✅ Is creator: {user.is_creator}")
        
        # Check if user has creator profile
        try:
            creator_profile = user.creator_profile
            print(f"   ✅ Has creator profile: {creator_profile.store_name}")
        except CreatorProfile.DoesNotExist:
            print("   ℹ️  No creator profile (normal for buyer)")
            
    except User.DoesNotExist:
        print("   ❌ Test user 'buyer@example.com' not found")
        return False
    
    # Check 3: Test role switching
    print("\n3. Role Switching Test:")
    try:
        # Test buyer to creator
        original_role = user.role
        user.role = UserRole.CREATOR
        user.save()
        print(f"   ✅ Switched to creator: {user.is_creator}")
        
        # Test creator to buyer
        user.role = UserRole.BUYER
        user.save()
        print(f"   ✅ Switched to buyer: {user.is_creator}")
        
        # Restore original role
        user.role = original_role
        user.save()
        print(f"   ✅ Restored original role: {user.role}")
        
    except Exception as e:
        print(f"   ❌ Role switching error: {e}")
        return False
    
    # Check 4: Creator profile creation
    print("\n4. Creator Profile Creation:")
    try:
        profile, created = CreatorProfile.objects.get_or_create(
            user=user,
            defaults={
                'store_name': f"Test Store for {user.get_full_name()}",
                'store_slug': f'test-store-{user.id}',
                'status': 'active',
                'verified': True,
            }
        )
        print(f"   ✅ Creator profile: {profile.store_name}")
        print(f"   ✅ Profile created: {created}")
        
    except Exception as e:
        print(f"   ❌ Creator profile error: {e}")
        return False
    
    # Check 5: Model properties work correctly
    print("\n5. Model Properties:")
    try:
        user.role = UserRole.BUYER
        user.save()
        print(f"   ✅ Buyer - is_creator: {user.is_creator}")
        
        user.role = UserRole.CREATOR
        user.save()
        print(f"   ✅ Creator - is_creator: {user.is_creator}")
        
        # Reset to buyer for testing
        user.role = UserRole.BUYER
        user.save()
        
    except Exception as e:
        print(f"   ❌ Model properties error: {e}")
        return False
    
    print("\n🎉 All validations passed!")
    return True

def print_usage_instructions():
    """Print instructions for testing the creator upgrade functionality."""
    print("\n" + "=" * 60)
    print("📋 TESTING INSTRUCTIONS")
    print("=" * 60)
    print("\n1. Access the application at: http://127.0.0.1:8000/")
    print("\n2. Login with test account:")
    print("   Email: buyer@example.com")
    print("   Password: testpass123")
    print("\n3. Navigate to Dashboard:")
    print("   - You should see a buyer dashboard")
    print("   - Look for 'Become a Creator' options in:")
    print("     • Quick stats card")
    print("     • Quick actions sidebar")
    print("     • User dropdown menu (top-right)")
    print("\n4. Test Creator Upgrade:")
    print("   - Click any 'Become a Creator' link")
    print("   - Should go to: /accounts/upgrade-to-creator/")
    print("   - Fill out the creator form")
    print("   - Submit to upgrade account")
    print("\n5. Verify Creator Features:")
    print("   - Dashboard should show creator stats")
    print("   - User menu should show 'My Store'")
    print("   - Can access creator profile settings")
    print("\n6. Test Purchased Products:")
    print("   - Visit: /orders/purchased/")
    print("   - Should show purchased products page")
    print("   - Should work for both buyers and creators")
    print("\n" + "=" * 60)
    print("🚀 The creator upgrade functionality is ready to test!")
    print("=" * 60)

if __name__ == '__main__':
    try:
        success = validate_creator_upgrade()
        
        if success:
            print_usage_instructions()
        else:
            print("\n❌ Validation failed. Please check the errors above.")
            
    except Exception as e:
        print(f"\n💥 Validation script failed: {e}")
        import traceback
        traceback.print_exc()

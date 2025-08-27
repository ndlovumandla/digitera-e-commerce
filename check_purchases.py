#!/usr/bin/env python
"""
Quick test to check if the sample buyer has purchased products.
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digitera_platform.settings')
django.setup()

from django.contrib.auth import get_user_model
from orders.models import Order, OrderItem

User = get_user_model()

def check_purchases():
    """Check if sample buyer has purchases."""
    
    try:
        buyer = User.objects.get(email='buyer@example.com')
        print(f"✅ Found buyer: {buyer.email}")
        print(f"   User role: {buyer.role}")
        print(f"   Is creator: {buyer.is_creator}")
        
        # Check orders
        orders = Order.objects.filter(buyer=buyer)
        print(f"\n📦 Total orders: {orders.count()}")
        
        completed_orders = orders.filter(status='completed')
        print(f"✅ Completed orders: {completed_orders.count()}")
        
        for order in completed_orders:
            print(f"\n🛍️ Order: {order.order_number}")
            print(f"   Status: {order.status}")
            print(f"   Payment Status: {order.payment_status}")
            print(f"   Total: R{order.total_amount}")
            
            items = order.items.all()
            print(f"   Items: {items.count()}")
            
            for item in items:
                print(f"     - {item.product_name}")
                print(f"       Access Granted: {item.access_granted}")
                print(f"       Fulfilled: {item.is_fulfilled}")
                print(f"       Downloads: {item.download_count}")
                
    except User.DoesNotExist:
        print("❌ Sample buyer not found!")
        print("   Run the enhanced sample data script first.")
        
    # Check all users
    print(f"\n👥 Total users: {User.objects.count()}")
    creators = User.objects.filter(role='creator')
    print(f"👨‍💼 Creators: {creators.count()}")
    
    if creators:
        print("   Creator accounts:")
        for creator in creators:
            profile = getattr(creator, 'creator_profile', None)
            if profile:
                print(f"     - {creator.email}: {profile.store_name}")
            else:
                print(f"     - {creator.email}: No creator profile!")


if __name__ == '__main__':
    check_purchases()

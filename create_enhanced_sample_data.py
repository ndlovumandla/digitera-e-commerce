#!/usr/bin/env python
"""
Enhanced sample data creation script for Digitera Platform.
Creates sample products with images, orders, and digital downloads.
"""

import os
import sys
import django
from decimal import Decimal
from django.utils import timezone

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digitera_platform.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import UserProfile, CreatorProfile, UserRole
from products.models import Product, DigitalDownload, Category, Tag
from orders.models import Order, OrderItem, Cart, CartItem

User = get_user_model()

def create_sample_data():
    """Create comprehensive sample data for testing."""
    
    print("🚀 Creating enhanced sample data for Digitera Platform...")
    
    # Create categories
    print("📂 Creating product categories...")
    categories = [
        {
            'name': 'Digital Art & Design', 
            'slug': 'digital-art-design',
            'description': 'Digital artwork, templates, and design resources',
            'image': 'https://images.unsplash.com/photo-1561070791-2526d30994b5?w=400'
        },
        {
            'name': 'Business Templates', 
            'slug': 'business-templates',
            'description': 'Professional business documents and templates',
            'image': 'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=400'
        },
        {
            'name': 'Educational Content', 
            'slug': 'educational-content',
            'description': 'Learning materials and educational resources',
            'image': 'https://images.unsplash.com/photo-1513475382585-d06e58bcb0e0?w=400'
        },
        {
            'name': 'Photography', 
            'slug': 'photography',
            'description': 'Stock photos and photography resources',
            'image': 'https://images.unsplash.com/photo-1452587925148-ce544e77e70d?w=400'
        },
        {
            'name': 'Software & Tools', 
            'slug': 'software-tools',
            'description': 'Applications, plugins, and digital tools',
            'image': 'https://images.unsplash.com/photo-1517077304055-6e89abbf09b0?w=400'
        }
    ]
    
    created_categories = []
    for cat_data in categories:
        category, created = Category.objects.get_or_create(
            slug=cat_data['slug'],
            defaults=cat_data
        )
        created_categories.append(category)
        if created:
            print(f"   ✅ Created category: {category.name}")
    
    # Create tags
    print("🏷️ Creating product tags...")
    tag_names = [
        'premium', 'bestseller', 'trending', 'new', 'south-african',
        'digital-download', 'template', 'creative', 'business', 'professional',
        'beginner-friendly', 'advanced', 'photoshop', 'canva', 'powerpoint'
    ]
    
    created_tags = []
    for tag_name in tag_names:
        try:
            tag, created = Tag.objects.get_or_create(
                name=tag_name,
                defaults={'slug': tag_name, 'color': '#3B82F6'}
            )
            created_tags.append(tag)
            if created:
                print(f"   ✅ Created tag: {tag.name}")
            else:
                print(f"   ♻️ Using existing tag: {tag.name}")
        except Exception as e:
            # Try to get existing tag by slug
            try:
                tag = Tag.objects.get(slug=tag_name)
                created_tags.append(tag)
                print(f"   ♻️ Using existing tag: {tag.name}")
            except Tag.DoesNotExist:
                print(f"   ❌ Could not create or find tag: {tag_name} - {e}")
                # Create a unique slug
                import time
                unique_slug = f"{tag_name}-{int(time.time())}"
                tag = Tag.objects.create(
                    name=tag_name,
                    slug=unique_slug,
                    color='#3B82F6'
                )
                created_tags.append(tag)
                print(f"   ✅ Created tag with unique slug: {tag.name}")
    
    # Create sample users
    print("👥 Creating sample users...")
    
    # Create buyer
    buyer_email = 'buyer@example.com'
    buyer, created = User.objects.get_or_create(
        email=buyer_email,
        defaults={
            'first_name': 'John',
            'last_name': 'Buyer',
            'role': UserRole.BUYER,
            'is_verified': True,
        }
    )
    if created:
        buyer.set_password('testpass123')
        buyer.save()
        UserProfile.objects.create(user=buyer)
        print(f"   ✅ Created buyer: {buyer.email}")
    
    # Create creators
    creators_data = [
        {
            'email': 'sarah@creativestudio.co.za',
            'first_name': 'Sarah',
            'last_name': 'Williams',
            'store_name': 'Creative Studio SA',
            'store_description': 'Premium digital design templates and graphics for South African businesses.',
            'business_category': 'art_design',
        },
        {
            'email': 'mike@bizpro.co.za',
            'first_name': 'Mike',
            'last_name': 'Johnson',
            'store_name': 'BizPro Templates',
            'store_description': 'Professional business templates and documents for entrepreneurs.',
            'business_category': 'business',
        },
        {
            'email': 'lisa@edutech.co.za',
            'first_name': 'Lisa',
            'last_name': 'van der Merwe',
            'store_name': 'EduTech Resources',
            'store_description': 'Educational content and learning materials for South African students.',
            'business_category': 'education',
        }
    ]
    
    created_creators = []
    for creator_data in creators_data:
        creator, created = User.objects.get_or_create(
            email=creator_data['email'],
            defaults={
                'first_name': creator_data['first_name'],
                'last_name': creator_data['last_name'],
                'role': UserRole.CREATOR,
                'is_verified': True,
            }
        )
        if created:
            creator.set_password('testpass123')
            creator.save()
            
            # Create user profile
            UserProfile.objects.create(user=creator)
            
            # Create creator profile
            CreatorProfile.objects.create(
                user=creator,
                store_name=creator_data['store_name'],
                store_slug=creator_data['store_name'].lower().replace(' ', '-'),
                store_description=creator_data['store_description'],
                business_category=creator_data['business_category'],
                status='active',
                verified=True,
                bank_name='fnb',
                account_holder=creator.get_full_name(),
                account_number='1234567890',
                branch_code='250655',
                account_type='business'
            )
            print(f"   ✅ Created creator: {creator.email} - {creator_data['store_name']}")
        
        created_creators.append(creator)
    
    # Create sample products with images
    print("🛍️ Creating sample products with images...")
    products_data = [
        {
            'creator': created_creators[0],  # Sarah
            'name': 'South African Business Card Templates',
            'description': 'A collection of 20 professional business card templates designed specifically for South African businesses. Includes Canva and Photoshop versions.',
            'short_description': 'Professional SA business card templates - 20 designs included',
            'price': Decimal('149.00'),
            'category': created_categories[1],  # Business Templates
            'featured_image': 'https://images.unsplash.com/photo-1590736969955-71cc94901144?w=600',
            'tags': ['business', 'template', 'south-african', 'canva'],
            'download_files': [
                'https://example.com/downloads/business-cards-canva.zip',
                'https://example.com/downloads/business-cards-psd.zip',
                'https://example.com/downloads/business-cards-guide.pdf'
            ]
        },
        {
            'creator': created_creators[0],  # Sarah
            'name': 'Instagram Story Templates - SA Edition',
            'description': 'Vibrant Instagram story templates featuring South African themes, landscapes, and cultural elements. Perfect for local businesses and influencers.',
            'short_description': 'Stunning SA-themed Instagram story templates',
            'price': Decimal('89.00'),
            'category': created_categories[0],  # Digital Art & Design
            'featured_image': 'https://images.unsplash.com/photo-1611224923853-80b023f02d71?w=600',
            'tags': ['social-media', 'instagram', 'south-african', 'templates'],
            'download_files': [
                'https://example.com/downloads/ig-stories-templates.zip',
                'https://example.com/downloads/ig-stories-fonts.zip'
            ]
        },
        {
            'creator': created_creators[1],  # Mike
            'name': 'Complete Business Plan Template (SA)',
            'description': 'Comprehensive business plan template compliant with South African business requirements. Includes financial projections, market analysis, and CIPC registration guide.',
            'short_description': 'SA-compliant business plan template with financial projections',
            'price': Decimal('299.00'),
            'category': created_categories[1],  # Business Templates
            'featured_image': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=600',
            'tags': ['business-plan', 'south-african', 'template', 'professional'],
            'download_files': [
                'https://example.com/downloads/business-plan-template.docx',
                'https://example.com/downloads/financial-projections.xlsx',
                'https://example.com/downloads/cipc-guide.pdf'
            ]
        },
        {
            'creator': created_creators[1],  # Mike
            'name': 'Invoice Templates for SA Businesses',
            'description': 'Professional invoice templates compliant with SARS requirements. Includes VAT calculations and multiple currency support.',
            'short_description': 'SARS-compliant invoice templates with VAT calculations',
            'price': Decimal('79.00'),
            'category': created_categories[1],  # Business Templates
            'featured_image': 'https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?w=600',
            'tags': ['invoice', 'vat', 'sars', 'business', 'template'],
            'download_files': [
                'https://example.com/downloads/invoice-templates.zip',
                'https://example.com/downloads/vat-calculator.xlsx'
            ]
        },
        {
            'creator': created_creators[2],  # Lisa
            'name': 'Grade 12 Mathematics Study Guide',
            'description': 'Comprehensive mathematics study guide for Grade 12 learners following the South African curriculum. Includes practice tests and solutions.',
            'short_description': 'Complete Grade 12 maths study guide with practice tests',
            'price': Decimal('199.00'),
            'category': created_categories[2],  # Educational Content
            'featured_image': 'https://images.unsplash.com/photo-1635070041078-e363dbe005cb?w=600',
            'tags': ['education', 'mathematics', 'grade-12', 'south-african'],
            'download_files': [
                'https://example.com/downloads/maths-study-guide.pdf',
                'https://example.com/downloads/practice-tests.pdf',
                'https://example.com/downloads/solutions.pdf'
            ]
        },
        {
            'creator': created_creators[2],  # Lisa
            'name': 'Afrikaans Language Learning Pack',
            'description': 'Interactive Afrikaans language learning materials for beginners. Includes audio files, vocabulary lists, and practice exercises.',
            'short_description': 'Beginner-friendly Afrikaans learning pack with audio',
            'price': Decimal('159.00'),
            'category': created_categories[2],  # Educational Content
            'featured_image': 'https://images.unsplash.com/photo-1577563908411-5077b6dc7624?w=600',
            'tags': ['afrikaans', 'language-learning', 'audio', 'beginner-friendly'],
            'download_files': [
                'https://example.com/downloads/afrikaans-lessons.pdf',
                'https://example.com/downloads/audio-files.zip',
                'https://example.com/downloads/vocabulary.pdf'
            ]
        },
    ]
    
    created_products = []
    for product_data in products_data:
        # Create digital download
        download_product = DigitalDownload.objects.create(
            creator=product_data['creator'],
            name=product_data['name'],
            slug=product_data['name'].lower().replace(' ', '-').replace('(', '').replace(')', ''),
            description=product_data['description'],
            short_description=product_data['short_description'],
            price=product_data['price'],
            category=product_data['category'],
            featured_image=product_data['featured_image'],
            status='published',
            visibility='public',
            product_type='digital_download',
            vat_inclusive=True,
            is_digital=True,
            delivery_method='instant',
            download_files=product_data['download_files'],
            license_type='Standard License',
            license_terms='Standard commercial use license. No redistribution allowed.',
            secure_delivery=True
        )
        
        # Add tags
        for tag_name in product_data['tags']:
            try:
                tag, _ = Tag.objects.get_or_create(
                    name=tag_name,
                    defaults={'slug': tag_name, 'color': '#3B82F6'}
                )
                download_product.tags.add(tag)
            except Exception:
                # Try to find existing tag
                try:
                    tag = Tag.objects.filter(name=tag_name).first()
                    if tag:
                        download_product.tags.add(tag)
                except Exception:
                    pass  # Skip this tag if it can't be created or found
        
        created_products.append(download_product)
        print(f"   ✅ Created product: {download_product.name} by {download_product.creator.get_full_name()}")
    
    # Create sample orders for the buyer
    print("🛒 Creating sample orders...")
    
    # Create a completed order
    order = Order.objects.create(
        buyer=buyer,
        order_number=f"DIG{timezone.now().strftime('%Y%m%d')}001",
        billing_name=buyer.get_full_name(),
        billing_email=buyer.email,
        status='completed',
        payment_status='captured',
        subtotal=Decimal('238.00'),
        total_amount=Decimal('238.00'),
        paid_at=timezone.now(),
        completed_at=timezone.now()
    )
    
    # Add order items
    OrderItem.objects.create(
        order=order,
        product=created_products[0],  # Business Card Templates
        product_name=created_products[0].name,
        quantity=1,
        unit_price=created_products[0].price,
        total_price=created_products[0].price,
        access_granted=True,
        is_fulfilled=True,
        fulfilled_at=timezone.now(),
        download_count=3
    )
    
    OrderItem.objects.create(
        order=order,
        product=created_products[1],  # Instagram Templates
        product_name=created_products[1].name,
        quantity=1,
        unit_price=created_products[1].price,
        total_price=created_products[1].price,
        access_granted=True,
        is_fulfilled=True,
        fulfilled_at=timezone.now(),
        download_count=1
    )
    
    print(f"   ✅ Created completed order: {order.order_number}")
    
    # Create a pending order
    pending_order = Order.objects.create(
        buyer=buyer,
        order_number=f"DIG{timezone.now().strftime('%Y%m%d')}002",
        billing_name=buyer.get_full_name(),
        billing_email=buyer.email,
        status='pending',
        payment_status='pending',
        subtotal=Decimal('299.00'),
        total_amount=Decimal('299.00')
    )
    
    OrderItem.objects.create(
        order=pending_order,
        product=created_products[2],  # Business Plan Template
        product_name=created_products[2].name,
        quantity=1,
        unit_price=created_products[2].price,
        total_price=created_products[2].price,
        access_granted=False,
        is_fulfilled=False
    )
    
    print(f"   ✅ Created pending order: {pending_order.order_number}")
    
    # Update product statistics
    print("📊 Updating product statistics...")
    for product in created_products:
        product.view_count = 50 + (hash(product.name) % 200)  # Random views
        product.purchase_count = 5 + (hash(product.name) % 15)  # Random purchases
        product.rating_average = Decimal('4.2') + (Decimal(str(hash(product.name) % 8)) / 10)
        product.rating_count = 8 + (hash(product.name) % 20)
        product.save()
    
    print("\n🎉 Enhanced sample data creation completed successfully!")
    print("\n📋 Summary:")
    print(f"   • Categories: {len(created_categories)}")
    print(f"   • Tags: {len(created_tags)}")
    print(f"   • Users: {len(created_creators) + 1} (including 1 buyer)")
    print(f"   • Products: {len(created_products)}")
    print(f"   • Orders: 2 (1 completed, 1 pending)")
    print("\n🔐 Login Credentials:")
    print(f"   Buyer: {buyer.email} / testpass123")
    for creator in created_creators:
        creator_profile = creator.creator_profile
        print(f"   Creator: {creator.email} / testpass123 ({creator_profile.store_name})")
    
    print("\n✨ You can now:")
    print("   • Login as a buyer to see purchased products")
    print("   • Login as a creator to manage products")
    print("   • Test the upgrade to creator functionality")
    print("   • Download sample products")
    print("   • Browse the marketplace with real data")


if __name__ == '__main__':
    create_sample_data()

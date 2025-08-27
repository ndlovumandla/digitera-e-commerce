#!/usr/bin/env python
"""
Simple script to add sample data through Django shell
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'digitera_platform.settings')
django.setup()

from django.contrib.auth import get_user_model
from products.models import Category, Tag, Product
from accounts.models import UserProfile, CreatorProfile
from decimal import Decimal

User = get_user_model()

def create_sample_data():
    print("Creating sample categories...")
    
    # Create categories
    categories_data = [
        {'name': 'Digital Downloads', 'slug': 'digital-downloads', 'description': 'Templates, graphics, and digital files'},
        {'name': 'Online Courses', 'slug': 'online-courses', 'description': 'Educational content and training'},
        {'name': 'Ebooks & Guides', 'slug': 'ebooks-guides', 'description': 'Written content and how-to guides'},
        {'name': 'Software & Tools', 'slug': 'software-tools', 'description': 'Applications and digital tools'},
        {'name': 'Music & Audio', 'slug': 'music-audio', 'description': 'Audio files, music, and sound effects'},
        {'name': 'Photography', 'slug': 'photography', 'description': 'Stock photos and image collections'},
    ]
    
    categories = []
    for cat_data in categories_data:
        category, created = Category.objects.get_or_create(
            slug=cat_data['slug'],
            defaults={
                'name': cat_data['name'],
                'description': cat_data['description'],
                'is_active': True,
                'sort_order': len(categories)
            }
        )
        categories.append(category)
        if created:
            print(f"Created category: {category.name}")
    
    # Create tags
    tag_names = [
        'Design', 'Business', 'Marketing', 'Photography', 'Education',
        'Technology', 'Health', 'Finance', 'Creative', 'Productivity',
        'South Africa', 'Afrikaans', 'isiZulu', 'Beginner', 'Advanced'
    ]
    
    tags = []
    for tag_name in tag_names:
        tag, created = Tag.objects.get_or_create(
            slug=tag_name.lower().replace(' ', '-'),
            defaults={'name': tag_name}
        )
        tags.append(tag)
        if created:
            print(f"Created tag: {tag.name}")
    
    # Create sample creators
    creators_data = [
        {
            'email': 'thabo@example.com',
            'first_name': 'Thabo',
            'last_name': 'Mthembu',
            'store_name': 'Thabo Design Studio',
            'store_description': 'Graphic designer from Johannesburg specializing in branding and digital art.'
        },
        {
            'email': 'sarah@example.com',
            'first_name': 'Sarah',
            'last_name': 'van der Merwe',
            'store_name': 'Cape Learning Hub',
            'store_description': 'Educational content creator and online course instructor from Cape Town.'
        },
        {
            'email': 'amahle@example.com',
            'first_name': 'Amahle',
            'last_name': 'Ndlovu',
            'store_name': 'Code Mastery KZN',
            'store_description': 'Software developer and coding instructor from Durban.'
        }
    ]
    
    creators = []
    for creator_data in creators_data:
        creator, created = User.objects.get_or_create(
            email=creator_data['email'],
            defaults={
                'first_name': creator_data['first_name'],
                'last_name': creator_data['last_name'],
                'role': 'creator',
                'is_active': True
            }
        )
        if created:
            creator.set_password('Demo123!')
            creator.save()
            print(f"Created user: {creator.get_full_name()}")
            
            # Create user profile
            profile, _ = UserProfile.objects.get_or_create(
                user=creator,
                defaults={
                    'city': 'Cape Town',
                    'province': 'WC',
                    'country': 'South Africa'
                }
            )
            
            # Create creator profile
            creator_profile, _ = CreatorProfile.objects.get_or_create(
                user=creator,
                defaults={
                    'store_name': creator_data['store_name'],
                    'store_slug': creator_data['store_name'].lower().replace(' ', '-'),
                    'store_description': creator_data['store_description'],
                    'status': 'active',
                }
            )
        
        creators.append(creator)
    
    # Create sample products
    products_data = [
        {
            'name': 'South African Business Card Templates',
            'description': 'Professional business card templates designed for South African businesses. Includes 20 unique designs with local themes and contact formats.',
            'short_description': 'Professional SA business card templates with local themes.',
            'price': Decimal('149.00'),
            'category': 'digital-downloads',
        },
        {
            'name': 'Digital Marketing for SA Small Business',
            'description': 'Complete course on digital marketing strategies specifically for South African small businesses. Covers local SEO, social media, and online advertising.',
            'short_description': 'Digital marketing course tailored for SA small businesses.',
            'price': Decimal('1299.00'),
            'category': 'online-courses',
        },
        {
            'name': 'Starting a Business in South Africa 2024',
            'description': 'Comprehensive guide to starting a business in South Africa. Covers legal requirements, tax obligations, and practical tips for entrepreneurs.',
            'short_description': 'Complete guide to starting a business in SA.',
            'price': Decimal('249.00'),
            'category': 'ebooks-guides',
        },
        {
            'name': 'Cape Town Stock Photo Collection',
            'description': '100 high-resolution stock photos of Cape Town landmarks, Table Mountain, and city scenes. Commercial use included.',
            'short_description': 'High-res Cape Town stock photos for commercial use.',
            'price': Decimal('499.00'),
            'category': 'photography',
        },
        {
            'name': 'Amapiano Loops & Samples Pack',
            'description': 'High-quality Amapiano loops and samples recorded by professional South African producers. Perfect for music production.',
            'short_description': 'Professional Amapiano loops and samples for producers.',
            'price': Decimal('399.00'),
            'category': 'music-audio',
        }
    ]
    
    for i, product_data in enumerate(products_data):
        creator = creators[i % len(creators)]
        category = next(cat for cat in categories if cat.slug == product_data['category'])
        
        product, created = Product.objects.get_or_create(
            name=product_data['name'],
            creator=creator,
            defaults={
                'description': product_data['description'],
                'short_description': product_data['short_description'],
                'price': product_data['price'],
                'category': category,
                'status': 'published',
                'visibility': 'public',
                'is_featured': i % 2 == 0,  # Make every other product featured
            }
        )
        
        if created:
            # Add some tags
            product_tags = tags[:3]  # Add first 3 tags to each product
            product.tags.set(product_tags)
            print(f"Created product: {product.name}")
    
    print("Sample data created successfully!")

if __name__ == '__main__':
    create_sample_data()

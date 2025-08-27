"""
Management command to create sample data for the marketplace.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decimal import Decimal
import random

from products.models import Category, Tag, Product, DigitalDownload, Course, Event
from accounts.models import UserProfile, CreatorProfile

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates sample data for the marketplace'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before creating new data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Product.objects.all().delete()
            Category.objects.all().delete()
            Tag.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()

        self.stdout.write('Creating sample data...')
        
        # Create categories
        categories = self.create_categories()
        
        # Create tags
        tags = self.create_tags()
        
        # Create sample creators
        creators = self.create_creators()
        
        # Create sample products
        self.create_products(categories, tags, creators)
        
        self.stdout.write(
            self.style.SUCCESS('Successfully created sample data!')
        )

    def create_categories(self):
        """Create sample categories."""
        categories_data = [
            {'name': 'Digital Downloads', 'slug': 'digital-downloads', 'description': 'Templates, graphics, and digital files'},
            {'name': 'Online Courses', 'slug': 'online-courses', 'description': 'Educational content and training'},
            {'name': 'Ebooks & Guides', 'slug': 'ebooks-guides', 'description': 'Written content and how-to guides'},
            {'name': 'Software & Tools', 'slug': 'software-tools', 'description': 'Applications and digital tools'},
            {'name': 'Music & Audio', 'slug': 'music-audio', 'description': 'Audio files, music, and sound effects'},
            {'name': 'Photography', 'slug': 'photography', 'description': 'Stock photos and image collections'},
            {'name': 'Business Templates', 'slug': 'business-templates', 'description': 'Templates for business use'},
            {'name': 'Events & Workshops', 'slug': 'events-workshops', 'description': 'Live events and workshops'},
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
                self.stdout.write(f'Created category: {category.name}')
        
        return categories

    def create_tags(self):
        """Create sample tags."""
        tag_names = [
            'Design', 'Business', 'Marketing', 'Photography', 'Education',
            'Technology', 'Health', 'Finance', 'Creative', 'Productivity',
            'Social Media', 'Web Development', 'Mobile App', 'Data Science',
            'Artificial Intelligence', 'South Africa', 'Afrikaans', 'isiZulu',
            'Beginner', 'Advanced', 'Professional', 'Personal Development',
            'Entrepreneurship', 'Small Business', 'Freelancing', 'Digital Marketing'
        ]
        
        tags = []
        for tag_name in tag_names:
            tag, created = Tag.objects.get_or_create(
                name=tag_name,
                defaults={'slug': tag_name.lower().replace(' ', '-')}
            )
            tags.append(tag)
            if created:
                self.stdout.write(f'Created tag: {tag.name}')
        
        return tags

    def create_creators(self):
        """Create sample creator accounts."""
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
            },
            {
                'email': 'pieter@example.com',
                'first_name': 'Pieter',
                'last_name': 'Botha',
                'store_name': 'Wild SA Photography',
                'store_description': 'Wildlife and landscape photographer specializing in South African scenes.'
            },
            {
                'email': 'nomsa@example.com',
                'first_name': 'Nomsa',
                'last_name': 'Zulu',
                'store_name': 'Business Growth SA',
                'store_description': 'Business consultant and entrepreneur helping SA SMEs grow.'
            }
        ]
        
        creators = []
        for creator_data in creators_data:
            user, created = User.objects.get_or_create(
                email=creator_data['email'],
                defaults={
                    'first_name': creator_data['first_name'],
                    'last_name': creator_data['last_name'],
                    'role': 'creator',
                    'is_active': True
                }
            )
            
            if created:
                user.set_password('Demo123!')
                user.save()
                
                # Create user profile
                profile, _ = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'city': random.choice(['Johannesburg', 'Cape Town', 'Durban', 'Pretoria', 'Port Elizabeth']),
                        'province': random.choice(['GP', 'WC', 'KZN', 'EC']),
                        'country': 'South Africa'
                    }
                )
                
                # Create creator profile
                creator_profile, _ = CreatorProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'store_name': creator_data['store_name'],
                        'store_slug': creator_data['store_name'].lower().replace(' ', '-'),
                        'store_description': creator_data['store_description'],
                        'status': 'active',
                    }
                )
                
                self.stdout.write(f'Created creator: {user.get_full_name()}')
            
            creators.append(user)
        
        return creators

    def create_products(self, categories, tags, creators):
        """Create sample products."""
        products_data = [
            # Digital Downloads
            {
                'name': 'South African Business Card Templates',
                'description': 'Professional business card templates designed for South African businesses. Includes 20 unique designs with local themes and contact formats.',
                'short_description': 'Professional SA business card templates with local themes.',
                'price': Decimal('149.00'),
                'category': 'digital-downloads',
                'product_type': 'digital_download',
                'tags': ['Design', 'Business', 'South Africa', 'Professional']
            },
            {
                'name': 'Heritage Day Marketing Kit',
                'description': 'Complete marketing kit for Heritage Day celebrations. Includes social media templates, poster designs, and promotional materials.',
                'short_description': 'Complete Heritage Day marketing templates and designs.',
                'price': Decimal('299.00'),
                'category': 'digital-downloads',
                'product_type': 'digital_download',
                'tags': ['Marketing', 'Design', 'South Africa', 'Social Media']
            },
            {
                'name': 'Ubuntu Philosophy Presentation Template',
                'description': 'Beautiful presentation templates incorporating Ubuntu philosophy and African design elements. Perfect for corporate and educational use.',
                'short_description': 'Ubuntu-inspired presentation templates with African design.',
                'price': Decimal('199.00'),
                'category': 'business-templates',
                'product_type': 'digital_download',
                'tags': ['Business', 'Design', 'South Africa', 'Professional']
            },
            
            # Courses
            {
                'name': 'Digital Marketing for SA Small Business',
                'description': 'Complete course on digital marketing strategies specifically for South African small businesses. Covers local SEO, social media, and online advertising.',
                'short_description': 'Digital marketing course tailored for SA small businesses.',
                'price': Decimal('1299.00'),
                'category': 'online-courses',
                'product_type': 'course',
                'tags': ['Digital Marketing', 'Small Business', 'South Africa', 'Education']
            },
            {
                'name': 'Python Programming in Afrikaans',
                'description': 'Learn Python programming with explanations in Afrikaans. Perfect for Afrikaans-speaking developers starting their coding journey.',
                'short_description': 'Python programming course taught in Afrikaans.',
                'price': Decimal('899.00'),
                'category': 'online-courses',
                'product_type': 'course',
                'tags': ['Technology', 'Programming', 'Afrikaans', 'Education', 'Beginner']
            },
            {
                'name': 'Photography of South African Wildlife',
                'description': 'Master wildlife photography techniques with focus on South African animals and landscapes. Includes location guides and equipment recommendations.',
                'short_description': 'Wildlife photography course for SA animals and landscapes.',
                'price': Decimal('1599.00'),
                'category': 'online-courses',
                'product_type': 'course',
                'tags': ['Photography', 'South Africa', 'Education', 'Advanced']
            },
            
            # Ebooks
            {
                'name': 'Starting a Business in South Africa 2024',
                'description': 'Comprehensive guide to starting a business in South Africa. Covers legal requirements, tax obligations, and practical tips for entrepreneurs.',
                'short_description': 'Complete guide to starting a business in SA.',
                'price': Decimal('249.00'),
                'category': 'ebooks-guides',
                'product_type': 'digital_download',
                'tags': ['Business', 'Entrepreneurship', 'South Africa', 'Legal']
            },
            {
                'name': 'Township Tourism: A Guide for Entrepreneurs',
                'description': 'How to start and run a successful township tourism business. Includes case studies, marketing strategies, and community engagement tips.',
                'short_description': 'Guide to starting township tourism businesses.',
                'price': Decimal('199.00'),
                'category': 'ebooks-guides',
                'product_type': 'digital_download',
                'tags': ['Tourism', 'Entrepreneurship', 'South Africa', 'Small Business']
            },
            
            # Music & Audio
            {
                'name': 'Amapiano Loops & Samples Pack',
                'description': 'High-quality Amapiano loops and samples recorded by professional South African producers. Perfect for music production.',
                'short_description': 'Professional Amapiano loops and samples for producers.',
                'price': Decimal('399.00'),
                'category': 'music-audio',
                'product_type': 'digital_download',
                'tags': ['Music', 'South Africa', 'Amapiano', 'Creative']
            },
            {
                'name': 'Traditional African Drums Sample Library',
                'description': 'Authentic African drum samples recorded live. Includes djembe, talking drums, and other traditional percussion instruments.',
                'short_description': 'Authentic African drum samples and loops.',
                'price': Decimal('299.00'),
                'category': 'music-audio',
                'product_type': 'digital_download',
                'tags': ['Music', 'South Africa', 'Traditional', 'Creative']
            },
            
            # Photography
            {
                'name': 'Cape Town Stock Photo Collection',
                'description': '100 high-resolution stock photos of Cape Town landmarks, Table Mountain, and city scenes. Commercial use included.',
                'short_description': 'High-res Cape Town stock photos for commercial use.',
                'price': Decimal('499.00'),
                'category': 'photography',
                'product_type': 'digital_download',
                'tags': ['Photography', 'Cape Town', 'South Africa', 'Stock Photos']
            },
            {
                'name': 'Kruger National Park Wildlife Photos',
                'description': 'Stunning wildlife photography from Kruger National Park. Features the Big 5 and other African animals in their natural habitat.',
                'short_description': 'Professional Kruger Park wildlife photography collection.',
                'price': Decimal('699.00'),
                'category': 'photography',
                'product_type': 'digital_download',
                'tags': ['Photography', 'Wildlife', 'South Africa', 'Nature']
            },
            
            # Events
            {
                'name': 'Digital Transformation Workshop',
                'description': 'Live online workshop on digital transformation for South African businesses. Learn practical strategies and tools.',
                'short_description': 'Live workshop on digital transformation for SA businesses.',
                'price': Decimal('799.00'),
                'category': 'events-workshops',
                'product_type': 'event',
                'tags': ['Business', 'Technology', 'Digital Transformation', 'Education']
            },
            {
                'name': 'African Design Thinking Masterclass',
                'description': 'Interactive masterclass on applying African design principles to modern UX/UI design. Includes hands-on exercises.',
                'short_description': 'Masterclass on African-inspired design thinking.',
                'price': Decimal('999.00'),
                'category': 'events-workshops',
                'product_type': 'event',
                'tags': ['Design', 'UX/UI', 'South Africa', 'Creative', 'Education']
            }
        ]
        
        for i, product_data in enumerate(products_data):
            creator = creators[i % len(creators)]
            category = next(cat for cat in categories if cat.slug == product_data['category'])
            
            # Create base product
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                creator=creator,
                defaults={
                    'description': product_data['description'],
                    'short_description': product_data['short_description'],
                    'price': product_data['price'],
                    'category': category,
                    'product_type': product_data['product_type'],
                    'status': 'published',
                    'visibility': 'public',
                    'is_featured': random.choice([True, False]),
                    'recommendation_score': random.uniform(0.1, 1.0)
                }
            )
            
            if created:
                # Add tags
                product_tags = [tag for tag in tags if tag.name in product_data['tags']]
                product.tags.set(product_tags)
                
                # Create specific product type instance
                if product_data['product_type'] == 'digital_download':
                    DigitalDownload.objects.get_or_create(
                        product_ptr=product,
                        defaults={
                            'file_size_mb': random.uniform(1.0, 100.0),
                            'download_limit': random.choice([None, 3, 5, 10]),
                            'expiry_days': random.choice([None, 30, 90, 365])
                        }
                    )
                elif product_data['product_type'] == 'course':
                    Course.objects.get_or_create(
                        product_ptr=product,
                        defaults={
                            'duration_hours': random.uniform(2.0, 20.0),
                            'skill_level': random.choice(['beginner', 'intermediate', 'advanced']),
                            'is_certification_provided': random.choice([True, False]),
                            'language': random.choice(['en', 'af', 'zu'])
                        }
                    )
                elif product_data['product_type'] == 'event':
                    Event.objects.get_or_create(
                        product_ptr=product,
                        defaults={
                            'event_type': random.choice(['webinar', 'workshop', 'conference']),
                            'is_live': True,
                            'max_attendees': random.choice([None, 50, 100, 200]),
                            'timezone': 'Africa/Johannesburg'
                        }
                    )
                
                self.stdout.write(f'Created product: {product.name}')
        
        self.stdout.write(f'Created {len(products_data)} sample products')

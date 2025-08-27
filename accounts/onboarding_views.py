"""
Creator onboarding views for the multi-step wizard.
Handles the complete creator signup and onboarding flow.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.generic import View, TemplateView
from django.utils.text import slugify
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import transaction
import json
import uuid

from .forms import DigiteraUserCreationForm
from .onboarding_forms import (
    CreatorProfileStepForm, 
    StorefrontCreationStepForm, 
    FirstProductStepForm,
    OnboardingPreferencesForm
)
from .models import User, UserProfile, CreatorProfile
from products.models import Product, DigitalDownload, Course, Membership, Event, Community
from storefronts.models import Storefront, StorefrontTheme


class CreatorSignupView(View):
    """Creator signup page with enhanced UX."""
    
    template_name = 'accounts/creator_signup.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            if request.user.is_creator:
                return redirect('accounts:onboarding_dashboard')
            else:
                messages.info(request, 'You already have a buyer account. You can upgrade to creator from your profile.')
                return redirect('accounts:creator_profile_update')
        
        form = DigiteraUserCreationForm()
        context = {
            'form': form,
            'page_title': 'Join Digitera as a Creator',
            'benefits': [
                'Zero setup costs - start selling immediately',
                'Built-in payment processing with local SA gateways',
                'Automatic VAT compliance and invoice generation',
                'AI-powered product discovery and recommendations',
                'Customizable storefront with your branding',
                'Community building and engagement tools',
                'Comprehensive analytics and insights',
                'Affiliate program management',
                'Mobile-optimized checkout experience',
                'Dedicated South African support team'
            ]
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        form = DigiteraUserCreationForm(request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create user with creator role
                    user = form.save(commit=False)
                    user.role = 'creator'
                    user.save()
                    
                    # Create user profile
                    profile = UserProfile.objects.create(user=user)
                    
                    # Create creator profile with basic info
                    creator_profile = CreatorProfile.objects.create(
                        user=user,
                        store_name=f"{user.get_full_name()}'s Store",
                        store_slug=self.generate_unique_slug(user.get_full_name()),
                        status='pending'
                    )
                    
                    # Log in the user
                    username = form.cleaned_data.get('email')
                    password = form.cleaned_data.get('password1')
                    user = authenticate(username=username, password=password)
                    if user:
                        login(request, user)
                        
                        # Store onboarding session data
                        request.session['onboarding_step'] = 1
                        request.session['onboarding_user_id'] = str(user.id)
                        
                        messages.success(request, f'Welcome to Digitera, {user.first_name}! Let\'s set up your creator profile.')
                        return redirect('accounts:onboarding_step_1')
            
            except Exception as e:
                messages.error(request, 'There was an error creating your account. Please try again.')
                
        context = {
            'form': form,
            'page_title': 'Join Digitera as a Creator',
        }
        return render(request, self.template_name, context)
    
    def generate_unique_slug(self, name):
        """Generate a unique slug for the store."""
        base_slug = slugify(name)
        if not base_slug:
            base_slug = 'creator-store'
        
        slug = base_slug
        counter = 1
        while CreatorProfile.objects.filter(store_slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug


class OnboardingStepMixin:
    """Mixin for onboarding step views."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_creator:
            return redirect('accounts:creator_signup')
        
        # Check if user has already completed onboarding
        if not request.session.get('onboarding_step'):
            creator_profile = getattr(request.user, 'creator_profile', None)
            if creator_profile and creator_profile.status == 'active':
                return redirect('accounts:dashboard')
        
        return super().dispatch(request, *args, **kwargs)


class OnboardingStep1View(OnboardingStepMixin, View):
    """Step 1: Creator profile setup."""
    
    template_name = 'accounts/onboarding_step_1.html'
    
    def get(self, request):
        # Initialize form with existing data if available
        user_profile = getattr(request.user, 'profile', None)
        initial_data = {}
        
        if user_profile:
            initial_data = {
                'bio': user_profile.bio,
                'street_address': user_profile.street_address,
                'suburb': user_profile.suburb,
                'city': user_profile.city,
                'province': user_profile.province,
                'postal_code': user_profile.postal_code,
            }
        
        # Add user data
        initial_data.update({
            'phone_number': request.user.phone_number,
            'vat_registered': request.user.vat_registered,
            'vat_number': request.user.vat_number,
            'company_name': request.user.company_name,
        })
        
        form = CreatorProfileStepForm(initial=initial_data)
        
        context = {
            'form': form,
            'step': 1,
            'total_steps': 4,
            'step_title': 'Profile Setup',
            'step_description': 'Let\'s set up your creator profile with SA-specific business information.',
            'progress_percentage': 25,
            'next_step_url': reverse('accounts:onboarding_step_2'),
            'tooltips': {
                'vat_registration': 'VAT registration is required if your annual turnover exceeds R1 million',
                'business_type': 'Choose the structure that matches your tax registration',
                'address': 'Required for VAT compliance and customer invoicing'
            }
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        form = CreatorProfileStepForm(request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Update user information
                    user = request.user
                    user.phone_number = form.cleaned_data.get('phone_number')
                    user.vat_registered = form.cleaned_data.get('vat_registered')
                    user.vat_number = form.cleaned_data.get('vat_number')
                    user.company_name = form.cleaned_data.get('company_name')
                    user.save()
                    
                    # Update or create user profile
                    profile, created = UserProfile.objects.get_or_create(user=user)
                    profile.bio = form.cleaned_data.get('bio', '')
                    profile.street_address = form.cleaned_data.get('street_address')
                    profile.suburb = form.cleaned_data.get('suburb')
                    profile.city = form.cleaned_data.get('city')
                    profile.province = form.cleaned_data.get('province')
                    profile.postal_code = form.cleaned_data.get('postal_code')
                    profile.business_registration_number = form.cleaned_data.get('business_registration_number', '')
                    profile.save()
                    
                    # Store form data in session for later use
                    request.session['onboarding_step_1_data'] = form.cleaned_data
                    request.session['onboarding_step'] = 2
                    
                    messages.success(request, 'Profile information saved! Now let\'s create your storefront.')
                    return redirect('accounts:onboarding_step_2')
            
            except Exception as e:
                messages.error(request, 'There was an error saving your profile. Please try again.')
        
        context = {
            'form': form,
            'step': 1,
            'total_steps': 4,
            'step_title': 'Profile Setup',
            'step_description': 'Let\'s set up your creator profile with SA-specific business information.',
            'progress_percentage': 25,
        }
        return render(request, self.template_name, context)


class OnboardingStep2View(OnboardingStepMixin, View):
    """Step 2: Storefront creation and branding."""
    
    template_name = 'accounts/onboarding_step_2.html'
    
    def get(self, request):
        creator_profile = get_object_or_404(CreatorProfile, user=request.user)
        
        initial_data = {
            'store_name': creator_profile.store_name,
            'store_description': creator_profile.store_description,
            'business_category': creator_profile.business_category,
            'primary_color': creator_profile.primary_color,
            'secondary_color': creator_profile.secondary_color,
        }
        
        form = StorefrontCreationStepForm(initial=initial_data)
        
        context = {
            'form': form,
            'step': 2,
            'total_steps': 4,
            'step_title': 'Storefront Creation',
            'step_description': 'Design your brand and create your customizable storefront.',
            'progress_percentage': 50,
            'current_store_url': f"https://digitera.co.za/store/{creator_profile.store_slug}",
            'preview_available': True,
            'color_presets': [
                {'name': 'Ocean Blue', 'primary': '#3B82F6', 'secondary': '#10B981'},
                {'name': 'Sunset Orange', 'primary': '#F59E0B', 'secondary': '#EF4444'},
                {'name': 'Forest Green', 'primary': '#10B981', 'secondary': '#3B82F6'},
                {'name': 'Royal Purple', 'primary': '#8B5CF6', 'secondary': '#F59E0B'},
                {'name': 'Rose Gold', 'primary': '#EC4899', 'secondary': '#F59E0B'},
            ]
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        creator_profile = get_object_or_404(CreatorProfile, user=request.user)
        form = StorefrontCreationStepForm(request.POST, request.FILES, instance=creator_profile)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Save creator profile
                    creator_profile = form.save(commit=False)
                    
                    # Generate unique slug from store name
                    if form.cleaned_data.get('store_name'):
                        creator_profile.store_slug = self.generate_unique_slug(
                            form.cleaned_data['store_name'], 
                            exclude_id=creator_profile.id
                        )
                    
                    # Handle file uploads (logo and banner)
                    if 'logo_upload' in request.FILES:
                        # Handle logo upload (in real implementation, upload to storage)
                        creator_profile.store_logo = f"/media/logos/{request.FILES['logo_upload'].name}"
                    
                    if 'banner_upload' in request.FILES:
                        # Handle banner upload (in real implementation, upload to storage)
                        creator_profile.store_banner = f"/media/banners/{request.FILES['banner_upload'].name}"
                    
                    creator_profile.save()
                    
                    # Create or update storefront record
                    storefront, created = Storefront.objects.get_or_create(
                        creator=creator_profile,
                        defaults={
                            'name': creator_profile.store_name,
                            'description': creator_profile.store_description,
                            'is_active': True,
                            'custom_domain': creator_profile.custom_domain,
                            'theme_settings': {
                                'primary_color': creator_profile.primary_color,
                                'secondary_color': creator_profile.secondary_color,
                                'store_theme': form.cleaned_data.get('store_theme', 'modern'),
                                'meta_description': form.cleaned_data.get('meta_description', ''),
                            }
                        }
                    )
                    
                    if not created:
                        storefront.name = creator_profile.store_name
                        storefront.description = creator_profile.store_description
                        storefront.theme_settings.update({
                            'primary_color': creator_profile.primary_color,
                            'secondary_color': creator_profile.secondary_color,
                            'store_theme': form.cleaned_data.get('store_theme', 'modern'),
                            'meta_description': form.cleaned_data.get('meta_description', ''),
                        })
                        storefront.save()
                    
                    # Store form data in session
                    request.session['onboarding_step_2_data'] = {
                        'store_theme': form.cleaned_data.get('store_theme'),
                        'meta_description': form.cleaned_data.get('meta_description'),
                        'enable_custom_domain': form.cleaned_data.get('enable_custom_domain'),
                    }
                    request.session['onboarding_step'] = 3
                    
                    messages.success(request, 'Storefront created successfully! Now let\'s add your first product.')
                    return redirect('accounts:onboarding_step_3')
            
            except Exception as e:
                messages.error(request, f'There was an error creating your storefront: {str(e)}')
        
        context = {
            'form': form,
            'step': 2,
            'total_steps': 4,
            'step_title': 'Storefront Creation',
            'step_description': 'Design your brand and create your customizable storefront.',
            'progress_percentage': 50,
        }
        return render(request, self.template_name, context)
    
    def generate_unique_slug(self, name, exclude_id=None):
        """Generate a unique slug for the store."""
        base_slug = slugify(name)
        if not base_slug:
            base_slug = 'creator-store'
        
        slug = base_slug
        counter = 1
        while True:
            query = CreatorProfile.objects.filter(store_slug=slug)
            if exclude_id:
                query = query.exclude(id=exclude_id)
            if not query.exists():
                break
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug


class OnboardingStep3View(OnboardingStepMixin, View):
    """Step 3: Add first product."""
    
    template_name = 'accounts/onboarding_step_3.html'
    
    def get(self, request):
        form = FirstProductStepForm()
        
        context = {
            'form': form,
            'step': 3,
            'total_steps': 4,
            'step_title': 'Add Your First Product',
            'step_description': 'Create your first product to start selling immediately.',
            'progress_percentage': 75,
            'product_examples': {
                'digital_download': 'E-books, templates, presets, digital art, PDFs',
                'course': 'Video tutorials, online workshops, skill-building courses',
                'membership': 'Monthly content, premium community access, exclusive resources',
                'event': 'Webinars, workshops, conferences, meetups',
                'community': 'Private Discord/Telegram groups, forums, masterminds'
            },
            'pricing_tips': [
                'Research similar products in the SA market',
                'Consider your target audience\'s purchasing power',
                'Start with competitive pricing, then adjust based on demand',
                'Remember: Digitera takes 5% on direct sales, 30% on marketplace sales'
            ]
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        form = FirstProductStepForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    creator_profile = get_object_or_404(CreatorProfile, user=request.user)
                    
                    # Create the appropriate product type
                    product_type = form.cleaned_data['product_type']
                    common_data = {
                        'title': form.cleaned_data['title'],
                        'description': form.cleaned_data['description'],
                        'price': form.cleaned_data['price'],
                        'currency': 'ZAR',
                        'creator': request.user,
                        'category': form.cleaned_data['category'],
                        'tags': form.cleaned_data.get('tags', ''),
                        'is_active': form.cleaned_data.get('publish_immediately', True),
                        'in_marketplace': form.cleaned_data.get('add_to_marketplace', True),
                    }
                    
                    # Handle product image
                    if 'product_image' in request.FILES:
                        common_data['image'] = f"/media/products/{request.FILES['product_image'].name}"
                    
                    # Create specific product type
                    if product_type == 'digital_download':
                        product = DigitalDownload.objects.create(
                            **common_data,
                            file_url=f"/media/downloads/{request.FILES.get('file_upload', 'placeholder.pdf').name}" if request.FILES.get('file_upload') else "",
                            download_limit=10,  # Default limit
                            file_size=1024 * 1024,  # Default 1MB
                        )
                    
                    elif product_type == 'course':
                        product = Course.objects.create(
                            **common_data,
                            duration_weeks=form.cleaned_data.get('course_duration', 4),
                            total_lessons=0,  # Will be updated when lessons are added
                            difficulty_level='beginner',
                            has_certificate=True,
                        )
                    
                    elif product_type == 'membership':
                        product = Membership.objects.create(
                            **common_data,
                            billing_period=form.cleaned_data.get('membership_duration', 'monthly'),
                            access_duration_days=30 if form.cleaned_data.get('membership_duration') == 'monthly' else 365,
                            max_members=1000,  # Default limit
                        )
                    
                    elif product_type == 'event':
                        product = Event.objects.create(
                            **common_data,
                            event_date=form.cleaned_data.get('event_date'),
                            capacity=form.cleaned_data.get('event_capacity', 50),
                            location='Online',  # Default to online
                            event_type='webinar',
                        )
                    
                    elif product_type == 'community':
                        product = Community.objects.create(
                            **common_data,
                            platform='digitera',  # Default platform
                            max_members=100,  # Default limit
                            is_private=True,
                        )
                    
                    # Update creator profile stats
                    creator_profile.total_products += 1
                    creator_profile.save()
                    
                    # Store product creation data
                    request.session['onboarding_step_3_data'] = {
                        'product_id': product.id,
                        'product_type': product_type,
                        'product_title': form.cleaned_data['title'],
                    }
                    request.session['onboarding_step'] = 4
                    
                    messages.success(request, f'Great! Your {product_type.replace("_", " ")} "{form.cleaned_data["title"]}" has been created.')
                    return redirect('accounts:onboarding_step_4')
            
            except Exception as e:
                messages.error(request, f'There was an error creating your product: {str(e)}')
        
        context = {
            'form': form,
            'step': 3,
            'total_steps': 4,
            'step_title': 'Add Your First Product',
            'step_description': 'Create your first product to start selling immediately.',
            'progress_percentage': 75,
        }
        return render(request, self.template_name, context)


class OnboardingStep4View(OnboardingStepMixin, View):
    """Step 4: Preferences and completion."""
    
    template_name = 'accounts/onboarding_step_4.html'
    
    def get(self, request):
        form = OnboardingPreferencesForm()
        
        # Get created product info
        step_3_data = request.session.get('onboarding_step_3_data', {})
        
        context = {
            'form': form,
            'step': 4,
            'total_steps': 4,
            'step_title': 'Final Setup & Preferences',
            'step_description': 'Set your preferences and complete your onboarding.',
            'progress_percentage': 100,
            'created_product': step_3_data,
            'marketing_packages': [
                {
                    'name': 'Starter Package',
                    'price': 'R499 once-off',
                    'features': ['Professional setup', 'SEO optimization', 'Custom templates', 'Basic analytics'],
                    'ideal_for': 'New creators getting started'
                },
                {
                    'name': 'Growth Package',
                    'price': 'R999/month',
                    'features': ['Social media posts', 'Sales funnel review', 'Marketplace spotlights', 'Email marketing'],
                    'ideal_for': 'Growing businesses seeking more visibility'
                },
                {
                    'name': 'Pro Package',
                    'price': 'R2499/month',
                    'features': ['Full marketing management', 'Ad campaign creation', 'Influencer connections', 'Priority support'],
                    'ideal_for': 'Established creators wanting maximum growth'
                }
            ]
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        form = OnboardingPreferencesForm(request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Update user preferences
                    user = request.user
                    user.marketing_emails = form.cleaned_data.get('email_marketing', True)
                    user.save()
                    
                    # Update user profile preferences
                    profile = user.profile
                    profile.email_notifications = form.cleaned_data.get('email_sales', True)
                    profile.sms_notifications = form.cleaned_data.get('sms_notifications', False)
                    profile.push_notifications = form.cleaned_data.get('email_product_updates', True)
                    profile.save()
                    
                    # Update creator profile
                    creator_profile = user.creator_profile
                    creator_profile.status = 'active'  # Activate the creator account
                    
                    # Store preferences in creator profile metadata
                    preferences = {
                        'business_goal': form.cleaned_data.get('business_goal'),
                        'expected_launch_time': form.cleaned_data.get('expected_launch_time'),
                        'interested_features': form.cleaned_data.get('interested_features', []),
                        'marketing_package_preference': form.cleaned_data.get('marketing_package_preference'),
                        'interested_in_marketing': form.cleaned_data.get('interested_in_marketing', False),
                        'onboarding_completed_at': timezone.now().isoformat(),
                    }
                    
                    # Store in custom_css field as JSON (in a real app, use JSONField)
                    creator_profile.custom_css = json.dumps(preferences)
                    creator_profile.save()
                    
                    # Clear onboarding session data
                    keys_to_remove = [
                        'onboarding_step', 'onboarding_user_id',
                        'onboarding_step_1_data', 'onboarding_step_2_data', 'onboarding_step_3_data'
                    ]
                    for key in keys_to_remove:
                        request.session.pop(key, None)
                    
                    # Set welcome message
                    messages.success(request, 'Congratulations! Your creator account is now active and ready to start generating income.')
                    
                    return redirect('accounts:onboarding_complete')
            
            except Exception as e:
                messages.error(request, f'There was an error completing your setup: {str(e)}')
        
        context = {
            'form': form,
            'step': 4,
            'total_steps': 4,
            'step_title': 'Final Setup & Preferences',
            'step_description': 'Set your preferences and complete your onboarding.',
            'progress_percentage': 100,
        }
        return render(request, self.template_name, context)


class OnboardingCompleteView(TemplateView):
    """Onboarding completion and dashboard redirect."""
    
    template_name = 'accounts/onboarding_complete.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        user = self.request.user
        creator_profile = getattr(user, 'creator_profile', None)
        
        context.update({
            'user': user,
            'creator_profile': creator_profile,
            'store_url': creator_profile.get_store_url() if creator_profile else None,
            'next_steps': [
                {
                    'title': 'Customize Your Storefront',
                    'description': 'Add more branding, create custom pages, and set up your domain',
                    'url': reverse('storefronts:customize'),
                    'icon': 'palette'
                },
                {
                    'title': 'Add More Products',
                    'description': 'Create additional products to grow your catalog',
                    'url': reverse('products:create'),
                    'icon': 'plus-circle'
                },
                {
                    'title': 'Set Up Analytics',
                    'description': 'Track your sales, visitors, and customer behavior',
                    'url': reverse('analytics:dashboard'),
                    'icon': 'chart-bar'
                },
                {
                    'title': 'Marketing Tools',
                    'description': 'Explore email marketing, affiliates, and promotional tools',
                    'url': reverse('marketing:tools'),
                    'icon': 'megaphone'
                },
                {
                    'title': 'Payment Setup',
                    'description': 'Configure your payout methods and tax settings',
                    'url': reverse('payments:settings'),
                    'icon': 'credit-card'
                }
            ],
            'quick_stats': {
                'products_created': creator_profile.total_products if creator_profile else 0,
                'store_views': 0,
                'completion_percentage': creator_profile.get_completion_percentage() if creator_profile else 0,
            }
        })
        
        return context


@login_required
@require_http_methods(["POST"])
def skip_onboarding_step(request):
    """AJAX endpoint to skip optional onboarding steps."""
    
    current_step = request.session.get('onboarding_step', 1)
    
    # Only allow skipping certain steps
    skippable_steps = [3, 4]  # Can skip product creation and preferences
    
    if current_step in skippable_steps:
        if current_step == 3:
            # Skip to preferences
            request.session['onboarding_step'] = 4
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('accounts:onboarding_step_4'),
                'message': 'You can add products later from your dashboard.'
            })
        elif current_step == 4:
            # Skip to completion
            creator_profile = request.user.creator_profile
            creator_profile.status = 'active'
            creator_profile.save()
            
            # Clear session
            keys_to_remove = [
                'onboarding_step', 'onboarding_user_id',
                'onboarding_step_1_data', 'onboarding_step_2_data', 'onboarding_step_3_data'
            ]
            for key in keys_to_remove:
                request.session.pop(key, None)
            
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('accounts:onboarding_complete'),
                'message': 'Onboarding completed! You can update preferences later.'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'This step cannot be skipped.'
    })


@login_required
def onboarding_dashboard(request):
    """Dashboard showing onboarding progress for existing users."""
    
    if not request.user.is_creator:
        messages.info(request, 'You need to be a creator to access this page. Please upgrade your account.')
        return redirect('accounts:creator_profile_update')
    
    creator_profile = getattr(request.user, 'creator_profile', None)
    if not creator_profile:
        return redirect('accounts:creator_signup')
    
    # Check completion status
    completion_data = {
        'profile_complete': creator_profile.get_completion_percentage() > 70,
        'storefront_complete': creator_profile.store_name and creator_profile.store_description,
        'product_created': creator_profile.total_products > 0,
        'preferences_set': bool(creator_profile.custom_css),  # Check if preferences are stored
    }
    
    overall_completion = sum(completion_data.values()) / len(completion_data) * 100
    
    context = {
        'creator_profile': creator_profile,
        'completion_data': completion_data,
        'overall_completion': overall_completion,
        'current_step': request.session.get('onboarding_step', 1),
        'can_resume': request.session.get('onboarding_step') is not None,
    }
    
    return render(request, 'accounts/onboarding_dashboard.html', context)

"""
Creator onboarding forms for the multi-step wizard.
Step-by-step forms for creator profile setup, storefront creation, and first product.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from .models import User, UserProfile, CreatorProfile
from products.models import Product, DigitalDownload, Membership, Course, Event, Community
import re
import json


class CreatorProfileStepForm(forms.ModelForm):
    """Step 1: Creator profile setup with SA-specific business information."""
    
    # Additional fields for enhanced profile
    business_type = forms.ChoiceField(
        choices=[
            ('individual', _('Individual Creator')),
            ('sole_proprietor', _('Sole Proprietorship')),
            ('pty_ltd', _('Private Company (Pty Ltd)')),
            ('cc', _('Close Corporation (CC)')),
            ('trust', _('Trust')),
            ('npo', _('Non-Profit Organization')),
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        }),
        help_text=_('Select your business structure for VAT and tax purposes')
    )
    
    # User profile fields
    bio = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'rows': 4,
            'placeholder': 'Tell potential customers about yourself and what you create...'
        }),
        help_text=_('This will be displayed on your public profile'),
        required=False
    )
    
    phone_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '+27 82 123 4567'
        }),
        help_text=_('Your contact number for customer and platform communications'),
        required=True
    )
    
    # Address fields for VAT compliance
    street_address = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Street address'
        }),
        help_text=_('Required for VAT registration and invoicing'),
        required=True
    )
    
    suburb = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Suburb'
        }),
        required=True
    )
    
    city = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'City'
        }),
        required=True
    )
    
    province = forms.ChoiceField(
        choices=UserProfile.PROVINCE_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
        }),
        required=True
    )
    
    postal_code = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '0000'
        }),
        required=True
    )
    
    # VAT registration
    vat_registered = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded text-blue-600 focus:ring-blue-500 h-5 w-5',
            'id': 'vat_registered'
        }),
        label=_('I am registered for VAT in South Africa')
    )
    
    vat_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '4123456789',
            'id': 'vat_number'
        }),
        help_text=_('Your 10-digit VAT registration number'),
        required=False
    )
    
    company_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Your Company Name (Pty) Ltd'
        }),
        help_text=_('Registered company name (if applicable)'),
        required=False
    )
    
    business_registration_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '2023/123456/07'
        }),
        help_text=_('CIPC registration number (if applicable)'),
        required=False
    )

    class Meta:
        model = UserProfile
        fields = []  # We'll handle saving manually

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number:
            # Basic SA phone number validation
            if not re.match(r'^\+27\d{9}$|^0\d{9}$', phone_number):
                raise ValidationError(_('Please enter a valid South African phone number'))
        return phone_number

    def clean_postal_code(self):
        postal_code = self.cleaned_data.get('postal_code')
        if postal_code and not re.match(r'^\d{4}$', postal_code):
            raise ValidationError(_('Please enter a valid 4-digit postal code'))
        return postal_code

    def clean_vat_number(self):
        vat_number = self.cleaned_data.get('vat_number')
        vat_registered = self.cleaned_data.get('vat_registered')
        
        if vat_registered and not vat_number:
            raise ValidationError(_('VAT number is required if you are VAT registered'))
        
        if vat_number and not re.match(r'^\d{10}$', vat_number):
            raise ValidationError(_('VAT number must be exactly 10 digits'))
        
        return vat_number

    def clean_company_name(self):
        company_name = self.cleaned_data.get('company_name')
        business_type = self.cleaned_data.get('business_type')
        
        if business_type in ['pty_ltd', 'cc', 'trust', 'npo'] and not company_name:
            raise ValidationError(_('Company name is required for this business type'))
        
        return company_name


class StorefrontCreationStepForm(forms.ModelForm):
    """Step 2: Storefront creation with branding and customization."""
    
    # Logo upload field
    logo_upload = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'hidden',
            'accept': 'image/*',
            'id': 'logo-upload'
        }),
        help_text=_('Upload your logo (PNG, JPG, max 2MB)')
    )
    
    # Banner upload field
    banner_upload = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'hidden',
            'accept': 'image/*',
            'id': 'banner-upload'
        }),
        help_text=_('Upload your banner image (PNG, JPG, max 5MB)')
    )
    
    # Color picker fields
    primary_color = forms.CharField(
        max_length=7,
        widget=forms.TextInput(attrs={
            'type': 'color',
            'class': 'h-12 w-20 border-2 border-gray-300 rounded-lg cursor-pointer',
            'id': 'primary-color'
        }),
        initial='#3B82F6',
        help_text=_('Your brand\'s primary color')
    )
    
    secondary_color = forms.CharField(
        max_length=7,
        widget=forms.TextInput(attrs={
            'type': 'color',
            'class': 'h-12 w-20 border-2 border-gray-300 rounded-lg cursor-pointer',
            'id': 'secondary-color'
        }),
        initial='#10B981',
        help_text=_('Your brand\'s secondary color')
    )
    
    # Store customization preferences
    store_theme = forms.ChoiceField(
        choices=[
            ('modern', _('Modern - Clean and minimalist')),
            ('creative', _('Creative - Bold and artistic')),
            ('professional', _('Professional - Business-focused')),
            ('vibrant', _('Vibrant - Colorful and energetic')),
            ('dark', _('Dark - Sleek dark theme')),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'text-blue-600 focus:ring-blue-500'
        }),
        initial='modern',
        help_text=_('Choose a theme that matches your brand')
    )
    
    # Advanced customization
    enable_custom_domain = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded text-blue-600 focus:ring-blue-500 h-5 w-5'
        }),
        label=_('I want to use a custom domain (can be set up later)')
    )
    
    # SEO and marketing
    meta_description = forms.CharField(
        max_length=160,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'rows': 3,
            'placeholder': 'A brief description of your store for search engines...'
        }),
        help_text=_('This will appear in search engine results (max 160 characters)'),
        required=False
    )

    class Meta:
        model = CreatorProfile
        fields = [
            'store_name', 'store_description', 'business_category',
            'primary_color', 'secondary_color'
        ]
        widgets = {
            'store_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Your Store Name'
            }),
            'store_description': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 4,
                'placeholder': 'Describe what you offer to customers...'
            }),
            'business_category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
        }

    def clean_store_name(self):
        store_name = self.cleaned_data.get('store_name')
        if store_name:
            # Generate slug and check uniqueness
            slug = slugify(store_name)
            if CreatorProfile.objects.filter(store_slug=slug).exists():
                raise ValidationError(_('A store with this name already exists. Please choose a different name.'))
            
            # Validate store name format
            if not re.match(r'^[a-zA-Z0-9\s\-_&]+$', store_name):
                raise ValidationError(_('Store name can only contain letters, numbers, spaces, hyphens, underscores, and ampersands.'))
        
        return store_name

    def clean_meta_description(self):
        meta_description = self.cleaned_data.get('meta_description')
        if meta_description and len(meta_description) > 160:
            raise ValidationError(_('Meta description must be 160 characters or less.'))
        return meta_description


class FirstProductStepForm(forms.Form):
    """Step 3: Add first product to get started."""
    
    PRODUCT_TYPE_CHOICES = [
        ('digital_download', _('Digital Download - Files, ebooks, templates, etc.')),
        ('course', _('Online Course - Video lessons, modules, certificates')),
        ('membership', _('Membership - Recurring access to content')),
        ('event', _('Event - Tickets for events, workshops, webinars')),
        ('community', _('Community - Access to private groups/forums')),
    ]
    
    # Product type selection
    product_type = forms.ChoiceField(
        choices=PRODUCT_TYPE_CHOICES,
        widget=forms.RadioSelect(attrs={
            'class': 'text-blue-600 focus:ring-blue-500'
        }),
        help_text=_('Choose the type of product you want to create first')
    )
    
    # Basic product information
    title = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Your Amazing Product Title'
        }),
        help_text=_('A compelling title for your product')
    )
    
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'rows': 5,
            'placeholder': 'Describe your product, its benefits, and what customers will get...'
        }),
        help_text=_('Detailed description of your product')
    )
    
    price = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '99.00',
            'step': '0.01',
            'min': '0'
        }),
        help_text=_('Price in ZAR (you can change currency later)')
    )
    
    # Product image
    product_image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'hidden',
            'accept': 'image/*',
            'id': 'product-image-upload'
        }),
        help_text=_('Main product image (PNG, JPG, max 3MB)')
    )
    
    # Category and tags
    category = forms.ChoiceField(
        choices=CreatorProfile.CATEGORY_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        }),
        help_text=_('Select the most relevant category')
    )
    
    tags = forms.CharField(
        max_length=500,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'design, template, business, creative'
        }),
        help_text=_('Add tags separated by commas to help customers find your product'),
        required=False
    )
    
    # Type-specific fields
    # For digital downloads
    file_upload = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'hidden',
            'id': 'file-upload'
        }),
        help_text=_('Upload the digital file customers will receive')
    )
    
    # For courses
    course_duration = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '8',
            'min': '1'
        }),
        help_text=_('Estimated course duration in weeks')
    )
    
    # For memberships
    membership_duration = forms.ChoiceField(
        choices=[
            ('monthly', _('Monthly')),
            ('quarterly', _('Quarterly')),
            ('yearly', _('Yearly')),
            ('lifetime', _('Lifetime')),
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        }),
        required=False,
        help_text=_('Membership billing period')
    )
    
    # For events
    event_date = forms.DateTimeField(
        required=False,
        widget=forms.DateTimeInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'type': 'datetime-local'
        }),
        help_text=_('Event date and time')
    )
    
    event_capacity = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': '50',
            'min': '1'
        }),
        help_text=_('Maximum number of attendees')
    )
    
    # Publishing options
    publish_immediately = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded text-blue-600 focus:ring-blue-500 h-5 w-5'
        }),
        label=_('Publish this product immediately')
    )
    
    add_to_marketplace = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded text-blue-600 focus:ring-blue-500 h-5 w-5'
        }),
        label=_('Add to Digitera marketplace for discovery (30% commission)')
    )

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price is not None and price < 0:
            raise ValidationError(_('Price cannot be negative.'))
        return price

    def clean_tags(self):
        tags = self.cleaned_data.get('tags')
        if tags:
            # Clean and validate tags
            tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            if len(tag_list) > 10:
                raise ValidationError(_('Maximum 10 tags allowed.'))
            return ', '.join(tag_list)
        return tags

    def clean(self):
        cleaned_data = super().clean()
        product_type = cleaned_data.get('product_type')
        
        # Validate type-specific required fields
        if product_type == 'digital_download':
            if not cleaned_data.get('file_upload'):
                # We'll handle file upload later in the view
                pass
        
        elif product_type == 'course':
            if not cleaned_data.get('course_duration'):
                raise ValidationError({'course_duration': _('Course duration is required for courses.')})
        
        elif product_type == 'membership':
            if not cleaned_data.get('membership_duration'):
                raise ValidationError({'membership_duration': _('Membership duration is required for memberships.')})
        
        elif product_type == 'event':
            if not cleaned_data.get('event_date'):
                raise ValidationError({'event_date': _('Event date is required for events.')})
            if not cleaned_data.get('event_capacity'):
                raise ValidationError({'event_capacity': _('Event capacity is required for events.')})
        
        return cleaned_data


class OnboardingPreferencesForm(forms.Form):
    """Step 4: Marketing and notification preferences."""
    
    # Marketing package interest
    interested_in_marketing = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded text-blue-600 focus:ring-blue-500 h-5 w-5'
        }),
        label=_('I\'m interested in marketing packages to grow my business')
    )
    
    marketing_package_preference = forms.ChoiceField(
        choices=[
            ('starter', _('Starter Package - R499 once-off (Setup, SEO, templates)')),
            ('growth', _('Growth Package - R999/month (Social posts, funnel review, spotlights)')),
            ('pro', _('Pro Package - R2499/month (Full management, ads, influencer connections)')),
            ('not_now', _('Not interested right now')),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'text-blue-600 focus:ring-blue-500'
        }),
        required=False,
        help_text=_('You can upgrade anytime from your dashboard')
    )
    
    # Notification preferences
    email_marketing = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded text-blue-600 focus:ring-blue-500 h-5 w-5'
        }),
        label=_('Marketing emails about platform features and tips')
    )
    
    email_sales = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded text-blue-600 focus:ring-blue-500 h-5 w-5'
        }),
        label=_('Sales notifications and order updates')
    )
    
    email_product_updates = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded text-blue-600 focus:ring-blue-500 h-5 w-5'
        }),
        label=_('Product and platform updates')
    )
    
    sms_notifications = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded text-blue-600 focus:ring-blue-500 h-5 w-5'
        }),
        label=_('SMS notifications for important updates')
    )
    
    # Goals and expectations
    business_goal = forms.ChoiceField(
        choices=[
            ('side_income', _('Generate side income (< R5,000/month)')),
            ('main_income', _('Replace my main income (R5,000-R20,000/month)')),
            ('scale_business', _('Scale existing business (> R20,000/month)')),
            ('test_idea', _('Test a business idea')),
            ('hobby', _('Share my hobby/passion')),
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        }),
        help_text=_('This helps us provide relevant tips and features')
    )
    
    expected_launch_time = forms.ChoiceField(
        choices=[
            ('immediately', _('I want to start selling immediately')),
            ('1_week', _('Within 1 week')),
            ('1_month', _('Within 1 month')),
            ('3_months', _('Within 3 months')),
            ('just_exploring', _('Just exploring options')),
        ],
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        }),
        help_text=_('When do you plan to launch your first product?')
    )
    
    # Platform features interest
    interested_features = forms.MultipleChoiceField(
        choices=[
            ('affiliate_program', _('Affiliate program')),
            ('community_building', _('Community building')),
            ('email_marketing', _('Email marketing tools')),
            ('analytics', _('Advanced analytics')),
            ('custom_domain', _('Custom domain')),
            ('api_integration', _('API integrations')),
            ('white_label', _('White-label solutions')),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'text-blue-600 focus:ring-blue-500'
        }),
        required=False,
        help_text=_('Select features you\'re most interested in (we\'ll prioritize these in your dashboard)')
    )

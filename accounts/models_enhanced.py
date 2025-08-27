"""
Enhanced Django models for the accounts app with SA-specific features.
Includes 2FA, comprehensive profiles, and role-based access control.
"""

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.core.validators import EmailValidator
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from decimal import Decimal
import uuid


class UserRole(models.TextChoices):
    """User role choices for role-based access control."""
    CREATOR = 'creator', _('Creator')
    BUYER = 'buyer', _('Buyer')
    ADMIN = 'admin', _('Admin')
    MODERATOR = 'moderator', _('Moderator')


class CustomUserManager(UserManager):
    """Custom manager for User model without username field."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('role', UserRole.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Enhanced Custom User model for Digitera platform with SA-specific features.
    """
    # Remove username field and use email for authentication
    username = None
    
    # Primary identification
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(
        _('email address'),
        unique=True,
        validators=[EmailValidator()],
        help_text=_('Required. Enter a valid email address.')
    )
    
    # User details
    first_name = models.CharField(_('first name'), max_length=100, blank=True)
    last_name = models.CharField(_('last name'), max_length=100, blank=True)
    
    # Enhanced phone number with SA support
    phone_number = PhoneNumberField(
        _('phone number'), 
        blank=True, 
        null=True, 
        region='ZA',
        help_text=_('Phone number with country code, e.g., +27 82 123 4567')
    )
    
    # Address information (basic)
    address = models.TextField(_('address'), blank=True)
    
    # Enhanced SA business information
    vat_registered = models.BooleanField(
        _('VAT registered'),
        default=False,
        help_text=_('Is this user/business registered for VAT in South Africa?')
    )
    vat_number = models.CharField(
        _('VAT number'), 
        max_length=20, 
        blank=True, 
        null=True,
        help_text=_('South African VAT registration number')
    )
    company_name = models.CharField(
        _('company name'), 
        max_length=200, 
        blank=True, 
        null=True,
        help_text=_('Registered company name (if applicable)')
    )
    
    # Role and permissions
    role = models.CharField(
        _('user role'),
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.BUYER
    )
    
    # Account verification and security
    is_verified = models.BooleanField(
        _('email verified'),
        default=False,
        help_text=_('Designates whether this user has verified their email address.')
    )
    email_verification_token = models.CharField(
        _('email verification token'),
        max_length=100, 
        blank=True, 
        null=True
    )
    
    # 2FA settings
    two_factor_enabled = models.BooleanField(
        _('two-factor authentication enabled'), 
        default=False
    )
    backup_tokens = models.JSONField(
        _('backup tokens'), 
        default=list, 
        blank=True,
        help_text=_('Emergency backup codes for 2FA recovery')
    )
    
    # Privacy and marketing preferences
    marketing_emails = models.BooleanField(
        _('receive marketing emails'), 
        default=True
    )
    data_processing_consent = models.BooleanField(
        _('data processing consent'), 
        default=False,
        help_text=_('Consent for data processing under POPIA compliance')
    )
    terms_accepted = models.BooleanField(
        _('terms accepted'), 
        default=False
    )
    terms_accepted_date = models.DateTimeField(
        _('terms accepted date'), 
        blank=True, 
        null=True
    )
    
    # Security tracking
    last_login_ip = models.GenericIPAddressField(
        _('last login IP'), 
        blank=True, 
        null=True
    )
    failed_login_attempts = models.PositiveIntegerField(
        _('failed login attempts'), 
        default=0
    )
    account_locked_until = models.DateTimeField(
        _('account locked until'), 
        blank=True, 
        null=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    last_activity = models.DateTimeField(_('last activity'), auto_now=True)
    
    # Use email as the unique identifier for authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    # Use custom manager
    objects = CustomUserManager()
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['created_at']),
            models.Index(fields=['vat_registered']),
        ]
    
    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
    
    @property
    def full_name(self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def is_creator(self):
        """Check if user is a creator."""
        return self.role == UserRole.CREATOR
    
    @property
    def is_buyer(self):
        """Check if user is a buyer."""
        return self.role == UserRole.BUYER
    
    @property
    def is_admin_user(self):
        """Check if user is an admin."""
        return self.role == UserRole.ADMIN
    
    def can_create_storefront(self):
        """Check if user can create a storefront."""
        return self.role in [UserRole.CREATOR, UserRole.ADMIN]
    
    def get_display_name(self):
        """Get the best display name for the user."""
        if self.full_name:
            return self.full_name
        return self.email.split('@')[0]


class UserProfile(models.Model):
    """Extended user profile with comprehensive SA-specific information."""
    
    PROVINCE_CHOICES = [
        ('EC', _('Eastern Cape')),
        ('FS', _('Free State')),
        ('GP', _('Gauteng')),
        ('KZN', _('KwaZulu-Natal')),
        ('LP', _('Limpopo')),
        ('MP', _('Mpumalanga')),
        ('NC', _('Northern Cape')),
        ('NW', _('North West')),
        ('WC', _('Western Cape')),
    ]
    
    LANGUAGE_CHOICES = [
        ('en', _('English')),
        ('af', _('Afrikaans')),
        ('zu', _('Zulu')),
        ('xh', _('Xhosa')),
        ('st', _('Sotho')),
        ('tn', _('Tswana')),
        ('ss', _('Swati')),
        ('ve', _('Venda')),
        ('ts', _('Tsonga')),
        ('nr', _('Ndebele')),
        ('nso', _('Northern Sotho')),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Personal information
    avatar = models.ImageField(
        _('avatar'), 
        upload_to='avatars/', 
        blank=True, 
        null=True,
        help_text=_('Profile picture (max 5MB)')
    )
    bio = models.TextField(
        _('bio'), 
        max_length=500, 
        blank=True,
        help_text=_('Tell us about yourself')
    )
    date_of_birth = models.DateField(
        _('date of birth'), 
        blank=True, 
        null=True
    )
    gender = models.CharField(
        _('gender'), 
        max_length=20, 
        blank=True,
        choices=[
            ('male', _('Male')),
            ('female', _('Female')),
            ('other', _('Other')),
            ('prefer_not_to_say', _('Prefer not to say')),
        ]
    )
    
    # Detailed SA Address information (for VAT compliance)
    street_address = models.CharField(
        _('street address'), 
        max_length=255, 
        blank=True
    )
    suburb = models.CharField(
        _('suburb'), 
        max_length=100, 
        blank=True
    )
    city = models.CharField(
        _('city'), 
        max_length=100, 
        blank=True
    )
    province = models.CharField(
        _('province'), 
        max_length=3, 
        choices=PROVINCE_CHOICES, 
        blank=True
    )
    postal_code = models.CharField(
        _('postal code'), 
        max_length=10, 
        blank=True
    )
    country = models.CharField(
        _('country'), 
        max_length=50, 
        default='South Africa'
    )
    
    # Business information (for creators and VAT)
    business_registration_number = models.CharField(
        _('business registration number'), 
        max_length=20, 
        blank=True,
        help_text=_('CIPC registration number')
    )
    tax_number = models.CharField(
        _('tax number'), 
        max_length=20, 
        blank=True,
        help_text=_('SARS tax reference number')
    )
    bee_certificate = models.FileField(
        _('BEE certificate'), 
        upload_to='bee_certificates/', 
        blank=True, 
        null=True,
        help_text=_('B-BBEE certificate for preferential procurement')
    )
    
    # Preferences
    language = models.CharField(
        _('preferred language'), 
        max_length=10, 
        default='en', 
        choices=LANGUAGE_CHOICES
    )
    timezone = models.CharField(
        _('timezone'), 
        max_length=50, 
        default='Africa/Johannesburg'
    )
    currency = models.CharField(
        _('preferred currency'), 
        max_length=3, 
        default='ZAR'
    )
    
    # Social media links
    website = models.URLField(_('website'), blank=True)
    twitter = models.CharField(_('Twitter username'), max_length=50, blank=True)
    instagram = models.CharField(_('Instagram username'), max_length=50, blank=True)
    linkedin = models.URLField(_('LinkedIn profile'), blank=True)
    facebook = models.URLField(_('Facebook profile'), blank=True)
    youtube = models.URLField(_('YouTube channel'), blank=True)
    tiktok = models.CharField(_('TikTok username'), max_length=50, blank=True)
    
    # Notifications preferences
    email_notifications = models.BooleanField(_('email notifications'), default=True)
    sms_notifications = models.BooleanField(_('SMS notifications'), default=False)
    push_notifications = models.BooleanField(_('push notifications'), default=True)
    marketing_sms = models.BooleanField(_('marketing SMS'), default=False)
    
    # Account statistics
    total_spent = models.DecimalField(
        _('total spent'), 
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    total_earned = models.DecimalField(
        _('total earned'), 
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    referral_count = models.PositiveIntegerField(
        _('referral count'), 
        default=0
    )
    
    # Verification and trust
    identity_verified = models.BooleanField(
        _('identity verified'), 
        default=False
    )
    bank_account_verified = models.BooleanField(
        _('bank account verified'), 
        default=False
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')
        db_table = 'user_profiles'

    def __str__(self):
        return f"{self.user.email} Profile"
    
    def get_full_address(self):
        """Return formatted SA address"""
        address_parts = [
            self.street_address,
            self.suburb,
            self.city,
            self.get_province_display(),
            self.postal_code,
            self.country
        ]
        return ', '.join([part for part in address_parts if part])
    
    def get_completion_percentage(self):
        """Calculate profile completion percentage"""
        total_fields = 15  # Key fields for completion
        completed_fields = 0
        
        if self.avatar: completed_fields += 1
        if self.bio: completed_fields += 1
        if self.date_of_birth: completed_fields += 1
        if self.street_address: completed_fields += 1
        if self.city: completed_fields += 1
        if self.province: completed_fields += 1
        if self.postal_code: completed_fields += 1
        if self.user.phone_number: completed_fields += 1
        if self.website: completed_fields += 1
        if self.twitter or self.instagram or self.linkedin: completed_fields += 1
        if self.business_registration_number: completed_fields += 1
        if self.language != 'en': completed_fields += 1
        if self.gender: completed_fields += 1
        if self.identity_verified: completed_fields += 1
        if self.bank_account_verified: completed_fields += 1
        
        return round((completed_fields / total_fields) * 100)


class CreatorProfile(models.Model):
    """Creator-specific profile for storefront customization and business management."""
    
    CREATOR_STATUS_CHOICES = [
        ('pending', _('Pending Approval')),
        ('active', _('Active')),
        ('suspended', _('Suspended')),
        ('banned', _('Banned')),
    ]
    
    CATEGORY_CHOICES = [
        ('art_design', _('Art & Design')),
        ('business', _('Business')),
        ('education', _('Education')),
        ('fitness_health', _('Fitness & Health')),
        ('food_cooking', _('Food & Cooking')),
        ('gaming', _('Gaming')),
        ('lifestyle', _('Lifestyle')),
        ('music', _('Music')),
        ('photography', _('Photography')),
        ('technology', _('Technology')),
        ('travel', _('Travel')),
        ('writing', _('Writing')),
        ('other', _('Other')),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='creator_profile')
    
    # Storefront basic information
    store_name = models.CharField(
        _('store name'), 
        max_length=100, 
        unique=True,
        help_text=_('Your unique store name')
    )
    store_slug = models.SlugField(
        _('store URL slug'), 
        max_length=100, 
        unique=True,
        help_text=_('URL-friendly version of your store name')
    )
    store_description = models.TextField(
        _('store description'), 
        max_length=1000, 
        blank=True,
        help_text=_('Describe what you offer to customers')
    )
    store_logo = models.ImageField(
        _('store logo'), 
        upload_to='store_logos/', 
        blank=True, 
        null=True,
        help_text=_('Square logo for your store (recommended 400x400px)')
    )
    store_banner = models.ImageField(
        _('store banner'), 
        upload_to='store_banners/', 
        blank=True, 
        null=True,
        help_text=_('Banner image for your store (recommended 1200x300px)')
    )
    
    # Branding and customization
    primary_color = models.CharField(
        _('primary color'), 
        max_length=7, 
        default='#3B82F6',
        help_text=_('Main brand color (hex code)')
    )
    secondary_color = models.CharField(
        _('secondary color'), 
        max_length=7, 
        default='#10B981',
        help_text=_('Secondary brand color (hex code)')
    )
    custom_css = models.TextField(
        _('custom CSS'), 
        blank=True,
        help_text=_('Advanced: Custom CSS for your storefront')
    )
    
    # Custom domain
    custom_domain = models.CharField(
        _('custom domain'), 
        max_length=100, 
        blank=True, 
        null=True,
        help_text=_('Your custom domain (e.g., shop.yourdomain.com)')
    )
    domain_verified = models.BooleanField(
        _('domain verified'), 
        default=False
    )
    
    # Creator status and verification
    status = models.CharField(
        _('status'), 
        max_length=20, 
        choices=CREATOR_STATUS_CHOICES, 
        default='pending'
    )
    verified = models.BooleanField(
        _('verified creator'), 
        default=False,
        help_text=_('Verified by Digitera team')
    )
    featured = models.BooleanField(
        _('featured creator'), 
        default=False
    )
    
    # Business information
    business_category = models.CharField(
        _('business category'), 
        max_length=50, 
        choices=CATEGORY_CHOICES,
        blank=True
    )
    years_in_business = models.PositiveIntegerField(
        _('years in business'), 
        blank=True, 
        null=True
    )
    business_license = models.FileField(
        _('business license'), 
        upload_to='business_licenses/', 
        blank=True, 
        null=True
    )
    
    # Marketing package subscription
    current_marketing_package = models.CharField(
        _('current marketing package'), 
        max_length=20, 
        choices=[
            ('starter', _('Starter - R499/month')), 
            ('growth', _('Growth - R999/month')), 
            ('pro', _('Pro - R2499/month'))
        ],
        blank=True, 
        null=True
    )
    package_expires_at = models.DateTimeField(
        _('package expires at'), 
        blank=True, 
        null=True
    )
    
    # Analytics and metrics
    total_sales = models.DecimalField(
        _('total sales'), 
        max_digits=12, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    total_products = models.PositiveIntegerField(
        _('total products'), 
        default=0
    )
    total_customers = models.PositiveIntegerField(
        _('total customers'), 
        default=0
    )
    rating = models.DecimalField(
        _('average rating'), 
        max_digits=3, 
        decimal_places=2, 
        default=Decimal('0.00')
    )
    review_count = models.PositiveIntegerField(
        _('review count'), 
        default=0
    )
    
    # SA Banking information for payouts
    bank_name = models.CharField(
        _('bank name'), 
        max_length=100, 
        blank=True,
        choices=[
            ('absa', _('ABSA Bank')),
            ('capitec', _('Capitec Bank')),
            ('fnb', _('First National Bank')),
            ('nedbank', _('Nedbank')),
            ('standard_bank', _('Standard Bank')),
            ('african_bank', _('African Bank')),
            ('investec', _('Investec')),
            ('discovery_bank', _('Discovery Bank')),
            ('other', _('Other')),
        ]
    )
    account_holder = models.CharField(
        _('account holder name'), 
        max_length=100, 
        blank=True
    )
    account_number = models.CharField(
        _('account number'), 
        max_length=20, 
        blank=True
    )
    branch_code = models.CharField(
        _('branch code'), 
        max_length=10, 
        blank=True
    )
    account_type = models.CharField(
        _('account type'), 
        max_length=20, 
        blank=True,
        choices=[
            ('current', _('Current Account')),
            ('savings', _('Savings Account')),
            ('business', _('Business Account')),
        ]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Creator Profile')
        verbose_name_plural = _('Creator Profiles')
        db_table = 'creator_profiles'
        indexes = [
            models.Index(fields=['store_slug']),
            models.Index(fields=['status']),
            models.Index(fields=['verified']),
            models.Index(fields=['business_category']),
        ]

    def __str__(self):
        return f"{self.store_name} ({self.user.email})"
    
    def get_store_url(self):
        """Get the full store URL"""
        if self.custom_domain and self.domain_verified:
            return f"https://{self.custom_domain}"
        return f"https://digitera.co.za/store/{self.store_slug}"
    
    def get_completion_percentage(self):
        """Calculate creator profile completion percentage"""
        total_fields = 12
        completed_fields = 0
        
        if self.store_name: completed_fields += 1
        if self.store_description: completed_fields += 1
        if self.store_logo: completed_fields += 1
        if self.store_banner: completed_fields += 1
        if self.business_category: completed_fields += 1
        if self.bank_name: completed_fields += 1
        if self.account_holder: completed_fields += 1
        if self.account_number: completed_fields += 1
        if self.branch_code: completed_fields += 1
        if self.years_in_business: completed_fields += 1
        if self.business_license: completed_fields += 1
        if self.verified: completed_fields += 1
        
        return round((completed_fields / total_fields) * 100)


class DeviceType(models.TextChoices):
    """Device type choices for user sessions."""
    DESKTOP = 'desktop', _('Desktop')
    MOBILE = 'mobile', _('Mobile')
    TABLET = 'tablet', _('Tablet')
    UNKNOWN = 'unknown', _('Unknown')


class UserSession(models.Model):
    """Enhanced model to track user sessions for analytics and security."""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    session_id = models.CharField(_('session ID'), max_length=255, unique=True)
    
    # Device and browser information
    device_type = models.CharField(
        _('device type'),
        max_length=20,
        choices=DeviceType.choices,
        default=DeviceType.UNKNOWN
    )
    user_agent = models.TextField(_('user agent'), blank=True)
    browser = models.CharField(_('browser'), max_length=50, blank=True)
    operating_system = models.CharField(_('operating system'), max_length=50, blank=True)
    
    # Location information
    ip_address = models.GenericIPAddressField(_('IP address'), null=True, blank=True)
    location = models.CharField(_('location'), max_length=100, blank=True)
    country = models.CharField(_('country'), max_length=50, blank=True)
    city = models.CharField(_('city'), max_length=50, blank=True)
    
    # Session data
    actions = models.JSONField(
        _('user actions'),
        default=dict,
        help_text=_('JSON data containing user actions during the session')
    )
    
    # Timestamps
    started_at = models.DateTimeField(_('started at'), auto_now_add=True)
    last_activity = models.DateTimeField(_('last activity'), auto_now=True)
    ended_at = models.DateTimeField(_('ended at'), null=True, blank=True)
    is_active = models.BooleanField(_('is active'), default=True)
    
    class Meta:
        verbose_name = _('User Session')
        verbose_name_plural = _('User Sessions')
        db_table = 'user_sessions'
        indexes = [
            models.Index(fields=['user', 'started_at']),
            models.Index(fields=['session_id']),
            models.Index(fields=['device_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"Session for {self.user.email} - {self.device_type} - {self.started_at}"


class RequestMethod(models.TextChoices):
    """HTTP request method choices."""
    GET = 'GET', _('GET')
    POST = 'POST', _('POST')
    PUT = 'PUT', _('PUT')
    PATCH = 'PATCH', _('PATCH')
    DELETE = 'DELETE', _('DELETE')
    OPTIONS = 'OPTIONS', _('OPTIONS')
    HEAD = 'HEAD', _('HEAD')


class APILog(models.Model):
    """Enhanced model to log API requests for monitoring and debugging."""
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='api_logs'
    )
    endpoint = models.CharField(_('API endpoint'), max_length=255)
    request_method = models.CharField(
        _('request method'),
        max_length=10,
        choices=RequestMethod.choices
    )
    
    # Request details
    ip_address = models.GenericIPAddressField(_('IP address'), null=True, blank=True)
    user_agent = models.TextField(_('user agent'), blank=True)
    request_data = models.JSONField(_('request data'), default=dict, blank=True)
    
    # Response details
    status_code = models.IntegerField(_('HTTP status code'))
    response_time = models.FloatField(_('response time (ms)'), null=True, blank=True)
    response_size = models.PositiveIntegerField(_('response size (bytes)'), null=True, blank=True)
    
    # Error tracking
    error_message = models.TextField(_('error message'), blank=True)
    stack_trace = models.TextField(_('stack trace'), blank=True)
    
    timestamp = models.DateTimeField(_('timestamp'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('API Log')
        verbose_name_plural = _('API Logs')
        db_table = 'api_logs'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['endpoint']),
            models.Index(fields=['status_code']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['request_method']),
        ]
    
    def __str__(self):
        user_email = self.user.email if self.user else 'Anonymous'
        return f"{self.request_method} {self.endpoint} - {user_email} - {self.status_code}"

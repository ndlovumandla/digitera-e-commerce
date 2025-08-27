"""
Enhanced Products models for Digitera Platform with polymorphic support.
Includes digital downloads, memberships, communities, courses, and events.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from polymorphic.models import PolymorphicModel
from decimal import Decimal
import uuid
import json

User = get_user_model()


class Category(models.Model):
    """Product categories for organization and discovery."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('name'), max_length=100, default='')
    slug = models.SlugField(_('slug'), unique=True, default='')
    description = models.TextField(_('description'), blank=True, default='')
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='children'
    )
    image = models.CharField(_('category image'), max_length=200, blank=True, default='')
    is_active = models.BooleanField(_('is active'), default=True)
    sort_order = models.PositiveIntegerField(_('sort order'), default=0)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', 'sort_order']),
        ]
    
    def __str__(self):
        return self.name


class Tag(models.Model):
    """Tags for product discovery and categorization."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('name'), max_length=50, unique=True, default='')
    slug = models.SlugField(_('slug'), unique=True, default='')
    color = models.CharField(_('color'), max_length=7, default='#3B82F6')
    usage_count = models.PositiveIntegerField(_('usage count'), default=0)
    
    class Meta:
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')
        ordering = ['-usage_count', 'name']
    
    def __str__(self):
        return self.name


class Product(PolymorphicModel):
    """Base product model with polymorphic support for different product types."""
    
    class ProductStatus(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        PENDING = 'pending', _('Pending Review')
        PUBLISHED = 'published', _('Published')
        SUSPENDED = 'suspended', _('Suspended')
        ARCHIVED = 'archived', _('Archived')
    
    class PricingType(models.TextChoices):
        FREE = 'free', _('Free')
        FIXED = 'fixed', _('Fixed Price')
        FLEXIBLE = 'flexible', _('Pay What You Want')
        SUBSCRIPTION = 'subscription', _('Subscription')
    
    class VisibilityType(models.TextChoices):
        PUBLIC = 'public', _('Public')
        UNLISTED = 'unlisted', _('Unlisted')
        PRIVATE = 'private', _('Private')
    
    class ProductType(models.TextChoices):
        DIGITAL_DOWNLOAD = 'digital_download', _('Digital Download')
        COURSE = 'course', _('Course')
        MEMBERSHIP = 'membership', _('Membership')
        EVENT = 'event', _('Event')
        COMMUNITY = 'community', _('Community')
    
    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')
    storefront = models.ForeignKey('storefronts.Storefront', on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    
    # Basic information
    name = models.CharField(_('name'), max_length=200, default='')
    slug = models.SlugField(_('slug'), max_length=200, blank=True, default='')
    description = models.TextField(_('description'), default='')
    short_description = models.TextField(_('short description'), max_length=500, blank=True, default='')
    
    # Media
    featured_image = models.CharField(_('featured image'), max_length=200, blank=True, default='')
    gallery_images = models.JSONField(_('gallery images'), default=list, blank=True)
    
    # Categorization
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    tags = models.ManyToManyField(Tag, related_name='products', blank=True)
    
    # Pricing
    pricing_type = models.CharField(_('pricing type'), max_length=20, choices=PricingType.choices, default=PricingType.FIXED)
    price = models.DecimalField(_('price'), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(_('currency'), max_length=3, default='ZAR')
    minimum_price = models.DecimalField(_('minimum price'), max_digits=10, decimal_places=2, null=True, blank=True)
    
    # VAT and Tax
    vat_inclusive = models.BooleanField(_('VAT inclusive'), default=True)
    vat_rate = models.DecimalField(_('VAT rate'), max_digits=5, decimal_places=4, default=Decimal('0.15'))
    
    # Status and visibility
    status = models.CharField(_('status'), max_length=20, choices=ProductStatus.choices, default=ProductStatus.DRAFT)
    visibility = models.CharField(_('visibility'), max_length=20, choices=VisibilityType.choices, default=VisibilityType.PUBLIC)
    product_type = models.CharField(_('product type'), max_length=20, choices=ProductType.choices, default=ProductType.DIGITAL_DOWNLOAD)
    is_featured = models.BooleanField(_('is featured'), default=False)
    is_digital = models.BooleanField(_('is digital'), default=True)
    is_marketplace_promoted = models.BooleanField(_('marketplace promoted'), default=False)
    marketplace_promotion_start = models.DateTimeField(_('promotion start'), null=True, blank=True)
    marketplace_promotion_end = models.DateTimeField(_('promotion end'), null=True, blank=True)
    commission_rate = models.DecimalField(_('commission rate'), max_digits=5, decimal_places=4, default=Decimal('0.30'))
    
    # Marketplace metrics
    trending_score = models.FloatField(_('trending score'), default=0.0)
    discovery_rank = models.PositiveIntegerField(_('discovery rank'), default=0)
    last_24h_sales = models.PositiveIntegerField(_('last 24h sales'), default=0)
    last_24h_revenue = models.DecimalField(_('last 24h revenue'), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # SEO
    meta_title = models.CharField(_('meta title'), max_length=60, blank=True, default='')
    meta_description = models.TextField(_('meta description'), max_length=160, blank=True, default='')
    
    # Analytics
    view_count = models.PositiveIntegerField(_('view count'), default=0)
    purchase_count = models.PositiveIntegerField(_('purchase count'), default=0)
    rating_average = models.DecimalField(_('rating average'), max_digits=3, decimal_places=2, default=Decimal('0.00'))
    rating_count = models.PositiveIntegerField(_('rating count'), default=0)
    
    # AI and Recommendations
    ai_tags = models.JSONField(_('AI generated tags'), default=list, blank=True)
    recommendation_score = models.FloatField(_('recommendation score'), default=0.0)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    published_at = models.DateTimeField(_('published at'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Product')
        verbose_name_plural = _('Products')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['creator', 'status']),
            models.Index(fields=['category']),
            models.Index(fields=['status']),
            models.Index(fields=['is_featured']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def price_with_vat(self):
        """Calculate price including VAT if not already inclusive."""
        if self.vat_inclusive:
            return self.price
        return self.price * (1 + self.vat_rate)
    
    @property
    def vat_amount(self):
        """Calculate VAT amount."""
        if self.vat_inclusive:
            return self.price * self.vat_rate / (1 + self.vat_rate)
        return self.price * self.vat_rate


class DigitalDownload(Product):
    """Digital download products (files, software, etc.)."""
    
    class DeliveryMethod(models.TextChoices):
        INSTANT = 'instant', _('Instant Download')
        EMAIL = 'email', _('Email Delivery')
        ACCOUNT = 'account', _('Account Access')
    
    # Download settings
    download_files = models.JSONField(_('download files'), default=list)
    delivery_method = models.CharField(_('delivery method'), max_length=20, choices=DeliveryMethod.choices, default=DeliveryMethod.INSTANT)
    download_limit = models.PositiveIntegerField(_('download limit'), null=True, blank=True)
    expiry_days = models.PositiveIntegerField(_('expiry days'), null=True, blank=True)
    file_size_mb = models.FloatField(_('file size (MB)'), default=0.0)
    
    # File security
    secure_delivery = models.BooleanField(_('secure delivery'), default=True)
    watermark_enabled = models.BooleanField(_('watermark enabled'), default=False)
    drm_protection = models.BooleanField(_('DRM protection'), default=False)
    
    # License
    license_type = models.CharField(_('license type'), max_length=100, default='Standard License')
    license_terms = models.TextField(_('license terms'), blank=True, default='')
    
    class Meta:
        verbose_name = _('Digital Download')
        verbose_name_plural = _('Digital Downloads')


class Membership(Product):
    """Membership/subscription products."""
    
    class BillingCycle(models.TextChoices):
        MONTHLY = 'monthly', _('Monthly')
        QUARTERLY = 'quarterly', _('Quarterly')
        ANNUALLY = 'annually', _('Annually')
        LIFETIME = 'lifetime', _('Lifetime')
    
    class AccessLevel(models.TextChoices):
        BASIC = 'basic', _('Basic')
        PREMIUM = 'premium', _('Premium')
        VIP = 'vip', _('VIP')
    
    # Subscription settings
    billing_cycle = models.CharField(_('billing cycle'), max_length=20, choices=BillingCycle.choices, default=BillingCycle.MONTHLY)
    access_level = models.CharField(_('access level'), max_length=20, choices=AccessLevel.choices, default=AccessLevel.BASIC)
    trial_days = models.PositiveIntegerField(_('trial days'), default=0)
    
    # Benefits
    benefits = models.JSONField(_('membership benefits'), default=list)
    max_downloads_per_month = models.PositiveIntegerField(_('max downloads per month'), null=True, blank=True)
    exclusive_content = models.BooleanField(_('exclusive content access'), default=False)
    
    # Community access
    discord_role_id = models.CharField(_('Discord role ID'), max_length=100, blank=True, default='')
    community_access = models.BooleanField(_('community access'), default=True)
    
    class Meta:
        verbose_name = _('Membership')
        verbose_name_plural = _('Memberships')


class Community(Product):
    """Community products (Discord, forums, chat groups)."""
    
    class CommunityType(models.TextChoices):
        DISCORD = 'discord', _('Discord Server')
        FORUM = 'forum', _('Forum')
        CHAT = 'chat', _('Chat Group')
        HYBRID = 'hybrid', _('Hybrid Community')
    
    # Community settings
    community_type = models.CharField(_('community type'), max_length=20, choices=CommunityType.choices, default=CommunityType.DISCORD)
    max_members = models.PositiveIntegerField(_('max members'), null=True, blank=True)
    moderation_level = models.CharField(_('moderation level'), max_length=20, default='standard')
    
    # Integration settings
    discord_server_id = models.CharField(_('Discord server ID'), max_length=100, blank=True, default='')
    discord_invite_link = models.URLField(_('Discord invite link'), blank=True)
    forum_url = models.URLField(_('forum URL'), blank=True)
    
    # Community features
    voice_channels = models.BooleanField(_('voice channels'), default=True)
    file_sharing = models.BooleanField(_('file sharing'), default=True)
    events_calendar = models.BooleanField(_('events calendar'), default=True)
    
    class Meta:
        verbose_name = _('Community')
        verbose_name_plural = _('Communities')


class Course(Product):
    """Online course products with lessons and content."""
    
    class CourseLevel(models.TextChoices):
        BEGINNER = 'beginner', _('Beginner')
        INTERMEDIATE = 'intermediate', _('Intermediate')
        ADVANCED = 'advanced', _('Advanced')
        ALL_LEVELS = 'all_levels', _('All Levels')
    
    class ContentDelivery(models.TextChoices):
        IMMEDIATE = 'immediate', _('Immediate Access')
        DRIP = 'drip', _('Drip Content')
        SCHEDULED = 'scheduled', _('Scheduled Release')
    
    # Course settings
    level = models.CharField(_('course level'), max_length=20, choices=CourseLevel.choices, default=CourseLevel.BEGINNER)
    duration_hours = models.PositiveIntegerField(_('duration (hours)'), default=1)
    content_delivery = models.CharField(_('content delivery'), max_length=20, choices=ContentDelivery.choices, default=ContentDelivery.IMMEDIATE)
    
    # Content settings
    drip_schedule_days = models.PositiveIntegerField(_('drip schedule (days)'), default=7)
    certificate_enabled = models.BooleanField(_('certificate enabled'), default=False)
    certificate_template = models.CharField(_('certificate template'), max_length=200, blank=True, default='')
    
    # Course structure
    total_lessons = models.PositiveIntegerField(_('total lessons'), default=0)
    total_videos = models.PositiveIntegerField(_('total videos'), default=0)
    total_pdfs = models.PositiveIntegerField(_('total PDFs'), default=0)
    
    # Engagement
    discussion_enabled = models.BooleanField(_('discussion enabled'), default=True)
    assignments_enabled = models.BooleanField(_('assignments enabled'), default=False)
    quiz_enabled = models.BooleanField(_('quiz enabled'), default=False)
    
    class Meta:
        verbose_name = _('Course')
        verbose_name_plural = _('Courses')


class Event(Product):
    """Event products with QR ticketing and management."""
    
    class EventType(models.TextChoices):
        PHYSICAL = 'physical', _('Physical Event')
        VIRTUAL = 'virtual', _('Virtual Event')
        HYBRID = 'hybrid', _('Hybrid Event')
    
    class TicketType(models.TextChoices):
        STANDARD = 'standard', _('Standard Ticket')
        VIP = 'vip', _('VIP Ticket')
        EARLY_BIRD = 'early_bird', _('Early Bird')
        GROUP = 'group', _('Group Ticket')
    
    # Event details
    event_type = models.CharField(_('event type'), max_length=20, choices=EventType.choices, default=EventType.PHYSICAL)
    start_datetime = models.DateTimeField(_('start date and time'), default=timezone.now)
    end_datetime = models.DateTimeField(_('end date and time'), default=timezone.now)
    timezone = models.CharField(_('timezone'), max_length=50, default='Africa/Johannesburg')
    
    # Location
    venue_name = models.CharField(_('venue name'), max_length=200, blank=True, default='')
    address = models.TextField(_('address'), blank=True, default='')
    virtual_link = models.URLField(_('virtual event link'), blank=True)
    
    # Ticketing
    ticket_type = models.CharField(_('ticket type'), max_length=20, choices=TicketType.choices, default=TicketType.STANDARD)
    max_attendees = models.PositiveIntegerField(_('max attendees'), null=True, blank=True)
    tickets_sold = models.PositiveIntegerField(_('tickets sold'), default=0)
    
    # QR Code settings
    qr_enabled = models.BooleanField(_('QR code enabled'), default=True)
    qr_template = models.CharField(_('QR template'), max_length=200, blank=True, default='')
    
    # Event features
    networking_enabled = models.BooleanField(_('networking enabled'), default=False)
    recording_available = models.BooleanField(_('recording available'), default=False)
    materials_included = models.BooleanField(_('materials included'), default=False)
    
    class Meta:
        verbose_name = _('Event')
        verbose_name_plural = _('Events')
        ordering = ['start_datetime']


class ProductReview(models.Model):
    """Product reviews and ratings."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='product_reviews')
    
    rating = models.PositiveIntegerField(_('rating'), validators=[MinValueValidator(1), MaxValueValidator(5)], default=5)
    title = models.CharField(_('review title'), max_length=200, blank=True, default='')
    content = models.TextField(_('review content'), blank=True, default='')
    
    is_verified_purchase = models.BooleanField(_('verified purchase'), default=False)
    is_featured = models.BooleanField(_('is featured'), default=False)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('Product Review')
        verbose_name_plural = _('Product Reviews')
        unique_together = ['product', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.product.title} - {self.rating}★ by {self.user.email}'


class ProductAnalytics(models.Model):
    """Product analytics and performance tracking."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='analytics')
    
    date = models.DateField(_('date'))
    views = models.PositiveIntegerField(_('views'), default=0)
    unique_views = models.PositiveIntegerField(_('unique views'), default=0)
    purchases = models.PositiveIntegerField(_('purchases'), default=0)
    revenue = models.DecimalField(_('revenue'), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Traffic sources
    organic_traffic = models.PositiveIntegerField(_('organic traffic'), default=0)
    social_traffic = models.PositiveIntegerField(_('social traffic'), default=0)
    direct_traffic = models.PositiveIntegerField(_('direct traffic'), default=0)
    referral_traffic = models.PositiveIntegerField(_('referral traffic'), default=0)
    
    # Engagement metrics
    bounce_rate = models.FloatField(_('bounce rate'), default=0.0)
    time_on_page = models.PositiveIntegerField(_('time on page (seconds)'), default=0)
    conversion_rate = models.FloatField(_('conversion rate'), default=0.0)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Product Analytics')
        verbose_name_plural = _('Product Analytics')
        unique_together = ['product', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['product', 'date']),
            models.Index(fields=['date']),
        ]

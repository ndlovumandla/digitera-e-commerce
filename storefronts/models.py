"""
Enhanced Storefronts models for Digitera Platform.
Includes drag-and-drop builde    meta_description = models.TextField(_('meta description'), max_length=160, blank=True, default='')
    google_analytics_id = models.CharField(_('Google Analytics ID'), max_length=20, blank=True, default='')
    facebook_pixel_id = models.CharField(_('Facebook Pixel ID'), max_length=20, blank=True, default='')
    
    # Contact information
    business_email = models.EmailField(_('business email'), blank=True, default='')
    business_phone = models.CharField(_('business phone'), max_length=20, blank=True, default='')
    business_address = models.TextField(_('business address'), blank=True, default='')tion, branding, and customization.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import URLValidator
import uuid

User = get_user_model()


class StorefrontTheme(models.Model):
    """Pre-built themes for storefronts."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('theme name'), max_length=100, default='')
    description = models.TextField(_('description'), blank=True, default='')
    preview_image = models.CharField(_('preview image'), max_length=200, blank=True, default='')
    
    # Theme configuration
    layout_config = models.JSONField(_('layout configuration'), default=dict)
    color_scheme = models.JSONField(_('color scheme'), default=dict)
    typography = models.JSONField(_('typography'), default=dict)
    
    # Theme features
    is_premium = models.BooleanField(_('is premium'), default=False)
    is_active = models.BooleanField(_('is active'), default=True)
    sort_order = models.PositiveIntegerField(_('sort order'), default=0)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('Storefront Theme')
        verbose_name_plural = _('Storefront Themes')
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return self.name


class Storefront(models.Model):
    """Enhanced storefront model with comprehensive customization."""
    
    class StorefrontStatus(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        ACTIVE = 'active', _('Active')
        SUSPENDED = 'suspended', _('Suspended')
        ARCHIVED = 'archived', _('Archived')
    
    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='storefronts')
    theme = models.ForeignKey(StorefrontTheme, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Basic information
    name = models.CharField(_('storefront name'), max_length=200, default='')
    slug = models.SlugField(_('slug'), max_length=200, unique=True, default='')
    description = models.TextField(_('description'), blank=True, default='')
    tagline = models.CharField(_('tagline'), max_length=200, blank=True, default='')
    
    # Branding
    logo = models.CharField(_('logo URL'), max_length=200, blank=True, default='')
    banner_image = models.CharField(_('banner image'), max_length=200, blank=True, default='')
    favicon = models.CharField(_('favicon URL'), max_length=200, blank=True, default='')
    
    # Customization - Drag-and-drop builder simulation via JSONB
    layout_config = models.JSONField(_('layout configuration'), default=dict)
    color_scheme = models.JSONField(_('color scheme'), default=dict)
    typography = models.JSONField(_('typography settings'), default=dict)
    navigation_config = models.JSONField(_('navigation configuration'), default=dict)
    footer_config = models.JSONField(_('footer configuration'), default=dict)
    
    # Page builder sections
    hero_section = models.JSONField(_('hero section'), default=dict)
    about_section = models.JSONField(_('about section'), default=dict)
    features_section = models.JSONField(_('features section'), default=dict)
    testimonials_section = models.JSONField(_('testimonials section'), default=dict)
    custom_sections = models.JSONField(_('custom sections'), default=list)
    
    # Domain and SEO
    custom_domain = models.CharField(_('custom domain'), max_length=255, unique=True, null=True, blank=True, default='')
    subdomain = models.CharField(_('subdomain'), max_length=100, unique=True, blank=True, default='')
    meta_title = models.CharField(_('meta title'), max_length=60, blank=True, default='')
    meta_description = models.TextField(_('meta description'), max_length=160, blank=True, default='')
    google_analytics_id = models.CharField(_('Google Analytics ID'), max_length=20, blank=True, default='')
    facebook_pixel_id = models.CharField(_('Facebook Pixel ID'), max_length=20, blank=True, default='')
    
    # Business information
    business_email = models.EmailField(_('business email'), blank=True)
    business_phone = models.CharField(_('business phone'), max_length=20, blank=True)
    business_address = models.TextField(_('business address'), blank=True)
    
    # Social media
    social_links = models.JSONField(_('social media links'), default=dict)
    
    # Settings and preferences
    currency = models.CharField(_('default currency'), max_length=3, default='ZAR')
    timezone = models.CharField(_('timezone'), max_length=50, default='Africa/Johannesburg')
    language = models.CharField(_('language'), max_length=10, default='en')
    
    # Features and capabilities
    enable_blog = models.BooleanField(_('enable blog'), default=False)
    enable_testimonials = models.BooleanField(_('enable testimonials'), default=True)
    enable_newsletter = models.BooleanField(_('enable newsletter'), default=False)
    enable_chat = models.BooleanField(_('enable live chat'), default=False)
    enable_reviews = models.BooleanField(_('enable reviews'), default=True)
    
    # Analytics and tracking
    view_count = models.PositiveIntegerField(_('view count'), default=0)
    unique_visitors = models.PositiveIntegerField(_('unique visitors'), default=0)
    conversion_rate = models.FloatField(_('conversion rate'), default=0.0)
    
    # Status and visibility
    status = models.CharField(_('status'), max_length=20, choices=StorefrontStatus.choices, default=StorefrontStatus.DRAFT)
    is_featured = models.BooleanField(_('is featured'), default=False)
    is_verified = models.BooleanField(_('is verified'), default=False)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    published_at = models.DateTimeField(_('published at'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Storefront')
        verbose_name_plural = _('Storefronts')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['slug']),
            models.Index(fields=['custom_domain']),
            models.Index(fields=['subdomain']),
            models.Index(fields=['status', 'is_featured']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} by {self.user.email}"
    
    @property
    def url(self):
        """Return the storefront URL."""
        if self.custom_domain:
            return f"https://{self.custom_domain}"
        elif self.subdomain:
            return f"https://{self.subdomain}.digitera.co.za"
        return f"https://digitera.co.za/store/{self.slug}"
    
    @property
    def primary_color(self):
        """Get the primary color from the color scheme."""
        return self.color_scheme.get('primary', '#3B82F6')
    
    @property
    def secondary_color(self):
        """Get the secondary color from the color scheme."""
        return self.color_scheme.get('secondary', '#6B7280')
    
    def get_product_count(self):
        """Get the number of products in this storefront."""
        return self.products.filter(status='published').count()


class StorefrontAnalytics(models.Model):
    """Daily analytics for storefronts."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    storefront = models.ForeignKey(Storefront, on_delete=models.CASCADE, related_name='analytics')
    
    date = models.DateField(_('date'))
    views = models.PositiveIntegerField(_('views'), default=0)
    unique_views = models.PositiveIntegerField(_('unique views'), default=0)
    product_views = models.PositiveIntegerField(_('product views'), default=0)
    conversions = models.PositiveIntegerField(_('conversions'), default=0)
    revenue = models.DecimalField(_('revenue'), max_digits=10, decimal_places=2, default=0)
    
    # Traffic sources
    organic_traffic = models.PositiveIntegerField(_('organic traffic'), default=0)
    social_traffic = models.PositiveIntegerField(_('social traffic'), default=0)
    direct_traffic = models.PositiveIntegerField(_('direct traffic'), default=0)
    referral_traffic = models.PositiveIntegerField(_('referral traffic'), default=0)
    
    # Device analytics
    desktop_views = models.PositiveIntegerField(_('desktop views'), default=0)
    mobile_views = models.PositiveIntegerField(_('mobile views'), default=0)
    tablet_views = models.PositiveIntegerField(_('tablet views'), default=0)
    
    # Geographic data
    top_countries = models.JSONField(_('top countries'), default=dict)
    top_cities = models.JSONField(_('top cities'), default=dict)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Storefront Analytics')
        verbose_name_plural = _('Storefront Analytics')
        unique_together = ['storefront', 'date']
        ordering = ['-date']
        indexes = [
            models.Index(fields=['storefront', 'date']),
            models.Index(fields=['date']),
        ]


class StorefrontCustomization(models.Model):
    """Extended customization options for storefronts."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    storefront = models.OneToOneField(Storefront, on_delete=models.CASCADE, related_name='customization')
    
    # Advanced styling
    custom_css = models.TextField(_('custom CSS'), blank=True, default='')
    custom_js = models.TextField(_('custom JavaScript'), blank=True, default='')
    custom_fonts = models.JSONField(_('custom fonts'), default=list)
    
    # Email templates
    email_templates = models.JSONField(_('email templates'), default=dict)
    
    # Advanced features
    password_protection = models.BooleanField(_('password protection'), default=False)
    access_password = models.CharField(_('access password'), max_length=100, blank=True, default='')
    maintenance_mode = models.BooleanField(_('maintenance mode'), default=False)
    maintenance_message = models.TextField(_('maintenance message'), blank=True, default='')
    
    # Integration settings
    webhook_urls = models.JSONField(_('webhook URLs'), default=dict)
    api_settings = models.JSONField(_('API settings'), default=dict)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('Storefront Customization')
        verbose_name_plural = _('Storefront Customizations')


class StorefrontPage(models.Model):
    """Custom pages for storefronts."""
    
    class PageType(models.TextChoices):
        PAGE = 'page', _('Static Page')
        BLOG_POST = 'blog_post', _('Blog Post')
        LANDING = 'landing', _('Landing Page')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    storefront = models.ForeignKey(Storefront, on_delete=models.CASCADE, related_name='pages')
    
    title = models.CharField(_('title'), max_length=200, default='')
    slug = models.SlugField(_('slug'), max_length=200, default='')
    content = models.TextField(_('content'), default='')
    page_type = models.CharField(_('page type'), max_length=20, choices=PageType.choices, default=PageType.PAGE)
    
    # SEO
    meta_title = models.CharField(_('meta title'), max_length=60, blank=True, default='')
    meta_description = models.TextField(_('meta description'), max_length=160, blank=True, default='')
    featured_image = models.CharField(_('featured image'), max_length=200, blank=True)
    
    # Publishing
    is_published = models.BooleanField(_('is published'), default=False)
    published_at = models.DateTimeField(_('published at'), null=True, blank=True)
    
    # Page builder content
    page_builder_data = models.JSONField(_('page builder data'), default=dict)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('Storefront Page')
        verbose_name_plural = _('Storefront Pages')
        unique_together = ['storefront', 'slug']
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['storefront', 'page_type']),
            models.Index(fields=['slug']),
            models.Index(fields=['is_published']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.storefront.name}"


class StorefrontReview(models.Model):
    """Reviews for storefronts."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    storefront = models.ForeignKey(Storefront, on_delete=models.CASCADE, related_name='storefront_reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='storefront_reviews')
    
    rating = models.PositiveIntegerField(_('rating'), choices=[(i, i) for i in range(1, 6)], default=5)
    title = models.CharField(_('review title'), max_length=200, blank=True, default='')
    content = models.TextField(_('review content'), blank=True, default='')
    
    is_verified = models.BooleanField(_('is verified'), default=False)
    is_featured = models.BooleanField(_('is featured'), default=False)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('Storefront Review')
        verbose_name_plural = _('Storefront Reviews')
        unique_together = ['storefront', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f'{self.storefront.name} - {self.rating}★ by {self.user.email}'

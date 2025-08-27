"""
Django models for the marketing app.
Contains models for marketing campaigns, packages, and promotional features.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal


class PackagePeriod(models.TextChoices):
    """Package billing period choices."""
    ONCE_OFF = 'once_off', _('Once-off')
    MONTHLY = 'monthly', _('Monthly')
    QUARTERLY = 'quarterly', _('Quarterly')
    YEARLY = 'yearly', _('Yearly')


class MarketingPackage(models.Model):
    """
    Model for marketing packages (Starter, Growth, Pro).
    """
    name = models.CharField(_('package name'), max_length=255)
    price = models.DecimalField(
        _('package price'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    period = models.CharField(
        _('billing period'),
        max_length=20,
        choices=PackagePeriod.choices,
        default=PackagePeriod.MONTHLY
    )
    description = models.TextField(_('package description'))
    
    # Package features (stored as JSON for flexibility)
    features = models.JSONField(
        _('package features'),
        default=dict,
        help_text=_('JSON object containing package features and limits')
    )
    
    # Package limits
    max_products = models.PositiveIntegerField(
        _('maximum products'),
        default=0,
        help_text=_('Maximum number of products allowed (0 = unlimited)')
    )
    max_monthly_sales = models.PositiveIntegerField(
        _('maximum monthly sales'),
        default=0,
        help_text=_('Maximum monthly sales volume (0 = unlimited)')
    )
    max_storage_gb = models.PositiveIntegerField(
        _('maximum storage (GB)'),
        default=0,
        help_text=_('Maximum storage allowance in GB (0 = unlimited)')
    )
    
    # Marketing features
    custom_domain_allowed = models.BooleanField(_('custom domain allowed'), default=False)
    advanced_analytics = models.BooleanField(_('advanced analytics'), default=False)
    priority_support = models.BooleanField(_('priority support'), default=False)
    marketplace_promotion = models.BooleanField(_('marketplace promotion'), default=False)
    
    # Package status
    is_active = models.BooleanField(_('is active'), default=True)
    is_featured = models.BooleanField(_('is featured'), default=False)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('Marketing Package')
        verbose_name_plural = _('Marketing Packages')
        db_table = 'marketing_packages'
        indexes = [
            models.Index(fields=['is_active', 'is_featured']),
            models.Index(fields=['price']),
        ]
    
    def __str__(self):
        return f"{self.name} - R{self.price} {self.period}"


class PackageStatus(models.TextChoices):
    """Creator package status choices."""
    ACTIVE = 'active', _('Active')
    EXPIRED = 'expired', _('Expired')
    CANCELLED = 'cancelled', _('Cancelled')
    SUSPENDED = 'suspended', _('Suspended')


class CreatorPackage(models.Model):
    """
    Model to track creator's purchased marketing packages.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='creator_packages'
    )
    package = models.ForeignKey(
        MarketingPackage,
        on_delete=models.PROTECT,
        related_name='creator_packages'
    )
    purchase_date = models.DateTimeField(_('purchase date'), auto_now_add=True)
    expiry_date = models.DateTimeField(
        _('expiry date'),
        null=True,
        blank=True,
        help_text=_('When the package expires (null for lifetime packages)')
    )
    status = models.CharField(
        _('package status'),
        max_length=20,
        choices=PackageStatus.choices,
        default=PackageStatus.ACTIVE
    )
    
    # Usage tracking
    products_used = models.PositiveIntegerField(_('products used'), default=0)
    storage_used_gb = models.DecimalField(
        _('storage used (GB)'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    monthly_sales_count = models.PositiveIntegerField(_('monthly sales count'), default=0)
    
    class Meta:
        verbose_name = _('Creator Package')
        verbose_name_plural = _('Creator Packages')
        db_table = 'creator_packages'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['package']),
            models.Index(fields=['expiry_date']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.package.name} - {self.status}"
    
    @property
    def is_expired(self):
        """Check if the package has expired."""
        from django.utils import timezone
        return self.expiry_date and self.expiry_date < timezone.now()
    
    def can_create_product(self):
        """Check if user can create another product within package limits."""
        if self.package.max_products == 0:  # Unlimited
            return True
        return self.products_used < self.package.max_products
    
    def can_make_sale(self):
        """Check if user can make another sale within package limits."""
        if self.package.max_monthly_sales == 0:  # Unlimited
            return True
        return self.monthly_sales_count < self.package.max_monthly_sales


class CampaignType(models.TextChoices):
    """Email campaign type choices."""
    WELCOME = 'welcome', _('Welcome Series')
    NEWSLETTER = 'newsletter', _('Newsletter')
    PRODUCT_LAUNCH = 'product_launch', _('Product Launch')
    PROMOTIONAL = 'promotional', _('Promotional')
    FOLLOW_UP = 'follow_up', _('Follow-up')
    CART_ABANDONMENT = 'cart_abandonment', _('Cart Abandonment')
    FEEDBACK = 'feedback', _('Feedback Request')
    ANNOUNCEMENT = 'announcement', _('Announcement')


class EmailCampaign(models.Model):
    """
    Model for email marketing campaigns.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='email_campaigns'
    )
    type = models.CharField(
        _('campaign type'),
        max_length=30,
        choices=CampaignType.choices
    )
    subject = models.CharField(_('email subject'), max_length=255)
    template = models.TextField(_('email template'))
    
    # Campaign targeting
    target_audience = models.JSONField(
        _('target audience'),
        default=dict,
        help_text=_('JSON object defining the target audience criteria')
    )
    
    # Campaign metrics
    recipients_count = models.PositiveIntegerField(_('recipients count'), default=0)
    opened_count = models.PositiveIntegerField(_('opened count'), default=0)
    clicked_count = models.PositiveIntegerField(_('clicked count'), default=0)
    unsubscribed_count = models.PositiveIntegerField(_('unsubscribed count'), default=0)
    
    # Campaign status
    is_scheduled = models.BooleanField(_('is scheduled'), default=False)
    scheduled_at = models.DateTimeField(_('scheduled at'), null=True, blank=True)
    sent_at = models.DateTimeField(_('sent at'), null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('Email Campaign')
        verbose_name_plural = _('Email Campaigns')
        db_table = 'email_campaigns'
        indexes = [
            models.Index(fields=['user', 'type']),
            models.Index(fields=['sent_at']),
            models.Index(fields=['scheduled_at']),
        ]
    
    def __str__(self):
        return f"{self.subject} - {self.user.email}"
    
    @property
    def open_rate(self):
        """Calculate email open rate."""
        if self.recipients_count == 0:
            return 0
        return (self.opened_count / self.recipients_count) * 100
    
    @property
    def click_rate(self):
        """Calculate email click rate."""
        if self.recipients_count == 0:
            return 0
        return (self.clicked_count / self.recipients_count) * 100
    
    @property
    def unsubscribe_rate(self):
        """Calculate unsubscribe rate."""
        if self.recipients_count == 0:
            return 0
        return (self.unsubscribed_count / self.recipients_count) * 100


class PromotionType(models.TextChoices):
    """Promotion type choices."""
    DISCOUNT_PERCENTAGE = 'discount_percentage', _('Percentage Discount')
    DISCOUNT_FIXED = 'discount_fixed', _('Fixed Amount Discount')
    FREE_SHIPPING = 'free_shipping', _('Free Shipping')
    BUY_ONE_GET_ONE = 'buy_one_get_one', _('Buy One Get One')
    LIMITED_TIME = 'limited_time', _('Limited Time Offer')


class Promotion(models.Model):
    """
    Model for promotional campaigns and discounts.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='promotions'
    )
    name = models.CharField(_('promotion name'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    type = models.CharField(
        _('promotion type'),
        max_length=30,
        choices=PromotionType.choices
    )
    
    # Promotion configuration
    discount_percentage = models.DecimalField(
        _('discount percentage'),
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    discount_amount = models.DecimalField(
        _('discount amount'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    
    # Promotion constraints
    minimum_order_amount = models.DecimalField(
        _('minimum order amount'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    maximum_uses = models.PositiveIntegerField(
        _('maximum uses'),
        null=True,
        blank=True,
        help_text=_('Maximum number of times this promotion can be used')
    )
    current_uses = models.PositiveIntegerField(_('current uses'), default=0)
    
    # Applicable products
    applicable_products = models.ManyToManyField(
        'products.Product',
        blank=True,
        related_name='promotions',
        help_text=_('Products this promotion applies to (empty = all products)')
    )
    
    # Time constraints
    valid_from = models.DateTimeField(_('valid from'))
    valid_until = models.DateTimeField(_('valid until'))
    
    # Promotion status
    is_active = models.BooleanField(_('is active'), default=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('Promotion')
        verbose_name_plural = _('Promotions')
        db_table = 'promotions'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['valid_from', 'valid_until']),
            models.Index(fields=['type']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.user.email}"
    
    @property
    def is_valid(self):
        """Check if promotion is currently valid."""
        from django.utils import timezone
        now = timezone.now()
        return (
            self.is_active and
            self.valid_from <= now <= self.valid_until and
            (self.maximum_uses is None or self.current_uses < self.maximum_uses)
        )
    
    def can_be_used(self, order_amount=None):
        """Check if promotion can be used for a given order amount."""
        if not self.is_valid:
            return False
        
        if self.minimum_order_amount and order_amount:
            return order_amount >= self.minimum_order_amount
        
        return True

"""
Django models for the analytics app.
Contains models for tracking user behavior, metrics, and business intelligence.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal


class MetricType(models.TextChoices):
    """Metric type choices for analytics tracking."""
    PAGE_VIEW = 'page_view', _('Page View')
    PRODUCT_VIEW = 'product_view', _('Product View')
    STOREFRONT_VIEW = 'storefront_view', _('Storefront View')
    PURCHASE = 'purchase', _('Purchase')
    SIGNUP = 'signup', _('User Signup')
    LOGIN = 'login', _('User Login')
    DOWNLOAD = 'download', _('File Download')
    SUBSCRIPTION_START = 'subscription_start', _('Subscription Start')
    SUBSCRIPTION_CANCEL = 'subscription_cancel', _('Subscription Cancel')
    REVENUE = 'revenue', _('Revenue')
    COMMISSION = 'commission', _('Commission')
    REFUND = 'refund', _('Refund')
    AFFILIATE_CLICK = 'affiliate_click', _('Affiliate Click')
    EMAIL_OPEN = 'email_open', _('Email Open')
    EMAIL_CLICK = 'email_click', _('Email Click')


class AnalyticsLog(models.Model):
    """
    Model for tracking various analytics metrics and user behavior.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='analytics_logs'
    )
    metric_type = models.CharField(
        _('metric type'),
        max_length=30,
        choices=MetricType.choices
    )
    value = models.DecimalField(
        _('metric value'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('1.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    timestamp = models.DateTimeField(_('timestamp'), auto_now_add=True)
    details = models.JSONField(
        _('additional details'),
        default=dict,
        help_text=_('JSON object containing additional metric data')
    )
    
    class Meta:
        verbose_name = _('Analytics Log')
        verbose_name_plural = _('Analytics Logs')
        db_table = 'analytics_logs'
        indexes = [
            models.Index(fields=['user', 'metric_type', 'timestamp']),
            models.Index(fields=['metric_type', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        user_info = self.user.email if self.user else 'Anonymous'
        return f"{self.metric_type} - {user_info} - {self.timestamp}"


class DashboardMetric(models.Model):
    """
    Model for storing pre-calculated dashboard metrics for performance.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dashboard_metrics'
    )
    
    # Revenue metrics
    total_revenue = models.DecimalField(
        _('total revenue'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    monthly_revenue = models.DecimalField(
        _('monthly revenue'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    daily_revenue = models.DecimalField(
        _('daily revenue'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Sales metrics
    total_sales = models.PositiveIntegerField(_('total sales'), default=0)
    monthly_sales = models.PositiveIntegerField(_('monthly sales'), default=0)
    daily_sales = models.PositiveIntegerField(_('daily sales'), default=0)
    
    # Traffic metrics
    total_views = models.PositiveIntegerField(_('total views'), default=0)
    monthly_views = models.PositiveIntegerField(_('monthly views'), default=0)
    daily_views = models.PositiveIntegerField(_('daily views'), default=0)
    
    # Conversion metrics
    conversion_rate = models.DecimalField(
        _('conversion rate'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_('Conversion rate percentage')
    )
    
    # Top performing product
    top_product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='top_performer_metrics'
    )
    
    # Subscription metrics
    active_subscribers = models.PositiveIntegerField(_('active subscribers'), default=0)
    churn_rate = models.DecimalField(
        _('churn rate'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_('Monthly churn rate percentage')
    )
    
    # Last updated timestamp
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    calculation_date = models.DateField(_('calculation date'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Dashboard Metric')
        verbose_name_plural = _('Dashboard Metrics')
        db_table = 'dashboard_metrics'
        unique_together = ['user', 'calculation_date']
        indexes = [
            models.Index(fields=['user', 'calculation_date']),
            models.Index(fields=['updated_at']),
        ]
    
    def __str__(self):
        return f"Metrics for {self.user.email} - {self.calculation_date}"


class TrafficSource(models.TextChoices):
    """Traffic source choices."""
    DIRECT = 'direct', _('Direct')
    SEARCH = 'search', _('Search Engine')
    SOCIAL = 'social', _('Social Media')
    EMAIL = 'email', _('Email')
    REFERRAL = 'referral', _('Referral')
    AFFILIATE = 'affiliate', _('Affiliate')
    ADVERTISEMENT = 'advertisement', _('Advertisement')
    UNKNOWN = 'unknown', _('Unknown')


class TrafficAnalytics(models.Model):
    """
    Model for tracking traffic sources and user acquisition.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='traffic_analytics'
    )
    source = models.CharField(
        _('traffic source'),
        max_length=20,
        choices=TrafficSource.choices,
        default=TrafficSource.UNKNOWN
    )
    medium = models.CharField(
        _('traffic medium'),
        max_length=50,
        blank=True,
        help_text=_('Traffic medium (e.g., organic, cpc, social)')
    )
    campaign = models.CharField(
        _('campaign name'),
        max_length=100,
        blank=True,
        help_text=_('Marketing campaign name')
    )
    referrer_url = models.URLField(
        _('referrer URL'),
        blank=True,
        help_text=_('URL of the referring site')
    )
    landing_page = models.CharField(
        _('landing page'),
        max_length=255,
        help_text=_('First page visited by the user')
    )
    session_duration = models.PositiveIntegerField(
        _('session duration'),
        default=0,
        help_text=_('Session duration in seconds')
    )
    pages_visited = models.PositiveIntegerField(
        _('pages visited'),
        default=1,
        help_text=_('Number of pages visited in this session')
    )
    converted = models.BooleanField(
        _('converted'),
        default=False,
        help_text=_('Whether this session resulted in a conversion (purchase)')
    )
    timestamp = models.DateTimeField(_('timestamp'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Traffic Analytics')
        verbose_name_plural = _('Traffic Analytics')
        db_table = 'traffic_analytics'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['source', 'medium']),
            models.Index(fields=['converted']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.source}/{self.medium} - {self.user.email} - {self.timestamp}"


class RevenueAnalytics(models.Model):
    """
    Model for detailed revenue analytics and reporting.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='revenue_analytics'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='revenue_analytics'
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='revenue_analytics'
    )
    
    # Revenue breakdown
    gross_revenue = models.DecimalField(
        _('gross revenue'),
        max_digits=10,
        decimal_places=2
    )
    platform_fee = models.DecimalField(
        _('platform fee'),
        max_digits=10,
        decimal_places=2
    )
    payment_fee = models.DecimalField(
        _('payment processing fee'),
        max_digits=10,
        decimal_places=2
    )
    vat_amount = models.DecimalField(
        _('VAT amount'),
        max_digits=10,
        decimal_places=2
    )
    net_revenue = models.DecimalField(
        _('net revenue'),
        max_digits=10,
        decimal_places=2
    )
    
    # Analytics metadata
    currency = models.CharField(_('currency'), max_length=3, default='ZAR')
    fee_type = models.CharField(
        _('fee type'),
        max_length=20,
        choices=[('direct_sales', 'Direct Sales'), ('marketplace_sales', 'Marketplace Sales')]
    )
    timestamp = models.DateTimeField(_('timestamp'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Revenue Analytics')
        verbose_name_plural = _('Revenue Analytics')
        db_table = 'revenue_analytics'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['product', 'timestamp']),
            models.Index(fields=['fee_type']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"Revenue: {self.net_revenue} for {self.product.name} - {self.timestamp}"


class ConversionFunnel(models.Model):
    """
    Model for tracking conversion funnel analytics.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversion_funnels'
    )
    
    # Funnel stages
    visitors = models.PositiveIntegerField(_('unique visitors'), default=0)
    product_views = models.PositiveIntegerField(_('product views'), default=0)
    add_to_cart = models.PositiveIntegerField(_('add to cart'), default=0)
    checkout_started = models.PositiveIntegerField(_('checkout started'), default=0)
    purchases = models.PositiveIntegerField(_('completed purchases'), default=0)
    
    # Calculated conversion rates
    view_to_cart_rate = models.DecimalField(
        _('view to cart rate'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00')
    )
    cart_to_checkout_rate = models.DecimalField(
        _('cart to checkout rate'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00')
    )
    checkout_to_purchase_rate = models.DecimalField(
        _('checkout to purchase rate'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00')
    )
    overall_conversion_rate = models.DecimalField(
        _('overall conversion rate'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Time period
    date = models.DateField(_('date'))
    
    class Meta:
        verbose_name = _('Conversion Funnel')
        verbose_name_plural = _('Conversion Funnels')
        db_table = 'conversion_funnels'
        unique_together = ['user', 'date']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['date']),
        ]
    
    def __str__(self):
        return f"Funnel for {self.user.email} - {self.date}"
    
    def calculate_conversion_rates(self):
        """Calculate conversion rates for the funnel."""
        if self.product_views > 0:
            self.view_to_cart_rate = (self.add_to_cart / self.product_views) * 100
        
        if self.add_to_cart > 0:
            self.cart_to_checkout_rate = (self.checkout_started / self.add_to_cart) * 100
        
        if self.checkout_started > 0:
            self.checkout_to_purchase_rate = (self.purchases / self.checkout_started) * 100
        
        if self.visitors > 0:
            self.overall_conversion_rate = (self.purchases / self.visitors) * 100

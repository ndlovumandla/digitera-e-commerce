"""
Django models for the payments app.
Contains models for payment processing, gateways, and financial operations.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal


class PaymentGateway(models.TextChoices):
    """Payment gateway choices for South African market."""
    STRIPE = 'stripe', _('Stripe')
    PAYFAST = 'payfast', _('PayFast')
    OZOW = 'ozow', _('Ozow')
    PAYGATE = 'paygate', _('PayGate')
    PEACH_PAYMENTS = 'peach_payments', _('Peach Payments')
    YOCO = 'yoco', _('Yoco')


class PaymentStatus(models.TextChoices):
    """Payment status choices."""
    PENDING = 'pending', _('Pending')
    PROCESSING = 'processing', _('Processing')
    COMPLETED = 'completed', _('Completed')
    FAILED = 'failed', _('Failed')
    CANCELLED = 'cancelled', _('Cancelled')
    REFUNDED = 'refunded', _('Refunded')
    PARTIALLY_REFUNDED = 'partially_refunded', _('Partially Refunded')


class Payment(models.Model):
    """
    Model for tracking payments and transactions.
    """
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='payments'
    )
    gateway = models.CharField(
        _('payment gateway'),
        max_length=20,
        choices=PaymentGateway.choices,
        default=PaymentGateway.STRIPE
    )
    transaction_id = models.CharField(
        _('transaction ID'),
        max_length=255,
        unique=True,
        help_text=_('Unique transaction ID from the payment gateway')
    )
    amount = models.DecimalField(
        _('payment amount'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    status = models.CharField(
        _('payment status'),
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Payment')
        verbose_name_plural = _('Payments')
        db_table = 'payments'
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['gateway', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Payment {self.transaction_id} - {self.gateway} - {self.status}"
    
    @property
    def is_successful(self):
        """Check if payment was successful."""
        return self.status == PaymentStatus.COMPLETED


class PayoutStatus(models.TextChoices):
    """Payout status choices."""
    PENDING = 'pending', _('Pending')
    PROCESSING = 'processing', _('Processing')
    COMPLETED = 'completed', _('Completed')
    FAILED = 'failed', _('Failed')
    CANCELLED = 'cancelled', _('Cancelled')


class Payout(models.Model):
    """
    Model for creator payouts and withdrawals.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payouts'
    )
    amount = models.DecimalField(
        _('payout amount'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    gateway = models.CharField(
        _('payout gateway'),
        max_length=20,
        choices=PaymentGateway.choices,
        default=PaymentGateway.STRIPE
    )
    status = models.CharField(
        _('payout status'),
        max_length=20,
        choices=PayoutStatus.choices,
        default=PayoutStatus.PENDING
    )
    fee = models.DecimalField(
        _('payout fee'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_('Fee charged for the payout')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Payout')
        verbose_name_plural = _('Payouts')
        db_table = 'payouts'
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['gateway']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Payout to {self.user.email} - {self.amount} - {self.status}"
    
    @property
    def net_amount(self):
        """Calculate net payout amount after fees."""
        return self.amount - self.fee


class Currency(models.Model):
    """
    Model for managing currency exchange rates.
    """
    code = models.CharField(
        _('currency code'),
        max_length=3,
        primary_key=True,
        help_text=_('ISO 4217 currency code (e.g., USD, EUR, GBP)')
    )
    conversion_rate_to_zar = models.DecimalField(
        _('conversion rate to ZAR'),
        max_digits=10,
        decimal_places=4,
        help_text=_('Exchange rate from this currency to South African Rand')
    )
    
    class Meta:
        verbose_name = _('Currency')
        verbose_name_plural = _('Currencies')
        db_table = 'currencies'
    
    def __str__(self):
        return self.code


class VATRate(models.Model):
    """
    Model for managing VAT rates by country and time period.
    """
    country = models.CharField(
        _('country code'),
        max_length=2,
        help_text=_('ISO 3166-1 alpha-2 country code')
    )
    rate = models.DecimalField(
        _('VAT rate'),
        max_digits=5,
        decimal_places=2,
        help_text=_('VAT rate percentage')
    )
    effective_from = models.DateField(
        _('effective from'),
        help_text=_('Date when this VAT rate becomes effective')
    )
    
    class Meta:
        verbose_name = _('VAT Rate')
        verbose_name_plural = _('VAT Rates')
        db_table = 'vat_rates'
        indexes = [
            models.Index(fields=['country', 'effective_from']),
        ]
        unique_together = ['country', 'effective_from']
    
    def __str__(self):
        return f"{self.country} - {self.rate}% (from {self.effective_from})"


class FraudCheckType(models.TextChoices):
    """Fraud check type choices."""
    EMAIL_VERIFICATION = 'email_verification', _('Email Verification')
    IP_GEOLOCATION = 'ip_geolocation', _('IP Geolocation')
    VELOCITY_CHECK = 'velocity_check', _('Velocity Check')
    CARD_VERIFICATION = 'card_verification', _('Card Verification')
    BEHAVIORAL_ANALYSIS = 'behavioral_analysis', _('Behavioral Analysis')
    BLACKLIST_CHECK = 'blacklist_check', _('Blacklist Check')


class FraudLog(models.Model):
    """
    Model for logging fraud detection checks and results.
    """
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='fraud_logs'
    )
    check_type = models.CharField(
        _('fraud check type'),
        max_length=30,
        choices=FraudCheckType.choices
    )
    flag = models.BooleanField(
        _('flagged as suspicious'),
        default=False,
        help_text=_('Whether this check flagged the order as potentially fraudulent')
    )
    details = models.TextField(
        _('check details'),
        help_text=_('Additional details about the fraud check results')
    )
    timestamp = models.DateTimeField(_('timestamp'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('Fraud Log')
        verbose_name_plural = _('Fraud Logs')
        db_table = 'fraud_logs'
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['check_type', 'flag']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        flag_status = "FLAGGED" if self.flag else "CLEAN"
        return f"Fraud Check: {self.check_type} - {flag_status} - Order #{self.order.id}"


class Affiliate(models.Model):
    """
    Model for managing affiliate relationships.
    """
    referrer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='referred_affiliates'
    )
    referred = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='referrer_affiliates'
    )
    commission_rate = models.DecimalField(
        _('commission rate'),
        max_digits=5,
        decimal_places=2,
        help_text=_('Commission rate percentage for affiliate sales')
    )
    
    class Meta:
        verbose_name = _('Affiliate')
        verbose_name_plural = _('Affiliates')
        db_table = 'affiliates'
        unique_together = ['referrer', 'referred']
        indexes = [
            models.Index(fields=['referrer']),
            models.Index(fields=['referred']),
        ]
    
    def __str__(self):
        return f"{self.referrer.email} referred {self.referred.email} ({self.commission_rate}%)"


class AffiliateCommission(models.Model):
    """
    Model for tracking affiliate commissions.
    """
    affiliate = models.ForeignKey(
        Affiliate,
        on_delete=models.CASCADE,
        related_name='commissions'
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='affiliate_commissions'
    )
    commission_amount = models.DecimalField(
        _('commission amount'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    paid_at = models.DateTimeField(_('paid at'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Affiliate Commission')
        verbose_name_plural = _('Affiliate Commissions')
        db_table = 'affiliate_commissions'
        indexes = [
            models.Index(fields=['affiliate']),
            models.Index(fields=['order']),
            models.Index(fields=['paid_at']),
        ]
    
    def __str__(self):
        return f"Commission {self.commission_amount} for {self.affiliate.referrer.email}"
    
    @property
    def is_paid(self):
        """Check if commission has been paid."""
        return self.paid_at is not None

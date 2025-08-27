"""
Enhanced Orders models for Digitera Platform.    order_number = models.CharField(_('order number'), max_length=20, unique=True, blank=True)
    
    # Customer information
    buyer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    guest_email = models.EmailField(_('guest email'), blank=True)
    
    # Billing information
    billing_name = models.CharField(_('billing name'), max_length=200, default='')
    billing_email = models.EmailField(_('billing email'), blank=True)
    billing_phone = models.CharField(_('billing phone'), max_length=20, blank=True, default='')transaction types, fee calculation, VAT compliance, and dispute resolution.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal
import uuid

User = get_user_model()


class Cart(models.Model):
    """Shopping cart for users and guests."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='cart')
    session_key = models.CharField(_('session key'), max_length=40, null=True, blank=True, db_index=True)
    
    created_at = models.DateTimeField(_('created at'), default=timezone.now)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('Cart')
        verbose_name_plural = _('Carts')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['session_key']),
        ]
    
    def __str__(self):
        return f"Cart for {self.user.email if self.user else f'Guest {self.session_key}'}"
    
    @property
    def total_items(self):
        """Get total number of items in cart."""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def total_amount(self):
        """Get total amount for all items in cart."""
        return sum(item.total_price for item in self.items.all())
    
    def add_item(self, product, quantity=1):
        """Add or update item in cart."""
        cart_item, created = self.items.get_or_create(
            product=product,
            defaults={'quantity': quantity, 'unit_price': product.price}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        return cart_item
    
    def remove_item(self, product):
        """Remove item from cart."""
        self.items.filter(product=product).delete()
    
    def clear(self):
        """Clear all items from cart."""
        self.items.all().delete()


class CartItem(models.Model):
    """Items in a shopping cart."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(_('quantity'), default=1)
    unit_price = models.DecimalField(_('unit price'), max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(_('created at'), default=timezone.now)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('Cart Item')
        verbose_name_plural = _('Cart Items')
        unique_together = ['cart', 'product']
        indexes = [
            models.Index(fields=['cart']),
            models.Index(fields=['product']),
        ]
    
    def __str__(self):
        return f"{self.quantity}x {self.product.name}"
    
    @property
    def total_price(self):
        """Get total price for this cart item."""
        return self.quantity * self.unit_price
    
    def save(self, *args, **kwargs):
        if not self.unit_price:
            self.unit_price = self.product.price
        super().save(*args, **kwargs)


def generate_dispute_id():
    """Generate unique dispute ID."""
    return f"DSP-{uuid.uuid4().hex[:8].upper()}"


def generate_invoice_number():
    """Generate unique invoice number."""
    return f"INV-{uuid.uuid4().hex[:8].upper()}"


def generate_order_number():
    """Generate unique order number."""
    return f"ORD-{uuid.uuid4().hex[:8].upper()}"


class Order(models.Model):
    """Enhanced order model with comprehensive transaction handling."""
    
    class OrderStatus(models.TextChoices):
        PENDING = 'pending', _('Pending Payment')
        PROCESSING = 'processing', _('Processing')
        COMPLETED = 'completed', _('Completed')
        CANCELLED = 'cancelled', _('Cancelled')
        REFUNDED = 'refunded', _('Refunded')
        FAILED = 'failed', _('Failed')
        DISPUTED = 'disputed', _('Disputed')
    
    class TransactionType(models.TextChoices):
        DIRECT = 'direct', _('Direct Sale (5% fee)')
        MARKETPLACE = 'marketplace', _('Marketplace Sale (30% fee)')
    
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        AUTHORIZED = 'authorized', _('Authorized')
        CAPTURED = 'captured', _('Captured')
        FAILED = 'failed', _('Failed')
        REFUNDED = 'refunded', _('Refunded')
        PARTIALLY_REFUNDED = 'partially_refunded', _('Partially Refunded')
    
    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(_('order number'), max_length=20, unique=True, blank=True)
    
    # Customer information
    buyer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    guest_email = models.EmailField(_('guest email'), blank=True, default='')
    
    # Billing information
    billing_name = models.CharField(_('billing name'), max_length=200, default='')
    billing_email = models.EmailField(_('billing email'), default='')
    billing_phone = models.CharField(_('billing phone'), max_length=20, blank=True, default='')
    billing_address = models.JSONField(_('billing address'), default=dict)
    
    # Transaction details
    transaction_type = models.CharField(_('transaction type'), max_length=20, choices=TransactionType.choices, default=TransactionType.DIRECT)
    currency = models.CharField(_('currency'), max_length=3, default='ZAR')
    
    # Amounts and fees
    subtotal = models.DecimalField(_('subtotal'), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    tax_amount = models.DecimalField(_('tax amount'), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(_('total amount'), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Fee calculations
    platform_fee_rate = models.DecimalField(_('platform fee rate'), max_digits=5, decimal_places=4, default=Decimal('0.05'))
    platform_fee_amount = models.DecimalField(_('platform fee amount'), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    processor_fee_amount = models.DecimalField(_('processor fee amount'), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # VAT and SARS compliance
    vat_rate = models.DecimalField(_('VAT rate'), max_digits=5, decimal_places=4, default=Decimal('0.15'))
    vat_amount = models.DecimalField(_('VAT amount'), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    vat_number = models.CharField(_('VAT number'), max_length=20, blank=True, default='')
    is_vat_registered = models.BooleanField(_('is VAT registered'), default=False)
    
    # Multi-currency support
    original_currency = models.CharField(_('original currency'), max_length=3, blank=True, default='')
    original_amount = models.DecimalField(_('original amount'), max_digits=12, decimal_places=2, null=True, blank=True)
    exchange_rate = models.DecimalField(_('exchange rate'), max_digits=10, decimal_places=6, null=True, blank=True)
    
    # Status tracking
    status = models.CharField(_('order status'), max_length=20, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    payment_status = models.CharField(_('payment status'), max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    
    # Payment information
    payment_method = models.CharField(_('payment method'), max_length=50, blank=True, default='')
    payment_reference = models.CharField(_('payment reference'), max_length=100, blank=True, default='')
    payment_gateway = models.CharField(_('payment gateway'), max_length=50, blank=True, default='')
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), default=timezone.now)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    paid_at = models.DateTimeField(_('paid at'), null=True, blank=True)
    shipped_at = models.DateTimeField(_('shipped at'), null=True, blank=True)
    completed_at = models.DateTimeField(_('completed at'), null=True, blank=True)
    
    # Notes and metadata
    notes = models.TextField(_('notes'), blank=True, default='')
    metadata = models.JSONField(_('metadata'), default=dict)
    
    class Meta:
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['buyer', 'status']),
            models.Index(fields=['order_number']),
            models.Index(fields=['status', 'payment_status']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['guest_email']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = generate_order_number()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Order {self.order_number} - {self.get_customer_email()}"
    
    def get_customer_email(self):
        """Get customer email (buyer or guest)."""
        return self.buyer.email if self.buyer else self.guest_email
    
    def calculate_fees(self):
        """Calculate all fees for this order."""
        # Platform fee based on transaction type
        if self.transaction_type == self.TransactionType.DIRECT:
            self.platform_fee_rate = Decimal('0.05')  # 5%
        else:
            self.platform_fee_rate = Decimal('0.30')  # 30%
        
        self.platform_fee_amount = self.subtotal * self.platform_fee_rate
        
        # Calculate VAT
        if self.is_vat_registered:
            self.vat_amount = self.subtotal * self.vat_rate
        
        # Update total
        self.total_amount = self.subtotal + self.vat_amount
        
    def save(self, *args, **kwargs):
        """Override save to generate order number and calculate fees."""
        if not self.order_number:
            # Generate order number (simplified)
            import random
            self.order_number = f"DIG{random.randint(100000, 999999)}"
        
        if not self.pk:  # New order
            self.calculate_fees()
        
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """Items within an order."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT, related_name='order_items')
    
    # Product details at time of purchase
    product_name = models.CharField(_('product name'), max_length=200, default='')
    product_sku = models.CharField(_('product SKU'), max_length=100, blank=True, default='')
    quantity = models.PositiveIntegerField(_('quantity'), default=1)
    unit_price = models.DecimalField(_('unit price'), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_price = models.DecimalField(_('total price'), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Digital delivery information
    download_links = models.JSONField(_('download links'), default=list)
    license_key = models.CharField(_('license key'), max_length=200, blank=True, default='')
    access_granted = models.BooleanField(_('access granted'), default=False)
    access_expires_at = models.DateTimeField(_('access expires at'), null=True, blank=True)
    download_count = models.PositiveIntegerField(_('download count'), default=0)
    
    # Fulfillment tracking
    is_fulfilled = models.BooleanField(_('is fulfilled'), default=False)
    fulfilled_at = models.DateTimeField(_('fulfilled at'), null=True, blank=True)
    
    created_at = models.DateTimeField(_('created at'), default=timezone.now)
    
    class Meta:
        verbose_name = _('Order Item')
        verbose_name_plural = _('Order Items')
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['product']),
            models.Index(fields=['is_fulfilled']),
        ]
    
    def __str__(self):
        return f"{self.quantity}x {self.product_name} in {self.order.order_number}"


class Subscription(models.Model):
    """Recurring subscription orders."""
    
    class SubscriptionStatus(models.TextChoices):
        ACTIVE = 'active', _('Active')
        PAUSED = 'paused', _('Paused')
        CANCELLED = 'cancelled', _('Cancelled')
        EXPIRED = 'expired', _('Expired')
        PAST_DUE = 'past_due', _('Past Due')
    
    class BillingInterval(models.TextChoices):
        WEEKLY = 'weekly', _('Weekly')
        MONTHLY = 'monthly', _('Monthly')
        QUARTERLY = 'quarterly', _('Quarterly')
        ANNUALLY = 'annually', _('Annually')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT, related_name='subscriptions')
    
    # Subscription details
    subscription_id = models.CharField(_('subscription ID'), max_length=50, unique=True, blank=True)
    status = models.CharField(_('status'), max_length=20, choices=SubscriptionStatus.choices, default=SubscriptionStatus.ACTIVE)
    billing_interval = models.CharField(_('billing interval'), max_length=20, choices=BillingInterval.choices, default=BillingInterval.MONTHLY)
    
    # Pricing
    amount = models.DecimalField(_('amount'), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(_('currency'), max_length=3, default='ZAR')
    
    # Dates
    start_date = models.DateTimeField(_('start date'), default=timezone.now)
    current_period_start = models.DateTimeField(_('current period start'), default=timezone.now)
    current_period_end = models.DateTimeField(_('current period end'), default=timezone.now)
    next_bill_date = models.DateTimeField(_('next billing date'), default=timezone.now)
    trial_end = models.DateTimeField(_('trial end'), null=True, blank=True)
    cancelled_at = models.DateTimeField(_('cancelled at'), null=True, blank=True)
    
    # Tracking
    failed_payment_attempts = models.PositiveIntegerField(_('failed payment attempts'), default=0)
    
    created_at = models.DateTimeField(_('created at'), default=timezone.now)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('Subscription')
        verbose_name_plural = _('Subscriptions')
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['subscription_id']),
            models.Index(fields=['next_bill_date']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Subscription {self.subscription_id} - {self.user.email}"


class Dispute(models.Model):
    """Order dispute and resolution tracking."""
    
    class DisputeStatus(models.TextChoices):
        OPEN = 'open', _('Open')
        IN_REVIEW = 'in_review', _('In Review')
        RESOLVED = 'resolved', _('Resolved')
        ESCALATED = 'escalated', _('Escalated')
        CLOSED = 'closed', _('Closed')
    
    class DisputeType(models.TextChoices):
        CHARGEBACK = 'chargeback', _('Chargeback')
        REFUND_REQUEST = 'refund_request', _('Refund Request')
        PRODUCT_ISSUE = 'product_issue', _('Product Issue')
        DELIVERY_ISSUE = 'delivery_issue', _('Delivery Issue')
        BILLING_ISSUE = 'billing_issue', _('Billing Issue')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='disputes')
    dispute_id = models.CharField(_('dispute ID'), max_length=50, unique=True, blank=True, default="")
    
    # Dispute details
    dispute_type = models.CharField(_('dispute type'), max_length=20, choices=DisputeType.choices, default=DisputeType.PRODUCT_ISSUE)
    status = models.CharField(_('status'), max_length=20, choices=DisputeStatus.choices, default=DisputeStatus.OPEN)
    reason = models.TextField(_('reason'), default='Customer dispute')
    customer_message = models.TextField(_('customer message'), blank=True, default='')
    
    # Resolution
    resolution = models.TextField(_('resolution'), blank=True, default='')
    refund_amount = models.DecimalField(_('refund amount'), max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Timestamps
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    resolved_at = models.DateTimeField(_('resolved at'), null=True, blank=True)
    
    # Assignment
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_disputes')
    
    def save(self, *args, **kwargs):
        if not self.dispute_id:
            self.dispute_id = generate_dispute_id()
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = _('Dispute')
        verbose_name_plural = _('Disputes')
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['dispute_id']),
            models.Index(fields=['status']),
            models.Index(fields=['assigned_to']),
        ]
    
    def __str__(self):
        return f"Dispute {self.dispute_id} - {self.order.order_number}"


class Invoice(models.Model):
    """SARS compliant invoices."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='invoice')
    
    # Invoice details
    invoice_number = models.CharField(_('invoice number'), max_length=50, unique=True, blank=True, default='')
    due_date = models.DateTimeField(_('due date'), null=True, blank=True)
    
    # SARS compliance fields
    tax_invoice = models.BooleanField(_('tax invoice'), default=True)
    vat_vendor_number = models.CharField(_('VAT vendor number'), max_length=20, blank=True, default='')
    
    # Amounts
    subtotal = models.DecimalField(_('subtotal'), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    vat_amount = models.DecimalField(_('VAT amount'), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(_('total amount'), max_digits=12, decimal_places=2, default=Decimal('0.00'))
    
    # Document storage
    pdf_url = models.CharField(_('PDF URL'), max_length=200, blank=True, default='')
    pdf_generated = models.BooleanField(_('PDF generated'), default=False)
    
    # Notes
    notes = models.TextField(_('notes'), blank=True, default='')
    
    # Use generated_at instead of created_at to match existing migration
    generated_at = models.DateTimeField(_('generated at'), default=timezone.now)
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = generate_invoice_number()
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = _('Invoice')
        verbose_name_plural = _('Invoices')
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['generated_at']),
            models.Index(fields=['order']),
        ]
    
    def __str__(self):
        return f"Invoice {self.invoice_number} for {self.order.order_number}"


class RefundRequest(models.Model):
    """Refund request tracking."""
    
    class RefundStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        APPROVED = 'approved', _('Approved')
        REJECTED = 'rejected', _('Rejected')
        PROCESSED = 'processed', _('Processed')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='refund_requests')
    
    # Refund details
    amount = models.DecimalField(_('refund amount'), max_digits=10, decimal_places=2, default=Decimal('0.00'))
    reason = models.TextField(_('refund reason'), default='')
    status = models.CharField(_('status'), max_length=20, choices=RefundStatus.choices, default=RefundStatus.PENDING)
    
    # Processing
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_refunds')
    processor_reference = models.CharField(_('processor reference'), max_length=100, blank=True, default='')
    
    # Timestamps
    requested_at = models.DateTimeField(_('requested at'), default=timezone.now)
    processed_at = models.DateTimeField(_('processed at'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Refund Request')
        verbose_name_plural = _('Refund Requests')
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['status']),
            models.Index(fields=['requested_at']),
        ]
    
    def __str__(self):
        return f"Refund {self.amount} for {self.order.order_number}"


class OrderStatusHistory(models.Model):
    """Track order status changes."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    
    previous_status = models.CharField(_('previous status'), max_length=20, blank=True, default='')
    new_status = models.CharField(_('new status'), max_length=20, default='')
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reason = models.TextField(_('reason'), blank=True, default='')
    
    created_at = models.DateTimeField(_('created at'), default=timezone.now)
    
    class Meta:
        verbose_name = _('Order Status History')
        verbose_name_plural = _('Order Status Histories')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.order.order_number}: {self.previous_status} → {self.new_status}"

"""
DRF Serializers for Orders models.
Includes transaction processing, fee calculation, and VAT compliance.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from decimal import Decimal
from .models import (
    Order, OrderItem, Subscription, Dispute, Invoice,
    RefundRequest, OrderStatusHistory
)

User = get_user_model()


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items."""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_slug = serializers.CharField(source='product.slug', read_only=True)
    product_image = serializers.CharField(source='product.featured_image', read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_name', 'product_slug', 'product_image',
            'product_name', 'product_sku', 'quantity', 'unit_price',
            'total_price', 'download_links', 'license_key',
            'access_granted', 'access_expires_at', 'is_fulfilled',
            'fulfilled_at', 'created_at'
        ]
        read_only_fields = [
            'id', 'total_price', 'download_links', 'license_key',
            'access_granted', 'access_expires_at', 'is_fulfilled',
            'fulfilled_at', 'created_at'
        ]
    
    def validate(self, data):
        """Validate order item data."""
        product = data.get('product')
        quantity = data.get('quantity', 1)
        
        if product and not product.is_active:
            raise serializers.ValidationError("Product is not available.")
        
        if quantity <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0.")
        
        return data


class OrderStatusHistorySerializer(serializers.ModelSerializer):
    """Serializer for order status history."""
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)
    
    class Meta:
        model = OrderStatusHistory
        fields = [
            'id', 'previous_status', 'new_status', 'changed_by',
            'changed_by_name', 'reason', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class OrderSerializer(serializers.ModelSerializer):
    """Main serializer for orders with comprehensive transaction handling."""
    buyer_email = serializers.SerializerMethodField()
    buyer_name = serializers.SerializerMethodField()
    items = OrderItemSerializer(many=True, read_only=True)
    status_history = OrderStatusHistorySerializer(many=True, read_only=True)
    
    # Computed fields
    item_count = serializers.SerializerMethodField()
    net_amount = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'buyer', 'guest_email',
            'buyer_email', 'buyer_name',
            
            # Billing information
            'billing_name', 'billing_email', 'billing_phone', 'billing_address',
            
            # Transaction details
            'transaction_type', 'currency',
            
            # Amounts and fees
            'subtotal', 'tax_amount', 'total_amount',
            'platform_fee_rate', 'platform_fee_amount', 'processor_fee_amount',
            
            # VAT and compliance
            'vat_rate', 'vat_amount', 'vat_number', 'is_vat_registered',
            
            # Multi-currency
            'original_currency', 'original_amount', 'exchange_rate',
            
            # Status
            'status', 'payment_status',
            
            # Payment info
            'payment_method', 'payment_reference', 'payment_gateway',
            
            # Timestamps
            'created_at', 'updated_at', 'paid_at', 'shipped_at', 'completed_at',
            
            # Notes and metadata
            'notes', 'metadata',
            
            # Related data
            'items', 'status_history',
            
            # Computed fields
            'item_count', 'net_amount'
        ]
        read_only_fields = [
            'id', 'order_number', 'platform_fee_rate', 'platform_fee_amount',
            'processor_fee_amount', 'vat_amount', 'tax_amount', 'total_amount',
            'created_at', 'updated_at', 'paid_at', 'shipped_at', 'completed_at'
        ]
    
    def get_buyer_email(self, obj):
        return obj.get_customer_email()
    
    def get_buyer_name(self, obj):
        if obj.buyer:
            return obj.buyer.get_full_name()
        return obj.billing_name
    
    def get_item_count(self, obj):
        return obj.items.count()
    
    def get_net_amount(self, obj):
        """Calculate net amount after fees."""
        return obj.subtotal - obj.platform_fee_amount - obj.processor_fee_amount
    
    def validate(self, data):
        """Validate order data."""
        # Ensure either buyer or guest_email is provided
        buyer = data.get('buyer')
        guest_email = data.get('guest_email')
        
        if not buyer and not guest_email:
            raise serializers.ValidationError(
                "Either buyer or guest_email must be provided."
            )
        
        if buyer and guest_email:
            raise serializers.ValidationError(
                "Cannot have both buyer and guest_email."
            )
        
        return data


class OrderCreateSerializer(serializers.ModelSerializer):
    """Specialized serializer for creating orders."""
    items = OrderItemSerializer(many=True)
    
    class Meta:
        model = Order
        fields = [
            'buyer', 'guest_email', 'billing_name', 'billing_email',
            'billing_phone', 'billing_address', 'transaction_type',
            'currency', 'is_vat_registered', 'vat_number',
            'payment_method', 'notes', 'metadata', 'items'
        ]
    
    @transaction.atomic
    def create(self, validated_data):
        """Create order with items and calculate all fees."""
        items_data = validated_data.pop('items')
        
        # Create order
        order = Order.objects.create(**validated_data)
        
        # Calculate subtotal from items
        subtotal = Decimal('0.00')
        
        # Create order items
        for item_data in items_data:
            product = item_data['product']
            quantity = item_data.get('quantity', 1)
            unit_price = product.sale_price or product.price
            total_price = unit_price * quantity
            
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                product_sku=getattr(product, 'sku', ''),
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price
            )
            
            subtotal += total_price
        
        # Update order with calculated amounts
        order.subtotal = subtotal
        order.calculate_fees()
        order.save()
        
        return order


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for subscription management."""
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    # Computed fields
    is_trial = serializers.SerializerMethodField()
    days_until_renewal = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'user_email', 'user_name',
            'product', 'product_name', 'subscription_id',
            'status', 'billing_interval', 'amount', 'currency',
            'start_date', 'current_period_start', 'current_period_end',
            'next_billing_date', 'trial_end', 'cancelled_at',
            'failed_payment_attempts', 'is_trial', 'days_until_renewal',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'subscription_id', 'created_at', 'updated_at',
            'failed_payment_attempts'
        ]
    
    def get_is_trial(self, obj):
        """Check if subscription is in trial period."""
        if obj.trial_end:
            from django.utils import timezone
            return timezone.now() < obj.trial_end
        return False
    
    def get_days_until_renewal(self, obj):
        """Calculate days until next billing."""
        if obj.next_billing_date:
            from django.utils import timezone
            delta = obj.next_billing_date - timezone.now()
            return max(0, delta.days)
        return None


class DisputeSerializer(serializers.ModelSerializer):
    """Serializer for dispute management."""
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    customer_email = serializers.CharField(source='order.get_customer_email', read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    
    class Meta:
        model = Dispute
        fields = [
            'id', 'order', 'order_number', 'customer_email',
            'dispute_id', 'dispute_type', 'status', 'reason',
            'customer_message', 'resolution', 'refund_amount',
            'assigned_to', 'assigned_to_name',
            'created_at', 'updated_at', 'resolved_at'
        ]
        read_only_fields = ['id', 'dispute_id', 'created_at', 'updated_at']


class InvoiceSerializer(serializers.ModelSerializer):
    """Serializer for SARS compliant invoices."""
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    customer_email = serializers.CharField(source='order.get_customer_email', read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'order', 'order_number', 'customer_email',
            'invoice_number', 'invoice_date', 'due_date',
            'tax_invoice', 'vat_vendor_number',
            'subtotal', 'vat_amount', 'total_amount',
            'pdf_url', 'pdf_generated', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'invoice_number', 'invoice_date', 'created_at']


class RefundRequestSerializer(serializers.ModelSerializer):
    """Serializer for refund request management."""
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    customer_email = serializers.CharField(source='order.get_customer_email', read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True)
    
    class Meta:
        model = RefundRequest
        fields = [
            'id', 'order', 'order_number', 'customer_email',
            'amount', 'reason', 'status', 'processed_by',
            'processed_by_name', 'processor_reference',
            'requested_at', 'processed_at'
        ]
        read_only_fields = ['id', 'requested_at', 'processed_at']


# List serializers for better performance
class OrderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for order lists."""
    buyer_email = serializers.SerializerMethodField()
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'buyer_email', 'billing_name',
            'status', 'payment_status', 'total_amount', 'currency',
            'transaction_type', 'item_count', 'created_at'
        ]
    
    def get_buyer_email(self, obj):
        return obj.get_customer_email()
    
    def get_item_count(self, obj):
        # This should be optimized with annotations
        return obj.items.count()


class OrderSummarySerializer(serializers.ModelSerializer):
    """Summary serializer for dashboard and reports."""
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'total_amount',
            'platform_fee_amount', 'created_at'
        ]

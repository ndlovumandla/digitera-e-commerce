"""
DRF Views for Orders API.
Includes transaction processing, fee calculation, VAT compliance, and dispute management.
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.http import HttpResponse

from .models import (
    Order, OrderItem, Subscription, Dispute, Invoice,
    RefundRequest, OrderStatusHistory
)
from .serializers import (
    OrderSerializer, OrderCreateSerializer, OrderListSerializer,
    OrderItemSerializer, SubscriptionSerializer, DisputeSerializer,
    InvoiceSerializer, RefundRequestSerializer, OrderStatusHistorySerializer
)


class OrderViewSet(viewsets.ModelViewSet):
    """Main ViewSet for order management."""
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['order_number', 'billing_email', 'billing_name']
    ordering_fields = ['created_at', 'total_amount', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter orders based on user permissions."""
        queryset = super().get_queryset()
        
        # Add related data for performance
        queryset = queryset.select_related('buyer').prefetch_related(
            'items__product', 'status_history', 'disputes', 'refund_requests'
        )
        
        # Filter based on user permissions
        if not self.request.user.is_staff:
            # Users can see orders they made or sold (as product creators)
            queryset = queryset.filter(
                Q(buyer=self.request.user) |
                Q(items__product__creator=self.request.user)
            ).distinct()
        
        # Apply additional filters
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        payment_status_filter = self.request.query_params.get('payment_status')
        if payment_status_filter:
            queryset = queryset.filter(payment_status=payment_status_filter)
        
        transaction_type_filter = self.request.query_params.get('transaction_type')
        if transaction_type_filter:
            queryset = queryset.filter(transaction_type=transaction_type_filter)
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return OrderCreateSerializer
        elif self.action == 'list':
            return OrderListSerializer
        return OrderSerializer
    
    @action(detail=False, methods=['get'])
    def my_orders(self, request):
        """Get current user's orders as a buyer."""
        user_orders = self.get_queryset().filter(buyer=request.user)
        
        page = self.paginate_queryset(user_orders)
        if page is not None:
            serializer = OrderListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = OrderListSerializer(user_orders, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_sales(self, request):
        """Get orders for products created by current user."""
        sales_orders = self.get_queryset().filter(
            items__product__creator=request.user
        ).distinct()
        
        page = self.paginate_queryset(sales_orders)
        if page is not None:
            serializer = OrderListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = OrderListSerializer(sales_orders, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Update order status with history tracking."""
        order = self.get_object()
        
        # Check permissions
        if not self.can_update_order(request.user, order):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        new_status = request.data.get('status')
        reason = request.data.get('reason', '')
        
        if not new_status:
            return Response(
                {'error': 'Status is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_status not in dict(Order.OrderStatus.choices):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create status history record
        OrderStatusHistory.objects.create(
            order=order,
            previous_status=order.status,
            new_status=new_status,
            changed_by=request.user,
            reason=reason
        )
        
        # Update order status
        order.status = new_status
        
        # Update timestamps based on status
        if new_status == Order.OrderStatus.COMPLETED:
            order.completed_at = timezone.now()
        elif new_status == Order.OrderStatus.CANCELLED:
            # Handle cancellation logic
            pass
        
        order.save()
        
        # Trigger fulfillment if order is completed
        if new_status == Order.OrderStatus.COMPLETED:
            self.fulfill_order(order)
        
        serializer = self.get_serializer(order)
        return Response(serializer.data)
    
    def can_update_order(self, user, order):
        """Check if user can update order status."""
        if user.is_staff:
            return True
        
        # Product creators can update orders for their products
        return order.items.filter(product__creator=user).exists()
    
    def fulfill_order(self, order):
        """Fulfill order items after successful payment."""
        for item in order.items.all():
            if not item.is_fulfilled:
                # Generate digital download links or grant access
                if hasattr(item.product, 'digitaldownload'):
                    item.download_links = self.generate_download_links(item)
                
                # Generate license keys for software
                if getattr(item.product, 'license_type', None):
                    item.license_key = self.generate_license_key(item)
                
                # Grant access
                item.access_granted = True
                item.is_fulfilled = True
                item.fulfilled_at = timezone.now()
                item.save()
    
    def generate_download_links(self, order_item):
        """Generate secure download links for digital products."""
        # This would integrate with your file storage system
        links = []
        for file in order_item.product.files.all():
            signed_url = f"/api/downloads/secure/{file.id}/?order={order_item.order.id}&token=secure_token"
            links.append({
                'file_id': file.id,
                'filename': file.name,
                'url': signed_url,
                'expires_at': timezone.now() + timezone.timedelta(days=30)
            })
        return links
    
    def generate_license_key(self, order_item):
        """Generate license key for software products."""
        import uuid
        return f"DIG-{uuid.uuid4().hex[:8].upper()}-{order_item.product.id}"
    
    @action(detail=True, methods=['get'])
    def invoice(self, request, pk=None):
        """Get or generate invoice for order."""
        order = self.get_object()
        
        # Check permissions
        if not self.can_view_order(request.user, order):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get or create invoice
        invoice, created = Invoice.objects.get_or_create(
            order=order,
            defaults={
                'invoice_number': self.generate_invoice_number(),
                'subtotal': order.subtotal,
                'vat_amount': order.vat_amount,
                'total_amount': order.total_amount,
                'tax_invoice': order.is_vat_registered,
                'vat_vendor_number': order.vat_number
            }
        )
        
        serializer = InvoiceSerializer(invoice)
        return Response(serializer.data)
    
    def can_view_order(self, user, order):
        """Check if user can view order details."""
        if user.is_staff:
            return True
        
        # Buyer can view their orders
        if order.buyer == user:
            return True
        
        # Product creators can view orders for their products
        return order.items.filter(product__creator=user).exists()
    
    def generate_invoice_number(self):
        """Generate unique invoice number."""
        import random
        timestamp = timezone.now().strftime('%Y%m%d')
        random_suffix = random.randint(1000, 9999)
        return f"INV-{timestamp}-{random_suffix}"
    
    @action(detail=True, methods=['post'])
    def request_refund(self, request, pk=None):
        """Request refund for an order."""
        order = self.get_object()
        
        # Check permissions - only buyer can request refund
        if order.buyer != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if order is eligible for refund
        if order.status not in [Order.OrderStatus.COMPLETED]:
            return Response(
                {'error': 'Order is not eligible for refund'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if refund already requested
        if order.refund_requests.filter(status='pending').exists():
            return Response(
                {'error': 'Refund already requested'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        amount = request.data.get('amount', order.total_amount)
        reason = request.data.get('reason', '')
        
        if not reason:
            return Response(
                {'error': 'Refund reason is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create refund request
        refund_request = RefundRequest.objects.create(
            order=order,
            amount=amount,
            reason=reason
        )
        
        serializer = RefundRequestSerializer(refund_request)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get order analytics for current user."""
        queryset = self.get_queryset()
        
        # Get date range
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timezone.timedelta(days=days)
        queryset = queryset.filter(created_at__gte=start_date)
        
        # Calculate analytics
        analytics = queryset.aggregate(
            total_orders=Count('id'),
            total_revenue=Sum('total_amount'),
            avg_order_value=Avg('total_amount'),
            total_fees=Sum('platform_fee_amount'),
            completed_orders=Count('id', filter=Q(status='completed')),
            pending_orders=Count('id', filter=Q(status='pending')),
            cancelled_orders=Count('id', filter=Q(status='cancelled'))
        )
        
        # Calculate conversion rate
        if analytics['total_orders']:
            analytics['completion_rate'] = (
                analytics['completed_orders'] / analytics['total_orders'] * 100
            )
        else:
            analytics['completion_rate'] = 0
        
        return Response({
            'period_days': days,
            'analytics': analytics,
            'start_date': start_date.date(),
            'end_date': timezone.now().date()
        })


class SubscriptionViewSet(viewsets.ModelViewSet):
    """ViewSet for subscription management."""
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['created_at', 'next_billing_date', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter subscriptions based on user permissions."""
        queryset = super().get_queryset()
        
        # Add related data
        queryset = queryset.select_related('user', 'product')
        
        # Filter based on user permissions
        if not self.request.user.is_staff:
            # Users can see their own subscriptions or ones for their products
            queryset = queryset.filter(
                Q(user=self.request.user) |
                Q(product__creator=self.request.user)
            )
        
        # Apply status filter
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def my_subscriptions(self, request):
        """Get current user's subscriptions."""
        user_subscriptions = self.get_queryset().filter(user=request.user)
        serializer = self.get_serializer(user_subscriptions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a subscription."""
        subscription = self.get_object()
        
        # Check permissions
        if subscription.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Cancel subscription
        subscription.status = Subscription.SubscriptionStatus.CANCELLED
        subscription.cancelled_at = timezone.now()
        subscription.save()
        
        serializer = self.get_serializer(subscription)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause a subscription."""
        subscription = self.get_object()
        
        # Check permissions
        if subscription.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if subscription.status != Subscription.SubscriptionStatus.ACTIVE:
            return Response(
                {'error': 'Can only pause active subscriptions'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        subscription.status = Subscription.SubscriptionStatus.PAUSED
        subscription.save()
        
        serializer = self.get_serializer(subscription)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def resume(self, request, pk=None):
        """Resume a paused subscription."""
        subscription = self.get_object()
        
        # Check permissions
        if subscription.user != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if subscription.status != Subscription.SubscriptionStatus.PAUSED:
            return Response(
                {'error': 'Can only resume paused subscriptions'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        subscription.status = Subscription.SubscriptionStatus.ACTIVE
        subscription.save()
        
        serializer = self.get_serializer(subscription)
        return Response(serializer.data)


class DisputeViewSet(viewsets.ModelViewSet):
    """ViewSet for dispute management."""
    queryset = Dispute.objects.all()
    serializer_class = DisputeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['created_at', 'status', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter disputes based on user permissions."""
        queryset = super().get_queryset()
        
        # Add related data
        queryset = queryset.select_related('order__buyer', 'assigned_to')
        
        # Filter based on user permissions
        if not self.request.user.is_staff:
            # Users can see disputes for their orders or products
            queryset = queryset.filter(
                Q(order__buyer=self.request.user) |
                Q(order__items__product__creator=self.request.user)
            ).distinct()
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve a dispute."""
        dispute = self.get_object()
        
        # Check permissions - only staff or assigned user can resolve
        if not request.user.is_staff and dispute.assigned_to != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        resolution = request.data.get('resolution', '')
        refund_amount = request.data.get('refund_amount')
        
        if not resolution:
            return Response(
                {'error': 'Resolution is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        dispute.status = Dispute.DisputeStatus.RESOLVED
        dispute.resolution = resolution
        dispute.resolved_at = timezone.now()
        
        if refund_amount:
            dispute.refund_amount = Decimal(str(refund_amount))
        
        dispute.save()
        
        serializer = self.get_serializer(dispute)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign dispute to a staff member."""
        dispute = self.get_object()
        
        # Only staff can assign disputes
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        assigned_to_id = request.data.get('assigned_to')
        if assigned_to_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                assigned_user = User.objects.get(id=assigned_to_id, is_staff=True)
                dispute.assigned_to = assigned_user
                dispute.save()
            except User.DoesNotExist:
                return Response(
                    {'error': 'Invalid user'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            dispute.assigned_to = request.user
            dispute.save()
        
        serializer = self.get_serializer(dispute)
        return Response(serializer.data)


class RefundRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for refund request management."""
    queryset = RefundRequest.objects.all()
    serializer_class = RefundRequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    ordering_fields = ['requested_at', 'status', 'amount']
    ordering = ['-requested_at']
    
    def get_queryset(self):
        """Filter refund requests based on user permissions."""
        queryset = super().get_queryset()
        
        # Add related data
        queryset = queryset.select_related('order__buyer', 'processed_by')
        
        # Filter based on user permissions
        if not self.request.user.is_staff:
            # Users can see refund requests for their orders or products
            queryset = queryset.filter(
                Q(order__buyer=self.request.user) |
                Q(order__items__product__creator=self.request.user)
            ).distinct()
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve a refund request."""
        refund_request = self.get_object()
        
        # Only staff can approve refunds
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if refund_request.status != RefundRequest.RefundStatus.PENDING:
            return Response(
                {'error': 'Can only approve pending refund requests'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        refund_request.status = RefundRequest.RefundStatus.APPROVED
        refund_request.processed_by = request.user
        refund_request.processed_at = timezone.now()
        refund_request.save()
        
        # Process the actual refund (integrate with payment processor)
        # This would call the payment gateway's refund API
        
        serializer = self.get_serializer(refund_request)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a refund request."""
        refund_request = self.get_object()
        
        # Only staff can reject refunds
        if not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if refund_request.status != RefundRequest.RefundStatus.PENDING:
            return Response(
                {'error': 'Can only reject pending refund requests'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        refund_request.status = RefundRequest.RefundStatus.REJECTED
        refund_request.processed_by = request.user
        refund_request.processed_at = timezone.now()
        refund_request.save()
        
        serializer = self.get_serializer(refund_request)
        return Response(serializer.data)


# Web-based views for traditional HTML pages
class OrderListView(LoginRequiredMixin, ListView):
    """Web view for listing user orders."""
    model = Order
    template_name = 'orders/list.html'
    context_object_name = 'orders'
    paginate_by = 20
    
    def get_queryset(self):
        return Order.objects.filter(buyer=self.request.user).order_by('-created_at')


class OrderDetailView(LoginRequiredMixin, DetailView):
    """Web view for order details."""
    model = Order
    template_name = 'orders/detail.html'
    context_object_name = 'order'
    
    def get_queryset(self):
        return Order.objects.filter(buyer=self.request.user)


class OrderInvoiceView(LoginRequiredMixin, DetailView):
    """Web view for order invoice."""
    model = Order
    template_name = 'orders/invoice.html'
    context_object_name = 'order'
    
    def get_queryset(self):
        return Order.objects.filter(buyer=self.request.user)


class SubscriptionListView(LoginRequiredMixin, ListView):
    """Web view for listing user subscriptions."""
    model = Subscription
    template_name = 'orders/subscriptions.html'
    context_object_name = 'subscriptions'
    paginate_by = 20
    
    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user).order_by('-created_at')


class SubscriptionDetailView(LoginRequiredMixin, DetailView):
    """Web view for subscription details."""
    model = Subscription
    template_name = 'orders/subscription_detail.html'
    context_object_name = 'subscription'
    
    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user)

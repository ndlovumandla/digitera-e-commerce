"""
Download and purchase management views for orders app.
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.http import HttpResponse, Http404, JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
import mimetypes
import os

from .models import Order, OrderItem


class PurchasedProductsView(LoginRequiredMixin, ListView):
    """View for displaying user's purchased products."""
    template_name = 'orders/purchased_products.html'
    context_object_name = 'orders'
    paginate_by = 20
    
    def get_queryset(self):
        """Get orders with completed status for the current user."""
        return Order.objects.filter(
            buyer=self.request.user,
            status=Order.OrderStatus.COMPLETED
        ).prefetch_related('items__product').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get statistics
        user_orders = self.get_queryset()
        context['total_purchases'] = user_orders.count()
        context['total_spent'] = sum(order.total_amount for order in user_orders)
        context['total_downloads'] = sum(
            item.download_count for order in user_orders 
            for item in order.items.all() 
            if hasattr(item, 'download_count')
        )
        
        return context


@login_required
def download_product(request, order_item_id):
    """Handle secure product downloads."""
    order_item = get_object_or_404(
        OrderItem, 
        id=order_item_id,
        order__buyer=request.user,
        order__status=Order.OrderStatus.COMPLETED
    )
    
    # Check if download is allowed
    if not order_item.access_granted:
        messages.error(request, 'Download access not granted for this product.')
        return redirect('orders:purchased_products')
    
    # Check download limits
    if order_item.download_limit and order_item.download_count >= order_item.download_limit:
        messages.error(request, 'Download limit exceeded for this product.')
        return redirect('orders:purchased_products')
    
    # Check expiry
    if order_item.access_expires_at and timezone.now() > order_item.access_expires_at:
        messages.error(request, 'Download access has expired for this product.')
        return redirect('orders:purchased_products')
    
    # Get the product and check if it has download files
    product = order_item.product
    
    # For demo purposes, create a simple download response
    # In production, this would serve actual files from secure storage
    if hasattr(product, 'digitaldownload') and product.digitaldownload.download_files:
        # Simulate file download
        download_files = product.digitaldownload.download_files
        if download_files:
            # For now, just increment download count and show success
            if not hasattr(order_item, 'download_count'):
                # Add download_count field if it doesn't exist
                order_item.download_count = 0
            
            # Increment download count
            order_item.download_count = getattr(order_item, 'download_count', 0) + 1
            order_item.save()
            
            # Create a demo file response
            filename = f"{product.name.replace(' ', '_')}_download.txt"
            content = f"""
Digital Product Download
========================

Product: {product.name}
Creator: {product.creator.get_full_name() or product.creator.email}
Purchase Date: {order_item.order.created_at.strftime('%Y-%m-%d')}
Order Number: {order_item.order.order_number}

Thank you for your purchase!

This is a demo download. In production, this would be your actual digital product file.

License: {getattr(product.digitaldownload, 'license_type', 'Standard License')}
Download #{order_item.download_count}
            """.strip()
            
            response = HttpResponse(content, content_type='text/plain')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            messages.success(request, f'Download started for "{product.name}"')
            return response
    
    # If no files available, show error
    messages.error(request, 'No download files available for this product.')
    return redirect('orders:purchased_products')


@login_required
def get_download_link(request, order_item_id):
    """Get secure download link for product."""
    order_item = get_object_or_404(
        OrderItem,
        id=order_item_id,
        order__buyer=request.user,
        order__status=Order.OrderStatus.COMPLETED
    )
    
    # Generate secure download URL
    download_url = reverse('orders:download_product', kwargs={'order_item_id': order_item.id})
    
    return JsonResponse({
        'success': True,
        'download_url': download_url,
        'product_name': order_item.product.name,
        'downloads_remaining': (
            order_item.download_limit - getattr(order_item, 'download_count', 0)
            if order_item.download_limit else 'Unlimited'
        )
    })

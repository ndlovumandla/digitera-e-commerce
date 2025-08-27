"""
Cart views for Digitera Platform.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.urls import reverse
from decimal import Decimal
import json

from products.models import Product
from .models import Cart, CartItem, Order, OrderItem


def get_or_create_cart(request):
    """Get or create cart for user or session."""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        if not request.session.session_key:
            request.session.create()
        cart, created = Cart.objects.get_or_create(session_key=request.session.session_key)
    return cart


@require_POST
def add_to_cart(request, product_id):
    """Add product to cart."""
    try:
        product = get_object_or_404(Product, id=product_id, status='published')
        cart = get_or_create_cart(request)
        quantity = int(request.POST.get('quantity', 1))
        
        cart_item = cart.add_item(product, quantity)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'{product.name} added to cart',
                'cart_total_items': cart.total_items,
                'cart_total_amount': str(cart.total_amount)
            })
        else:
            messages.success(request, f'{product.name} added to cart')
            return redirect('products:detail', pk=product_id)
    
    except Product.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Product not found'})
        else:
            messages.error(request, 'Product not found')
            return redirect('products:marketplace')
    
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Error adding to cart'})
        else:
            messages.error(request, 'Error adding product to cart')
            return redirect('products:detail', pk=product_id)


@require_POST
def remove_from_cart(request, product_id):
    """Remove product from cart."""
    try:
        product = get_object_or_404(Product, id=product_id)
        cart = get_or_create_cart(request)
        cart.remove_item(product)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'{product.name} removed from cart',
                'cart_total_items': cart.total_items,
                'cart_total_amount': str(cart.total_amount)
            })
        else:
            messages.success(request, f'{product.name} removed from cart')
            return redirect('orders:cart')
    
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Error removing from cart'})
        else:
            messages.error(request, 'Error removing product from cart')
            return redirect('orders:cart')


@require_POST
def update_cart_item(request, product_id):
    """Update cart item quantity."""
    try:
        product = get_object_or_404(Product, id=product_id)
        cart = get_or_create_cart(request)
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity <= 0:
            cart.remove_item(product)
            message = f'{product.name} removed from cart'
        else:
            cart_item = cart.items.get(product=product)
            cart_item.quantity = quantity
            cart_item.save()
            message = f'{product.name} quantity updated'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': message,
                'cart_total_items': cart.total_items,
                'cart_total_amount': str(cart.total_amount)
            })
        else:
            messages.success(request, message)
            return redirect('orders:cart')
    
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Error updating cart'})
        else:
            messages.error(request, 'Error updating cart')
            return redirect('orders:cart')


def cart_detail(request):
    """Display cart contents."""
    cart = get_or_create_cart(request)
    context = {
        'cart': cart,
        'cart_items': cart.items.select_related('product').all(),
        'total_amount': cart.total_amount,
        'total_items': cart.total_items,
    }
    return render(request, 'orders/cart.html', context)


def buy_now(request, product_id):
    """Direct buy now - skip cart and go to checkout."""
    product = get_object_or_404(Product, id=product_id, status='published')
    
    # Create temporary cart with single item
    cart = get_or_create_cart(request)
    cart.clear()  # Clear existing items
    cart.add_item(product, 1)
    
    return redirect('orders:checkout')


def checkout(request):
    """Checkout process."""
    cart = get_or_create_cart(request)
    cart_items = cart.items.select_related('product').all()
    
    if not cart_items.exists():
        messages.warning(request, 'Your cart is empty')
        return redirect('products:marketplace')
    
    if request.method == 'POST':
        try:
            # Create order from cart
            order = Order.objects.create(
                buyer=request.user if request.user.is_authenticated else None,
                guest_email=request.POST.get('email', ''),
                billing_name=request.POST.get('billing_name', ''),
                billing_email=request.POST.get('billing_email', ''),
                billing_phone=request.POST.get('billing_phone', ''),
                subtotal=cart.total_amount,
                total_amount=cart.total_amount,
                transaction_type=Order.TransactionType.MARKETPLACE,
                currency='ZAR'
            )
            
            # Add cart items to order
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    product_name=cart_item.product.name,
                    quantity=cart_item.quantity,
                    unit_price=cart_item.unit_price,
                    total_price=cart_item.total_price
                )
            
            # Calculate fees
            order.calculate_fees()
            order.save()
            
            # Clear cart
            cart.clear()
            
            # Redirect to payment
            return redirect('payments:process_payment', order_id=order.id)
        
        except Exception as e:
            messages.error(request, 'Error processing order. Please try again.')
            return redirect('orders:checkout')
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_amount': cart.total_amount,
        'total_items': cart.total_items,
    }
    return render(request, 'orders/checkout.html', context)


def get_cart_count(request):
    """Get cart item count for AJAX requests."""
    cart = get_or_create_cart(request)
    return JsonResponse({'count': cart.total_items})

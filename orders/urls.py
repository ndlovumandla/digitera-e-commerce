"""
URL configuration for the orders app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, cart_views
from .download_views import PurchasedProductsView, download_product, get_download_link

app_name = 'orders'

# DRF Router for API endpoints
router = DefaultRouter()
router.register(r'api', views.OrderViewSet, basename='order')

urlpatterns = [
    # Include DRF API routes
    path('', include(router.urls)),
    
    # Cart functionality
    path('cart/', cart_views.cart_detail, name='cart'),
    path('cart/add/<uuid:product_id>/', cart_views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<uuid:product_id>/', cart_views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<uuid:product_id>/', cart_views.update_cart_item, name='update_cart_item'),
    path('cart/count/', cart_views.get_cart_count, name='cart_count'),
    path('buy-now/<uuid:product_id>/', cart_views.buy_now, name='buy_now'),
    path('checkout/', cart_views.checkout, name='checkout'),
    
    # Web-based views
    path('orders/', views.OrderListView.as_view(), name='list'),
    path('orders/<uuid:pk>/', views.OrderDetailView.as_view(), name='detail'),
    path('orders/<uuid:pk>/invoice/', views.OrderInvoiceView.as_view(), name='invoice'),
    path('subscriptions/', views.SubscriptionListView.as_view(), name='subscriptions'),
    path('subscriptions/<uuid:pk>/', views.SubscriptionDetailView.as_view(), name='subscription-detail'),
    
    # Purchased products and downloads
    path('purchased/', PurchasedProductsView.as_view(), name='purchased_products'),
    path('download/<uuid:order_item_id>/', download_product, name='download_product'),
    path('download-link/<uuid:order_item_id>/', get_download_link, name='get_download_link'),
]

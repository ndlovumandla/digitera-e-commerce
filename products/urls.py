"""
URL configuration for the products app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .creator_views import (
    CreatorProductListView, ProductCreateView, ProductUpdateView, 
    ProductDeleteView, product_quick_edit, product_duplicate,
    upload_product_image, product_analytics
)

app_name = 'products'

# DRF Router for API endpoints
router = DefaultRouter()
router.register(r'api/categories', views.CategoryViewSet)
router.register(r'api/tags', views.TagViewSet)
router.register(r'api/products', views.ProductViewSet)
router.register(r'api/downloads', views.DigitalDownloadViewSet)
router.register(r'api/events', views.EventViewSet)

urlpatterns = [
    # Include DRF API routes
    path('', include(router.urls)),
    
    # Public web-based views
    path('', views.MarketplaceView.as_view(), name='product_list'),
    path('marketplace/', views.MarketplaceView.as_view(), name='marketplace'),
    path('product/<uuid:pk>/', views.ProductDetailView.as_view(), name='detail'),
    path('categories/', views.CategoryListView.as_view(), name='categories'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category_detail'),
    
    # Creator management views
    path('creator/', CreatorProductListView.as_view(), name='creator_list'),
    path('creator/create/', ProductCreateView.as_view(), name='creator_create'),
    path('creator/<uuid:pk>/edit/', ProductUpdateView.as_view(), name='creator_edit'),
    path('creator/<uuid:pk>/delete/', ProductDeleteView.as_view(), name='creator_delete'),
    path('creator/<uuid:pk>/duplicate/', product_duplicate, name='creator_duplicate'),
    path('creator/<uuid:pk>/analytics/', product_analytics, name='creator_analytics'),
    path('creator/quick-edit/<uuid:product_id>/', product_quick_edit, name='creator_quick_edit'),
    path('creator/upload-image/', upload_product_image, name='upload_image'),
]

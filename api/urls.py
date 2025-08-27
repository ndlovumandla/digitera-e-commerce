"""
URL configuration for the API app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from . import views

# API Router
router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'storefronts', views.StorefrontViewSet, basename='storefront')
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'orders', views.OrderViewSet, basename='order')

app_name = 'api'

urlpatterns = [
    # API Root
    path('', include(router.urls)),
    
    # Authentication
    path('auth/token/', obtain_auth_token, name='token'),
    path('auth/', include('rest_framework.urls', namespace='rest_framework')),
    
    # Custom API endpoints
    path('dashboard/metrics/', views.DashboardMetricsAPIView.as_view(), name='dashboard-metrics'),
    path('analytics/revenue/', views.RevenueAnalyticsAPIView.as_view(), name='revenue-analytics'),
    path('products/<int:product_id>/trends/', views.ProductTrendsAPIView.as_view(), name='product-trends'),
]

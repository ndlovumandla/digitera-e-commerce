"""
URL configuration for the storefronts app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'storefronts'

# DRF Router for API endpoints
router = DefaultRouter()
router.register(r'api', views.StorefrontViewSet, basename='storefront')

urlpatterns = [
    # Include DRF API routes
    path('', include(router.urls)),
    
    # Web-based views
    path('', views.StorefrontListView.as_view(), name='list'),
    path('create/', views.StorefrontCreateView.as_view(), name='create'),
    path('<slug:slug>/', views.StorefrontDetailView.as_view(), name='detail'),
    path('<slug:slug>/edit/', views.StorefrontUpdateView.as_view(), name='edit'),
    path('<slug:slug>/analytics/', views.StorefrontAnalyticsView.as_view(), name='analytics'),
]

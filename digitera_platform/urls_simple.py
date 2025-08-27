"""
Basic URL configuration for testing without DRF
"""
from django.contrib import admin
from django.urls import path, include
from digitera_platform import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    
    # Accounts URLs
    path('accounts/', include('accounts.urls', namespace='accounts')),
    
    # Simple API endpoints
    path('api/', views.api_status, name='api_status'),
    path('api/products/', views.api_products, name='api_products'),
    path('api/storefronts/', views.api_storefronts, name='api_storefronts'),
]

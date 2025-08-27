"""
Enhanced URL configuration for Digitera Platform.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import HomeView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', HomeView.as_view(), name='home'),
    
    # Authentication
    path('accounts/', include('accounts.urls')),
    path('api/auth/', include('rest_framework.urls')),
    
    # API endpoints
    path('api/v1/', include('api.urls')),
    
    # App-specific API endpoints
    path('', include('products.urls')),
    path('', include('storefronts.urls')),
    path('', include('orders.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

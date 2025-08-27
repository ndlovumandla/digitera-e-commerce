"""
URL configuration for Digitera Platform.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from .static_views import TermsView, PrivacyView, AboutView, ContactView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Accounts app (namespaced) and Authentication (django-allauth)
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('accounts/', include('allauth.urls')),

    # Core app feature routes
    path('storefronts/', include(('storefronts.urls', 'storefronts'), namespace='storefronts')),
    path('products/', include(('products.urls', 'products'), namespace='products')),
    path('orders/', include(('orders.urls', 'orders'), namespace='orders')),
    path('payments/', include(('payments.urls', 'payments'), namespace='payments')),
    path('analytics/', include(('analytics.urls', 'analytics'), namespace='analytics')),
    path('marketing/', include(('marketing.urls', 'marketing'), namespace='marketing')),
    
    # Marketplace discovery
    path('marketplace/', include(('products.urls', 'products'), namespace='marketplace')),
    
    # Static pages
    path('terms/', TermsView.as_view(), name='terms'),
    path('privacy/', PrivacyView.as_view(), name='privacy'),
    path('about/', AboutView.as_view(), name='about'),
    path('contact/', ContactView.as_view(), name='contact'),
    path('faq/', TemplateView.as_view(template_name='faq.html'), name='faq'),
    path('creator-resources/', TemplateView.as_view(template_name='accounts/creator_resources.html'), name='creator_resources'),
    path('landing/', TemplateView.as_view(template_name='marketplace/landing.html'), name='marketplace_landing'),
    
    # API endpoints (commented out for initial setup)
    # path('api/', include('api.urls')),
    
    # Home page
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug toolbar
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
    except ImportError:
        pass

# Customize admin site
admin.site.site_header = "Digitera Administration"
admin.site.site_title = "Digitera Admin"
admin.site.index_title = "Welcome to Digitera Administration"

"""
URL configuration for marketplace discovery features.
Includes both web views and API endpoints.
"""

from django.urls import path, include
from . import marketplace_views

app_name = 'marketplace'

# Web views
urlpatterns = [
    path('', marketplace_views.MarketplaceDiscoveryView.as_view(), name='discovery'),
]

# API endpoints
api_urlpatterns = [
    path('marketplace/', marketplace_views.marketplace_api, name='marketplace_api'),
    path('trending/', marketplace_views.trending_products_api, name='trending_api'),
    path('track-interaction/', marketplace_views.track_product_interaction, name='track_interaction'),
    path('recommendations/', marketplace_views.personalized_recommendations, name='recommendations'),
    path('search-suggestions/', marketplace_views.search_suggestions, name='search_suggestions'),
    path('stats/', marketplace_views.marketplace_stats_api, name='stats_api'),
]

# Include API endpoints with 'api/' prefix
urlpatterns += [path('api/', include(api_urlpatterns))]

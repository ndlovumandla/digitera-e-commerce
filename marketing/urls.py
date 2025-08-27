"""
URL configuration for the marketing app.
"""

from django.urls import path
from . import views

app_name = 'marketing'

urlpatterns = [
    # Marketing packages
    path('packages/', views.PackageListView.as_view(), name='packages'),
    path('packages/<int:pk>/', views.PackageDetailView.as_view(), name='package-detail'),
    path('packages/<int:pk>/purchase/', views.PackagePurchaseView.as_view(), name='package-purchase'),
    
    # Email campaigns
    path('campaigns/', views.CampaignListView.as_view(), name='campaigns'),
    path('campaigns/create/', views.CampaignCreateView.as_view(), name='campaign-create'),
    path('campaigns/<int:pk>/', views.CampaignDetailView.as_view(), name='campaign-detail'),
    
    # Promotions
    path('promotions/', views.PromotionListView.as_view(), name='promotions'),
    path('promotions/create/', views.PromotionCreateView.as_view(), name='promotion-create'),
]

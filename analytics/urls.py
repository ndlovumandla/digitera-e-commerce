"""
URL configuration for the analytics app.
"""

from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Analytics dashboard
    path('', views.AnalyticsDashboardView.as_view(), name='dashboard'),
    path('revenue/', views.RevenueAnalyticsView.as_view(), name='revenue'),
    path('traffic/', views.TrafficAnalyticsView.as_view(), name='traffic'),
    path('conversion/', views.ConversionAnalyticsView.as_view(), name='conversion'),
    
    # Export data
    path('export/csv/', views.ExportCSVView.as_view(), name='export-csv'),
    path('export/pdf/', views.ExportPDFView.as_view(), name='export-pdf'),
]

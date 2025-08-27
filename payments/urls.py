"""
URL configuration for the payments app.
"""

from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Payment processing
    path('process/<uuid:order_id>/', views.PaymentProcessView.as_view(), name='process_payment'),
    path('success/<uuid:order_id>/', views.PaymentSuccessView.as_view(), name='success'),
    path('cancelled/', views.PaymentCancelledView.as_view(), name='cancelled'),
    
    # Webhooks
    path('webhooks/stripe/', views.StripeWebhookView.as_view(), name='stripe-webhook'),
    
    # Payouts
    path('payouts/', views.PayoutListView.as_view(), name='payouts'),
    path('payouts/request/', views.PayoutRequestView.as_view(), name='payout-request'),
]

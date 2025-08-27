"""
URL configuration for the accounts app.
Includes authentication, profile management, creator onboarding, and 2FA endpoints.
"""

from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views
from .basic_views import (
    BuyerSignupView,
    UserLoginView,
    UserLogoutView,
    DashboardView,
    UserRegistrationView,
    ProfileUpdateView,
    CreatorProfileUpdateView,
    TwoFactorSetupView,
    GuestCheckoutView,
    DeleteAccountView,
    CreatorResourcesView,
    CreatorProfileView,
    disable_two_factor,
)
from .onboarding_views import (
    CreatorSignupView,
    OnboardingStep1View,
    OnboardingStep2View,
    OnboardingStep3View,
    OnboardingStep4View,
    OnboardingCompleteView,
    skip_onboarding_step,
    onboarding_dashboard,
)

app_name = 'accounts'

urlpatterns = [
    # Creator Signup and Onboarding
    path('creator/signup/', CreatorSignupView.as_view(), name='creator_signup'),
    path('onboarding/step-1/', OnboardingStep1View.as_view(), name='onboarding_step_1'),
    path('onboarding/step-2/', OnboardingStep2View.as_view(), name='onboarding_step_2'),
    path('onboarding/step-3/', OnboardingStep3View.as_view(), name='onboarding_step_3'),
    path('onboarding/step-4/', OnboardingStep4View.as_view(), name='onboarding_step_4'),
    path('onboarding/complete/', OnboardingCompleteView.as_view(), name='onboarding_complete'),
    path('onboarding/skip/', skip_onboarding_step, name='skip_onboarding_step'),
    path('onboarding/dashboard/', onboarding_dashboard, name='onboarding_dashboard'),
    
    # Buyer Signup and Authentication
    path('buyer/signup/', BuyerSignupView.as_view(), name='buyer_signup'),
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    
    # Dashboard and Profile
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('profile/', ProfileUpdateView.as_view(), name='profile_update'),
    path('creator-profile/', CreatorProfileUpdateView.as_view(), name='creator_profile_update'),
    path('upgrade-to-creator/', views.CreatorUpgradeView.as_view(), name='upgrade_to_creator'),
    path('switch-role/', views.switch_role, name='switch_role'),
    path('delete-account/', DeleteAccountView.as_view(), name='delete_account'),
    
    # Two-Factor Authentication
    path('2fa/setup/', TwoFactorSetupView.as_view(), name='two_factor_setup'),
    path('2fa/verify/', TwoFactorSetupView.as_view(), name='two_factor_verify'),
    path('2fa/disable/', disable_two_factor, name='two_factor_disable'),
    
    # Password Reset
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html',
        email_template_name='accounts/password_reset_email.html',
        success_url='/accounts/password-reset/done/'
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_confirm.html',
        success_url='/accounts/reset/done/'
    ), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'
    ), name='password_reset_complete'),
    
    # Guest Checkout
    path('guest-checkout/', GuestCheckoutView.as_view(), name='guest_checkout'),
    
    # Creator Resources
    path('creator-resources/', CreatorResourcesView.as_view(), name='creator_resources'),
    
    # Creator Profile View
    path('creator/<uuid:creator_id>/', CreatorProfileView.as_view(), name='creator_profile'),
    
    # API Endpoints (temporarily disabled)
    # path('api/register/', views.api_register, name='api_register'),
    # path('api/login/', views.api_login, name='api_login'),
    # path('api/profile/', views.api_profile, name='api_profile'),
    
    # Django Allauth URLs (for social authentication) - Temporarily disabled
    # path('', include('allauth.urls')),
]

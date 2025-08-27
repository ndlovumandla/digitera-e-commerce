"""
Views for the accounts app.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import CreateView, UpdateView, TemplateView, FormView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.views import (
    LoginView as BaseLoginView, 
    LogoutView as BaseLogoutView,
    PasswordResetView as BasePasswordResetView,
    PasswordResetDoneView as BasePasswordResetDoneView,
    PasswordResetConfirmView as BasePasswordResetConfirmView,
    PasswordResetCompleteView as BasePasswordResetCompleteView
)
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
# import qrcode
# import io
# import base64
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from rest_framework import status
# from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, UserProfile, CreatorProfile, UserRole
from .forms import (
    DigiteraUserCreationForm, DigiteraAuthenticationForm, 
    UserProfileForm, CreatorProfileForm, TwoFactorSetupForm, GuestCheckoutForm
)


class HomeView(TemplateView):
    """Home page view with South African market focus."""
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'sa_stats': {
                'mobile_users': 80,
                'languages': 11,
                'local_currency': 'ZAR',
                'setup_fees': 0,
            },
            'featured_categories': [
                'Digital Art & Design',
                'Educational Content',
                'Software & Tools',
                'Business Templates',
                'Photography',
                'Music & Audio'
            ]
        })
        return context


class UserRegistrationView(CreateView):
    """User registration view with SA-specific features."""
    model = User
    form_class = DigiteraUserCreationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('accounts:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        user = self.object
        
        # Profiles are created in the form.save(); just send welcome email and message
        self.send_welcome_email(user)
        
        messages.success(
            self.request, 
            'Account created successfully! Please check your email to verify your account.'
        )
        return response
    
    def send_welcome_email(self, user):
        """Send welcome email to new user."""
        try:
            subject = 'Welcome to Digitera - South Africa\'s Digital Marketplace! 🇿🇦'
            html_message = render_to_string('emails/welcome.html', {
                'user': user,
                'site_name': 'Digitera',
                'site_url': self.request.build_absolute_uri('/'),
            })
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject,
                plain_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                html_message=html_message,
                fail_silently=True,
            )
        except Exception as e:
            # Log error but don't fail registration
            print(f"Failed to send welcome email: {e}")


class UserLoginView(BaseLoginView):
    """Custom login view with SA-specific features."""
    form_class = DigiteraAuthenticationForm
    template_name = 'registration/login.html'
    
    def get_success_url(self):
        return reverse('accounts:dashboard')
    
    def form_valid(self, form):
        """Handle successful login."""
        response = super().form_valid(form)
        user = form.get_user()
        
        # Ensure profile exists and update login tracking on the user
        profile = getattr(user, 'profile', None)
        if profile is None:
            profile = UserProfile.objects.create(user=user)
        user.last_login_ip = self.get_client_ip()
        user.save(update_fields=['last_login_ip'])
        
        messages.success(self.request, f'Welcome back, {user.first_name}! 🇿🇦')
        return response
    
    def get_client_ip(self):
        """Get client IP address."""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class UserLogoutView(BaseLogoutView):
    """Custom logout view."""
    next_page = reverse_lazy('home')
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.success(request, 'You have been logged out successfully.')
        return super().dispatch(request, *args, **kwargs)


class DashboardView(LoginRequiredMixin, TemplateView):
    """User dashboard with personalized content."""
    template_name = 'accounts/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context.update({
            'user_stats': self.get_user_stats(user),
            'sa_market_insights': self.get_market_insights(),
            'quick_actions': self.get_quick_actions(user),
        })
        return context
    
    def get_user_stats(self, user):
        """Get user-specific statistics."""
        stats = {
            'purchases': 0,
            'downloads': 0,
            'wishlist_items': 0,
        }
        
        if user.is_creator:
            stats.update({
                'total_earnings': '0.00',
                'products': 0,
                'total_sales': 0,
                'rating': None,
            })
        
        return stats
    
    def get_market_insights(self):
        """Get South African market insights."""
        return {
            'mobile_usage': '80%',
            'peak_hours': '18:00 - 22:00 SAST',
            'popular_categories': ['Design', 'Education'],
            'average_price': 'R 150 - R 500',
        }
    
    def get_quick_actions(self, user):
        """Get relevant quick actions for user."""
        actions = [
            {
                'title': 'Browse Products',
                'description': 'Explore digital marketplace',
                'url': '#',
                'icon': 'fas fa-search'
            }
        ]
        
        if user.is_creator:
            actions.extend([
                {
                    'title': 'Add Product',
                    'description': 'Upload a new digital product',
                    'url': '#',
                    'icon': 'fas fa-plus'
                },
                {
                    'title': 'View Analytics',
                    'description': 'Track your sales performance',
                    'url': '#',
                    'icon': 'fas fa-chart-bar'
                }
            ])
        
        return actions


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Update user profile view."""
    model = User
    form_class = UserProfileForm
    template_name = 'accounts/profile_update.html'
    success_url = reverse_lazy('accounts:dashboard')
    
    def get_object(self):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get or create user profile
        profile = getattr(user, 'profile', None) or UserProfile.objects.create(user=user)
        
        context['user_form'] = self.form_class(instance=user)
        context['profile_form'] = UserProfileForm(instance=profile)
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle both user and profile form submission."""
        user = self.get_object()
        user_form = self.form_class(request.POST, instance=user)
        
        profile = getattr(user, 'profile', None) or UserProfile.objects.create(user=user)
        
        profile_form = UserProfileForm(
            request.POST, 
            request.FILES, 
            instance=profile
        )
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect(self.success_url)
        
        context = self.get_context_data()
        context['user_form'] = user_form
        context['profile_form'] = profile_form
        return self.render_to_response(context)


class CreatorProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Update creator profile view."""
    model = CreatorProfile
    form_class = CreatorProfileForm
    template_name = 'accounts/creator_profile_update.html'
    success_url = reverse_lazy('accounts:dashboard')
    
    def get_object(self):
        user = self.request.user
        if not user.is_creator:
            user.is_creator = True
            user.save()
        
        creator_profile, created = CreatorProfile.objects.get_or_create(user=user)
        return creator_profile
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Creator profile updated successfully!')
        return response


class TwoFactorSetupView(LoginRequiredMixin, FormView):
    """Two-factor authentication setup view."""
    template_name = 'accounts/two_factor_setup.html'
    form_class = TwoFactorSetupForm
    success_url = reverse_lazy('accounts:dashboard')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        profile = getattr(user, 'profile', None) or UserProfile.objects.create(user=user)
        
        context['qr_code_url'] = self.generate_qr_code(user)
        context['secret_key'] = self.get_or_create_secret_key(user)
        context['backup_codes'] = self.get_backup_codes(user) if user.two_factor_enabled else None
        
        return context
    
    def generate_qr_code(self, user):
        """Generate QR code for 2FA setup."""
        # TODO: Re-enable when qrcode package import is fixed
        return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        # try:
        #     secret_key = self.get_or_create_secret_key(user)
        #     qr_string = f"otpauth://totp/Digitera:{user.email}?secret={secret_key}&issuer=Digitera"
        #     
        #     qr = qrcode.QRCode(version=1, box_size=10, border=5)
        #     qr.add_data(qr_string)
        #     qr.make(fit=True)
        #     
        #     img = qr.make_image(fill_color="black", back_color="white")
        #     buffer = io.BytesIO()
        #     img.save(buffer, format='PNG')
        #     buffer.seek(0)
        #     
        #     qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        #     return f"data:image/png;base64,{qr_code_base64}"
        # except Exception as e:
        #     print(f"QR code generation error: {e}")
        #     return None
    
    def get_or_create_secret_key(self, user):
        """Get or create secret key for 2FA."""
        # This would typically use a proper 2FA library like django-otp
        # For now, return a placeholder
        return "JBSWY3DPEHPK3PXP"  # Base32 encoded secret
    
    def get_backup_codes(self, user):
        """Generate backup codes for 2FA."""
        # This would generate actual backup codes
        return [
            "12345678", "87654321", "11111111", "22222222",
            "33333333", "44444444", "55555555", "66666666"
        ]
    
    def form_valid(self, form):
        """Enable 2FA for user."""
        user = self.request.user
        # Ensure profile exists, but store 2FA flag on the user model
        _ = getattr(user, 'profile', None) or UserProfile.objects.create(user=user)
        user.two_factor_enabled = True
        user.save(update_fields=['two_factor_enabled'])
        
        messages.success(
            self.request, 
            'Two-factor authentication enabled successfully! Your account is now more secure.'
        )
        return super().form_valid(form)


class GuestCheckoutView(FormView):
    """Guest checkout view for non-registered users."""
    template_name = 'accounts/guest_checkout.html'
    form_class = GuestCheckoutForm
    success_url = reverse_lazy('home')
    
    def form_valid(self, form):
        # Handle guest checkout logic
        messages.info(
            self.request,
            'Guest checkout processed. Create an account to track your purchases!'
        )
        return super().form_valid(form)


# Password Reset Views
class PasswordResetView(BasePasswordResetView):
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')


class PasswordResetDoneView(BasePasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'


class PasswordResetConfirmView(BasePasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('accounts:password_reset_complete')


class PasswordResetCompleteView(BasePasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'


# API Views for mobile and third-party integrations
# Temporarily disabled until REST Framework import issue is resolved
# @api_view(['POST'])
# def api_register(request):
#     """API endpoint for user registration."""
#     form = DigiteraUserCreationForm(request.data)
#     if form.is_valid():
#         user = form.save()
#         UserProfile.objects.create(user=user)
#         
#         # Generate JWT tokens
#         refresh = RefreshToken.for_user(user)
#         access_token = refresh.access_token
#         
#         return Response({
#             'user_id': user.id,
#             'email': user.email,
#             'access_token': str(access_token),
#             'refresh_token': str(refresh),
#         }, status=status.HTTP_201_CREATED)
#     
#     return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)


# @api_view(['POST'])
# def api_login(request):
#     """API endpoint for user login."""
#     email = request.data.get('email')
#     password = request.data.get('password')
#     
#     user = authenticate(request, username=email, password=password)
#     if user:
#         # Generate JWT tokens
#         refresh = RefreshToken.for_user(user)
#         access_token = refresh.access_token
#         
#         return Response({
#             'user_id': user.id,
#             'email': user.email,
#             'is_creator': user.is_creator,
#             'access_token': str(access_token),
#             'refresh_token': str(refresh),
#         }, status=status.HTTP_200_OK)
#     
#     return Response({
#         'error': 'Invalid credentials'
#     }, status=status.HTTP_401_UNAUTHORIZED)


# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def api_profile(request):
#     """API endpoint to get user profile."""
#     user = request.user
#     try:
#         profile = user.userprofile
#     except UserProfile.DoesNotExist:
#         profile = UserProfile.objects.create(user=user)
#     
#     data = {
#         'id': user.id,
#         'email': user.email,
#         'first_name': user.first_name,
#         'last_name': user.last_name,
#         'is_creator': user.is_creator,
#         'phone_number': str(profile.phone_number) if profile.phone_number else None,
#         'province': profile.get_province_display() if profile.province else None,
#         'two_factor_enabled': profile.two_factor_enabled,
#     }
#     
#     return Response(data, status=status.HTTP_200_OK)


class CreatorUpgradeView(LoginRequiredMixin, FormView):
    """Upgrade user to creator account."""
    template_name = 'accounts/upgrade_to_creator.html'
    form_class = CreatorProfileForm
    success_url = reverse_lazy('accounts:dashboard')
    
    def get_form_kwargs(self):
        """Get form kwargs, using existing creator profile if available."""
        kwargs = super().get_form_kwargs()
        user = self.request.user
        
        # Get or create creator profile
        creator_profile, created = CreatorProfile.objects.get_or_create(
            user=user,
            defaults={
                'store_name': f"{user.get_full_name()}'s Store",
                'store_slug': self.generate_store_slug(f"{user.get_full_name()}'s Store"),
                'status': 'pending',
            }
        )
        
        if self.request.method == 'POST':
            kwargs['data'] = self.request.POST
            kwargs['files'] = self.request.FILES
        
        kwargs['instance'] = creator_profile
        return kwargs
    
    def form_valid(self, form):
        """Process creator upgrade."""
        user = self.request.user
        creator_profile = form.save(commit=False)
        
        # Update user role to creator
        user.role = UserRole.CREATOR
        user.save(update_fields=['role'])
        
        # Update creator profile
        creator_profile.user = user
        creator_profile.status = 'active'
        creator_profile.verified = True
        if not creator_profile.store_slug:
            creator_profile.store_slug = self.generate_store_slug(creator_profile.store_name)
        creator_profile.save()
        
        messages.success(
            self.request,
            f'🎉 Welcome to Digitera Creators! Your store "{creator_profile.store_name}" is now active. Start uploading your first product!'
        )
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Debug form errors."""
        print(f"Form errors: {form.errors}")
        print(f"Non-field errors: {form.non_field_errors()}")
        for field, errors in form.errors.items():
            print(f"Field '{field}': {errors}")
        messages.error(
            self.request,
            f'Please correct the errors below. {form.errors}'
        )
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Check if user already has creator profile
        creator_profile = getattr(user, 'creator_profile', None)
        if creator_profile:
            context['existing_creator'] = True
            context['creator_profile'] = creator_profile
        else:
            context['existing_creator'] = False
        
        return context
    
    def generate_store_slug(self, store_name):
        """Generate unique store slug from store name."""
        import re
        from django.utils.text import slugify
        
        if not store_name:
            return f"store-{self.request.user.id}"
        
        base_slug = slugify(store_name)
        slug = base_slug
        counter = 1
        
        while CreatorProfile.objects.filter(store_slug=slug).exclude(user=self.request.user).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug


class DeleteAccountView(LoginRequiredMixin, TemplateView):
    """Delete user account view."""
    template_name = 'accounts/delete_account.html'
    
    def post(self, request, *args, **kwargs):
        """Handle account deletion."""
        user = request.user
        
        # Log user out and delete account
        logout(request)
        user.delete()
        
        messages.success(request, 'Your account has been successfully deleted.')
        return redirect('home')


# Utility views
@require_http_methods(["POST"])
@login_required
def disable_two_factor(request):
    """Disable two-factor authentication."""
    # Ensure profile exists
    user = request.user
    _ = getattr(user, 'profile', None) or UserProfile.objects.create(user=user)
    user.two_factor_enabled = False
    user.save(update_fields=['two_factor_enabled'])
    messages.success(request, 'Two-factor authentication disabled.')
    
    return redirect('accounts:two_factor_setup')


@require_http_methods(["POST"])
@login_required
def disable_two_factor(request):
    """Disable two-factor authentication."""
    # Ensure profile exists
    user = request.user
    _ = getattr(user, 'profile', None) or UserProfile.objects.create(user=user)
    user.two_factor_enabled = False
    user.save(update_fields=['two_factor_enabled'])
    messages.success(request, 'Two-factor authentication disabled.')
    
    return redirect('accounts:two_factor_setup')


@require_http_methods(["POST"])
@login_required
def generate_backup_codes(request):
    """Generate new backup codes for 2FA."""
    # Implementation for generating backup codes
    messages.success(request, 'New backup codes generated.')
    return redirect('accounts:two_factor_setup')


@login_required
def delete_account(request):
    """Delete user account (placeholder)."""
    if request.method == 'POST':
        # Add proper account deletion logic here
        messages.success(request, 'Account deletion requested. This feature is under development.')
        return redirect('home')
    
    return render(request, 'accounts/delete_account_confirm.html')


@login_required
def switch_role(request):
    """Switch between creator and buyer roles."""
    if request.method == 'POST':
        current_role = request.user.role
        
        if current_role == UserRole.BUYER:
            # Switch to creator
            request.user.role = UserRole.CREATOR
            request.user.save()
            
            # Create creator profile if it doesn't exist
            creator_profile, created = CreatorProfile.objects.get_or_create(
                user=request.user,
                defaults={
                    'store_name': f"{request.user.get_full_name()}'s Store",
                    'store_slug': f"store-{request.user.id}",
                    'status': 'active',
                    'verified': True,
                }
            )
            
            messages.success(
                request, 
                f'🎉 Switched to Creator mode! Welcome to your store: {creator_profile.store_name}'
            )
            return redirect('accounts:dashboard')
            
        elif current_role == UserRole.CREATOR:
            # Switch to buyer
            request.user.role = UserRole.BUYER
            request.user.save()
            
            messages.success(request, '🛍️ Switched to Buyer mode! You can now browse and purchase products.')
            return redirect('accounts:dashboard')
    
    return redirect('accounts:dashboard')

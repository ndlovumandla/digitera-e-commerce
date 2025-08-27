"""
Basic views for accounts app to support onboarding and user management.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View, TemplateView, DetailView
from django.contrib import messages
from django.db import transaction
from .forms import DigiteraUserCreationForm, DigiteraAuthenticationForm, CreatorProfileForm
from .models import User, UserProfile, CreatorProfile


class BuyerSignupView(View):
    """Buyer signup page."""
    
    template_name = 'accounts/buyer_signup.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        
        form = DigiteraUserCreationForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = DigiteraUserCreationForm(request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save(commit=False)
                    user.role = 'buyer'
                    user.save()
                    
                    # Create user profile
                    UserProfile.objects.create(user=user)
                    
                    # Log in the user
                    username = form.cleaned_data.get('email')
                    password = form.cleaned_data.get('password1')
                    user = authenticate(username=username, password=password)
                    if user:
                        login(request, user)
                        messages.success(request, f'Welcome to Digitera, {user.first_name}!')
                        return redirect('products:marketplace')
            
            except Exception as e:
                messages.error(request, 'There was an error creating your account. Please try again.')
                
        return render(request, self.template_name, {'form': form})


class UserLoginView(View):
    """Enhanced login view."""
    
    template_name = 'accounts/login.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        
        form = DigiteraAuthenticationForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        form = DigiteraAuthenticationForm(request, data=request.POST)
        
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                
                # Redirect based on user role and setup completion
                if user.is_creator:
                    creator_profile = getattr(user, 'creator_profile', None)
                    if creator_profile and creator_profile.status == 'pending':
                        return redirect('accounts:onboarding_dashboard')
                    else:
                        return redirect('accounts:dashboard')
                else:
                    return redirect('products:marketplace')
        
        return render(request, self.template_name, {'form': form})


class UserLogoutView(View):
    """Logout view."""
    
    def get(self, request):
        from django.contrib.auth import logout
        logout(request)
        messages.info(request, 'You have been logged out successfully.')
        return redirect('home')


class DashboardView(LoginRequiredMixin, TemplateView):
    """Main dashboard for authenticated users."""
    
    template_name = 'accounts/dashboard.html'
    
    def get_template_names(self):
        if self.request.user.is_creator:
            return ['accounts/creator_dashboard.html']
        else:
            return ['accounts/buyer_dashboard.html']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        if user.is_creator:
            creator_profile = getattr(user, 'creator_profile', None)
            context.update({
                'creator_profile': creator_profile,
                'total_products': creator_profile.total_products if creator_profile else 0,
                'total_sales': creator_profile.total_sales if creator_profile else 0,
                'store_url': creator_profile.get_store_url() if creator_profile else None,
            })
        else:
            # Buyer dashboard context
            context.update({
                'recent_purchases': [],  # Add recent purchases logic
                'wishlist_count': 0,     # Add wishlist logic
            })
        
        return context


class UserRegistrationView(View):
    """Generic user registration view (redirects to specific signup)."""
    
    def get(self, request):
        # Redirect to buyer signup by default
        return redirect('accounts:buyer_signup')


class ProfileUpdateView(LoginRequiredMixin, View):
    """User profile update view."""
    
    template_name = 'accounts/profile_update.html'
    
    def get(self, request):
        return render(request, self.template_name)


class CreatorProfileUpdateView(LoginRequiredMixin, View):
    """Creator profile update view."""
    
    template_name = 'accounts/creator_profile_update.html'
    
    def get(self, request):
        if not request.user.is_creator:
            messages.warning(request, 'You need to be a creator to access this page.')
            return redirect('accounts:profile_update')
        
        # Get or create creator profile
        creator_profile, created = CreatorProfile.objects.get_or_create(
            user=request.user,
            defaults={
                'store_name': f"{request.user.first_name}'s Store",
                'store_description': '',
                'business_category': 'other'
            }
        )
        
        form = CreatorProfileForm(instance=creator_profile)
        
        return render(request, self.template_name, {
            'form': form,
            'creator_profile': creator_profile
        })
    
    def post(self, request):
        if not request.user.is_creator:
            messages.warning(request, 'You need to be a creator to access this page.')
            return redirect('accounts:profile_update')
        
        # Get or create creator profile
        creator_profile, created = CreatorProfile.objects.get_or_create(
            user=request.user,
            defaults={
                'store_name': f"{request.user.first_name}'s Store",
                'store_description': '',
                'business_category': 'other'
            }
        )
        
        form = CreatorProfileForm(request.POST, request.FILES, instance=creator_profile)
        
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Your creator profile has been updated successfully!')
                return redirect('accounts:creator_profile_update')
            except Exception as e:
                messages.error(request, f'Error saving profile: {str(e)}')
        else:
            # Add form errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field.replace("_", " ").title()}: {error}')
        
        return render(request, self.template_name, {
            'form': form,
            'creator_profile': creator_profile
        })


class TwoFactorSetupView(LoginRequiredMixin, View):
    """Two-factor authentication setup."""
    
    template_name = 'accounts/two_factor_setup.html'
    
    def get(self, request):
        return render(request, self.template_name)


class GuestCheckoutView(View):
    """Guest checkout view."""
    
    template_name = 'accounts/guest_checkout.html'
    
    def get(self, request):
        return render(request, self.template_name)


@login_required
def disable_two_factor(request):
    """Disable two-factor authentication."""
    user = request.user
    user.two_factor_enabled = False
    user.backup_tokens = []
    user.save()
    
    messages.success(request, 'Two-factor authentication has been disabled.')
    return redirect('accounts:profile_update')


class DeleteAccountView(LoginRequiredMixin, View):
    """Handle account deletion."""
    
    def post(self, request):
        """Delete the user's account and all associated data."""
        user = request.user
        
        try:
            # Log out the user first
            from django.contrib.auth import logout
            logout(request)
            
            # Delete the user (this will cascade to related objects)
            user.delete()
            
            messages.success(request, 'Your account has been successfully deleted.')
            return redirect('/')
            
        except Exception as e:
            messages.error(request, 'There was an error deleting your account. Please contact support.')
            return redirect('accounts:profile_update')
    
    def get(self, request):
        """Redirect GET requests to profile page."""
        return redirect('accounts:profile_update')


class CreatorResourcesView(TemplateView):
    """Display creator resources and guides."""
    template_name = 'accounts/creator_resources.html'


class CreatorProfileView(DetailView):
    """Display a creator's public profile."""
    model = User
    template_name = 'accounts/creator_profile.html'
    context_object_name = 'creator'
    pk_url_kwarg = 'creator_id'
    
    def get_queryset(self):
        """Only show creators (users with role='creator')."""
        return User.objects.filter(role='creator').select_related('profile')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        creator = self.get_object()
        
        # Get creator's products (using status='published' instead of is_active)
        context['products'] = creator.products.filter(status='published').order_by('-created_at')[:6]
        context['total_products'] = creator.products.filter(status='published').count()
        
        # Calculate some stats (you can enhance this with real data)
        context['total_sales'] = getattr(creator, 'total_sales', 0)
        context['avg_rating'] = 4.5  # Placeholder - implement real rating system
        
        return context

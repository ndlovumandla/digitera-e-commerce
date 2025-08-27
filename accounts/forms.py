"""
Django forms for user authentication and profile management.
Includes SA-specific features, 2FA setup, and comprehensive validation.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import authenticate
from django.utils import timezone
# from phonenumber_field.formfields import PhoneNumberField
from .models import User, UserProfile, CreatorProfile
import re


class DigiteraUserCreationForm(UserCreationForm):
    """Enhanced user registration form with SA-specific features."""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'your.email@example.com'
        }),
        help_text=_('We will send a verification email to this address.')
    )
    
    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'First name'
        })
    )
    
    last_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Last name'
        })
    )
    
    phone_number = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': '+27 82 123 4567'
        }),
        help_text=_('South African phone number (optional)')
    )
    
    role = forms.ChoiceField(
        choices=[
            ('buyer', _('Buyer - I want to purchase digital products')),
            ('creator', _('Creator - I want to sell digital products')),
        ],
        widget=forms.RadioSelect(attrs={
            'class': 'text-blue-600'
        }),
        initial='buyer'
    )
    
    marketing_emails = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded text-blue-600 focus:ring-blue-500'
        }),
        label=_('I want to receive marketing emails about new features and promotions')
    )
    
    data_processing_consent = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded text-blue-600 focus:ring-blue-500'
        }),
        label=_('I consent to the processing of my personal data in accordance with POPIA')
    )
    
    terms_accepted = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded text-blue-600 focus:ring-blue-500'
        }),
        label=_('I agree to the Terms of Service and Privacy Policy')
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone_number', 'role', 
                 'password1', 'password2', 'marketing_emails', 'data_processing_consent', 'terms_accepted')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Confirm password'
        })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError(_('A user with this email already exists.'))
        return email

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number and User.objects.filter(phone_number=phone_number).exists():
            raise ValidationError(_('A user with this phone number already exists.'))
        return phone_number

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data.get('phone_number')
        user.role = self.cleaned_data['role']
        user.marketing_emails = self.cleaned_data['marketing_emails']
        user.data_processing_consent = self.cleaned_data['data_processing_consent']
        user.terms_accepted = self.cleaned_data['terms_accepted']
        
        if commit:
            user.save()
            # Create associated profile
            UserProfile.objects.create(user=user)
            # Create creator profile if user is a creator
            if user.role == 'creator':
                CreatorProfile.objects.create(
                    user=user,
                    store_name=f"{user.get_full_name()}'s Store",
                    store_slug=f"{user.first_name.lower()}-{user.last_name.lower()}-store"
                )
        return user


class DigiteraAuthenticationForm(AuthenticationForm):
    """Enhanced login form with better styling and security features."""
    
    username = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'your.email@example.com',
            'autocomplete': 'email'
        }),
        label=_('Email address')
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Password',
            'autocomplete': 'current-password'
        })
    )
    
    remember_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded text-blue-600 focus:ring-blue-500'
        }),
        label=_('Remember me for 30 days')
    )

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            # Check if account is locked
            try:
                user = User.objects.get(email=username)
                if user.account_locked_until and user.account_locked_until > timezone.now():
                    raise ValidationError(
                        _('Account is temporarily locked due to too many failed login attempts. Please try again later.')
                    )
            except User.DoesNotExist:
                pass

            self.user_cache = authenticate(
                self.request,
                username=username,
                password=password,
            )
            
            if self.user_cache is None:
                # Increment failed login attempts
                try:
                    user = User.objects.get(email=username)
                    user.failed_login_attempts += 1
                    if user.failed_login_attempts >= 5:
                        from django.utils import timezone
                        from datetime import timedelta
                        user.account_locked_until = timezone.now() + timedelta(minutes=30)
                    user.save()
                except User.DoesNotExist:
                    pass
                
                raise self.get_invalid_login_error()
            else:
                # Reset failed login attempts on successful login
                self.user_cache.failed_login_attempts = 0
                self.user_cache.account_locked_until = None
                self.user_cache.save()
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class UserProfileForm(forms.ModelForm):
    """Comprehensive user profile form with SA-specific fields."""
    
    class Meta:
        model = UserProfile
        fields = [
            'avatar', 'bio', 'date_of_birth', 'gender',
            'street_address', 'suburb', 'city', 'province', 'postal_code',
            'business_registration_number', 'tax_number',
            'language', 'website', 'twitter', 'instagram', 'linkedin',
            'email_notifications', 'sms_notifications', 'push_notifications'
        ]
        widgets = {
            'avatar': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100',
                'accept': 'image/*'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 4,
                'placeholder': 'Tell us about yourself...'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'type': 'date'
            }),
            'gender': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'street_address': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Street address'
            }),
            'suburb': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Suburb'
            }),
            'city': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'City'
            }),
            'province': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '0000'
            }),
            'business_registration_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'CIPC registration number'
            }),
            'tax_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'SARS tax reference number'
            }),
            'language': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'website': forms.URLInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'https://yourwebsite.com'
            }),
            'twitter': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '@username'
            }),
            'instagram': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '@username'
            }),
            'linkedin': forms.URLInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'https://linkedin.com/in/username'
            }),
            'email_notifications': forms.CheckboxInput(attrs={
                'class': 'rounded text-blue-600 focus:ring-blue-500'
            }),
            'sms_notifications': forms.CheckboxInput(attrs={
                'class': 'rounded text-blue-600 focus:ring-blue-500'
            }),
            'push_notifications': forms.CheckboxInput(attrs={
                'class': 'rounded text-blue-600 focus:ring-blue-500'
            }),
        }

    def clean_postal_code(self):
        postal_code = self.cleaned_data.get('postal_code')
        if postal_code and not re.match(r'^\d{4}$', postal_code):
            raise ValidationError(_('Please enter a valid 4-digit South African postal code.'))
        return postal_code

    def clean_twitter(self):
        twitter = self.cleaned_data.get('twitter')
        if twitter and not twitter.startswith('@'):
            twitter = '@' + twitter
        return twitter

    def clean_instagram(self):
        instagram = self.cleaned_data.get('instagram')
        if instagram and not instagram.startswith('@'):
            instagram = '@' + instagram
        return instagram


class CreatorProfileForm(forms.ModelForm):
    """Creator-specific profile form for storefront management."""
    
    terms_accepted = forms.BooleanField(
        required=True,
        error_messages={'required': 'You must accept the terms and conditions to become a creator.'}
    )
    
    class Meta:
        model = CreatorProfile
        fields = [
            'store_name', 'store_description', 'store_logo', 'store_banner',
            'primary_color', 'secondary_color', 'business_category',
            'years_in_business', 'bank_name', 'account_holder',
            'account_number', 'branch_code', 'account_type'
        ]
        widgets = {
            'store_name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Your Store Name'
            }),
            'store_description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'rows': 4,
                'placeholder': 'Describe what you offer to customers...'
            }),
            'store_logo': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100',
                'accept': 'image/*'
            }),
            'store_banner': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100',
                'accept': 'image/*'
            }),
            'primary_color': forms.TextInput(attrs={
                'class': 'w-20 h-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'type': 'color'
            }),
            'secondary_color': forms.TextInput(attrs={
                'class': 'w-20 h-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'type': 'color'
            }),
            'business_category': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'years_in_business': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': 0,
                'max': 50
            }),
            'bank_name': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'account_holder': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Account holder name'
            }),
            'account_number': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Bank account number'
            }),
            'branch_code': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': '123456'
            }),
            'account_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
        }

    def clean_store_name(self):
        store_name = self.cleaned_data.get('store_name')
        if store_name:
            # Check if store name is unique (excluding current instance)
            existing = CreatorProfile.objects.filter(store_name=store_name)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError(_('A store with this name already exists.'))
        return store_name

    def clean_account_number(self):
        account_number = self.cleaned_data.get('account_number')
        if account_number and not re.match(r'^\d{8,12}$', account_number):
            raise ValidationError(_('Please enter a valid SA bank account number (8-12 digits).'))
        return account_number

    def clean_branch_code(self):
        branch_code = self.cleaned_data.get('branch_code')
        if branch_code and not re.match(r'^\d{6}$', branch_code):
            raise ValidationError(_('Please enter a valid SA bank branch code (6 digits).'))
        return branch_code


class TwoFactorSetupForm(forms.Form):
    """Form for setting up 2FA with TOTP."""
    
    token = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-center text-lg tracking-widest',
            'placeholder': '123456',
            'autocomplete': 'off'
        }),
        help_text=_('Enter the 6-digit code from your authenticator app')
    )

    def clean_token(self):
        token = self.cleaned_data.get('token')
        if token and not re.match(r'^\d{6}$', token):
            raise ValidationError(_('Token must be exactly 6 digits.'))
        return token


class PasswordResetRequestForm(forms.Form):
    """Form for requesting password reset."""
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'your.email@example.com'
        }),
        help_text=_('Enter the email address associated with your account')
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and not User.objects.filter(email=email).exists():
            raise ValidationError(_('No account found with this email address.'))
        return email


class GuestCheckoutForm(forms.Form):
    """Form for guest users to provide basic information for checkout."""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'your.email@example.com'
        }),
        help_text=_('We will send your purchase confirmation to this email')
    )
    
    first_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'First name'
        })
    )
    
    last_name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': 'Last name'
        })
    )
    
    phone_number = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
            'placeholder': '+27 82 123 4567'
        }),
        help_text=_('Phone number for order updates (optional)')
    )
    
    create_account = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded text-blue-600 focus:ring-blue-500'
        }),
        label=_('Create an account for faster future purchases')
    )

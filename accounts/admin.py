"""
Django admin configuration for accounts app.
Enhanced admin interface with South African business features.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import User, UserProfile, CreatorProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Enhanced admin interface for User model."""
    
    # Display configuration
    list_display = [
        'email', 'full_name', 'role', 'is_verified', 
        'two_factor_enabled', 'vat_registered', 'date_joined', 'is_active'
    ]
    list_filter = [
        'role', 'is_verified', 'two_factor_enabled', 'vat_registered', 
        'is_active', 'is_staff', 'date_joined'
    ]
    search_fields = ['email', 'first_name', 'last_name', 'company_name', 'vat_number']
    readonly_fields = ['id', 'date_joined', 'last_login', 'created_at', 'updated_at', 'last_activity']
    ordering = ['-date_joined']
    
    # Fieldsets for organized display
    fieldsets = (
        (_('Authentication'), {
            'fields': ('id', 'email', 'password', 'is_verified', 'email_verification_token')
        }),
        (_('Personal Information'), {
            'fields': (
                'first_name', 'last_name', 'phone_number', 'address',
                'date_joined', 'last_login'
            )
        }),
        (_('South African Business Information'), {
            'fields': (
                'vat_registered', 'vat_number', 'company_name'
            ),
            'classes': ('collapse',)
        }),
        (_('Account & Permissions'), {
            'fields': (
                'role', 'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            )
        }),
        (_('Security & Privacy'), {
            'fields': (
                'two_factor_enabled', 'backup_tokens',
                'marketing_emails', 'data_processing_consent',
                'terms_accepted', 'terms_accepted_date'
            ),
            'classes': ('collapse',)
        }),
        (_('Security Tracking'), {
            'fields': (
                'last_login_ip', 'failed_login_attempts', 
                'account_locked_until'
            ),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'last_activity'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (_('Create New User'), {
            'fields': (
                'email', 'password1', 'password2', 
                'first_name', 'last_name', 'role'
            )
        }),
    )
    
    # Custom actions
    actions = ['verify_users', 'enable_2fa', 'reset_failed_logins']
    
    def verify_users(self, request, queryset):
        """Bulk verify selected users."""
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} users verified successfully.')
    verify_users.short_description = 'Mark selected users as verified'
    
    def enable_2fa(self, request, queryset):
        """Bulk enable 2FA for selected users."""
        updated = queryset.update(two_factor_enabled=True)
        self.message_user(request, f'2FA enabled for {updated} users.')
    enable_2fa.short_description = 'Enable 2FA for selected users'
    
    def reset_failed_logins(self, request, queryset):
        """Reset failed login attempts for selected users."""
        updated = queryset.update(failed_login_attempts=0, account_locked_until=None)
        self.message_user(request, f'Failed login attempts reset for {updated} users.')
    reset_failed_logins.short_description = 'Reset failed login attempts'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for UserProfile model."""
    
    list_display = [
        'user', 'get_phone_number', 'province', 'city', 
        'language', 'identity_verified'
    ]
    list_filter = [
        'province', 'language', 'identity_verified', 
        'bank_account_verified', 'email_notifications', 'created_at'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name',
        'street_address', 'city', 'business_registration_number'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    def get_phone_number(self, obj):
        """Get user's phone number."""
        return obj.user.phone_number or '-'
    get_phone_number.short_description = 'Phone Number'


@admin.register(CreatorProfile)
class CreatorProfileAdmin(admin.ModelAdmin):
    """Admin interface for CreatorProfile model."""
    
    list_display = [
        'store_name', 'user', 'status', 'verified', 
        'business_category', 'total_sales', 'total_products'
    ]
    list_filter = [
        'status', 'verified', 'featured', 'business_category', 
        'current_marketing_package', 'created_at'
    ]
    search_fields = [
        'store_name', 'store_slug', 'user__email', 
        'store_description', 'business_category'
    ]
    readonly_fields = [
        'store_slug', 'total_sales', 'total_products', 
        'total_customers', 'rating', 'review_count',
        'created_at', 'updated_at'
    ]
    
    # Custom actions
    actions = ['verify_creators', 'feature_creators', 'approve_creators']
    
    def verify_creators(self, request, queryset):
        """Verify selected creators."""
        updated = queryset.update(verified=True)
        self.message_user(request, f'{updated} creators verified successfully.')
    verify_creators.short_description = 'Mark selected creators as verified'
    
    def feature_creators(self, request, queryset):
        """Feature selected creators."""
        updated = queryset.update(featured=True)
        self.message_user(request, f'{updated} creators featured successfully.')
    feature_creators.short_description = 'Mark selected creators as featured'
    
    def approve_creators(self, request, queryset):
        """Approve pending creators."""
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} creators approved successfully.')
    approve_creators.short_description = 'Approve selected creators'

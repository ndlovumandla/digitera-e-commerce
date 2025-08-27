"""
Django models for the accounts app.
Contains user management, authentication, and profile models.
"""

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.core.validators import EmailValidator
from django.utils.translation import gettext_lazy as _


class UserRole(models.TextChoices):
    """User role choices for role-based access control."""
    CREATOR = 'creator', _('Creator')
    BUYER = 'buyer', _('Buyer')
    ADMIN = 'admin', _('Admin')
    MODERATOR = 'moderator', _('Moderator')


class CustomUserManager(UserManager):
    """Custom manager for User model without username field."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('role', UserRole.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model for Digitera platform.
    Extends Django's AbstractUser to include additional fields required for the platform.
    """
    # Remove username field and use email for authentication
    username = None
    
    # Primary identification
    email = models.EmailField(
        _('email address'),
        unique=True,
        validators=[EmailValidator()],
        help_text=_('Required. Enter a valid email address.')
    )
    
    # User details
    first_name = models.CharField(_('first name'), max_length=100, blank=True)
    last_name = models.CharField(_('last name'), max_length=100, blank=True)
    phone = models.CharField(_('phone number'), max_length=20, blank=True)
    
    # Address information
    address = models.TextField(_('address'), blank=True)
    
    # Business information
    vat_registered = models.BooleanField(
        _('VAT registered'),
        default=False,
        help_text=_('Is this user/business registered for VAT in South Africa?')
    )
    
    # Role and permissions
    role = models.CharField(
        _('user role'),
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.BUYER
    )
    
    # Account status
    is_verified = models.BooleanField(
        _('verified'),
        default=False,
        help_text=_('Designates whether this user has verified their email address.')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    # Use email as the unique identifier for authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    # Use custom manager
    objects = CustomUserManager()
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['is_verified']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"
    
    @property
    def full_name(self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def is_creator(self):
        """Check if user is a creator."""
        return self.role == UserRole.CREATOR
    
    @property
    def is_buyer(self):
        """Check if user is a buyer."""
        return self.role == UserRole.BUYER
    
    def can_create_storefront(self):
        """Check if user can create a storefront."""
        return self.role in [UserRole.CREATOR, UserRole.ADMIN]


class DeviceType(models.TextChoices):
    """Device type choices for user sessions."""
    DESKTOP = 'desktop', _('Desktop')
    MOBILE = 'mobile', _('Mobile')
    TABLET = 'tablet', _('Tablet')
    UNKNOWN = 'unknown', _('Unknown')


class UserSession(models.Model):
    """
    Model to track user sessions for analytics and security.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sessions'
    )
    session_id = models.CharField(_('session ID'), max_length=255, unique=True)
    device_type = models.CharField(
        _('device type'),
        max_length=20,
        choices=DeviceType.choices,
        default=DeviceType.UNKNOWN
    )
    actions = models.JSONField(
        _('user actions'),
        default=dict,
        help_text=_('JSON data containing user actions during the session')
    )
    started_at = models.DateTimeField(_('started at'), auto_now_add=True)
    ended_at = models.DateTimeField(_('ended at'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('User Session')
        verbose_name_plural = _('User Sessions')
        db_table = 'user_sessions'
        indexes = [
            models.Index(fields=['user', 'started_at']),
            models.Index(fields=['session_id']),
            models.Index(fields=['device_type']),
        ]
    
    def __str__(self):
        return f"Session for {self.user.email} - {self.started_at}"


class RequestMethod(models.TextChoices):
    """HTTP request method choices."""
    GET = 'GET', _('GET')
    POST = 'POST', _('POST')
    PUT = 'PUT', _('PUT')
    PATCH = 'PATCH', _('PATCH')
    DELETE = 'DELETE', _('DELETE')
    OPTIONS = 'OPTIONS', _('OPTIONS')
    HEAD = 'HEAD', _('HEAD')


class APILog(models.Model):
    """
    Model to log API requests for monitoring and debugging.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='api_logs'
    )
    endpoint = models.CharField(_('API endpoint'), max_length=255)
    request_method = models.CharField(
        _('request method'),
        max_length=10,
        choices=RequestMethod.choices
    )
    status_code = models.IntegerField(_('HTTP status code'))
    timestamp = models.DateTimeField(_('timestamp'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('API Log')
        verbose_name_plural = _('API Logs')
        db_table = 'api_logs'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['endpoint']),
            models.Index(fields=['status_code']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        user_email = self.user.email if self.user else 'Anonymous'
        return f"{self.request_method} {self.endpoint} - {user_email}"

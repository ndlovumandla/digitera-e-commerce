"""
Django filters for Products API.
Includes advanced filtering, search, and sorting capabilities.
"""

import django_filters
from django.db.models import Q
from .models import Product, Category, Tag


class ProductFilter(django_filters.FilterSet):
    """Advanced filter for products with multiple criteria."""
    
    # Basic filters
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    creator = django_filters.NumberFilter(field_name='creator__id')
    category = django_filters.ModelChoiceFilter(queryset=Category.objects.all())
    
    # Price filters
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    price_range = django_filters.RangeFilter(field_name='price')
    
    # Boolean filters
    is_featured = django_filters.BooleanFilter()
    is_active = django_filters.BooleanFilter()
    is_on_sale = django_filters.BooleanFilter(method='filter_on_sale')
    
    # Status and visibility
    status = django_filters.ChoiceFilter(choices=Product.ProductStatus.choices)
    visibility = django_filters.ChoiceFilter(choices=Product.ProductVisibility.choices)
    
    # Tags (multiple selection)
    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__id',
        to_field_name='id'
    )
    tag_names = django_filters.CharFilter(method='filter_by_tag_names')
    
    # Category hierarchy
    category_tree = django_filters.NumberFilter(method='filter_by_category_tree')
    
    # Date filters
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    updated_after = django_filters.DateTimeFilter(field_name='updated_at', lookup_expr='gte')
    
    # Product type filters
    product_type = django_filters.CharFilter(method='filter_by_product_type')
    
    # Search across multiple fields
    search = django_filters.CharFilter(method='filter_search')
    
    # Rating filter
    min_rating = django_filters.NumberFilter(method='filter_min_rating')
    
    # Sales performance
    min_sales = django_filters.NumberFilter(method='filter_min_sales')
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'creator', 'category',
            'min_price', 'max_price', 'price_range',
            'is_featured', 'is_active', 'is_on_sale',
            'status', 'visibility', 'tags', 'tag_names',
            'category_tree', 'created_after', 'created_before',
            'updated_after', 'product_type', 'search',
            'min_rating', 'min_sales'
        ]
    
    def filter_on_sale(self, queryset, name, value):
        """Filter products that are on sale."""
        if value:
            return queryset.filter(sale_price__isnull=False, sale_price__lt=models.F('price'))
        return queryset.filter(Q(sale_price__isnull=True) | Q(sale_price__gte=models.F('price')))
    
    def filter_by_tag_names(self, queryset, name, value):
        """Filter by tag names (comma-separated)."""
        if value:
            tag_names = [name.strip() for name in value.split(',')]
            return queryset.filter(tags__name__in=tag_names).distinct()
        return queryset
    
    def filter_by_category_tree(self, queryset, name, value):
        """Filter by category and its subcategories."""
        try:
            category = Category.objects.get(id=value)
            # Get all subcategories
            subcategories = category.get_descendants(include_self=True)
            return queryset.filter(category__in=subcategories)
        except Category.DoesNotExist:
            return queryset
    
    def filter_by_product_type(self, queryset, name, value):
        """Filter by product type (polymorphic)."""
        type_map = {
            'digitaldownload': 'DigitalDownload',
            'membership': 'Membership',
            'community': 'Community',
            'course': 'Course',
            'event': 'Event'
        }
        
        if value.lower() in type_map:
            model_name = type_map[value.lower()]
            return queryset.filter(polymorphic_ctype__model=model_name.lower())
        return queryset
    
    def filter_search(self, queryset, name, value):
        """Search across multiple fields."""
        if value:
            return queryset.filter(
                Q(name__icontains=value) |
                Q(description__icontains=value) |
                Q(short_description__icontains=value) |
                Q(tags__name__icontains=value) |
                Q(category__name__icontains=value) |
                Q(creator__first_name__icontains=value) |
                Q(creator__last_name__icontains=value)
            ).distinct()
        return queryset
    
    def filter_min_rating(self, queryset, name, value):
        """Filter by minimum average rating."""
        from django.db.models import Avg
        if value:
            return queryset.annotate(
                avg_rating=Avg('reviews__rating')
            ).filter(avg_rating__gte=value)
        return queryset
    
    def filter_min_sales(self, queryset, name, value):
        """Filter by minimum sales count."""
        from django.db.models import Count
        if value:
            return queryset.annotate(
                sales_count=Count('order_items')
            ).filter(sales_count__gte=value)
        return queryset


class DigitalDownloadFilter(ProductFilter):
    """Specialized filter for digital downloads."""
    
    # Digital download specific filters
    file_type = django_filters.CharFilter(method='filter_by_file_type')
    license_type = django_filters.ChoiceFilter(choices=[
        ('personal', 'Personal Use'),
        ('commercial', 'Commercial Use'),
        ('extended', 'Extended License'),
        ('royalty_free', 'Royalty Free')
    ])
    instant_download = django_filters.BooleanFilter()
    max_file_size = django_filters.NumberFilter(method='filter_max_file_size')
    
    class Meta(ProductFilter.Meta):
        fields = ProductFilter.Meta.fields + [
            'file_type', 'license_type', 'instant_download', 'max_file_size'
        ]
    
    def filter_by_file_type(self, queryset, name, value):
        """Filter by file type in allowed file types."""
        if value:
            return queryset.filter(allowed_file_types__contains=[value])
        return queryset
    
    def filter_max_file_size(self, queryset, name, value):
        """Filter by maximum file size."""
        if value:
            return queryset.filter(file_size_limit__lte=value)
        return queryset


class EventFilter(ProductFilter):
    """Specialized filter for events."""
    
    # Event specific filters
    event_type = django_filters.ChoiceFilter(choices=[
        ('workshop', 'Workshop'),
        ('conference', 'Conference'),
        ('webinar', 'Webinar'),
        ('meetup', 'Meetup'),
        ('course', 'Course'),
        ('networking', 'Networking')
    ])
    
    # Date filters
    start_date_after = django_filters.DateTimeFilter(field_name='start_date', lookup_expr='gte')
    start_date_before = django_filters.DateTimeFilter(field_name='start_date', lookup_expr='lte')
    end_date_after = django_filters.DateTimeFilter(field_name='end_date', lookup_expr='gte')
    end_date_before = django_filters.DateTimeFilter(field_name='end_date', lookup_expr='lte')
    
    # Location filters
    location = django_filters.CharFilter(field_name='location', lookup_expr='icontains')
    timezone = django_filters.CharFilter()
    
    # Capacity filters
    min_capacity = django_filters.NumberFilter(field_name='max_attendees', lookup_expr='gte')
    max_capacity = django_filters.NumberFilter(field_name='max_attendees', lookup_expr='lte')
    has_capacity = django_filters.BooleanFilter(method='filter_has_capacity')
    
    # Registration status
    registration_open = django_filters.BooleanFilter(method='filter_registration_open')
    
    class Meta(ProductFilter.Meta):
        fields = ProductFilter.Meta.fields + [
            'event_type', 'start_date_after', 'start_date_before',
            'end_date_after', 'end_date_before', 'location',
            'timezone', 'min_capacity', 'max_capacity',
            'has_capacity', 'registration_open'
        ]
    
    def filter_has_capacity(self, queryset, name, value):
        """Filter events that have available capacity."""
        if value:
            # This would require calculating current registrations
            # For now, just filter events with max_attendees set
            return queryset.filter(max_attendees__isnull=False)
        return queryset
    
    def filter_registration_open(self, queryset, name, value):
        """Filter events with open registration."""
        from django.utils import timezone
        now = timezone.now()
        
        if value:
            return queryset.filter(
                Q(registration_deadline__isnull=True) |
                Q(registration_deadline__gt=now)
            ).filter(start_date__gt=now)
        else:
            return queryset.filter(
                Q(registration_deadline__lte=now) |
                Q(start_date__lte=now)
            )


class CourseFilter(ProductFilter):
    """Specialized filter for courses."""
    
    # Course specific filters
    course_level = django_filters.ChoiceFilter(choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert')
    ])
    
    # Duration filters
    min_duration = django_filters.NumberFilter(field_name='duration_hours', lookup_expr='gte')
    max_duration = django_filters.NumberFilter(field_name='duration_hours', lookup_expr='lte')
    
    # Language filter
    language = django_filters.CharFilter()
    
    # Certificate availability
    has_certificate = django_filters.BooleanFilter()
    
    # Prerequisites
    has_prerequisites = django_filters.BooleanFilter(method='filter_has_prerequisites')
    
    class Meta(ProductFilter.Meta):
        fields = ProductFilter.Meta.fields + [
            'course_level', 'min_duration', 'max_duration',
            'language', 'has_certificate', 'has_prerequisites'
        ]
    
    def filter_has_prerequisites(self, queryset, name, value):
        """Filter courses with/without prerequisites."""
        if value:
            return queryset.filter(prerequisites__isnull=False)
        return queryset.filter(prerequisites__isnull=True)


class MembershipFilter(ProductFilter):
    """Specialized filter for memberships."""
    
    # Membership specific filters
    membership_level = django_filters.ChoiceFilter(choices=[
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('vip', 'VIP'),
        ('enterprise', 'Enterprise')
    ])
    
    billing_cycle = django_filters.ChoiceFilter(choices=[
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually')
    ])
    
    # Trial period
    has_trial = django_filters.BooleanFilter(method='filter_has_trial')
    min_trial_days = django_filters.NumberFilter(field_name='trial_period_days', lookup_expr='gte')
    
    # Auto renewal
    auto_renewal = django_filters.BooleanFilter()
    
    # Member limit
    has_member_limit = django_filters.BooleanFilter(method='filter_has_member_limit')
    
    class Meta(ProductFilter.Meta):
        fields = ProductFilter.Meta.fields + [
            'membership_level', 'billing_cycle', 'has_trial',
            'min_trial_days', 'auto_renewal', 'has_member_limit'
        ]
    
    def filter_has_trial(self, queryset, name, value):
        """Filter memberships with/without trial period."""
        if value:
            return queryset.filter(trial_period_days__gt=0)
        return queryset.filter(trial_period_days__lte=0)
    
    def filter_has_member_limit(self, queryset, name, value):
        """Filter memberships with/without member limits."""
        if value:
            return queryset.filter(member_limit__isnull=False)
        return queryset.filter(member_limit__isnull=True)

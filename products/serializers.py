"""
DRF Serializers for Products models.
Includes polymorphic serialization and comprehensive field handling.
"""

from rest_framework import serializers
from rest_framework.fields import SerializerMethodField
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import (
    Product, DigitalDownload, Membership, Community, Course, Event,
    Category, Tag, ProductReview, ProductAnalytics
)

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for product categories."""
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    children_count = serializers.SerializerMethodField()
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'parent', 'parent_name',
            'image', 'is_active', 'sort_order', 'created_at',
            'children_count', 'products_count'
        ]
        read_only_fields = ['id', 'created_at', 'slug']
    
    def get_children_count(self, obj):
        return obj.children.count()
    
    def get_products_count(self, obj):
        return obj.products.count()


class TagSerializer(serializers.ModelSerializer):
    """Serializer for product tags."""
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'color', 'is_ai_generated', 'products_count']
        read_only_fields = ['id', 'slug']
    
    def get_products_count(self, obj):
        return obj.products.count()


class ProductReviewSerializer(serializers.ModelSerializer):
    """Serializer for product reviews."""
    reviewer_name = serializers.CharField(source='reviewer.get_full_name', read_only=True)
    reviewer_email = serializers.CharField(source='reviewer.email', read_only=True)
    
    class Meta:
        model = ProductReview
        fields = [
            'id', 'product', 'reviewer', 'reviewer_name', 'reviewer_email',
            'rating', 'title', 'content', 'is_verified_purchase',
            'is_approved', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'is_verified_purchase', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        # Set reviewer to current user if not provided
        if 'reviewer' not in validated_data:
            validated_data['reviewer'] = self.context['request'].user
        return super().create(validated_data)


class ProductAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for product analytics."""
    
    class Meta:
        model = ProductAnalytics
        fields = [
            'id', 'product', 'views', 'unique_views', 'sales_count',
            'revenue', 'conversion_rate', 'bounce_rate', 'avg_session_duration',
            'date', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class BaseProductSerializer(serializers.ModelSerializer):
    """Base serializer for all product types."""
    creator_name = serializers.CharField(source='creator.get_full_name', read_only=True)
    creator_email = serializers.CharField(source='creator.email', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(), many=True, write_only=True, source='tags'
    )
    reviews = ProductReviewSerializer(many=True, read_only=True)
    analytics = ProductAnalyticsSerializer(many=True, read_only=True)
    
    # Computed fields
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    is_on_sale = serializers.SerializerMethodField()
    discounted_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'slug', 'description', 'short_description',
            'creator', 'creator_name', 'creator_email',
            'category', 'category_name', 'tags', 'tag_ids',
            'price', 'sale_price', 'currency', 'is_on_sale', 'discounted_price',
            'is_active', 'is_featured', 'status', 'visibility',
            'seo_title', 'seo_description', 'featured_image',
            'gallery_images', 'demo_url', 'preview_url',
            'ai_tags', 'recommendation_score', 'metadata',
            'created_at', 'updated_at', 'published_at',
            'reviews', 'analytics',
            'average_rating', 'review_count'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at', 'recommendation_score']
    
    def get_average_rating(self, obj):
        reviews = obj.reviews.filter(is_approved=True)
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return None
    
    def get_review_count(self, obj):
        return obj.reviews.filter(is_approved=True).count()
    
    def get_is_on_sale(self, obj):
        return obj.sale_price is not None and obj.sale_price < obj.price
    
    def get_discounted_price(self, obj):
        if self.get_is_on_sale(obj):
            return obj.sale_price
        return obj.price


class DigitalDownloadSerializer(BaseProductSerializer):
    """Serializer for digital download products."""
    download_count = serializers.SerializerMethodField()
    total_file_size = serializers.SerializerMethodField()
    
    class Meta(BaseProductSerializer.Meta):
        model = DigitalDownload
        fields = BaseProductSerializer.Meta.fields + [
            'file_size_limit', 'download_limit', 'license_type',
            'allowed_file_types', 'instant_download', 'requires_registration',
            'download_instructions', 'download_count', 'total_file_size'
        ]
    
    def get_download_count(self, obj):
        # This would need to be tracked in OrderItems or Downloads model
        return 0  # Placeholder
    
    def get_total_file_size(self, obj):
        total_size = sum(f.file_size or 0 for f in obj.files.all())
        return round(total_size / (1024 * 1024), 2) if total_size else 0


class MembershipSerializer(BaseProductSerializer):
    """Serializer for membership products."""
    active_subscribers = serializers.SerializerMethodField()
    
    class Meta(BaseProductSerializer.Meta):
        model = Membership
        fields = BaseProductSerializer.Meta.fields + [
            'membership_level', 'billing_cycle', 'trial_period_days',
            'benefits', 'access_level', 'auto_renewal', 'member_limit',
            'onboarding_materials', 'member_portal_url', 'active_subscribers'
        ]
    
    def get_active_subscribers(self, obj):
        # This would come from Subscription model
        return 0  # Placeholder


class CommunitySerializer(BaseProductSerializer):
    """Serializer for community products."""
    member_count = serializers.SerializerMethodField()
    
    class Meta(BaseProductSerializer.Meta):
        model = Community
        fields = BaseProductSerializer.Meta.fields + [
            'community_type', 'access_level', 'moderation_level',
            'member_limit', 'is_private', 'join_approval_required',
            'community_rules', 'featured_content', 'discussion_categories',
            'member_count'
        ]
    
    def get_member_count(self, obj):
        # This would come from community membership tracking
        return 0  # Placeholder


class CourseSerializer(BaseProductSerializer):
    """Serializer for course products."""
    enrolled_count = serializers.SerializerMethodField()
    completion_rate = serializers.SerializerMethodField()
    
    class Meta(BaseProductSerializer.Meta):
        model = Course
        fields = BaseProductSerializer.Meta.fields + [
            'course_level', 'duration_hours', 'language', 'has_certificate',
            'prerequisites', 'learning_outcomes', 'course_modules',
            'instructor_bio', 'course_materials', 'assignment_types',
            'enrolled_count', 'completion_rate'
        ]
    
    def get_enrolled_count(self, obj):
        # This would come from course enrollment tracking
        return 0  # Placeholder
    
    def get_completion_rate(self, obj):
        # This would be calculated from course progress data
        return None  # Placeholder


class EventSerializer(BaseProductSerializer):
    """Serializer for event products."""
    attendee_count = serializers.SerializerMethodField()
    is_past_event = serializers.SerializerMethodField()
    spots_remaining = serializers.SerializerMethodField()
    
    class Meta(BaseProductSerializer.Meta):
        model = Event
        fields = BaseProductSerializer.Meta.fields + [
            'event_type', 'start_date', 'end_date', 'timezone',
            'location', 'venue_details', 'max_attendees',
            'registration_deadline', 'event_agenda', 'speaker_info',
            'event_materials', 'networking_info', 'dress_code',
            'special_requirements', 'attendee_count', 'is_past_event',
            'spots_remaining'
        ]
    
    def get_attendee_count(self, obj):
        # This would come from event registration tracking
        return 0  # Placeholder
    
    def get_is_past_event(self, obj):
        return obj.end_date < timezone.now() if obj.end_date else False
    
    def get_spots_remaining(self, obj):
        if obj.max_attendees:
            return obj.max_attendees - self.get_attendee_count(obj)
        return None


class ProductSerializer(serializers.ModelSerializer):
    """Polymorphic serializer that handles all product types."""
    
    def to_representation(self, instance):
        """Return the appropriate serializer based on product type."""
        if isinstance(instance, DigitalDownload):
            return DigitalDownloadSerializer(instance, context=self.context).data
        elif isinstance(instance, Membership):
            return MembershipSerializer(instance, context=self.context).data
        elif isinstance(instance, Community):
            return CommunitySerializer(instance, context=self.context).data
        elif isinstance(instance, Course):
            return CourseSerializer(instance, context=self.context).data
        elif isinstance(instance, Event):
            return EventSerializer(instance, context=self.context).data
        else:
            return BaseProductSerializer(instance, context=self.context).data
    
    class Meta:
        model = Product
        fields = '__all__'


# Marketplace-specific serializers
class MarketplaceProductSerializer(serializers.ModelSerializer):
    """Enhanced serializer for marketplace discovery with all required fields."""
    creator_name = serializers.CharField(source='creator.get_full_name', read_only=True)
    creator_avatar = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_slug = serializers.CharField(source='category.slug', read_only=True)
    product_type = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    is_trending = serializers.SerializerMethodField()
    is_new = serializers.SerializerMethodField()
    sales_count_24h = serializers.IntegerField(source='last_24h_sales', read_only=True)
    revenue_24h = serializers.DecimalField(source='last_24h_revenue', max_digits=10, decimal_places=2, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'slug', 'description', 'short_description',
            'creator_name', 'creator_avatar', 'category_name', 'category_slug',
            'product_type', 'price', 'sale_price', 'currency',
            'featured_image', 'gallery_images', 'demo_url', 'preview_url',
            'is_featured', 'is_marketplace_promoted', 'status',
            'average_rating', 'review_count', 'view_count',
            'is_trending', 'is_new', 'trending_score', 'discovery_rank',
            'commission_rate', 'sales_count_24h', 'revenue_24h',
            'tags', 'published_at', 'created_at'
        ]
    
    def get_creator_avatar(self, obj):
        if hasattr(obj.creator, 'profile') and obj.creator.profile.avatar:
            return self.context['request'].build_absolute_uri(obj.creator.profile.avatar.url)
        return None
    
    def get_product_type(self, obj):
        return obj.__class__.__name__.lower()
    
    def get_average_rating(self, obj):
        reviews = obj.reviews.filter(is_approved=True)
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return None
    
    def get_review_count(self, obj):
        return obj.reviews.filter(is_approved=True).count()
    
    def get_is_trending(self, obj):
        return obj.trending_score > 0
    
    def get_is_new(self, obj):
        from django.utils import timezone
        from datetime import timedelta
        return obj.published_at and obj.published_at >= timezone.now() - timedelta(days=7)


class TrendingProductSerializer(serializers.ModelSerializer):
    """Optimized serializer for trending products with minimal data."""
    creator_name = serializers.CharField(source='creator.get_full_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    average_rating = serializers.SerializerMethodField()
    sales_velocity = serializers.SerializerMethodField()
    trend_direction = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'slug', 'creator_name', 'category_name',
            'price', 'sale_price', 'currency', 'featured_image',
            'trending_score', 'last_24h_sales', 'last_24h_revenue',
            'average_rating', 'sales_velocity', 'trend_direction'
        ]
    
    def get_average_rating(self, obj):
        return obj.rating_average if hasattr(obj, 'rating_average') else None
    
    def get_sales_velocity(self, obj):
        """Calculate sales velocity (sales per hour in last 24h)."""
        if obj.last_24h_sales:
            return round(obj.last_24h_sales / 24, 2)
        return 0
    
    def get_trend_direction(self, obj):
        """Determine if product is trending up, down, or stable."""
        # This would compare with previous period - simplified for now
        if obj.trending_score > 50:
            return 'up'
        elif obj.trending_score > 20:
            return 'stable'
        else:
            return 'down'


class CategoryTreeSerializer(serializers.ModelSerializer):
    """Hierarchical category serializer for marketplace navigation."""
    children = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    trending_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'image',
            'sort_order', 'children', 'product_count', 'trending_count'
        ]
    
    def get_children(self, obj):
        children = obj.children.filter(is_active=True).order_by('sort_order')
        return CategoryTreeSerializer(children, many=True, context=self.context).data
    
    def get_product_count(self, obj):
        return obj.products.filter(status=Product.ProductStatus.PUBLISHED).count()
    
    def get_trending_count(self, obj):
        return obj.products.filter(
            status=Product.ProductStatus.PUBLISHED,
            trending_score__gt=0
        ).count()


class SearchResultSerializer(serializers.ModelSerializer):
    """Serializer for search results with highlighting."""
    creator_name = serializers.CharField(source='creator.get_full_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    product_type = serializers.SerializerMethodField()
    match_score = serializers.SerializerMethodField()
    highlighted_title = serializers.SerializerMethodField()
    highlighted_description = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'slug', 'short_description',
            'creator_name', 'category_name', 'product_type',
            'price', 'sale_price', 'currency', 'featured_image',
            'average_rating', 'review_count', 'match_score',
            'highlighted_title', 'highlighted_description'
        ]
    
    def get_product_type(self, obj):
        return obj.__class__.__name__.lower()
    
    def get_match_score(self, obj):
        # Search relevance score (would be calculated by search backend)
        return 0.85  # Placeholder
    
    def get_highlighted_title(self, obj):
        # Would include highlighting from search backend
        return obj.title
    
    def get_highlighted_description(self, obj):
        # Would include highlighting from search backend
        return obj.short_description


class CreatorSpotlightSerializer(serializers.ModelSerializer):
    """Serializer for featuring creators in marketplace."""
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    profile_data = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    total_sales = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    featured_products = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'full_name', 'email',
            'profile_data', 'product_count', 'total_sales',
            'average_rating', 'featured_products'
        ]
    
    def get_profile_data(self, obj):
        if hasattr(obj, 'profile'):
            return {
                'bio': obj.profile.bio,
                'avatar': self.context['request'].build_absolute_uri(obj.profile.avatar.url) if obj.profile.avatar else None,
                'website': obj.profile.website,
                'social_links': getattr(obj.profile, 'social_links', {}),
                'verified': getattr(obj.profile, 'is_verified', False)
            }
        return None
    
    def get_product_count(self, obj):
        return obj.products.filter(status=Product.ProductStatus.PUBLISHED).count()
    
    def get_total_sales(self, obj):
        # This would come from order analytics
        return 0  # Placeholder
    
    def get_average_rating(self, obj):
        # Average rating across all creator's products
        return 4.5  # Placeholder
    
    def get_featured_products(self, obj):
        featured = obj.products.filter(
            status=Product.ProductStatus.PUBLISHED,
            is_featured=True
        )[:3]
        return MarketplaceProductSerializer(
            featured, many=True, context=self.context
        ).data


# List serializers for better performance
class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for product lists."""
    creator_name = serializers.CharField(source='creator.get_full_name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    product_type = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'slug', 'short_description',
            'creator_name', 'category_name', 'product_type',
            'price', 'sale_price', 'currency', 'featured_image',
            'is_featured', 'status', 'average_rating', 'review_count',
            'created_at', 'updated_at'
        ]
    
    def get_product_type(self, obj):
        return obj.__class__.__name__.lower()
    
    def get_average_rating(self, obj):
        # Optimized for list view - could be pre-calculated
        return 4.5  # Placeholder
    
    def get_review_count(self, obj):
        # Optimized for list view - could be pre-calculated
        return 10  # Placeholder

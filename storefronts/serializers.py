"""
DRF Serializers for Storefronts models.
Includes drag-and-drop builder simulation and customization handling.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Storefront, StorefrontTheme, StorefrontAnalytics, StorefrontCustomization
)

User = get_user_model()


class StorefrontThemeSerializer(serializers.ModelSerializer):
    """Serializer for storefront themes."""
    usage_count = serializers.SerializerMethodField()
    
    class Meta:
        model = StorefrontTheme
        fields = [
            'id', 'name', 'description', 'thumbnail', 'preview_url',
            'is_premium', 'price', 'category', 'color_scheme',
            'layout_config', 'custom_css', 'is_active',
            'created_at', 'updated_at', 'usage_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_usage_count(self, obj):
        return obj.storefronts.count()


class StorefrontAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for storefront analytics."""
    
    class Meta:
        model = StorefrontAnalytics
        fields = [
            'id', 'storefront', 'page_views', 'unique_visitors',
            'bounce_rate', 'avg_session_duration', 'conversion_rate',
            'revenue', 'orders_count', 'traffic_sources',
            'popular_products', 'visitor_countries', 'device_breakdown',
            'date', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class StorefrontCustomizationSerializer(serializers.ModelSerializer):
    """Serializer for storefront customization settings."""
    
    class Meta:
        model = StorefrontCustomization
        fields = [
            'id', 'storefront', 'custom_css', 'custom_html',
            'header_code', 'footer_code', 'custom_fonts',
            'animation_settings', 'interaction_effects',
            'mobile_optimizations', 'accessibility_features',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class StorefrontSerializer(serializers.ModelSerializer):
    """Main serializer for storefronts with drag-and-drop builder support."""
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    owner_email = serializers.CharField(source='owner.email', read_only=True)
    theme_name = serializers.CharField(source='theme.name', read_only=True)
    
    # Related objects
    customization = StorefrontCustomizationSerializer(read_only=True)
    analytics = StorefrontAnalyticsSerializer(many=True, read_only=True)
    
    # Computed fields
    total_products = serializers.SerializerMethodField()
    total_revenue = serializers.SerializerMethodField()
    monthly_visitors = serializers.SerializerMethodField()
    
    class Meta:
        model = Storefront
        fields = [
            'id', 'name', 'slug', 'description', 'tagline',
            'owner', 'owner_name', 'owner_email',
            'theme', 'theme_name', 'custom_domain', 'subdomain',
            'logo', 'favicon', 'banner_image',
            
            # Drag-and-drop builder fields
            'layout_config', 'color_scheme', 'typography',
            'navigation_config', 'footer_config', 'sidebar_config',
            'homepage_sections', 'product_grid_config',
            
            # Settings
            'is_active', 'is_published', 'maintenance_mode',
            'password_protected', 'store_password',
            'currency', 'timezone', 'language',
            
            # Features
            'features_enabled', 'payment_methods', 'shipping_options',
            'tax_settings', 'notification_settings',
            
            # Business info
            'business_info', 'contact_info', 'legal_pages',
            
            # SEO and analytics
            'analytics_enabled', 'google_analytics_id',
            
            # Customization
            'customization',
            
            # Analytics and computed fields
            'analytics', 'total_products', 'total_revenue',
            'monthly_visitors',
            
            'created_at', 'updated_at', 'published_at'
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at']
    
    def get_total_products(self, obj):
        """Get total number of products in this storefront."""
        # This would be calculated based on products assigned to storefront
        return 0  # Placeholder
    
    def get_total_revenue(self, obj):
        """Get total revenue for this storefront."""
        # This would be calculated from orders
        return "0.00"  # Placeholder
    
    def get_monthly_visitors(self, obj):
        """Get monthly visitor count."""
        # This would be calculated from analytics
        return 0  # Placeholder
    
    def validate_subdomain(self, value):
        """Validate subdomain format and availability."""
        import re
        if not re.match(r'^[a-zA-Z0-9-]+$', value):
            raise serializers.ValidationError(
                "Subdomain can only contain letters, numbers, and hyphens."
            )
        if value.startswith('-') or value.endswith('-'):
            raise serializers.ValidationError(
                "Subdomain cannot start or end with a hyphen."
            )
        return value
    
    def validate_layout_config(self, value):
        """Validate drag-and-drop layout configuration."""
        required_keys = ['header', 'main', 'footer']
        if not all(key in value for key in required_keys):
            raise serializers.ValidationError(
                f"Layout config must include: {', '.join(required_keys)}"
            )
        return value
    
    def create(self, validated_data):
        """Create storefront with default configurations."""
        # Set owner to current user if not provided
        if 'owner' not in validated_data:
            validated_data['owner'] = self.context['request'].user
        
        # Set default layout if not provided
        if 'layout_config' not in validated_data:
            validated_data['layout_config'] = self.get_default_layout()
        
        # Set default color scheme if not provided
        if 'color_scheme' not in validated_data:
            validated_data['color_scheme'] = self.get_default_colors()
        
        return super().create(validated_data)
    
    def get_default_layout(self):
        """Get default drag-and-drop layout configuration."""
        return {
            "header": {
                "type": "header",
                "components": [
                    {
                        "id": "logo",
                        "type": "logo",
                        "position": {"x": 0, "y": 0},
                        "size": {"width": 200, "height": 60},
                        "settings": {"alignment": "left"}
                    },
                    {
                        "id": "navigation",
                        "type": "navigation",
                        "position": {"x": 220, "y": 0},
                        "size": {"width": 600, "height": 60},
                        "settings": {"style": "horizontal", "alignment": "center"}
                    },
                    {
                        "id": "cart_icon",
                        "type": "cart",
                        "position": {"x": 840, "y": 0},
                        "size": {"width": 60, "height": 60},
                        "settings": {"show_count": True}
                    }
                ],
                "style": {
                    "background": "#ffffff",
                    "height": "80px",
                    "shadow": True
                }
            },
            "main": {
                "type": "main",
                "sections": [
                    {
                        "id": "hero",
                        "type": "hero_banner",
                        "position": 0,
                        "settings": {
                            "title": "Welcome to Our Store",
                            "subtitle": "Discover amazing products",
                            "button_text": "Shop Now",
                            "background_type": "image"
                        }
                    },
                    {
                        "id": "featured_products",
                        "type": "product_grid",
                        "position": 1,
                        "settings": {
                            "title": "Featured Products",
                            "columns": 4,
                            "rows": 2,
                            "show_filters": True
                        }
                    },
                    {
                        "id": "testimonials",
                        "type": "testimonials",
                        "position": 2,
                        "settings": {
                            "title": "What Our Customers Say",
                            "layout": "carousel",
                            "auto_play": True
                        }
                    }
                ]
            },
            "footer": {
                "type": "footer",
                "components": [
                    {
                        "id": "footer_links",
                        "type": "link_columns",
                        "settings": {
                            "columns": [
                                {
                                    "title": "Shop",
                                    "links": [
                                        {"text": "All Products", "url": "/products"},
                                        {"text": "Categories", "url": "/categories"},
                                        {"text": "New Arrivals", "url": "/new"}
                                    ]
                                },
                                {
                                    "title": "Support",
                                    "links": [
                                        {"text": "Contact Us", "url": "/contact"},
                                        {"text": "FAQ", "url": "/faq"},
                                        {"text": "Returns", "url": "/returns"}
                                    ]
                                }
                            ]
                        }
                    },
                    {
                        "id": "social_links",
                        "type": "social_media",
                        "settings": {
                            "platforms": ["facebook", "twitter", "instagram"],
                            "style": "icons"
                        }
                    }
                ],
                "style": {
                    "background": "#f8f9fa",
                    "padding": "40px 0"
                }
            }
        }
    
    def get_default_colors(self):
        """Get default color scheme."""
        return {
            "primary": "#007bff",
            "secondary": "#6c757d",
            "success": "#28a745",
            "danger": "#dc3545",
            "warning": "#ffc107",
            "info": "#17a2b8",
            "light": "#f8f9fa",
            "dark": "#343a40",
            "background": "#ffffff",
            "text": "#212529",
            "text_muted": "#6c757d",
            "border": "#dee2e6"
        }


class StorefrontListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for storefront lists."""
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    theme_name = serializers.CharField(source='theme.name', read_only=True)
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Storefront
        fields = [
            'id', 'name', 'slug', 'description',
            'owner_name', 'theme_name', 'logo',
            'custom_domain', 'subdomain', 'is_active',
            'is_published', 'product_count', 'created_at'
        ]
    
    def get_product_count(self, obj):
        # This would be optimized with annotations
        return 0  # Placeholder


class StorefrontBuilderSerializer(serializers.ModelSerializer):
    """Specialized serializer for the drag-and-drop builder interface."""
    
    class Meta:
        model = Storefront
        fields = [
            'id', 'name', 'layout_config', 'color_scheme',
            'typography', 'navigation_config', 'footer_config',
            'sidebar_config', 'homepage_sections', 'product_grid_config'
        ]
    
    def validate_layout_config(self, value):
        """Enhanced validation for builder operations."""
        # Validate component structure
        for section_name, section_data in value.items():
            if 'type' not in section_data:
                raise serializers.ValidationError(
                    f"Section '{section_name}' must have a 'type' field"
                )
            
            # Validate components if present
            if 'components' in section_data:
                for component in section_data['components']:
                    required_fields = ['id', 'type']
                    if not all(field in component for field in required_fields):
                        raise serializers.ValidationError(
                            f"Component must have fields: {', '.join(required_fields)}"
                        )
        
        return value

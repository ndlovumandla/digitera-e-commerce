"""
DRF Views for Storefronts API.
Includes drag-and-drop builder support and comprehensive customization.
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from django.core.cache import cache
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.http import HttpResponse

from .models import (
    Storefront, StorefrontTheme, StorefrontAnalytics,
    StorefrontCustomization
)
from .serializers import (
    StorefrontSerializer, StorefrontListSerializer, StorefrontBuilderSerializer,
    StorefrontThemeSerializer, StorefrontAnalyticsSerializer,
    StorefrontCustomizationSerializer
)


class StorefrontThemeViewSet(viewsets.ModelViewSet):
    """ViewSet for storefront themes."""
    queryset = StorefrontTheme.objects.filter(is_active=True)
    serializer_class = StorefrontThemeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'category']
    ordering_fields = ['name', 'price', 'created_at', 'usage_count']
    ordering = ['name']
    
    def get_queryset(self):
        """Filter themes and add usage counts."""
        queryset = super().get_queryset()
        
        # Add usage count annotation
        queryset = queryset.annotate(
            usage_count=Count('storefronts')
        )
        
        # Filter by category if specified
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # Filter premium themes
        is_premium = self.request.query_params.get('is_premium')
        if is_premium is not None:
            queryset = queryset.filter(is_premium=is_premium.lower() == 'true')
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get available theme categories."""
        categories = self.get_queryset().values_list('category', flat=True).distinct()
        return Response(list(categories))
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get most popular themes."""
        popular_themes = self.get_queryset().order_by('-usage_count')[:10]
        serializer = self.get_serializer(popular_themes, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def free(self, request):
        """Get free themes."""
        free_themes = self.get_queryset().filter(is_premium=False)
        serializer = self.get_serializer(free_themes, many=True)
        return Response(serializer.data)


class StorefrontViewSet(viewsets.ModelViewSet):
    """Main ViewSet for storefronts with drag-and-drop builder support."""
    queryset = Storefront.objects.all()
    serializer_class = StorefrontSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'tagline']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-updated_at']
    
    def get_queryset(self):
        """Filter storefronts based on user permissions."""
        queryset = super().get_queryset()
        
        # Add related data for performance
        queryset = queryset.select_related(
            'owner', 'theme', 'seo_settings', 'social_settings', 'customization'
        ).prefetch_related('analytics')
        
        # Filter based on user permissions
        if not self.request.user.is_staff:
            # Users can only see their own storefronts or published ones
            queryset = queryset.filter(
                Q(owner=self.request.user) |
                Q(status='active')
            )
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'list':
            return StorefrontListSerializer
        elif self.action in ['builder_update', 'builder_preview']:
            return StorefrontBuilderSerializer
        return StorefrontSerializer
    
    def perform_create(self, serializer):
        """Set owner to current user."""
        serializer.save(owner=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_storefronts(self, request):
        """Get current user's storefronts."""
        user_storefronts = self.get_queryset().filter(owner=request.user)
        
        page = self.paginate_queryset(user_storefronts)
        if page is not None:
            serializer = StorefrontListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = StorefrontListSerializer(user_storefronts, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['get', 'put', 'patch'])
    def builder(self, request, pk=None):
        """Drag-and-drop builder interface."""
        storefront = self.get_object()
        
        # Check permissions
        if storefront.owner != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if request.method == 'GET':
            # Return builder data
            serializer = StorefrontBuilderSerializer(storefront, context={'request': request})
            return Response(serializer.data)
        
        else:
            # Update builder configuration
            serializer = StorefrontBuilderSerializer(
                storefront, 
                data=request.data, 
                partial=True,
                context={'request': request}
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def preview(self, request, pk=None):
        """Generate preview of storefront with current builder settings."""
        storefront = self.get_object()
        
        # Check permissions
        if storefront.owner != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generate preview URL or data
        preview_data = self.generate_preview(storefront, request.data)
        
        return Response({
            'preview_url': f"/preview/{storefront.slug}",
            'preview_data': preview_data,
            'timestamp': timezone.now()
        })
    
    def generate_preview(self, storefront, builder_data):
        """Generate preview data for the storefront."""
        # This would render the storefront with current builder settings
        # For now, return the layout configuration
        return {
            'layout_config': builder_data.get('layout_config', storefront.layout_config),
            'color_scheme': builder_data.get('color_scheme', storefront.color_scheme),
            'typography': builder_data.get('typography', storefront.typography)
        }
    
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """Publish storefront."""
        storefront = self.get_object()
        
        # Check permissions
        if storefront.owner != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate storefront is ready for publishing
        validation_errors = self.validate_for_publishing(storefront)
        if validation_errors:
            return Response(
                {'errors': validation_errors},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Publish storefront
        storefront.is_published = True
        storefront.published_at = timezone.now()
        storefront.save()
        
        return Response({
            'status': 'published',
            'published_at': storefront.published_at,
            'storefront_url': f"https://{storefront.subdomain}.digitera.co.za"
        })
    
    def validate_for_publishing(self, storefront):
        """Validate storefront is ready for publishing."""
        errors = []
        
        if not storefront.name:
            errors.append("Storefront name is required")
        
        if not storefront.subdomain:
            errors.append("Subdomain is required")
        
        if not storefront.layout_config:
            errors.append("Layout configuration is required")
        
        # Check if storefront has products
        # (This would be implemented when products are linked to storefronts)
        
        return errors
    
    @action(detail=True, methods=['post'])
    def unpublish(self, request, pk=None):
        """Unpublish storefront."""
        storefront = self.get_object()
        
        # Check permissions
        if storefront.owner != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        storefront.is_published = False
        storefront.save()
        
        return Response({'status': 'unpublished'})
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get storefront analytics."""
        storefront = self.get_object()
        
        # Check permissions
        if storefront.owner != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get analytics data
        analytics = StorefrontAnalytics.objects.filter(
            storefront=storefront
        ).order_by('-date')
        
        # Apply date filters
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        if date_from:
            analytics = analytics.filter(date__gte=date_from)
        if date_to:
            analytics = analytics.filter(date__lte=date_to)
        
        # Paginate results
        page = self.paginate_queryset(analytics)
        if page is not None:
            serializer = StorefrontAnalyticsSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = StorefrontAnalyticsSerializer(analytics, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def analytics_summary(self, request, pk=None):
        """Get analytics summary for storefront."""
        storefront = self.get_object()
        
        # Check permissions
        if storefront.owner != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Calculate summary statistics
        analytics = StorefrontAnalytics.objects.filter(storefront=storefront)
        
        # Get date range for filtering
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now().date() - timezone.timedelta(days=days)
        analytics = analytics.filter(date__gte=start_date)
        
        summary = analytics.aggregate(
            total_views=Sum('page_views'),
            total_visitors=Sum('unique_visitors'),
            avg_bounce_rate=Avg('bounce_rate'),
            avg_session_duration=Avg('avg_session_duration'),
            avg_conversion_rate=Avg('conversion_rate'),
            total_revenue=Sum('revenue'),
            total_orders=Sum('orders_count')
        )
        
        # Add growth metrics
        previous_period_start = start_date - timezone.timedelta(days=days)
        previous_analytics = StorefrontAnalytics.objects.filter(
            storefront=storefront,
            date__gte=previous_period_start,
            date__lt=start_date
        )
        
        previous_summary = previous_analytics.aggregate(
            prev_views=Sum('page_views'),
            prev_visitors=Sum('unique_visitors'),
            prev_revenue=Sum('revenue')
        )
        
        # Calculate growth percentages
        growth = {}
        for key, value in summary.items():
            prev_key = f"prev_{key.replace('total_', '').replace('avg_', '')}"
            if prev_key in previous_summary and previous_summary[prev_key]:
                growth[f"{key}_growth"] = (
                    (value - previous_summary[prev_key]) / previous_summary[prev_key] * 100
                    if value else 0
                )
        
        return Response({
            'period_days': days,
            'summary': summary,
            'growth': growth,
            'period_start': start_date,
            'period_end': timezone.now().date()
        })
    
    @action(detail=True, methods=['get', 'put', 'patch'])
    def seo(self, request, pk=None):
        """Manage storefront SEO settings."""
        storefront = self.get_object()
        
        # Check permissions
        if storefront.owner != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        seo_settings, created = StorefrontSEO.objects.get_or_create(
            storefront=storefront
        )
        
        if request.method == 'GET':
            serializer = StorefrontSEOSerializer(seo_settings)
            return Response(serializer.data)
        
        else:
            serializer = StorefrontSEOSerializer(
                seo_settings,
                data=request.data,
                partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get', 'put', 'patch'])
    def social(self, request, pk=None):
        """Manage storefront social media settings."""
        storefront = self.get_object()
        
        # Check permissions
        if storefront.owner != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        social_settings, created = StorefrontSocial.objects.get_or_create(
            storefront=storefront
        )
        
        if request.method == 'GET':
            serializer = StorefrontSocialSerializer(social_settings)
            return Response(serializer.data)
        
        else:
            serializer = StorefrontSocialSerializer(
                social_settings,
                data=request.data,
                partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get', 'put', 'patch'])
    def customization(self, request, pk=None):
        """Manage advanced storefront customizations."""
        storefront = self.get_object()
        
        # Check permissions
        if storefront.owner != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        customization, created = StorefrontCustomization.objects.get_or_create(
            storefront=storefront
        )
        
        if request.method == 'GET':
            serializer = StorefrontCustomizationSerializer(customization)
            return Response(serializer.data)
        
        else:
            serializer = StorefrontCustomizationSerializer(
                customization,
                data=request.data,
                partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """Duplicate a storefront."""
        original_storefront = self.get_object()
        
        # Check permissions
        if original_storefront.owner != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Create duplicate
        duplicate_data = {
            'name': f"{original_storefront.name} (Copy)",
            'description': original_storefront.description,
            'tagline': original_storefront.tagline,
            'theme': original_storefront.theme,
            'layout_config': original_storefront.layout_config,
            'color_scheme': original_storefront.color_scheme,
            'typography': original_storefront.typography,
            'navigation_config': original_storefront.navigation_config,
            'footer_config': original_storefront.footer_config,
            'sidebar_config': original_storefront.sidebar_config,
            'homepage_sections': original_storefront.homepage_sections,
            'product_grid_config': original_storefront.product_grid_config,
            'features_enabled': original_storefront.features_enabled,
            'payment_methods': original_storefront.payment_methods,
            'shipping_options': original_storefront.shipping_options,
            'tax_settings': original_storefront.tax_settings,
            'notification_settings': original_storefront.notification_settings,
            'business_info': original_storefront.business_info,
            'contact_info': original_storefront.contact_info,
            'is_published': False,  # Don't publish duplicates automatically
        }
        
        serializer = StorefrontSerializer(data=duplicate_data, context={'request': request})
        if serializer.is_valid():
            duplicate = serializer.save(owner=request.user)
            return Response(
                StorefrontSerializer(duplicate, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PublicStorefrontViewSet(viewsets.ReadOnlyModelViewSet):
    """Public ViewSet for published storefronts (no authentication required)."""
    queryset = Storefront.objects.filter(status='active')
    serializer_class = StorefrontSerializer
    permission_classes = []
    lookup_field = 'slug'
    
    @action(detail=True, methods=['get'])
    def public_view(self, request, slug=None):
        """Public view of storefront (tracks analytics)."""
        storefront = self.get_object()
        
        # Track view (implement async with Celery in production)
        self.track_storefront_view(storefront, request)
        
        # Return public storefront data
        serializer = self.get_serializer(storefront)
        return Response(serializer.data)
    
    def track_storefront_view(self, storefront, request):
        """Track storefront view for analytics."""
        try:
            analytics, created = StorefrontAnalytics.objects.get_or_create(
                storefront=storefront,
                date=timezone.now().date(),
                defaults={
                    'page_views': 0,
                    'unique_visitors': 0,
                    'bounce_rate': 0.0,
                    'avg_session_duration': 0.0,
                    'conversion_rate': 0.0,
                    'revenue': 0.0,
                    'orders_count': 0,
                    'traffic_sources': {},
                    'popular_products': [],
                    'visitor_countries': {},
                    'device_breakdown': {}
                }
            )
            
            analytics.page_views += 1
            
            # Track unique visitors using session or IP
            session_key = f"visited_storefront_{storefront.id}"
            if not request.session.get(session_key):
                analytics.unique_visitors += 1
                request.session[session_key] = True
            
            analytics.save()
        except Exception:
            pass  # Fail silently for analytics


# Web-based views for traditional HTML pages
class StorefrontListView(ListView):
    """Web view for listing storefronts."""
    model = Storefront
    template_name = 'storefronts/list.html'
    context_object_name = 'storefronts'
    paginate_by = 20
    
    def get_queryset(self):
        return Storefront.objects.filter(is_active=True).order_by('-created_at')


class StorefrontCreateView(LoginRequiredMixin, CreateView):
    """Web view for creating storefronts."""
    model = Storefront
    fields = ['name', 'description', 'theme']
    template_name = 'storefronts/create.html'
    
    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super().form_valid(form)


class StorefrontDetailView(DetailView):
    """Web view for storefront details."""
    model = Storefront
    template_name = 'storefronts/detail.html'
    context_object_name = 'storefront'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'


class StorefrontUpdateView(LoginRequiredMixin, UpdateView):
    """Web view for updating storefronts."""
    model = Storefront
    fields = ['name', 'description', 'theme']
    template_name = 'storefronts/edit.html'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        return Storefront.objects.filter(user=self.request.user)


class StorefrontAnalyticsView(LoginRequiredMixin, DetailView):
    """Web view for storefront analytics."""
    model = Storefront
    template_name = 'storefronts/analytics.html'
    context_object_name = 'storefront'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        return Storefront.objects.filter(user=self.request.user)

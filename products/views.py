"""
DRF Views for Products API.
Includes polymorphic product handling, advanced filtering, and AI recommendations.
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Count, Sum
from django.utils import timezone
from django.core.cache import cache
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse_lazy

from .models import (
    Product, DigitalDownload, Membership, Community, Course, Event,
    Category, Tag, ProductReview, ProductAnalytics
)
from .serializers import (
    ProductSerializer, ProductListSerializer,
    DigitalDownloadSerializer, MembershipSerializer,
    CommunitySerializer, CourseSerializer, EventSerializer,
    CategorySerializer, TagSerializer, ProductReviewSerializer,
    ProductAnalyticsSerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for product categories."""
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'sort_order', 'created_at']
    ordering = ['sort_order', 'name']
    
    def get_queryset(self):
        """Filter categories based on user permissions."""
        queryset = super().get_queryset()
        
        # Add annotations for better performance
        queryset = queryset.annotate(
            products_count=Count('products'),
            children_count=Count('children')
        ).select_related('parent').prefetch_related('children')
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """Get products in this category."""
        category = self.get_object()
        products = Product.objects.filter(
            category=category,
            status='published'
        )
        
        # Apply additional filters
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Get category tree structure."""
        root_categories = self.get_queryset().filter(parent=None)
        
        def build_tree(categories):
            tree = []
            for category in categories:
                node = CategorySerializer(category, context={'request': request}).data
                children = category.children.filter(is_active=True)
                if children:
                    node['children'] = build_tree(children)
                tree.append(node)
            return tree
        
        tree = build_tree(root_categories)
        return Response(tree)


class TagViewSet(viewsets.ModelViewSet):
    """ViewSet for product tags."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'products_count']
    ordering = ['name']
    
    def get_queryset(self):
        """Annotate tags with product counts."""
        return super().get_queryset().annotate(
            products_count=Count('products')
        )
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Get most popular tags."""
        popular_tags = self.get_queryset().order_by('-products_count')[:20]
        serializer = self.get_serializer(popular_tags, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def ai_generated(self, request):
        """Get AI-generated tags."""
        ai_tags = self.get_queryset().filter(is_ai_generated=True)
        serializer = self.get_serializer(ai_tags, many=True)
        return Response(serializer.data)


class ProductViewSet(viewsets.ModelViewSet):
    """Main ViewSet for all product types with polymorphic support."""
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'short_description', 'tags__name']
    ordering_fields = ['name', 'price', 'created_at', 'updated_at', 'recommendation_score']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Optimize queryset with prefetch and annotations."""
        queryset = super().get_queryset()
        
        # Add select_related and prefetch_related for performance
        queryset = queryset.select_related('creator', 'category').prefetch_related(
            'tags', 'files', 'reviews__reviewer'
        )
        
        # Add annotations for computed fields
        queryset = queryset.annotate(
            avg_rating=Avg('reviews__rating'),
            review_count=Count('reviews', filter=Q(reviews__is_approved=True)),
            sales_count=Count('order_items')
        )
        
        # Filter based on user permissions
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(
                status='published',
                visibility='public'
            )
        elif not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(creator=self.request.user) |
                Q(status='published', visibility__in=['public', 'unlisted'])
            )
        
        return queryset
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action and product type."""
        if self.action == 'list':
            return ProductListSerializer
        
        # For detail views, return specific serializer based on product type
        if hasattr(self, 'object') and self.object:
            if isinstance(self.object, DigitalDownload):
                return DigitalDownloadSerializer
            elif isinstance(self.object, Membership):
                return MembershipSerializer
            elif isinstance(self.object, Community):
                return CommunitySerializer
            elif isinstance(self.object, Course):
                return CourseSerializer
            elif isinstance(self.object, Event):
                return EventSerializer
        
        return ProductSerializer
    
    def perform_create(self, serializer):
        """Set creator to current user."""
        serializer.save(creator=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        """Track product views and return product details."""
        instance = self.get_object()
        
        # Track view (implement async with Celery in production)
        self.track_product_view(instance, request)
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def track_product_view(self, product, request):
        """Track product view for analytics."""
        # This should be implemented as a Celery task in production
        try:
            analytics, created = ProductAnalytics.objects.get_or_create(
                product=product,
                date=timezone.now().date(),
                defaults={'views': 0, 'unique_views': 0}
            )
            analytics.views += 1
            
            # Track unique views using session or IP
            session_key = f"viewed_product_{product.id}"
            if not request.session.get(session_key):
                analytics.unique_views += 1
                request.session[session_key] = True
            
            analytics.save()
        except Exception:
            pass  # Fail silently for analytics
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured products."""
        featured_products = self.get_queryset().filter(is_featured=True)[:10]
        serializer = ProductListSerializer(featured_products, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending products based on recent views and sales."""
        # Get products with high recent activity
        trending_products = self.get_queryset().filter(
            analytics__date__gte=timezone.now().date() - timezone.timedelta(days=7)
        ).annotate(
            recent_views=Sum('analytics__views'),
            recent_sales=Count('order_items__order', 
                filter=Q(order_items__order__created_at__gte=timezone.now() - timezone.timedelta(days=7))
            )
        ).order_by('-recent_views', '-recent_sales')[:20]
        
        serializer = ProductListSerializer(trending_products, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        """Get AI-powered product recommendations."""
        if not request.user.is_authenticated:
            # Return popular products for anonymous users
            popular_products = self.get_queryset().order_by('-recommendation_score')[:10]
            serializer = ProductListSerializer(popular_products, many=True, context={'request': request})
            return Response(serializer.data)
        
        # Get personalized recommendations
        recommendations = self.get_personalized_recommendations(request.user)
        serializer = ProductListSerializer(recommendations, many=True, context={'request': request})
        return Response(serializer.data)
    
    def get_personalized_recommendations(self, user):
        """Get personalized recommendations for a user."""
        cache_key = f"recommendations_user_{user.id}"
        recommendations = cache.get(cache_key)
        
        if recommendations is None:
            # Simple recommendation algorithm (enhance with ML in production)
            user_purchases = Product.objects.filter(
                order_items__order__buyer=user
            ).values_list('category', 'tags')
            
            # Get products in similar categories/tags
            similar_products = self.get_queryset().filter(
                Q(category__in=[p[0] for p in user_purchases]) |
                Q(tags__in=[p[1] for p in user_purchases if p[1]])
            ).exclude(
                order_items__order__buyer=user
            ).distinct().order_by('-recommendation_score')[:10]
            
            recommendations = list(similar_products)
            cache.set(cache_key, recommendations, 3600)  # Cache for 1 hour
        
        return recommendations
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Like/unlike a product."""
        product = self.get_object()
        user = request.user
        
        if not user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Implement product liking logic here
        # This would typically involve a ProductLike model
        
        return Response({'status': 'liked'})
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """Get product reviews."""
        product = self.get_object()
        reviews = ProductReview.objects.filter(
            product=product,
            is_approved=True
        ).select_related('reviewer').order_by('-created_at')
        
        # Pagination
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = ProductReviewSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductReviewSerializer(reviews, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_review(self, request, pk=None):
        """Add a review for a product."""
        product = self.get_object()
        
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if user has already reviewed this product
        existing_review = ProductReview.objects.filter(
            product=product,
            reviewer=request.user
        ).first()
        
        if existing_review:
            return Response(
                {'error': 'You have already reviewed this product'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ProductReviewSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(product=product, reviewer=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get product analytics (creator only)."""
        product = self.get_object()
        
        if product.creator != request.user and not request.user.is_staff:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        analytics = ProductAnalytics.objects.filter(product=product).order_by('-date')
        serializer = ProductAnalyticsSerializer(analytics, many=True)
        return Response(serializer.data)


class DigitalDownloadViewSet(viewsets.ModelViewSet):
    """Specialized ViewSet for digital downloads."""
    queryset = DigitalDownload.objects.filter(status='published')
    serializer_class = DigitalDownloadSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    @action(detail=True, methods=['post'])
    def download(self, request, pk=None):
        """Generate secure download link."""
        product = self.get_object()
        
        # Check if user has purchased this product
        if not self.has_download_access(request.user, product):
            return Response(
                {'error': 'Purchase required to download'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Generate secure download links
        download_links = self.generate_download_links(product, request.user)
        
        return Response({
            'download_links': download_links,
            'expires_at': timezone.now() + timezone.timedelta(hours=24)
        })
    
    def has_download_access(self, user, product):
        """Check if user has access to download this product."""
        if not user.is_authenticated:
            return False
        
        # Check if user has purchased this product
        from orders.models import OrderItem
        return OrderItem.objects.filter(
            product=product,
            order__buyer=user,
            order__status='completed',
            access_granted=True
        ).exists()
    
    def generate_download_links(self, product, user):
        """Generate secure, time-limited download links."""
        # This would integrate with your file storage system
        # and generate signed URLs for security
        links = []
        for file in product.files.all():
            # Generate signed URL (placeholder)
            signed_url = f"/api/downloads/secure/{file.id}/?token=secure_token"
            links.append({
                'file_id': file.id,
                'filename': file.name,
                'url': signed_url,
                'expires_at': timezone.now() + timezone.timedelta(hours=24)
            })
        return links


class EventViewSet(viewsets.ModelViewSet):
    """Specialized ViewSet for events with QR code generation."""
    queryset = Event.objects.filter(status='published')
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming events."""
        upcoming_events = self.get_queryset().filter(
            start_date__gte=timezone.now()
        ).order_by('start_date')[:20]
        
        serializer = self.get_serializer(upcoming_events, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def register(self, request, pk=None):
        """Register for an event."""
        event = self.get_object()
        
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Check if event is full
        if event.max_attendees:
            current_attendees = self.get_attendee_count(event)
            if current_attendees >= event.max_attendees:
                return Response(
                    {'error': 'Event is full'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Check registration deadline
        if event.registration_deadline and timezone.now() > event.registration_deadline:
            return Response(
                {'error': 'Registration deadline has passed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process registration (this would create an order)
        # Return QR code for ticket
        qr_code = self.generate_qr_ticket(event, request.user)
        
        return Response({
            'status': 'registered',
            'qr_code': qr_code,
            'message': 'Registration successful'
        })
    
    def get_attendee_count(self, event):
        """Get current attendee count for an event."""
        # This would be calculated from orders/registrations
        return 0  # Placeholder
    
    def generate_qr_ticket(self, event, user):
        """Generate QR code ticket for event."""
        import qrcode
        from io import BytesIO
        import base64
        
        # Create ticket data
        ticket_data = f"EVENT:{event.id}|USER:{user.id}|TIME:{timezone.now().isoformat()}"
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(ticket_data)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{qr_code_base64}"


# Web-based views for traditional HTML pages
class ProductCreateView(LoginRequiredMixin, CreateView):
    """Web view for creating products."""
    model = Product
    fields = ['name', 'description', 'price', 'category']
    template_name = 'products/create.html'
    
    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super().form_valid(form)


class ProductDetailView(DetailView):
    """Web view for product details."""
    model = Product
    template_name = 'products/detail.html'
    context_object_name = 'product'


class ProductUpdateView(LoginRequiredMixin, UpdateView):
    """Web view for updating products."""
    model = Product
    fields = ['name', 'description', 'price', 'category']
    template_name = 'products/edit.html'
    
    def get_queryset(self):
        return Product.objects.filter(creator=self.request.user)


class ProductDeleteView(LoginRequiredMixin, DeleteView):
    """Web view for deleting products."""
    model = Product
    template_name = 'products/delete.html'
    success_url = reverse_lazy('products:category_list')
    
    def get_queryset(self):
        return Product.objects.filter(creator=self.request.user)


class CategoryListView(ListView):
    """Web view for listing categories."""
    model = Category
    template_name = 'products/categories.html'
    context_object_name = 'categories'
    
    def get_queryset(self):
        return Category.objects.filter(is_active=True).order_by('name')


class CategoryDetailView(DetailView):
    """Web view for category details."""
    model = Category
    template_name = 'products/category_detail.html'
    context_object_name = 'category'


class MarketplaceView(ListView):
    """Web view for browsing all products (marketplace)."""
    model = Product
    template_name = 'products/marketplace.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Product.objects.filter(
            status='published',
            visibility='public'
        ).select_related('creator', 'category').prefetch_related('tags')
        
        # Add search functionality
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(tags__name__icontains=search)
            ).distinct()
        
        # Add category filtering
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        
        # Add sorting
        sort = self.request.GET.get('sort', '-created_at')
        if sort in ['name', '-name', 'price', '-price', 'created_at', '-created_at']:
            queryset = queryset.order_by(sort)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        context['current_search'] = self.request.GET.get('search', '')
        context['current_category'] = self.request.GET.get('category', '')
        context['current_sort'] = self.request.GET.get('sort', '-created_at')
        return context

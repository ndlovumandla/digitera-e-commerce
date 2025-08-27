"""
Enhanced marketplace discovery views with AI recommendations and modern features.
Inspired by Whop's marketplace with South African focus.
"""

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q, F, Count, Sum, Avg, Case, When, Value
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from datetime import timedelta
import json
import random
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from .models import Product, Category, Tag, ProductAnalytics, ProductReview
from .serializers import (
    ProductListSerializer, CategorySerializer, 
    MarketplaceProductSerializer, TrendingProductSerializer
)
from accounts.models import UserProfile


class MarketplaceDiscoveryView(TemplateView):
    """Main marketplace discovery page with curated content."""
    template_name = 'marketplace/discovery.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get curated sections
        context.update({
            'featured_products': self.get_featured_products(),
            'trending_products': self.get_trending_products(),
            'new_arrivals': self.get_new_arrivals(),
            'top_earners': self.get_top_earners(),
            'categories': self.get_popular_categories(),
            'recommended_products': self.get_recommendations(),
            'marketplace_stats': self.get_marketplace_stats(),
        })
        
        return context
    
    def get_featured_products(self):
        """Get marketplace promoted/featured products."""
        return Product.objects.filter(
            status=Product.ProductStatus.PUBLISHED,
            is_marketplace_promoted=True,
            marketplace_promotion_start__lte=timezone.now(),
            marketplace_promotion_end__gte=timezone.now()
        ).annotate(
            avg_rating=Avg('reviews__rating'),
            sales_count=Count('order_items')
        ).order_by('-discovery_rank', '-trending_score')[:8]
    
    def get_trending_products(self):
        """Get trending products based on 24h activity."""
        return Product.objects.filter(
            status=Product.ProductStatus.PUBLISHED
        ).annotate(
            recent_views=Sum(
                'analytics__views',
                filter=Q(analytics__date__gte=timezone.now().date() - timedelta(days=1))
            ),
            avg_rating=Avg('reviews__rating')
        ).filter(
            recent_views__gt=0
        ).order_by('-trending_score', '-last_24h_sales')[:12]
    
    def get_new_arrivals(self):
        """Get recently published products."""
        return Product.objects.filter(
            status=Product.ProductStatus.PUBLISHED,
            published_at__gte=timezone.now() - timedelta(days=7)
        ).annotate(
            avg_rating=Avg('reviews__rating')
        ).order_by('-published_at')[:10]
    
    def get_top_earners(self):
        """Get top earning products in last 24h."""
        return Product.objects.filter(
            status=Product.ProductStatus.PUBLISHED,
            last_24h_revenue__gt=0
        ).annotate(
            avg_rating=Avg('reviews__rating')
        ).order_by('-last_24h_revenue', '-last_24h_sales')[:8]
    
    def get_popular_categories(self):
        """Get categories with most active products."""
        return Category.objects.filter(
            is_active=True,
            products__status=Product.ProductStatus.PUBLISHED
        ).annotate(
            products_count=Count('products'),
            total_sales=Sum('products__last_24h_sales')
        ).filter(products_count__gt=0).order_by('-total_sales', '-products_count')[:8]
    
    def get_recommendations(self):
        """Get AI-powered recommendations."""
        if self.request.user.is_authenticated:
            return self.get_personalized_recommendations()
        else:
            return self.get_popular_products()
    
    def get_personalized_recommendations(self):
        """Get personalized recommendations for authenticated users."""
        user = self.request.user
        cache_key = f"recommendations_user_{user.id}"
        recommendations = cache.get(cache_key)
        
        if recommendations is None:
            # Get user's purchase history and preferences
            user_products = Product.objects.filter(
                order_items__order__user=user
            ).values_list('id', flat=True)
            
            if user_products:
                # Use collaborative filtering
                recommendations = self.collaborative_filtering(user, user_products)
            else:
                # Use content-based filtering based on profile
                recommendations = self.content_based_filtering(user)
            
            cache.set(cache_key, recommendations, 1800)  # Cache for 30 minutes
        
        return recommendations[:8]
    
    def collaborative_filtering(self, user, user_products):
        """Simple collaborative filtering algorithm."""
        # Find similar users based on purchase history
        similar_users = Product.objects.filter(
            order_items__order__user__in=Product.objects.filter(
                id__in=user_products
            ).values_list('order_items__order__user', flat=True)
        ).exclude(
            order_items__order__user=user
        ).values_list('order_items__order__user', flat=True).distinct()
        
        # Get products purchased by similar users
        recommended_products = Product.objects.filter(
            order_items__order__user__in=similar_users,
            status=Product.ProductStatus.PUBLISHED
        ).exclude(
            id__in=user_products
        ).annotate(
            similarity_score=Count('order_items'),
            avg_rating=Avg('reviews__rating')
        ).order_by('-similarity_score', '-avg_rating')
        
        return recommended_products
    
    def content_based_filtering(self, user):
        """Content-based filtering using user profile and preferences."""
        try:
            profile = user.profile
            interests = getattr(profile, 'interests', [])
            preferred_categories = getattr(profile, 'preferred_categories', [])
            
            # Get products in preferred categories or matching interests
            recommendations = Product.objects.filter(
                status=Product.ProductStatus.PUBLISHED
            ).filter(
                Q(category__name__in=preferred_categories) |
                Q(tags__name__in=interests)
            ).annotate(
                avg_rating=Avg('reviews__rating'),
                relevance_score=Case(
                    When(category__name__in=preferred_categories, then=Value(2)),
                    When(tags__name__in=interests, then=Value(1)),
                    default=Value(0)
                )
            ).order_by('-relevance_score', '-avg_rating', '-trending_score')
            
            return recommendations
        except:
            return self.get_popular_products()
    
    def get_popular_products(self):
        """Fallback: get generally popular products."""
        return Product.objects.filter(
            status=Product.ProductStatus.PUBLISHED
        ).annotate(
            avg_rating=Avg('reviews__rating'),
            total_sales=Count('order_items')
        ).order_by('-total_sales', '-avg_rating')[:8]
    
    def get_marketplace_stats(self):
        """Get marketplace statistics."""
        cache_key = "marketplace_stats"
        stats = cache.get(cache_key)
        
        if stats is None:
            total_products = Product.objects.filter(
                status=Product.ProductStatus.PUBLISHED
            ).count()
            
            total_creators = Product.objects.filter(
                status=Product.ProductStatus.PUBLISHED
            ).values('creator').distinct().count()
            
            today = timezone.now().date()
            today_sales = Product.objects.filter(
                analytics__date=today
            ).aggregate(
                total_sales=Sum('analytics__purchases'),
                total_revenue=Sum('analytics__revenue')
            )
            
            stats = {
                'total_products': total_products,
                'total_creators': total_creators,
                'today_sales': today_sales.get('total_sales') or 0,
                'today_revenue': today_sales.get('total_revenue') or 0,
                'currencies_supported': ['ZAR', 'USD', 'EUR'],
                'countries_served': ['South Africa', 'Global']
            }
            
            cache.set(cache_key, stats, 600)  # Cache for 10 minutes
        
        return stats


@api_view(['GET'])
@permission_classes([AllowAny])
def marketplace_api(request):
    """API endpoint for marketplace data with infinite scrolling."""
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    category = request.GET.get('category')
    search = request.GET.get('search')
    sort_by = request.GET.get('sort_by', 'trending')
    filter_type = request.GET.get('filter', 'all')
    
    # Base queryset
    queryset = Product.objects.filter(
        status=Product.ProductStatus.PUBLISHED
    ).select_related('creator', 'category').prefetch_related('tags')
    
    # Apply filters
    if category and category != 'all':
        queryset = queryset.filter(category__slug=category)
    
    if search:
        queryset = queryset.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(tags__name__icontains=search)
        ).distinct()
    
    if filter_type == 'featured':
        queryset = queryset.filter(is_marketplace_promoted=True)
    elif filter_type == 'new':
        queryset = queryset.filter(
            published_at__gte=timezone.now() - timedelta(days=7)
        )
    elif filter_type == 'trending':
        queryset = queryset.filter(trending_score__gt=0)
    
    # Apply sorting
    if sort_by == 'price_low':
        queryset = queryset.order_by('price')
    elif sort_by == 'price_high':
        queryset = queryset.order_by('-price')
    elif sort_by == 'newest':
        queryset = queryset.order_by('-published_at')
    elif sort_by == 'rating':
        queryset = queryset.annotate(
            avg_rating=Avg('reviews__rating')
        ).order_by('-avg_rating')
    elif sort_by == 'sales':
        queryset = queryset.order_by('-last_24h_sales')
    else:  # trending (default)
        queryset = queryset.order_by('-trending_score', '-discovery_rank')
    
    # Paginate results
    paginator = Paginator(queryset, page_size)
    products_page = paginator.get_page(page)
    
    # Serialize data
    serializer = MarketplaceProductSerializer(
        products_page.object_list, 
        many=True, 
        context={'request': request}
    )
    
    return Response({
        'results': serializer.data,
        'has_next': products_page.has_next(),
        'page': page,
        'total_pages': paginator.num_pages,
        'total_count': paginator.count
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def trending_products_api(request):
    """API for trending products with real-time updates."""
    # Get trending products based on recent activity
    trending_products = Product.objects.filter(
        status=Product.ProductStatus.PUBLISHED,
        trending_score__gt=0
    ).annotate(
        recent_views=Sum(
            'analytics__views',
            filter=Q(analytics__date__gte=timezone.now().date() - timedelta(days=1))
        ),
        avg_rating=Avg('reviews__rating')
    ).order_by('-trending_score', '-last_24h_sales')[:20]
    
    serializer = TrendingProductSerializer(
        trending_products, 
        many=True, 
        context={'request': request}
    )
    
    return Response({
        'trending_products': serializer.data,
        'last_updated': timezone.now().isoformat()
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def track_product_interaction(request):
    """Track user interactions for AI recommendations."""
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        interaction_type = data.get('type')  # view, like, share, purchase_intent
        duration = data.get('duration', 0)
        
        product = get_object_or_404(Product, id=product_id)
        
        # Track interaction (implement with Celery for production)
        cache_key = f"user_interactions_{request.user.id}"
        interactions = cache.get(cache_key, [])
        
        interaction = {
            'product_id': product_id,
            'type': interaction_type,
            'duration': duration,
            'timestamp': timezone.now().isoformat(),
            'category': product.category.slug if product.category else None
        }
        
        interactions.append(interaction)
        cache.set(cache_key, interactions[-100:], 86400)  # Keep last 100 interactions
        
        # Update product analytics
        if interaction_type == 'view':
            product.view_count = F('view_count') + 1
            product.save(update_fields=['view_count'])
        
        return Response({'status': 'tracked'})
    
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def personalized_recommendations(request):
    """Get personalized recommendations using advanced ML."""
    user = request.user
    limit = int(request.GET.get('limit', 10))
    
    # Get user's interaction history
    cache_key = f"user_interactions_{user.id}"
    interactions = cache.get(cache_key, [])
    
    if not interactions:
        # Return popular products for new users
        popular_products = Product.objects.filter(
            status=Product.ProductStatus.PUBLISHED
        ).order_by('-trending_score')[:limit]
        
        serializer = MarketplaceProductSerializer(
            popular_products, 
            many=True, 
            context={'request': request}
        )
        return Response({'recommendations': serializer.data})
    
    # Advanced recommendation algorithm
    recommendations = get_ml_recommendations(user, interactions, limit)
    
    serializer = MarketplaceProductSerializer(
        recommendations, 
        many=True, 
        context={'request': request}
    )
    
    return Response({'recommendations': serializer.data})


def get_ml_recommendations(user, interactions, limit=10):
    """Get ML-powered recommendations using scikit-learn."""
    try:
        # Get all products for analysis
        products = Product.objects.filter(
            status=Product.ProductStatus.PUBLISHED
        ).select_related('category').prefetch_related('tags')
        
        if not products:
            return []
        
        # Create feature vectors for products
        product_features = []
        product_objects = []
        
        for product in products:
            # Create text representation of product
            tags = ' '.join([tag.name for tag in product.tags.all()])
            category = product.category.name if product.category else ''
            text_features = f"{product.title} {product.description} {tags} {category}"
            
            product_features.append(text_features)
            product_objects.append(product)
        
        # Use TF-IDF to create feature vectors
        vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        feature_matrix = vectorizer.fit_transform(product_features)
        
        # Get user's interaction-based preferences
        interacted_products = [i['product_id'] for i in interactions]
        user_preferences = []
        
        for product_id in set(interacted_products):
            try:
                product = Product.objects.get(id=product_id)
                product_index = next(
                    i for i, p in enumerate(product_objects) 
                    if p.id == product.id
                )
                user_preferences.append(feature_matrix[product_index].toarray()[0])
            except (Product.DoesNotExist, StopIteration):
                continue
        
        if not user_preferences:
            return Product.objects.filter(
                status=Product.ProductStatus.PUBLISHED
            ).order_by('-trending_score')[:limit]
        
        # Calculate average user preference vector
        user_vector = np.mean(user_preferences, axis=0).reshape(1, -1)
        
        # Calculate similarity scores
        similarity_scores = cosine_similarity(user_vector, feature_matrix)[0]
        
        # Get top recommendations (excluding already interacted products)
        product_scores = list(zip(product_objects, similarity_scores))
        product_scores.sort(key=lambda x: x[1], reverse=True)
        
        recommendations = []
        for product, score in product_scores:
            if product.id not in interacted_products and len(recommendations) < limit:
                recommendations.append(product)
        
        return recommendations
    
    except Exception as e:
        # Fallback to simple recommendations
        return Product.objects.filter(
            status=Product.ProductStatus.PUBLISHED
        ).order_by('-trending_score')[:limit]


@api_view(['GET'])
@permission_classes([AllowAny])
def search_suggestions(request):
    """Get search suggestions with autocomplete."""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return Response({'suggestions': []})
    
    # Get product suggestions
    product_suggestions = Product.objects.filter(
        status=Product.ProductStatus.PUBLISHED,
        title__icontains=query
    ).values_list('title', flat=True)[:5]
    
    # Get category suggestions
    category_suggestions = Category.objects.filter(
        is_active=True,
        name__icontains=query
    ).values_list('name', flat=True)[:3]
    
    # Get tag suggestions
    tag_suggestions = Tag.objects.filter(
        name__icontains=query
    ).values_list('name', flat=True)[:3]
    
    suggestions = {
        'products': list(product_suggestions),
        'categories': list(category_suggestions),
        'tags': list(tag_suggestions)
    }
    
    return Response({'suggestions': suggestions})


@api_view(['GET'])
@permission_classes([AllowAny])
def marketplace_stats_api(request):
    """Get live marketplace statistics."""
    cache_key = "live_marketplace_stats"
    stats = cache.get(cache_key)
    
    if stats is None:
        # Calculate real-time stats
        today = timezone.now().date()
        
        stats = {
            'total_products': Product.objects.filter(
                status=Product.ProductStatus.PUBLISHED
            ).count(),
            'active_creators': Product.objects.filter(
                status=Product.ProductStatus.PUBLISHED
            ).values('creator').distinct().count(),
            'today_sales': ProductAnalytics.objects.filter(
                date=today
            ).aggregate(Sum('purchases'))['purchases__sum'] or 0,
            'trending_count': Product.objects.filter(
                trending_score__gt=0
            ).count(),
            'featured_count': Product.objects.filter(
                is_marketplace_promoted=True
            ).count(),
            'categories_count': Category.objects.filter(
                is_active=True
            ).count(),
            'average_rating': ProductReview.objects.aggregate(
                Avg('rating')
            )['rating__avg'] or 0,
            'total_reviews': ProductReview.objects.count()
        }
        
        cache.set(cache_key, stats, 300)  # Cache for 5 minutes
    
    return Response(stats)


# Utility functions for background tasks
def update_trending_scores():
    """Update trending scores for all products (run as Celery task)."""
    from django.db import transaction
    
    with transaction.atomic():
        # Calculate trending scores based on recent activity
        for product in Product.objects.filter(status=Product.ProductStatus.PUBLISHED):
            # Get recent analytics
            recent_analytics = ProductAnalytics.objects.filter(
                product=product,
                date__gte=timezone.now().date() - timedelta(days=7)
            ).aggregate(
                total_views=Sum('views'),
                total_purchases=Sum('purchases'),
                total_revenue=Sum('revenue')
            )
            
            views = recent_analytics['total_views'] or 0
            purchases = recent_analytics['total_purchases'] or 0
            revenue = float(recent_analytics['total_revenue'] or 0)
            
            # Calculate trending score (weighted formula)
            trending_score = (
                views * 0.3 +
                purchases * 2.0 +
                revenue * 0.01 +
                product.rating_average * 5.0
            )
            
            # Update product
            product.trending_score = trending_score
            product.last_24h_sales = ProductAnalytics.objects.filter(
                product=product,
                date=timezone.now().date()
            ).aggregate(Sum('purchases'))['purchases__sum'] or 0
            
            product.save(update_fields=['trending_score', 'last_24h_sales'])


def update_discovery_ranks():
    """Update discovery rankings for marketplace promotion."""
    from django.db import transaction
    
    with transaction.atomic():
        # Get promoted products and rank them
        promoted_products = Product.objects.filter(
            is_marketplace_promoted=True,
            marketplace_promotion_start__lte=timezone.now(),
            marketplace_promotion_end__gte=timezone.now()
        ).order_by('-trending_score', '-rating_average', '-view_count')
        
        for index, product in enumerate(promoted_products):
            product.discovery_rank = index + 1
            product.save(update_fields=['discovery_rank'])

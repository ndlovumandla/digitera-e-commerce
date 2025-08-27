"""
API Views for the Digitera Platform.
Provides basic API endpoints and dashboard functionality.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """Basic user management ViewSet."""
    queryset = User.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        # Import here to avoid circular import
        from accounts.serializers import UserSerializer
        return UserSerializer


class StorefrontViewSet(viewsets.ModelViewSet):
    """Basic storefront ViewSet - redirects to main storefront views."""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from storefronts.models import Storefront
        return Storefront.objects.filter(owner=self.request.user)
    
    def get_serializer_class(self):
        from storefronts.serializers import StorefrontListSerializer
        return StorefrontListSerializer


class ProductViewSet(viewsets.ModelViewSet):
    """Basic product ViewSet - redirects to main product views."""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from products.models import Product
        return Product.objects.filter(creator=self.request.user)
    
    def get_serializer_class(self):
        from products.serializers import ProductListSerializer
        return ProductListSerializer


class OrderViewSet(viewsets.ModelViewSet):
    """Basic order ViewSet - redirects to main order views."""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from orders.models import Order
        return Order.objects.filter(buyer=self.request.user)
    
    def get_serializer_class(self):
        from orders.serializers import OrderListSerializer
        return OrderListSerializer


class DashboardMetricsAPIView(APIView):
    """API view for dashboard metrics."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get user dashboard metrics."""
        user = request.user
        
        # Calculate basic metrics
        metrics = {
            'total_products': 0,
            'total_orders': 0,
            'total_revenue': '0.00',
            'total_customers': 0,
            'recent_activity': []
        }
        
        try:
            from products.models import Product
            from orders.models import Order
            
            # User's products
            user_products = Product.objects.filter(creator=user)
            metrics['total_products'] = user_products.count()
            
            # User's orders (as seller)
            user_orders = Order.objects.filter(
                items__product__creator=user
            ).distinct()
            metrics['total_orders'] = user_orders.count()
            
            # Total revenue
            revenue = user_orders.aggregate(
                total=Sum('total_amount')
            )['total'] or 0
            metrics['total_revenue'] = str(revenue)
            
            # Unique customers
            customers = user_orders.values('buyer').distinct().count()
            metrics['total_customers'] = customers
            
        except Exception:
            pass  # Return default metrics if models not available
        
        return Response(metrics)


class RevenueAnalyticsAPIView(APIView):
    """API view for revenue analytics."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get revenue analytics for user."""
        user = request.user
        days = int(request.query_params.get('days', 30))
        
        analytics = {
            'total_revenue': '0.00',
            'period_revenue': '0.00',
            'growth_rate': 0.0,
            'revenue_by_day': [],
            'top_products': []
        }
        
        try:
            from orders.models import Order
            from django.db.models import F
            
            # Get orders for user's products
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            user_orders = Order.objects.filter(
                items__product__creator=user,
                created_at__gte=start_date,
                status='completed'
            ).distinct()
            
            # Calculate period revenue
            period_revenue = user_orders.aggregate(
                total=Sum('total_amount')
            )['total'] or 0
            analytics['period_revenue'] = str(period_revenue)
            
            # Calculate growth rate (comparing to previous period)
            prev_start = start_date - timedelta(days=days)
            prev_orders = Order.objects.filter(
                items__product__creator=user,
                created_at__gte=prev_start,
                created_at__lt=start_date,
                status='completed'
            ).distinct()
            
            prev_revenue = prev_orders.aggregate(
                total=Sum('total_amount')
            )['total'] or 0
            
            if prev_revenue > 0:
                analytics['growth_rate'] = (
                    (period_revenue - prev_revenue) / prev_revenue * 100
                )
            
        except Exception:
            pass
        
        return Response(analytics)


class ProductTrendsAPIView(APIView):
    """API view for product trends."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, product_id):
        """Get trends for a specific product."""
        trends = {
            'views_trend': [],
            'sales_trend': [],
            'revenue_trend': [],
            'conversion_rate': 0.0
        }
        
        try:
            from products.models import Product, ProductAnalytics
            from orders.models import OrderItem
            
            product = Product.objects.get(id=product_id, creator=request.user)
            
            # Get analytics for last 30 days
            analytics = ProductAnalytics.objects.filter(
                product=product,
                date__gte=timezone.now().date() - timedelta(days=30)
            ).order_by('date')
            
            for analytic in analytics:
                trends['views_trend'].append({
                    'date': analytic.date,
                    'views': analytic.views,
                    'unique_views': analytic.unique_views
                })
            
            # Get sales data
            sales = OrderItem.objects.filter(
                product=product,
                order__created_at__gte=timezone.now() - timedelta(days=30),
                order__status='completed'
            ).values('order__created_at__date').annotate(
                sales=Count('id'),
                revenue=Sum('total_price')
            ).order_by('order__created_at__date')
            
            for sale in sales:
                trends['sales_trend'].append({
                    'date': sale['order__created_at__date'],
                    'sales': sale['sales'],
                    'revenue': str(sale['revenue'])
                })
            
        except Exception:
            pass
        
        return Response(trends)


@api_view(['GET'])
def api_root(request):
    """API root endpoint."""
    return Response({
        'message': 'Welcome to Digitera API',
        'version': '1.0',
        'endpoints': {
            'authentication': '/api/auth/',
            'users': '/api/v1/users/',
            'products': '/products/api/',
            'storefronts': '/storefronts/api/',
            'orders': '/orders/api/',
            'dashboard': '/api/v1/dashboard/metrics/',
        }
    })

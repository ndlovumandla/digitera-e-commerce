"""
Digitera Platform Views - Basic implementation
"""
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


def home(request):
    """Home page for Digitera platform"""
    context = {
        'title': 'Digitera - South African Digital Marketplace',
        'description': 'All-in-one platform for South African creators to sell digital products',
        'features': [
            'Zero setup costs',
            'Only pay on successful transactions',
            'South African VAT compliance',
            'Multiple payment gateways',
            'Advanced analytics',
            'Marketing tools'
        ]
    }
    return render(request, 'home.html', context)


def about(request):
    """About page"""
    return HttpResponse("""
    <html>
    <head><title>About Digitera</title></head>
    <body>
        <h1>About Digitera</h1>
        <p>Digitera is South Africa's premier digital marketplace platform.</p>
        <p>We help creators sell digital products with zero upfront costs.</p>
        <p><a href="/">Home</a> | <a href="/admin/">Admin</a> | <a href="/api/">API</a></p>
    </body>
    </html>
    """)


@csrf_exempt
def api_status(request):
    """Simple API endpoint to test functionality"""
    if request.method == 'GET':
        return JsonResponse({
            'status': 'success',
            'message': 'Digitera API is running',
            'version': '1.0',
            'features': [
                'User Authentication',
                'Product Management', 
                'Storefront Builder',
                'Order Processing',
                'Analytics Dashboard'
            ]
        })
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            return JsonResponse({
                'status': 'success',
                'message': 'Data received',
                'received_data': data
            })
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)


def api_products(request):
    """Simple products API endpoint"""
    # Mock product data
    products = [
        {
            'id': 1,
            'name': 'Digital Photography Course',
            'type': 'course',
            'price': '299.00',
            'currency': 'ZAR',
            'description': 'Complete digital photography course for beginners',
            'created_at': '2025-08-18T10:00:00Z'
        },
        {
            'id': 2,
            'name': 'Premium Lightroom Presets',
            'type': 'digital_download',
            'price': '49.00',
            'currency': 'ZAR',
            'description': 'Professional Lightroom presets pack',
            'created_at': '2025-08-18T11:00:00Z'
        },
        {
            'id': 3,
            'name': 'Photography Community Access',
            'type': 'membership',
            'price': '99.00',
            'currency': 'ZAR',
            'description': 'Monthly access to exclusive photography community',
            'created_at': '2025-08-18T12:00:00Z'
        }
    ]
    
    return JsonResponse({
        'status': 'success',
        'data': products,
        'count': len(products)
    })


def api_storefronts(request):
    """Simple storefronts API endpoint"""
    storefronts = [
        {
            'id': 1,
            'name': 'PhotoPro Studio',
            'subdomain': 'photopro',
            'description': 'Professional photography courses and presets',
            'owner': 'john@example.com',
            'status': 'active',
            'created_at': '2025-08-18T09:00:00Z'
        },
        {
            'id': 2,
            'name': 'Creative Arts Hub',
            'subdomain': 'creativehub',
            'description': 'Digital art resources and tutorials',
            'owner': 'jane@example.com',
            'status': 'active',
            'created_at': '2025-08-18T10:30:00Z'
        }
    ]
    
    return JsonResponse({
        'status': 'success',
        'data': storefronts,
        'count': len(storefronts)
    })

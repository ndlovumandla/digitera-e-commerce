"""
Celery tasks for async processing in Digitera Platform.
Includes email notifications, file processing, analytics, and AI recommendations.
"""

from celery import shared_task
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal
import logging
import uuid

logger = logging.getLogger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3)
def send_email_notification(self, recipient_email, subject, template_name, context=None):
    """Send email notification with template rendering."""
    try:
        context = context or {}
        
        # Render email content
        html_content = render_to_string(f'emails/{template_name}.html', context)
        text_content = render_to_string(f'emails/{template_name}.txt', context)
        
        # Create email message
        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email]
        )
        email.content_subtype = 'html'
        
        # Send email
        email.send()
        
        logger.info(f"Email sent successfully to {recipient_email}")
        return f"Email sent to {recipient_email}"
        
    except Exception as exc:
        logger.error(f"Failed to send email to {recipient_email}: {str(exc)}")
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@shared_task
def send_order_confirmation_email(order_id):
    """Send order confirmation email to customer."""
    try:
        from orders.models import Order
        order = Order.objects.get(id=order_id)
        
        context = {
            'order': order,
            'order_items': order.items.all(),
            'customer_name': order.billing_name,
            'site_name': 'Digitera'
        }
        
        send_email_notification.delay(
            recipient_email=order.get_customer_email(),
            subject=f'Order Confirmation - {order.order_number}',
            template_name='order_confirmation',
            context=context
        )
        
    except Exception as exc:
        logger.error(f"Failed to send order confirmation for order {order_id}: {str(exc)}")


@shared_task
def send_digital_delivery_email(order_item_id):
    """Send digital product delivery email with download links."""
    try:
        from orders.models import OrderItem
        order_item = OrderItem.objects.get(id=order_item_id)
        
        if not order_item.download_links:
            logger.warning(f"No download links available for order item {order_item_id}")
            return
        
        context = {
            'order_item': order_item,
            'order': order_item.order,
            'product': order_item.product,
            'download_links': order_item.download_links,
            'license_key': order_item.license_key,
            'site_name': 'Digitera'
        }
        
        send_email_notification.delay(
            recipient_email=order_item.order.get_customer_email(),
            subject=f'Your Digital Download is Ready - {order_item.product_name}',
            template_name='digital_delivery',
            context=context
        )
        
    except Exception as exc:
        logger.error(f"Failed to send digital delivery email for order item {order_item_id}: {str(exc)}")


@shared_task
def send_subscription_renewal_reminder(subscription_id):
    """Send subscription renewal reminder email."""
    try:
        from orders.models import Subscription
        subscription = Subscription.objects.get(id=subscription_id)
        
        context = {
            'subscription': subscription,
            'user': subscription.user,
            'product': subscription.product,
            'renewal_date': subscription.next_billing_date,
            'site_name': 'Digitera'
        }
        
        send_email_notification.delay(
            recipient_email=subscription.user.email,
            subject=f'Subscription Renewal Reminder - {subscription.product.name}',
            template_name='subscription_renewal_reminder',
            context=context
        )
        
    except Exception as exc:
        logger.error(f"Failed to send renewal reminder for subscription {subscription_id}: {str(exc)}")


@shared_task
def process_file_upload(file_id, file_type='product'):
    """Process uploaded files (virus scan, thumbnails, metadata extraction)."""
    try:
        if file_type == 'product':
            from products.models import ProductFile
            file_obj = ProductFile.objects.get(id=file_id)
        else:
            logger.error(f"Unknown file type: {file_type}")
            return
        
        # Virus scan (placeholder - integrate with actual service)
        scan_result = perform_virus_scan(file_obj.file.path)
        if not scan_result['clean']:
            file_obj.delete()
            logger.warning(f"File {file_id} deleted due to virus scan failure")
            return
        
        # Generate thumbnail for images
        if file_obj.file_type in ['image', 'video']:
            generate_thumbnail(file_obj)
        
        # Extract metadata
        extract_file_metadata(file_obj)
        
        logger.info(f"File processing completed for file {file_id}")
        
    except Exception as exc:
        logger.error(f"Failed to process file {file_id}: {str(exc)}")


def perform_virus_scan(file_path):
    """Perform virus scan on uploaded file."""
    # Placeholder for virus scanning integration
    # In production, integrate with services like ClamAV, VirusTotal, etc.
    return {'clean': True, 'scan_id': str(uuid.uuid4())}


def generate_thumbnail(file_obj):
    """Generate thumbnail for image/video files."""
    # Placeholder for thumbnail generation
    # In production, use PIL for images, FFmpeg for videos
    pass


def extract_file_metadata(file_obj):
    """Extract metadata from files."""
    # Placeholder for metadata extraction
    # In production, use libraries like python-magic, mutagen, etc.
    pass


@shared_task
def update_product_analytics(product_id, analytics_data):
    """Update product analytics in background."""
    try:
        from products.models import Product, ProductAnalytics
        
        product = Product.objects.get(id=product_id)
        today = timezone.now().date()
        
        analytics, created = ProductAnalytics.objects.get_or_create(
            product=product,
            date=today,
            defaults={
                'views': 0,
                'unique_views': 0,
                'sales_count': 0,
                'revenue': Decimal('0.00'),
                'conversion_rate': 0.0,
                'bounce_rate': 0.0,
                'avg_session_duration': 0.0
            }
        )
        
        # Update analytics with new data
        for key, value in analytics_data.items():
            if hasattr(analytics, key):
                setattr(analytics, key, value)
        
        analytics.save()
        
        logger.info(f"Analytics updated for product {product_id}")
        
    except Exception as exc:
        logger.error(f"Failed to update analytics for product {product_id}: {str(exc)}")


@shared_task
def update_storefront_analytics(storefront_id, analytics_data):
    """Update storefront analytics in background."""
    try:
        from storefronts.models import Storefront, StorefrontAnalytics
        
        storefront = Storefront.objects.get(id=storefront_id)
        today = timezone.now().date()
        
        analytics, created = StorefrontAnalytics.objects.get_or_create(
            storefront=storefront,
            date=today,
            defaults={
                'page_views': 0,
                'unique_visitors': 0,
                'bounce_rate': 0.0,
                'avg_session_duration': 0.0,
                'conversion_rate': 0.0,
                'revenue': Decimal('0.00'),
                'orders_count': 0,
                'traffic_sources': {},
                'popular_products': [],
                'visitor_countries': {},
                'device_breakdown': {}
            }
        )
        
        # Update analytics with new data
        for key, value in analytics_data.items():
            if hasattr(analytics, key):
                setattr(analytics, key, value)
        
        analytics.save()
        
        logger.info(f"Analytics updated for storefront {storefront_id}")
        
    except Exception as exc:
        logger.error(f"Failed to update analytics for storefront {storefront_id}: {str(exc)}")


@shared_task
def generate_ai_product_recommendations(user_id):
    """Generate AI-powered product recommendations for a user."""
    try:
        from products.models import Product
        from orders.models import Order
        
        user = User.objects.get(id=user_id)
        
        # Get user's purchase history
        user_orders = Order.objects.filter(buyer=user, status='completed')
        purchased_products = Product.objects.filter(
            order_items__order__in=user_orders
        ).distinct()
        
        # Simple recommendation algorithm (enhance with ML in production)
        recommendations = []
        
        # Category-based recommendations
        user_categories = purchased_products.values_list('category', flat=True).distinct()
        category_recommendations = Product.objects.filter(
            category__in=user_categories,
            is_active=True,
            status='published'
        ).exclude(
            id__in=purchased_products.values_list('id', flat=True)
        ).order_by('-recommendation_score')[:5]
        
        recommendations.extend(category_recommendations)
        
        # Tag-based recommendations
        user_tags = []
        for product in purchased_products:
            user_tags.extend(product.tags.values_list('id', flat=True))
        
        if user_tags:
            tag_recommendations = Product.objects.filter(
                tags__in=user_tags,
                is_active=True,
                status='published'
            ).exclude(
                id__in=purchased_products.values_list('id', flat=True)
            ).exclude(
                id__in=[p.id for p in recommendations]
            ).distinct().order_by('-recommendation_score')[:5]
            
            recommendations.extend(tag_recommendations)
        
        # Store recommendations in cache or database
        from django.core.cache import cache
        cache.set(f'recommendations_user_{user_id}', recommendations, 3600)
        
        logger.info(f"Generated {len(recommendations)} recommendations for user {user_id}")
        
    except Exception as exc:
        logger.error(f"Failed to generate recommendations for user {user_id}: {str(exc)}")


@shared_task
def generate_ai_product_tags(product_id):
    """Generate AI tags for a product based on its content."""
    try:
        from products.models import Product, Tag
        
        product = Product.objects.get(id=product_id)
        
        # Simple keyword extraction (enhance with NLP in production)
        text_content = f"{product.name} {product.description} {product.short_description}"
        
        # Placeholder for AI tag generation
        # In production, use services like OpenAI, spaCy, NLTK, etc.
        suggested_tags = extract_keywords_from_text(text_content)
        
        # Create or get tags
        for tag_name in suggested_tags:
            tag, created = Tag.objects.get_or_create(
                name=tag_name,
                defaults={'is_ai_generated': True}
            )
            product.tags.add(tag)
        
        logger.info(f"Generated {len(suggested_tags)} AI tags for product {product_id}")
        
    except Exception as exc:
        logger.error(f"Failed to generate AI tags for product {product_id}: {str(exc)}")


def extract_keywords_from_text(text):
    """Extract keywords from text content."""
    # Placeholder for keyword extraction
    # In production, use NLP libraries or AI services
    import re
    
    # Simple word extraction and filtering
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Filter common words and short words
    stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    keywords = [word for word in words if len(word) > 3 and word not in stop_words]
    
    # Return unique keywords (limit to top 5)
    return list(set(keywords))[:5]


@shared_task
def process_subscription_billing():
    """Process subscription billing for due subscriptions."""
    try:
        from orders.models import Subscription
        
        # Get subscriptions due for billing
        due_subscriptions = Subscription.objects.filter(
            status=Subscription.SubscriptionStatus.ACTIVE,
            next_billing_date__lte=timezone.now()
        )
        
        for subscription in due_subscriptions:
            try:
                # Process payment (integrate with payment gateway)
                payment_result = process_subscription_payment(subscription)
                
                if payment_result['success']:
                    # Update subscription for next billing cycle
                    update_subscription_billing_cycle(subscription)
                    
                    # Send confirmation email
                    send_subscription_billing_confirmation.delay(subscription.id)
                    
                else:
                    # Handle failed payment
                    handle_subscription_payment_failure.delay(subscription.id)
                
            except Exception as exc:
                logger.error(f"Failed to process billing for subscription {subscription.id}: {str(exc)}")
        
        logger.info(f"Processed billing for {len(due_subscriptions)} subscriptions")
        
    except Exception as exc:
        logger.error(f"Failed to process subscription billing: {str(exc)}")


def process_subscription_payment(subscription):
    """Process payment for subscription."""
    # Placeholder for payment processing
    # In production, integrate with payment gateways like Stripe, PayPal, etc.
    return {'success': True, 'transaction_id': str(uuid.uuid4())}


def update_subscription_billing_cycle(subscription):
    """Update subscription for next billing cycle."""
    from dateutil.relativedelta import relativedelta
    
    if subscription.billing_interval == 'monthly':
        subscription.next_billing_date += relativedelta(months=1)
    elif subscription.billing_interval == 'quarterly':
        subscription.next_billing_date += relativedelta(months=3)
    elif subscription.billing_interval == 'annually':
        subscription.next_billing_date += relativedelta(years=1)
    elif subscription.billing_interval == 'weekly':
        subscription.next_billing_date += relativedelta(weeks=1)
    
    subscription.current_period_start = subscription.current_period_end
    subscription.current_period_end = subscription.next_billing_date
    subscription.save()


@shared_task
def send_subscription_billing_confirmation(subscription_id):
    """Send subscription billing confirmation email."""
    try:
        from orders.models import Subscription
        subscription = Subscription.objects.get(id=subscription_id)
        
        context = {
            'subscription': subscription,
            'user': subscription.user,
            'product': subscription.product,
            'next_billing_date': subscription.next_billing_date,
            'site_name': 'Digitera'
        }
        
        send_email_notification.delay(
            recipient_email=subscription.user.email,
            subject=f'Subscription Renewed - {subscription.product.name}',
            template_name='subscription_billing_confirmation',
            context=context
        )
        
    except Exception as exc:
        logger.error(f"Failed to send billing confirmation for subscription {subscription_id}: {str(exc)}")


@shared_task
def handle_subscription_payment_failure(subscription_id):
    """Handle subscription payment failure."""
    try:
        from orders.models import Subscription
        subscription = Subscription.objects.get(id=subscription_id)
        
        # Increment failed payment attempts
        subscription.failed_payment_attempts += 1
        
        if subscription.failed_payment_attempts >= 3:
            # Suspend subscription after 3 failed attempts
            subscription.status = Subscription.SubscriptionStatus.PAST_DUE
        
        subscription.save()
        
        # Send payment failure notification
        context = {
            'subscription': subscription,
            'user': subscription.user,
            'product': subscription.product,
            'failed_attempts': subscription.failed_payment_attempts,
            'site_name': 'Digitera'
        }
        
        send_email_notification.delay(
            recipient_email=subscription.user.email,
            subject=f'Payment Failed - {subscription.product.name}',
            template_name='subscription_payment_failure',
            context=context
        )
        
    except Exception as exc:
        logger.error(f"Failed to handle payment failure for subscription {subscription_id}: {str(exc)}")


@shared_task
def generate_invoice_pdf(invoice_id):
    """Generate PDF for invoice."""
    try:
        from orders.models import Invoice
        from django.template.loader import get_template
        from xhtml2pdf import pisa
        from django.core.files.base import ContentFile
        import io
        
        invoice = Invoice.objects.get(id=invoice_id)
        
        # Render invoice template
        template = get_template('invoices/invoice_pdf.html')
        context = {
            'invoice': invoice,
            'order': invoice.order,
            'site_name': 'Digitera'
        }
        html = template.render(context)
        
        # Generate PDF
        result = io.BytesIO()
        pdf = pisa.pisaDocument(io.BytesIO(html.encode("ISO-8859-1")), result)
        
        if not pdf.err:
            # Save PDF file
            pdf_content = ContentFile(result.getvalue())
            filename = f"invoice_{invoice.invoice_number}.pdf"
            
            # In production, save to cloud storage (S3, GCS, etc.)
            invoice.pdf_url = f"/media/invoices/{filename}"
            invoice.pdf_generated = True
            invoice.save()
            
            logger.info(f"PDF generated for invoice {invoice_id}")
        else:
            logger.error(f"Failed to generate PDF for invoice {invoice_id}")
        
    except Exception as exc:
        logger.error(f"Failed to generate PDF for invoice {invoice_id}: {str(exc)}")

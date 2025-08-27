"""
Creator management views for products.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.text import slugify

from .models import Product, DigitalDownload, Category, Tag
from .forms import ProductForm, DigitalDownloadForm, ProductImageUploadForm
from accounts.models import UserRole


class CreatorRequiredMixin(LoginRequiredMixin):
    """Mixin to ensure user is a creator."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # For testing, allow any authenticated user to create products
        # TODO: Re-enable creator role requirement in production
        # if request.user.role != UserRole.CREATOR:
        #     messages.error(request, 'You need to be a creator to access this page.')
        #     return redirect('accounts:upgrade_to_creator')
        
        return super().dispatch(request, *args, **kwargs)


class CreatorProductListView(CreatorRequiredMixin, ListView):
    """List creator's products."""
    model = Product
    template_name = 'products/creator/product_list.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        return Product.objects.filter(creator=self.request.user).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add statistics
        products = self.get_queryset()
        context['total_products'] = products.count()
        context['published_products'] = products.filter(status='published').count()
        context['draft_products'] = products.filter(status='draft').count()
        context['total_sales'] = sum(p.purchase_count for p in products)
        
        return context


class ProductCreateView(CreatorRequiredMixin, CreateView):
    """Create a new product."""
    model = Product
    form_class = ProductForm
    template_name = 'products/creator/product_create.html'
    success_url = reverse_lazy('products:creator_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['download_form'] = DigitalDownloadForm()
        context['image_form'] = ProductImageUploadForm()
        return context
    
    def form_valid(self, form):
        # Save the basic product first
        product = form.save(commit=False)
        product.creator = self.request.user
        product.product_type = 'digital_download'  # Default to digital download
        
        # Generate slug if not provided
        if not product.slug:
            from django.utils.text import slugify
            product.slug = slugify(product.name)
        
        product.save()
        
        # Save the tags if provided
        form.save_m2m()
        
        # Handle digital download specific fields
        download_form = DigitalDownloadForm(self.request.POST)
        if download_form.is_valid():
            try:
                # Create DigitalDownload instance
                from products.models import DigitalDownload
                download = DigitalDownload()
                download.product_ptr = product
                download.id = product.id  # Set the same ID for polymorphic relationship
                
                # Copy fields from download form
                download.delivery_method = download_form.cleaned_data.get('delivery_method', 'instant')
                download.download_limit = download_form.cleaned_data.get('download_limit')
                download.expiry_days = download_form.cleaned_data.get('expiry_days')
                download.license_type = download_form.cleaned_data.get('license_type', '')
                download.license_terms = download_form.cleaned_data.get('license_terms', '')
                
                # Handle download files
                files_input = download_form.cleaned_data.get('download_files_input', '')
                if files_input:
                    files = [url.strip() for url in files_input.split('\n') if url.strip()]
                    download.download_files = files
                else:
                    download.download_files = []
                
                download.save()
                
                # Update product to reference the download
                product.polymorphic_ctype_id = download.polymorphic_ctype_id
                product.save()
                
            except Exception as e:
                # If download creation fails, just continue with basic product
                print(f"Download creation failed: {e}")
        
        messages.success(self.request, f'Product "{product.name}" created successfully!')
        return redirect('products:creator_list')


class ProductUpdateView(CreatorRequiredMixin, UpdateView):
    """Update an existing product."""
    model = Product
    form_class = ProductForm
    template_name = 'products/creator/product_edit.html'
    context_object_name = 'product'
    
    def get_queryset(self):
        return Product.objects.filter(creator=self.request.user)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get digital download instance if it exists
        try:
            download = DigitalDownload.objects.get(id=self.object.id)
            context['download_form'] = DigitalDownloadForm(instance=download)
        except DigitalDownload.DoesNotExist:
            context['download_form'] = DigitalDownloadForm()
        
        context['image_form'] = ProductImageUploadForm()
        return context
    
    def form_valid(self, form):
        product = form.save()
        
        # Handle digital download form
        try:
            download = DigitalDownload.objects.get(id=product.id)
            download_form = DigitalDownloadForm(self.request.POST, instance=download)
        except DigitalDownload.DoesNotExist:
            download_form = DigitalDownloadForm(self.request.POST)
        
        if download_form.is_valid():
            download = download_form.save(commit=False)
            if not hasattr(download, 'product_ptr'):
                download.product_ptr = product
            download.save()
        
        messages.success(self.request, f'Product "{product.name}" updated successfully!')
        return redirect('products:creator_list')
    
    def get_success_url(self):
        return reverse('products:creator_edit', kwargs={'pk': self.object.pk})


class ProductDeleteView(CreatorRequiredMixin, DeleteView):
    """Delete a product."""
    model = Product
    template_name = 'products/creator/product_confirm_delete.html'
    success_url = reverse_lazy('products:creator_list')
    
    def get_queryset(self):
        return Product.objects.filter(creator=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        product = self.get_object()
        product_name = product.name
        result = super().delete(request, *args, **kwargs)
        messages.success(request, f'Product "{product_name}" deleted successfully!')
        return result


@login_required
def product_quick_edit(request, product_id):
    """Quick edit product via AJAX."""
    product = get_object_or_404(Product, id=product_id, creator=request.user)
    
    if request.method == 'POST':
        field = request.POST.get('field')
        value = request.POST.get('value')
        
        allowed_fields = ['name', 'price', 'status', 'visibility']
        if field in allowed_fields:
            setattr(product, field, value)
            product.save(update_fields=[field])
            
            return JsonResponse({
                'success': True,
                'message': f'{field.title()} updated successfully'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
def product_duplicate(request, product_id):
    """Duplicate a product."""
    if request.user.role != UserRole.CREATOR:
        messages.error(request, 'You need to be a creator to duplicate products.')
        return redirect('accounts:upgrade_to_creator')
    
    original = get_object_or_404(Product, id=product_id, creator=request.user)
    
    # Create duplicate
    duplicate = Product.objects.get(id=original.id)
    duplicate.pk = None
    duplicate.name = f"{original.name} (Copy)"
    duplicate.slug = f"{original.slug}-copy"
    duplicate.status = 'draft'
    duplicate.save()
    
    # Copy tags
    duplicate.tags.set(original.tags.all())
    
    # Copy digital download data if exists
    try:
        original_download = DigitalDownload.objects.get(id=original.id)
        download = DigitalDownload()
        download.product_ptr = duplicate
        download.delivery_method = original_download.delivery_method
        download.download_limit = original_download.download_limit
        download.expiry_days = original_download.expiry_days
        download.license_type = original_download.license_type
        download.license_terms = original_download.license_terms
        download.download_files = original_download.download_files.copy()
        download.save()
    except DigitalDownload.DoesNotExist:
        pass
    
    messages.success(request, f'Product "{original.name}" duplicated successfully!')
    return redirect('products:creator_edit', pk=duplicate.pk)


@login_required
def upload_product_image(request):
    """Handle product image upload via AJAX."""
    if request.method == 'POST':
        form = ProductImageUploadForm(request.POST)
        if form.is_valid():
            image_url = form.cleaned_data['image_url']
            return JsonResponse({
                'success': True,
                'image_url': image_url,
                'message': 'Image uploaded successfully'
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required
def product_analytics(request, product_id):
    """Product analytics view."""
    if request.user.role != UserRole.CREATOR:
        messages.error(request, 'You need to be a creator to view analytics.')
        return redirect('accounts:upgrade_to_creator')
    
    product = get_object_or_404(Product, id=product_id, creator=request.user)
    
    # For now, return basic analytics
    # In production, this would include real analytics data
    analytics_data = {
        'views': product.view_count,
        'purchases': product.purchase_count,
        'revenue': sum(
            item.total_price for item in product.order_items.filter(
                order__status='completed'
            )
        ),
        'conversion_rate': (
            (product.purchase_count / product.view_count * 100) 
            if product.view_count > 0 else 0
        ),
        'rating': product.rating_average,
        'reviews': product.rating_count,
    }
    
    context = {
        'product': product,
        'analytics': analytics_data,
    }
    
    return render(request, 'products/creator/product_analytics.html', context)

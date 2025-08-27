"""
Forms for the products app.
"""

from django import forms
from django.core.exceptions import ValidationError
from .models import Product, DigitalDownload, Category, Tag


class ProductForm(forms.ModelForm):
    """Form for creating/editing products."""
    
    tags_input = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter tags separated by commas',
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        }),
        help_text='Enter tags separated by commas (e.g., design, template, business)'
    )
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'short_description', 'category',
            'pricing_type', 'price', 'minimum_price', 'featured_image',
            'status', 'visibility', 'meta_title', 'meta_description'
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Enter product name'
            }),
            'description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 6,
                'placeholder': 'Describe your product in detail...'
            }),
            'short_description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'Brief product description for listings...'
            }),
            'category': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'pricing_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'minimum_price': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0'
            }),
            'featured_image': forms.URLInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'https://example.com/image.jpg'
            }),
            'status': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'visibility': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'meta_title': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'SEO title (60 chars max)',
                'maxlength': '60'
            }),
            'meta_description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 3,
                'placeholder': 'SEO description (160 chars max)',
                'maxlength': '160'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # If editing existing product, populate tags
        if self.instance and self.instance.pk:
            tags = self.instance.tags.all()
            self.fields['tags_input'].initial = ', '.join([tag.name for tag in tags])
    
    def clean_price(self):
        price = self.cleaned_data.get('price')
        pricing_type = self.cleaned_data.get('pricing_type')
        
        if pricing_type != 'free' and price <= 0:
            raise ValidationError('Price must be greater than 0 for paid products.')
        
        return price
    
    def clean_minimum_price(self):
        minimum_price = self.cleaned_data.get('minimum_price')
        pricing_type = self.cleaned_data.get('pricing_type')
        
        if pricing_type == 'flexible' and not minimum_price:
            raise ValidationError('Minimum price is required for flexible pricing.')
        
        return minimum_price
    
    def save(self, commit=True):
        product = super().save(commit=False)
        
        if self.user:
            product.creator = self.user
        
        # Generate slug from name
        if not product.slug:
            from django.utils.text import slugify
            product.slug = slugify(product.name)
        
        if commit:
            product.save()
            
            # Handle tags
            tags_input = self.cleaned_data.get('tags_input', '')
            if tags_input:
                tag_names = [name.strip() for name in tags_input.split(',') if name.strip()]
                tags = []
                for tag_name in tag_names:
                    tag, created = Tag.objects.get_or_create(
                        name=tag_name.lower(),
                        defaults={'slug': slugify(tag_name)}
                    )
                    tags.append(tag)
                product.tags.set(tags)
        
        return product


class DigitalDownloadForm(forms.ModelForm):
    """Form for digital download specific fields."""
    
    download_files_input = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'rows': 4,
            'placeholder': 'Enter download file URLs, one per line'
        }),
        help_text='Enter file URLs, one per line. These will be the downloadable files for customers.'
    )
    
    class Meta:
        model = DigitalDownload
        fields = [
            'delivery_method', 'download_limit', 'expiry_days',
            'license_type', 'license_terms', 'secure_delivery',
            'watermark_enabled', 'drm_protection'
        ]
        
        widgets = {
            'delivery_method': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
            }),
            'download_limit': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Leave empty for unlimited',
                'min': '1'
            }),
            'expiry_days': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'Leave empty for no expiry',
                'min': '1'
            }),
            'license_type': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'placeholder': 'e.g., Standard License, Commercial License'
            }),
            'license_terms': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
                'rows': 4,
                'placeholder': 'Detailed license terms and conditions...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If editing existing product, populate download files
        if self.instance and self.instance.pk and self.instance.download_files:
            files_text = '\n'.join(self.instance.download_files)
            self.fields['download_files_input'].initial = files_text
    
    def save(self, commit=True):
        download = super().save(commit=False)
        
        # Handle download files
        files_input = self.cleaned_data.get('download_files_input', '')
        if files_input:
            files = [url.strip() for url in files_input.split('\n') if url.strip()]
            download.download_files = files
        else:
            download.download_files = []
        
        if commit:
            download.save()
        
        return download


class ProductImageUploadForm(forms.Form):
    """Form for uploading product images."""
    
    image_url = forms.URLField(
        required=True,
        widget=forms.URLInput(attrs={
            'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'https://example.com/your-image.jpg'
        }),
        help_text='Enter the URL of your product image. For best results, use a 16:9 aspect ratio (e.g., 1200x675px).'
    )
    
    def clean_image_url(self):
        url = self.cleaned_data.get('image_url')
        
        # Basic validation for image file extensions
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        if not any(url.lower().endswith(ext) for ext in valid_extensions):
            raise ValidationError('Please provide a valid image URL ending with .jpg, .png, .webp, or .gif')
        
        return url


class ProductSearchForm(forms.Form):
    """Form for searching products."""
    
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Search products...'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=False,
        empty_label='All Categories',
        widget=forms.Select(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
    )
    
    price_min = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Min price'
        })
    )
    
    price_max = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500',
            'placeholder': 'Max price'
        })
    )
    
    sort_by = forms.ChoiceField(
        choices=[
            ('newest', 'Newest First'),
            ('oldest', 'Oldest First'),
            ('price_low', 'Price: Low to High'),
            ('price_high', 'Price: High to Low'),
            ('popular', 'Most Popular'),
            ('rating', 'Highest Rated'),
        ],
        required=False,
        initial='newest',
        widget=forms.Select(attrs={
            'class': 'px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500'
        })
    )

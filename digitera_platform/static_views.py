"""
Static page views for Digitera Platform.
Handles terms, privacy, and other static pages.
"""

from django.shortcuts import render
from django.views.generic import TemplateView


class TermsView(TemplateView):
    """Terms and Conditions page."""
    template_name = 'static_pages/terms.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Terms and Conditions'
        return context


class PrivacyView(TemplateView):
    """Privacy Policy page."""
    template_name = 'static_pages/privacy.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Privacy Policy'
        return context


class AboutView(TemplateView):
    """About page."""
    template_name = 'static_pages/about.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'About Digitera'
        return context


class ContactView(TemplateView):
    """Contact page."""
    template_name = 'static_pages/contact.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Contact Us'
        return context

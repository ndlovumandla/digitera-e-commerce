from django.views.generic import TemplateView
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin


class PackageListView(LoginRequiredMixin, TemplateView):
    template_name = 'marketing/packages.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any marketing package data here
        context.update({
            'packages': [
                {
                    'name': 'Starter',
                    'price': 499,
                    'features': ['Basic Analytics', 'Email Support', '5 Products'],
                },
                {
                    'name': 'Growth', 
                    'price': 999,
                    'features': ['Advanced Analytics', 'Priority Support', 'Unlimited Products'],
                },
                {
                    'name': 'Pro',
                    'price': 2499,
                    'features': ['Full Analytics Suite', '24/7 Support', 'White Label'],
                }
            ]
        })
        return context


class PackageDetailView(LoginRequiredMixin, TemplateView):
    def get(self, request, pk, *args, **kwargs):
        return HttpResponse(f'Marketing package detail placeholder: {pk}')


class PackagePurchaseView(LoginRequiredMixin, TemplateView):
    def post(self, request, pk, *args, **kwargs):
        return HttpResponse(f'Purchased package {pk}')


class CampaignListView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        return HttpResponse('Campaign list placeholder')


class CampaignCreateView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        return HttpResponse('Campaign create placeholder')


class CampaignDetailView(LoginRequiredMixin, TemplateView):
    def get(self, request, pk, *args, **kwargs):
        return HttpResponse(f'Campaign detail placeholder: {pk}')


class PromotionListView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        return HttpResponse('Promotion list placeholder')


class PromotionCreateView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        return HttpResponse('Promotion create placeholder')

from django.views.generic import TemplateView
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin


class AnalyticsDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add any analytics data here
        context.update({
            'total_revenue': 15750.00,
            'total_sales': 45,
            'conversion_rate': 3.2,
            'avg_order_value': 350.00,
            'revenue_growth': 12.5,
            'sales_growth': 8.3,
        })
        return context


class RevenueAnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics/revenue.html'

    def get(self, request, *args, **kwargs):
        return HttpResponse('Revenue analytics placeholder')


class TrafficAnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics/traffic.html'

    def get(self, request, *args, **kwargs):
        return HttpResponse('Traffic analytics placeholder')


class ConversionAnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics/conversion.html'

    def get(self, request, *args, **kwargs):
        return HttpResponse('Conversion analytics placeholder')


class ExportCSVView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        return HttpResponse('csv,data\nplaceholder,true', content_type='text/csv')


class ExportPDFView(LoginRequiredMixin, TemplateView):
    def get(self, request, *args, **kwargs):
        return HttpResponse('%PDF-1.4\n% placeholder', content_type='application/pdf')

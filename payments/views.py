from django.views.generic import TemplateView, ListView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from orders.models import Order


class PaymentProcessView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/process.html'

    def get(self, request, order_id=None, *args, **kwargs):
        if order_id:
            order = get_object_or_404(Order, id=order_id)
            context = {
                'order': order,
                'order_items': order.items.all(),
            }
            return render(request, self.template_name, context)
        return HttpResponse('Payment processing placeholder')

    def post(self, request, order_id=None, *args, **kwargs):
        if order_id:
            order = get_object_or_404(Order, id=order_id)
            
            # Simulate payment processing
            order.status = Order.OrderStatus.COMPLETED
            order.payment_status = Order.PaymentStatus.CAPTURED
            order.paid_at = timezone.now()
            order.completed_at = timezone.now()
            order.save()
            
            # Fulfill digital products
            for item in order.items.all():
                item.is_fulfilled = True
                item.access_granted = True
                item.fulfilled_at = timezone.now()
                item.save()
            
            messages.success(request, 'Payment successful! You can now access your digital products.')
            return redirect('payments:success', order_id=order.id)
        
        return HttpResponse('Invalid payment request')


class PaymentSuccessView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/success.html'

    def get(self, request, order_id=None, *args, **kwargs):
        if order_id:
            order = get_object_or_404(Order, id=order_id)
            context = {
                'order': order,
                'order_items': order.items.all(),
            }
            return render(request, self.template_name, context)
        return HttpResponse('Payment success placeholder')


class PaymentCancelledView(LoginRequiredMixin, TemplateView):
	template_name = 'payments/cancelled.html'

	def get(self, request, *args, **kwargs):
		return HttpResponse('Payment cancelled placeholder')


class StripeWebhookView(TemplateView):
	def post(self, request, *args, **kwargs):
		return HttpResponse('OK')


class PayoutListView(LoginRequiredMixin, TemplateView):
	template_name = 'payments/payouts.html'

	def get(self, request, *args, **kwargs):
		return HttpResponse('Payouts list placeholder')


class PayoutRequestView(LoginRequiredMixin, TemplateView):
	template_name = 'payments/payout_request.html'

	def get(self, request, *args, **kwargs):
		return HttpResponse('Payout request placeholder')

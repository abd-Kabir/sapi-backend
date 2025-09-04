from django.urls import path

from apps.integrations.routes.multibank import MultiBankBindCardCallbackWebhookAPIView, \
    MultiBankPaymentCallbackWebhookAPIView

urlpatterns = [
    path('multibank/bind-card/webhook/', MultiBankBindCardCallbackWebhookAPIView.as_view(),
         name='multibank_bind_card_webhook'),
    path('multibank/payment/webhook/', MultiBankPaymentCallbackWebhookAPIView.as_view(),
         name='multibank_payment_webhook'),
]

from django.urls import path

from apps.integrations.routes.multibank import MultiBankBindCardCallbackWebhookAPIView

urlpatterns = [
    path('multibank/bind-card/webhook/', MultiBankBindCardCallbackWebhookAPIView.as_view(), name='multibank_bind_card_webhook'),
]
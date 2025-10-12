import logging

from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.models import User, Card
from apps.integrations.models import MultibankTransaction, MultibankTransactionStatusEnum

logger = logging.getLogger()


class MultiBankBindCardCallbackWebhookAPIView(APIView):
    permission_classes = [AllowAny, ]

    def post(self, request, *args, **kwargs):
        data = request.data
        logger.debug(f'Multibank bind card webhook request: {data};')
        card = (
            Card.all_objects
            .filter(multibank_session_id=data.get('session_id'), user__phone_number=data.get('phone'))
        )
        if card.exists():
            card = card.first()
            card.number = data.get('card_pan')
            card.card_owner = data.get('holder_name')
            card.token = data.get('card_token')
            card.is_active = True
            if data.get('ps') in ['visa', 'uzcard', 'humo', 'mastercard', ]:
                card.type = data.get('ps')
            card.save()
        return Response()


class MultiBankPaymentCallbackWebhookAPIView(APIView):
    permission_classes = [AllowAny, ]

    @staticmethod
    def match_status(status):
        mb_statuses = {
            'draft': 'new',
            'progress': 'new',
            'success': 'paid',
            'error': 'failed',
        }
        return mb_statuses.get(status, 'new')

    def post(self, request, *args, **kwargs):
        data = request.data
        logger.debug(f'Multibank payment webhook request: {data};')
        transaction = MultibankTransaction.objects.filter(id=data.get('invoice_id'))
        if transaction.exists():
            transaction = transaction.first()
            transaction.callback_data = data
            if transaction.subscription:
                transaction.subscription.is_active = True
                transaction.subscription.save()
                transaction.status = 'paid'
            elif transaction.donation:
                transaction.donation.is_active = True
                transaction.donation.save()
                transaction.status = 'paid'
                if transaction.donation.fundraising_id:
                    transaction.donation.fundraising.current_amount += transaction.creator_amount
                    transaction.donation.fundraising.save()
        else:
            transaction.status = 'failed'
        transaction.save()
        return Response()

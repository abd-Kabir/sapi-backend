from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.authentication.models import User, Card


class MultiBankBindCardCallbackWebhookAPIView(APIView):
    permission_classes = [AllowAny, ]

    def post(self, request, *args, **kwargs):
        data = request.data
        print(data)
        card = (
            Card.objects
            .filter(user__phone_number=data.get('phone'), number__endswith=data.get('card_pan')[12:], is_active=False)
        )
        if card.exists():
            card = card.first()
            card.card_owner = data.get('holder_name')
            card.token = data.get('card_token')
            card.is_active = True
            if data.get('ps') in ['visa', 'uzcard', 'humo', 'mastercard', ]:
                card.type = data.get('ps')
            card.save()
        return Response()

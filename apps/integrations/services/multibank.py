from apps.authentication.models import User, Card
from apps.integrations.api_integrations.multibank import multibank_dev_app
from apps.integrations.models import MultibankTransaction
from config.core.api_exceptions import APIValidation

from django.utils.translation import gettext_lazy as _


def multibank_payment(user: User, creator: User, card: Card, amount, payment_type):
    transaction = MultibankTransaction.objects.create(store_id=6, amount=amount, transaction_type=payment_type,
                                                      user=user, creator=creator, card_token=card.token)
    creator_amount = ((100 - creator.sapi_share) / 100) * amount
    creator_receipient, receipient_sc = multibank_dev_app.get_receipient(data={
        'pinfl': creator.pinfl,
        'mfo': "00491",
        'account_no': creator.multibank_account,
        'commitent': True
    })
    if not str(receipient_sc).startswith('2'):
        raise APIValidation(_('Ошибка во время получение данных от Multibank'), status_code=400)
    creator_split = {
        'type': 'account',
        'receipient': creator_receipient.get('data', {}).get('uuid'),
        # 'receipient': '5378f655-ae41-11ee-97a8-005056b4367d',
        'amount': int(creator_amount),
    }

    sapi_amount = (creator.sapi_share / 100) * amount
    sapi_split = {
        'type': 'account',
        'receipient': '7bd7ad8e-b2d5-11ee-97a8-005056b4367d',
        'amount': int(sapi_amount),
    }

    body = {
        'card': {
            'token': card.token
        },
        'amount': amount,
        'store_id': 6,
        'invoice_id': str(transaction.id),
        'split': [creator_split, sapi_split]
    }
    payment_response, payment_sc  = multibank_dev_app.create_payment(data=body)
    if not str(payment_sc).startswith('2'):
        raise APIValidation(_('Ошибка во время получение данных от Multibank'), status_code=400)
    return payment_response

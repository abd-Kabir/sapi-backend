from django.conf import settings

from apps.authentication.models import User, Card
from apps.integrations.api_integrations.multibank import multibank_prod_app
from apps.integrations.models import MultibankTransaction
from config.core.api_exceptions import APIValidation

from django.utils.translation import gettext_lazy as _


def multibank_payment(user: User, creator: User, card: Card, amount, payment_type, fundraising=None):
    # SAPI TRANSACTION CREATION
    transaction = MultibankTransaction.objects.create(
        store_id=settings.MULTIBANK_INTEGRATION_SETTINGS['PROD']['STORE_ID'], amount=amount,
        transaction_type=payment_type, user=user, creator=creator, card_token=card.token
    )

    # GET CREATOR RECEIPIENT
    creator_receipient, receipient_sc = multibank_prod_app.get_receipient(data={
        'tin': creator.pinfl,
        'mfo': '00491',  # Hard coded bank's MFO
        'account_no': creator.multibank_account,
        'commitent': True
    }, merchant_id=settings.MULTIBANK_INTEGRATION_SETTINGS['PROD']['MERCHANT_ID'])
    if not str(receipient_sc).startswith('2'):
        raise APIValidation(_('Ошибка во время получение данных от Multibank'), status_code=400)

    # PAYMENT CREATION
    multicard_commission = amount * 0.02
    creator_amount = (((100 - creator.sapi_share) / 100) * amount) - multicard_commission
    creator_split = {
        'type': 'account',
        'receipient': creator_receipient.get('data', {}).get('uuid'),
        'amount': int(creator_amount),
        'details': 'Донат для креатора SAPI'
    }
    sapi_amount = (creator.sapi_share / 100) * amount
    sapi_split = {
        'type': 'account',
        'receipient': '900addbc-4fed-11f0-8b0d-00505680eaf6',  # Hard coded SAPI's ID
        'amount': int(sapi_amount),
        'details': 'Донат для креатора SAPI'
    }
    transaction.sapi_amount = sapi_amount
    transaction.creator_amount = creator_amount
    body = {
        'card': {
            'token': card.token
        },
        'amount': amount,
        'store_id': settings.MULTIBANK_INTEGRATION_SETTINGS['PROD']['STORE_ID'],
        'invoice_id': str(transaction.id),
        'split': [creator_split, sapi_split]
    }
    payment_response, payment_sc = multibank_prod_app.create_payment(data=body)
    if not str(payment_sc).startswith('2'):
        transaction.status = 'failed'
        transaction.save()
        raise APIValidation(_('Ошибка во время получение данных от Multibank'), status_code=400)
    payment_transaction_id = payment_response.get('data', {}).get('uuid')
    transaction.transaction_id = payment_transaction_id

    # PAYMENT CONFIRMATION
    need_otp_confirmation = True if payment_response.get('data', {}).get('otp_hash') else False
    if need_otp_confirmation:
        transaction.save()
        return {'need_otp': need_otp_confirmation, 'transaction_id': payment_transaction_id}
    payment_confirm_resp, payment_confirm_sc = multibank_prod_app.confirm_payment(
        transaction_id=payment_transaction_id
    )
    if not str(payment_confirm_sc).startswith('2'):
        transaction.status = 'failed'
        transaction.save()
        raise APIValidation(_('Ошибка во время подтверждении оплаты Multibank'), status_code=400)
    if payment_confirm_resp.get('data', {}).get('status') == 'success':
        transaction.status = 'paid'
    transaction.save()
    if fundraising:
        fundraising.current_amount += creator_amount
        fundraising.save(update_fields=['current_amount'])
    return {'need_otp': need_otp_confirmation, 'transaction_id': payment_transaction_id}

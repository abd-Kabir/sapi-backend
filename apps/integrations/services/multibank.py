import logging

from django.conf import settings

from apps.authentication.models import User, Card, UserSubscription, Donation
from apps.integrations.api_integrations.multibank import multibank_prod_app
from apps.integrations.models import MultibankTransaction
from config.core.api_exceptions import APIValidation

from django.utils.translation import gettext_lazy as _

logger = logging.getLogger()


def calculate_payment_amount(amount, sapi_share, commission_by_subscriber):
    multicard_commission = amount * 0.02
    sapi_amount = (sapi_share / 100) * amount

    if commission_by_subscriber:
        creator_amount = amount
        amount = amount + sapi_amount + multicard_commission
    else:
        creator_amount = (((100 - sapi_share) / 100) * amount) - multicard_commission
    return creator_amount, amount, sapi_amount


def multibank_payment(user: User, creator: User, card: Card, amount, transaction_type, fundraising=None,
                      commission_by_subscriber=False, subscription: UserSubscription = None, donation: Donation = None):
    # AMOUNT calculation:
    amount = amount * 100
    creator_amount, amount, sapi_amount = calculate_payment_amount(amount, creator.sapi_share, commission_by_subscriber)

    # SAPI TRANSACTION CREATION
    transaction = MultibankTransaction.objects.create(
        store_id=settings.MULTIBANK_INTEGRATION_SETTINGS['PROD']['STORE_ID'], amount=amount,
        transaction_type=transaction_type, user=user, creator=creator, card_token=card.token
    )
    if subscription:
        transaction.subscription = subscription
    elif donation:
        transaction.donation = donation
    transaction.save()

    # GET CREATOR RECEIPIENT
    receipient_req_body = {
        'tin': creator.pinfl,
        'mfo': '00491',  # Hard coded bank's MFO
        'account_no': creator.multibank_account,
        'commitent': True
    }
    logger.debug(f'Multibank receipient request body: {receipient_req_body};')
    creator_receipient, receipient_sc = multibank_prod_app.get_receipient(
        data=receipient_req_body,
        merchant_id=settings.MULTIBANK_INTEGRATION_SETTINGS['PROD']['MERCHANT_ID']
    )
    logger.debug(f'Multibank receipient response: {creator_receipient}; '
                 f'Multibank receipient status_code: {receipient_sc};')
    if not str(receipient_sc).startswith('2'):
        raise APIValidation(creator_receipient, status_code=400)
        # raise APIValidation(_('Ошибка во время получение данных от Multibank'), status_code=400)

    # PAYMENT CREATION
    creator_split = {
        'type': 'account',
        'receipient': creator_receipient.get('data', {}).get('uuid'),
        'amount': int(creator_amount),
        'details': 'Донат для креатора SAPI'
    }
    sapi_split = {
        'type': 'account',
        'receipient': '900addbc-4fed-11f0-8b0d-00505680eaf6',  # Hard coded SAPI's ID
        'amount': int(sapi_amount),
        'details': 'Донат для креатора SAPI'
    }
    ofd = [
        # Услуга креатора
        {
            'qty': 1,
            'price': creator_amount,
            'mxik': '10305008005000000',
            'total': creator_amount,
            'package_code': '1660595',
            'name': 'Оплата за креатору за доступ.',
            # 'tin': "307578794"
        },
        # Услуги SAPI
        {
            'qty': 1,
            'price': sapi_amount,
            'mxik': '10305008003000000',
            'total': sapi_amount,
            'package_code': '1545646',
            'name': 'Комиссия SAPI за услугу.',
            # 'tin': "307578794"
        }
    ]
    transaction.sapi_amount = sapi_amount
    transaction.creator_amount = creator_amount
    transaction.ofd_items = ofd
    body = {
        'card': {
            'token': card.token
        },
        'amount': amount,
        'store_id': settings.MULTIBANK_INTEGRATION_SETTINGS['PROD']['STORE_ID'],
        'invoice_id': str(transaction.id),
        'split': [creator_split, sapi_split],
        'ofd': ofd,
        'callback_url': 'https://api.sapi.uz/api/multibank/payment/webhook/',
    }
    logger.debug(f'Multibank payment request body: {body};')
    payment_response, payment_sc = multibank_prod_app.create_payment(data=body)
    logger.debug(f'Multibank payment response: {payment_response}; '
                 f'Multibank payment status_code: {payment_sc};')
    if not str(payment_sc).startswith('2'):
        transaction.status = 'failed'
        transaction.save()
        raise APIValidation(payment_response, status_code=400)
        # raise APIValidation(_('Ошибка во время получение данных от Multibank'), status_code=400)
    payment_transaction_id = payment_response.get('data', {}).get('uuid')
    transaction.transaction_id = payment_transaction_id

    # PAYMENT CONFIRMATION
    need_otp_confirmation = True if payment_response.get('data', {}).get('otp_hash') else False
    if need_otp_confirmation:
        transaction.save()
        if subscription:
            subscription.is_active = False
        if donation:
            donation.is_active = False
        return {
            'need_otp': need_otp_confirmation, 'transaction_id': payment_transaction_id,
            'url': payment_response.get('data', {}).get('checkout_url')
        }
    payment_confirm_resp, payment_confirm_sc = multibank_prod_app.confirm_payment(
        transaction_id=payment_transaction_id
    )
    logger.debug(f'Multibank payment confirm response: {payment_confirm_resp}; '
                 f'Multibank payment confirm status_code: {payment_confirm_sc};')
    if not str(payment_confirm_sc).startswith('2'):
        transaction.status = 'failed'
        transaction.save()
        raise APIValidation(payment_confirm_sc, status_code=400)
        # raise APIValidation(_('Ошибка во время подтверждении оплаты Multibank'), status_code=400)
    if payment_confirm_resp.get('data', {}).get('status') == 'success':
        transaction.status = 'paid'
    transaction.save()
    # if fundraising:
    #     fundraising.current_amount += creator_amount
    #     fundraising.save(update_fields=['current_amount'])
    return {'need_otp': need_otp_confirmation, 'transaction_id': payment_transaction_id}


def multibank_side_system_payment(user: User, creator: User, amount, transaction_type, payment_type,
                                  fundraising=None, commission_by_subscriber=False,
                                  subscription: UserSubscription = None, donation: Donation = None):
    # AMOUNT calculation:
    amount = amount * 100
    creator_amount, amount, sapi_amount = calculate_payment_amount(amount, creator.sapi_share, commission_by_subscriber)

    # SAPI TRANSACTION CREATION
    transaction = MultibankTransaction.objects.create(
        store_id=settings.MULTIBANK_INTEGRATION_SETTINGS['PROD']['STORE_ID'], amount=amount,
        transaction_type=transaction_type, payment_type=payment_type, user=user, creator=creator,
    )
    if subscription:
        transaction.subscription = subscription
    elif donation:
        transaction.donation = donation
    transaction.save()

    # GET CREATOR RECEIPIENT
    receipient_req_body = {
        'tin': creator.pinfl,
        'mfo': '00491',  # Hard coded bank's MFO
        'account_no': creator.multibank_account,
        'commitent': True
    }
    logger.debug(f'Multibank receipient request body: {receipient_req_body};')
    creator_receipient, receipient_sc = multibank_prod_app.get_receipient(
        data=receipient_req_body,
        merchant_id=settings.MULTIBANK_INTEGRATION_SETTINGS['PROD']['MERCHANT_ID']
    )
    logger.debug(f'Multibank receipient response: {creator_receipient}; '
                 f'Multibank receipient status_code: {receipient_sc};')
    if not str(receipient_sc).startswith('2'):
        raise APIValidation(creator_receipient, status_code=400)
        # raise APIValidation(_('Ошибка во время получение данных от Multibank'), status_code=400)

    # PAYMENT CREATION
    creator_split = {
        'type': 'account',
        'receipient': creator_receipient.get('data', {}).get('uuid'),
        'amount': int(creator_amount),
        'details': 'Донат для креатора SAPI'
    }
    sapi_split = {
        'type': 'account',
        'receipient': '900addbc-4fed-11f0-8b0d-00505680eaf6',  # Hard coded SAPI's ID
        'amount': int(sapi_amount),
        'details': 'Донат для креатора SAPI'
    }
    ofd = [
        # Услуга креатора
        {
            'qty': 1,
            'price': creator_amount,
            'mxik': '10305008005000000',
            'total': creator_amount,
            'package_code': '1660595',
            'name': 'Оплата за креатору за доступ.',
            # 'tin': "307578794"
        },
        # Услуги SAPI
        {
            'qty': 1,
            'price': sapi_amount,
            'mxik': '10305008003000000',
            'total': sapi_amount,
            'package_code': '1545646',
            'name': 'Комиссия SAPI за услугу.',
            # 'tin': "307578794"
        }
    ]
    transaction.sapi_amount = sapi_amount
    transaction.creator_amount = creator_amount
    transaction.ofd_items = ofd
    body = {
        'payment_system': payment_type,
        'amount': amount,
        'store_id': settings.MULTIBANK_INTEGRATION_SETTINGS['PROD']['STORE_ID'],
        'invoice_id': str(transaction.id),
        'split': [creator_split, sapi_split],
        'ofd': ofd,
        'callback_url': 'https://c004fbeaa9da.ngrok-free.app/api/multibank/payment/webhook/',
        # 'callback_url': 'https://api.sapi.uz/api/multibank/payment/webhook/',
    }
    logger.debug(f'Multibank payment request body: {body};')
    payment_response, payment_sc = multibank_prod_app.create_payment(data=body)
    logger.debug(f'Multibank payment response: {payment_response}; '
                 f'Multibank payment status_code: {payment_sc};')
    if not str(payment_sc).startswith('2'):
        transaction.status = 'failed'
        transaction.save()
        raise APIValidation(payment_response, status_code=400)
        # raise APIValidation(_('Ошибка во время получение данных от Multibank'), status_code=400)
    payment_transaction_id = payment_response.get('data', {}).get('uuid')
    transaction.transaction_id = payment_transaction_id

    transaction.save()
    # if fundraising:
    #     fundraising.current_amount += creator_amount
    #     fundraising.save(update_fields=['current_amount'])
    return {'url': payment_response.get('data', {}).get('checkout_url'), 'transaction_id': payment_transaction_id}

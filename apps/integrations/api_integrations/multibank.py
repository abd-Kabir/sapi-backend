from django.conf import settings
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from apps.integrations.models import MultibankAuthToken
from config.core.api_exceptions import APIValidation
from config.core.request import HTTPClient


class MultibankRequestHandler(HTTPClient):
    def __init__(self, base_url, application_id, secret):
        self.base_url = base_url
        self.application_id = application_id
        self.secret = secret

    def auth(self, method: str = 'POST', endpoint: str = 'auth'):
        payload = {
            'application_id': self.application_id,
            'secret': self.secret
        }
        token = MultibankAuthToken.objects.filter(expires_at__gt=now())
        if token.exists():
            token = token.first().token
        else:
            token_response, status_code = self.make_request(method=method, endpoint=endpoint, json=payload)
            if str(status_code).startswith('2'):
                MultibankAuthToken.objects.all().delete()
                token_instance = MultibankAuthToken.objects.create(token=token_response.get('token'),
                                                                   expires_at=token_response.get('expiry'))
                token = token_instance.token
            else:
                raise APIValidation(_(f'Ошибка в получении ответа от Multibank: {token_response}'),
                                    status_code=status_code)
        return token

    def bind_card(self, data: dict, method: str = 'POST', endpoint: str = 'payment/card/bind'):
        headers = {
            'Authorization': f'Bearer {self.auth()}'
        }
        return self.make_request(method=method, endpoint=endpoint, headers=headers, json=data)

    def remove_card(self, card_token, method: str = 'DELETE'):
        endpoint: str = f'payment/card/{card_token}'
        headers = {'Authorization': f'Bearer {self.auth()}'}
        return self.make_request(method=method, endpoint=endpoint, headers=headers)

    def create_payment(self, data: dict, method: str = 'POST', endpoint: str = 'payment'):
        headers = {
            'Authorization': f'Bearer {self.auth()}'
        }
        return self.make_request(method=method, endpoint=endpoint, headers=headers, json=data)

    def confirm_payment(self, transaction_id, data: dict = None, method: str = 'PUT'):
        endpoint: str = f'payment/{transaction_id}'
        headers = {
            'Authorization': f'Bearer {self.auth()}'
        }
        if data:
            return self.make_request(method=method, endpoint=endpoint, headers=headers, json=data)
        return self.make_request(method=method, endpoint=endpoint, headers=headers)

    def check_account(self, phone, method: str = 'GET', endpoint: str = 'mobile/user/check_account'):
        params = {'phone': phone}
        headers = {
            'Authorization': f'Bearer {self.auth()}'
        }
        return self.make_request(method=method, endpoint=endpoint, headers=headers, params=params)

    def get_receipient(self, merchant_id, data: dict, method: str = 'POST'):
        endpoint: str = f'payment/merchant/{merchant_id}/account'
        headers = {
            'Authorization': f'Bearer {self.auth()}'
        }
        return self.make_request(method=method, endpoint=endpoint, headers=headers, json=data)

    def make_request(self, method: str, endpoint: str, **kwargs):
        response = self._request(method, f"{self.base_url}/{endpoint}", **kwargs)
        try:
            return response.json(), response.status_code
        except Exception:  # noqa
            return {"detail": f"Error occurred: {response.text}"}, 400


multibank_prod_app = MultibankRequestHandler(
    base_url=settings.MULTIBANK_INTEGRATION_SETTINGS['PROD']['BASE_URL'],
    application_id=settings.MULTIBANK_INTEGRATION_SETTINGS['PROD']['APPLICATION_ID'],
    secret=settings.MULTIBANK_INTEGRATION_SETTINGS['PROD']['SECRET']
)

from django.conf import settings

from config.core.request import HTTPClient


class SMSRequestHandler(HTTPClient):
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password

    def token(self, method: str = 'POST', endpoint: str = 'api/auth/login'):
        payload = {
            'email': self.username,
            'password': self.password
        }
        return self.make_request(method=method, endpoint=endpoint, json=payload)

    def user_information(self, method: str = 'GET', endpoint: str = 'api/auth/user'):
        headers = {
            'Authorization': f'Bearer {self.token().get("data", {}).get("token")}'
        }
        return self.make_request(method=method, endpoint=endpoint, headers=headers)

    def templates_list(self, method: str = 'GET', endpoint: str = 'api/user/templates'):
        headers = {
            'Authorization': f'Bearer {self.token().get("data", {}).get("token")}'
        }
        return self.make_request(method=method, endpoint=endpoint, headers=headers)

    def send_sms(self, method: str = 'POST', endpoint: str = 'api/message/sms/send', data: dict = None):
        headers = {
            'Authorization': f'Bearer {self.token().get("data", {}).get("token")}'
        }
        return self.make_request(method=method, endpoint=endpoint, headers=headers, json=data)

    def make_request(self, method: str, endpoint: str, **kwargs):
        response = self._request(method, f"{self.base_url}/{endpoint}", **kwargs)
        try:
            return response.json()
        except Exception:  # noqa
            return {"detail": f"Error occurred: {response.text}"}


sms_app = SMSRequestHandler(
    base_url=settings.SMS_INTEGRATION_SETTINGS['SMS_BASE_URL'],
    username=settings.SMS_INTEGRATION_SETTINGS['SMS_USERNAME'],
    password=settings.SMS_INTEGRATION_SETTINGS['SMS_PASSWORD']
)

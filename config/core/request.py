import ssl
import requests
from requests.adapters import HTTPAdapter
from requests.auth import HTTPBasicAuth


class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.set_ciphers('DEFAULT@SECLEVEL=1')
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        kwargs['ssl_context'] = context
        return super(SSLAdapter, self).init_poolmanager(*args, **kwargs)


class HTTPClient:
    @staticmethod
    def basic_auth(username: str, password: str) -> HTTPBasicAuth:
        return HTTPBasicAuth(username, password)

    @staticmethod
    def _request(method: str, url: str, **kwargs) -> requests.Response:
        response = requests.request(method=method, url=url, **kwargs)
        return response

    @staticmethod
    def _no_ssl_request(method: str, url: str, **kwargs) -> requests.Response:
        # response = requests.request(method=method, url=url, verify=False, **kwargs)

        session = requests.Session()
        session.mount('https://', SSLAdapter())
        response = session.request(method=method, url=url, verify=False, **kwargs)
        return response

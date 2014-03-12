from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from azurepython3.auth import SharedKeyAuthentication
from urllib.parse import quote_plus

USE_SSL = True

try:
    import ssl
except ImportError:
    USE_SSL = False

class AzureService:

    timeout = None
    retry = True

    def __init__(self, account_name, account_key):
        self.account_name = account_name
        self.account_key = account_key
        self.auth = SharedKeyAuthentication(account_name, account_key)

    def get_host(self, protocol=None):
        if protocol is None:
            protocol = 'https' if USE_SSL else 'http'
        return "%s://%s.blob.core.windows.net" % (protocol, self.account_name)

    def get_url(self, query = '/', protocol=None):
        return self.get_host(protocol) + quote_plus(query, safe='/')

    def _headers(self):
        return {
            'x-ms-version': '2011-08-18',
            'x-ms-date': datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT'),
            'Content-Type': 'application/octet-stream Charset=UTF-8'
        }

    def _params(self):
        return {
            'timeout': self.timeout
        }

    def _request(self, method, uri, headers = None, params = None, content = None):
        if content is None:
            content = dict()

        # filter empty headers
        if headers != None:
            headers = { key: value for key, value in headers.items() if value != None }

        headers = dict(self._headers(), **headers) if headers else self._headers()
        params = dict(self._params(), **params) if params else self._params()
        req = requests.Request(method, self.get_url(uri), data=content, headers=headers, params=params)

        # Give content length for modifying requests
        if method.lower() in ['put', 'post', 'merge', 'delete'] and not content:
            req.headers['Content-Length'] = '0'

        # Generate and append Authorization signature to request headers
        self.auth.authenticate(req, len(content))
        request = req.prepare()

        session = requests.session()
        session.mount('http://', HTTPAdapter(max_retries=5))
        session.mount('https://', HTTPAdapter(max_retries=5))

        response = session.send(request)
        response.encoding = 'utf-8-sig'

        # raise underlying HTTPError if something goes wrong
        if response.status_code >= 300:
            response.raise_for_status()

        return response
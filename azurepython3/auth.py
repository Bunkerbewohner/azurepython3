import base64
import hashlib
import hmac
from urllib.parse import urlparse
import itertools
import requests

class SharedKeyAuthentication:

    def __init__(self, account_name, account_key):
        """
        Initializes the authenticator using credentials provided
        """
        self.account_name = account_name
        self.account_key = account_key

    def auth_header(self, request : requests.Request, content_length = None):
        """ Computes the value of the Authorization header, following the form "SharedKey accountname:signature" """
        signature = self._signature(request, content_length)
        return 'SharedKey %s:%s' % (self.account_name, self._sign(signature))

    def authenticate(self, request : requests.Request, content_length = None):
        """ Computes and adds the Authorization header to request """
        request.headers['Authorization'] = self.auth_header(request, content_length)

    def _signature(self, request : requests.Request, content_length = None):
        """
        Creates the signature string for this request according to
        http://msdn.microsoft.com/en-us/library/windowsazure/dd179428.aspx
        """

        headers = {str(name).lower(): value for name, value in request.headers.items()}
        if content_length > 0:
            headers['content-length'] = str(content_length)

        # method to sign
        signature = request.method.upper() + '\n'

        # get headers to sign
        headers_to_sign = ['content-encoding', 'content-language', 'content-length',
                           'content-md5', 'content-type', 'date', 'if-modified-since',
                           'if-match', 'if-none-match', 'if-unmodified-since', 'range']

        signature += "\n".join(headers.get(h, '') for h in headers_to_sign) + "\n"

        # get x-ms header to sign
        signature += ''.join("%s:%s\n" % (k, v) for k, v in sorted(headers.items()) if v and 'x-ms' in k)

        # get account_name and uri path to sign
        signature += '/' + self.account_name + urlparse(request.url).path

        # get query string to sign
        signature += ''.join("\n%s:%s" % (k, v) for k, v in sorted(request.params.items()) if v)

        return signature

    def _sign(self, string):
        " Signs given string using SHA256 with the account key. Returns the base64 encoded signature. "
        decode_account_key = base64.b64decode(self.account_key)
        signed_hmac_sha256 = hmac.HMAC(decode_account_key, string.encode('utf-8'), hashlib.sha256)
        digest = signed_hmac_sha256.digest()
        return base64.b64encode(digest).decode('utf-8')
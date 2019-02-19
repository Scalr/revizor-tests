# coding: utf-8
"""
Created on 01.06.18
@author: Eugeny Kurkovich
"""
import os
import hmac
import json
import pytz
import logging
import hashlib
import binascii
import datetime

import box
import requests

from urllib.parse import urlencode, urlparse, urlunparse

SIGNATURE_VER = "V1-HMAC-SHA256"
API_DEBUG_VER = "1"


requests.Response.box = lambda self: box.Box(self.json())


LOG = logging.getLogger(__name__)


class ScalrApiSession(requests.Session):

    def __init__(self, secret_key_id, secret_key):
        self.secret_key_id = secret_key_id
        self.secret_key = secret_key

        super().__init__()

    def prepare_request(self, request):
        """Implements Scalr authentication mechanism"""

        parsed_url = urlparse(request.url)

        now = datetime.datetime.now(tz=pytz.timezone(os.environ.get("TZ", "UTC")))
        sig_date = now.isoformat()

        canonical_qs = parsed_url.query
        uri = parsed_url.path
        method = request.method.upper()

        body = request.data or ""
        string_to_sign = "\n".join((
            method,
            sig_date,
            uri,
            canonical_qs,
            body))
        # Sign request
        digest = hmac.new(self.secret_key.encode(), string_to_sign.encode(), hashlib.sha256).digest()
        signature = binascii.b2a_base64(digest).strip().decode()

        # Update request headers, set auth
        headers = dict()
        headers['Content-Type'] = 'application/json; charset=utf-8'
        headers['X-Scalr-Key-Id'] = self.secret_key_id
        headers['X-Scalr-Date'] = sig_date
        headers['X-Scalr-Signature'] = '%s %s' % (SIGNATURE_VER, signature)
        headers['X-Scalr-Debug'] = API_DEBUG_VER
        request.headers.update(headers)

        # Prepare request
        request = super().prepare_request(request)

        return request

    def request(self, method, url, params=None, body=None, filters=None,  serializer=None, *args, **kwargs):
        # Set uri
        uri = url.format(**params)
        parsed_url = urlparse(uri)
        # Set string to sign
        query_filters = urlencode(sorted(filters.items())) if filters else ""
        # Set url
        url = urlunparse((parsed_url[0],
                          parsed_url[1],
                          parsed_url[2],
                          '',
                          query_filters,
                          ''))
        body = json.dumps(body, default=serializer) if body else body
        resp = super().request(method.lower(), url, data=body, *args, **kwargs)
        try:
            resp.raise_for_status()
        except requests.HTTPError as e:
            message = e.args
            if 'errors' in resp.text:
                message = '\n'.join(['{}: {}'.format(err['code'], err['message']) for err in resp.json().get('errors')])
            raise e.__class__(message, request=e.request, response=e.response)
        return resp

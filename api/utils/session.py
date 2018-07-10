# coding: utf-8
"""
Created on 01.06.18
@author: Eugeny Kurkovich
"""
import os
import hmac
import json
import pytz
import hashlib
import binascii
import datetime
import requests

from urllib.parse import urlencode, urlparse, urlunparse


SIGNATURE_VER = "V1-HMAC-SHA256"
API_DEBUG_VER = "1"


class ScalrApiSession(requests.Session):

    def __init__(self, host, secret_key_id, secret_key, schema=None):
        self.base_path = host
        self.secret_key_id = secret_key_id
        self.secret_key = secret_key
        self.schema = schema or "http"
        super().__init__()

    def prepare_request(self, request):
        """Implements Scalr authentication mechanism"""
        parsed_url = urlparse(request.url)

        now = datetime.datetime.now(tz=pytz.timezone(os.environ.get("TZ", "UTC")))
        sig_date = now.isoformat()

        canonical_qs = parsed_url.query
        uri = parsed_url.path
        # Set body
        body = request.data
        body = json.dumps(body, separators=(",", ":")) if body else ""
        method = request.method.upper()

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

    def request(self, method, endpoint, params, body=None, filters=None, *args, **kwargs):
        # Set uri
        uri = endpoint.format(**params)
        # Set string to sign
        query_string = urlencode(sorted(filters.items())) if filters else ""
        # Set url
        url = urlunparse((self.schema, self.base_path, uri, '', query_string, ''))
        resp = super().request(method.lower(), url, data=body, *args, **kwargs)

        resp.raise_for_status()
        return resp



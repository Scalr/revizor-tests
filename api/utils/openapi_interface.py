import urllib.parse
from openapi_core.wrappers.base import BaseOpenAPIRequest, BaseOpenAPIResponse


class RequestsOpenAPIRequest(BaseOpenAPIRequest):
    def __init__(self, response):
        self._response = response
        parsed_url = urllib.parse.urlparse(self._response.url)
        self.host_url = f'{parsed_url.scheme}://{parsed_url.netloc}'
        self.path = parsed_url.path
        self.path_pattern = self._response.path_url
        self.method = self._response.request.method.lower()
        self.parameters = {
            'path': self._response.params,
            'query': parsed_url.query,
            'header': self._response.request.headers,
            'cookie': self._response.request._cookies.get_dict(),
        }
        self.body = self._response.request.body
        self.mimetype = 'application/json'


class RequestsOpenAPIResponse(BaseOpenAPIResponse):
    def __init__(self, response):
        self._response = response
        self.data = self._response.text
        self.status_code = self._response.status_code
        self.mimetype = self._response.headers.get('Content-Type', 'application/json')
        if ';' in self.mimetype:
            self.mimetype = self.mimetype.split(';')[0]

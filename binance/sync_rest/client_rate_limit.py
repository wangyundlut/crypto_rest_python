
import hashlib
import hmac
import requests
import time
from operator import itemgetter




class Client(object):
    
    def __init__(self, api_key=None, api_secret=None, requests_params=None):

        self.API_KEY = api_key
        self.API_SECRET = api_secret
        self.session = self._init_session()
        self._requests_params = requests_params
        self.response = None
        # 添加base_url
        self.base_url = 'https://api.binance.com'

    def _init_session(self):

        session = requests.session()
        session.headers.update({'Accept': 'application/json',
                                'User-Agent': 'binance/python',
                                'X-MBX-APIKEY': self.API_KEY})
        return session

    def _generate_signature(self, data):
        # 生成签名必须有排序
        ordered_data = self._order_params(data)
        query_string = '&'.join(["{}={}".format(d[0], d[1]) for d in ordered_data])
        m = hmac.new(self.API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256)
        return m.hexdigest()

    def _order_params(self, data):
        """Convert params to list with signature as last element

        :param data:
        :return:

        """
        has_signature = False
        params = []
        for key, value in data.items():
            if key == 'signature':
                has_signature = True
            else:
                params.append((key, value))
        # sort parameters by key
        params.sort(key=itemgetter(0))
        if has_signature:
            params.append(('signature', data['signature']))
        return params

    def _request(self, method, uri, signed=False, force_params=False, **kwargs):

        # set default requests timeout
        kwargs['timeout'] = 10

        # add our global requests params
        if self._requests_params:
            kwargs.update(self._requests_params)

        data = kwargs.get('data', None)
        if data and isinstance(data, dict):
            kwargs['data'] = data

            # find any requests params passed and apply them
            if 'requests_params' in kwargs['data']:
                # merge requests params into kwargs
                kwargs.update(kwargs['data']['requests_params'])
                del(kwargs['data']['requests_params'])

        if signed:
            # generate signature
            # time.time() return with local timezone, which is the same 
            kwargs['data']['timestamp'] = int(time.time() * 1000)
            kwargs['data']['signature'] = self._generate_signature(kwargs['data'])

        # sort get and post params to match signature order
        if data:
            # sort post params
            kwargs['data'] = self._order_params(kwargs['data'])
            # Remove any arguments with values of None.
            null_args = [i for i, (key, value) in enumerate(kwargs['data']) if value is None]
            for i in reversed(null_args):
                del kwargs['data'][i]

        # if get request assign data array to params value for requests lib
        if data and (method == 'get' or force_params):
            kwargs['params'] = '&'.join('%s=%s' % (data[0], data[1]) for data in kwargs['data'])
            del(kwargs['data'])

        self.response = getattr(self.session, method)(uri, **kwargs)
        return self._handle_response()

    def _request_api(self, method, path, signed=False, **kwargs):
        uri = self.base_url + path
        return self._request(method, uri, signed, **kwargs)

    def _handle_response(self):
        """Internal helper for handling API responses from the Binance server.
        Raises the appropriate exceptions when necessary; otherwise, returns the
        response.
        """
        return self.response

if __name__ == "__main__":
    key = 'wj4e957S1nlyLXch97J6u6cHYBncsmJ4pz7T4iB6n5HxC7aTbr8X4U0jUbNyZQjp'
    secret = 'sdacA3hRZbKflJmDQNdvoqQQqXYenb08nOtRTxSHzge0HowsCR81nqupeHauWMfw' 
    client = Client(key, secret)
    result = client._request_api("get", "/sapi/v1/margin/rateLimit/order", True, data={})
    print(result.json())

    """
    {'rateLimitType': 'ORDERS', 'interval': 'SECOND', 'intervalNum': 10, 'limit': 50, 'count': 0}
    {'rateLimitType': 'ORDERS', 'interval': 'DAY', 'intervalNum': 1, 'limit': 160000, 'count': 15057}
    """
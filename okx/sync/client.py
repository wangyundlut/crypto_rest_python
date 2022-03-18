import requests
import json

from .consts import GET, POST, DELETE, API_URL

from .utils import parse_params_to_str, get_timestamp, sign, get_header, pre_hash
from .exceptions import OKXAPIException, OKXRequestException




class Client(object):

    def __init__(self, api_key, api_secret_key, passphrase, use_server_time=False, test=False, first=False):

        self.API_KEY = api_key
        self.API_SECRET_KEY = api_secret_key
        self.PASSPHRASE = passphrase
        self.first = first
        self.test = test

    def _request(self, method, request_path, params, cursor=False):
        # get 方法下 params 都被解析到了request_path 里面去
        if method == GET:
            request_path = request_path + parse_params_to_str(params)
        # url
        url = API_URL + request_path

        # 获取本地时间
        # format: %Y-%m-%dT%H:%M:%S.%3fZ
        timestamp = get_timestamp()

        # sign & header

        # body 如果不是post 都是空，也就是非post 所有的东西都写到url中去
        body = json.dumps(params) if method == POST else ""
        sign_msg = sign(pre_hash(timestamp, method, request_path, str(body)), self.API_SECRET_KEY)
        header = get_header(self.API_KEY, sign_msg, timestamp, self.PASSPHRASE)

        if self.test:
            header['x-simulated-trading'] = '1'

        if self.first:
            print("url:", url)
            self.first = False

        # print("url:", url)
        # print("headers:", header)
        # print("body:", body)

        # send request
        response = None
        if method == GET:
            response = requests.get(url, headers=header)
        elif method == POST:
            response = requests.post(url, data=body, headers=header)
        elif method == DELETE:
            response = requests.delete(url, headers=header)

        # exception handle
        if not str(response.status_code).startswith('2'):
            raise OKXAPIException(response)
        try:
            res_header = response.headers
            if cursor:
                r = dict()
                try:
                    r['before'] = res_header['OK-BEFORE']
                    r['after'] = res_header['OK-AFTER']
                except:
                    pass
                return response.json(), r
            else:
                return response.json()

        except ValueError:
            raise OKXRequestException('Invalid Response: %s' % response.text)

    def _request_without_params(self, method, request_path):
        return self._request(method, request_path, {})

    def _request_with_params(self, method, request_path, params, cursor=False):
        return self._request(method, request_path, params, cursor)

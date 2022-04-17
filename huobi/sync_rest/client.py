# -*- coding: utf-8 -*-

from getpass import GetPassWarning
import json
from pickletools import long1
from unittest.case import _BaseTestCaseContext
import urllib
import datetime
import requests
import hmac, base64, hashlib
import time
import io
import gzip

from pprint import pprint
from typing import Dict, List

from .consts import SPOT_REST_HOST, GET, POST, DELETE, EXCHANGE_NAME
from .exception import huobiException, huobiRequestException
# for rest spot
def create_signature(
    api_key: str,
    method: str,
    host: str,
    path: str,
    secret_key: str,
    get_params=None
) -> Dict[str, str]:
    """
    for huobi, http get different with http post
    http get:  get_params is not none, they are in params, with data
    http post: get_params is none, sign_info in url + ? + urllib.parse.urlencode(sign_info)
    """
    sorted_params: list = [
        ("AccessKeyId", api_key),
        ("SignatureMethod", "HmacSHA256"),
        ("SignatureVersion", "2"),
        ("Timestamp", datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"))
    ]

    if get_params:
        sorted_params.extend(list(get_params.items()))
        sorted_params = list(sorted(sorted_params))
    encode_params = urllib.parse.urlencode(sorted_params)
    
    host_name = urllib.parse.urlparse(host + path).hostname
    path_name = urllib.parse.urlparse(host + path).path

    payload: list = [method, host_name, path_name, encode_params]
    payload: str = "\n".join(payload)
    payload: str = payload.encode(encoding="UTF8")

    secret_key: str = secret_key.encode(encoding="UTF8")

    digest: bytes = hmac.new(secret_key, payload, digestmod=hashlib.sha256).digest()
    signature: bytes = base64.b64encode(digest)

    params: dict = dict(sorted_params)
    params["Signature"] = signature.decode("UTF8")
    
    # if method == POST:
    #     print(params)

    # params = {key: params[key] for key in sorted(params)}
    return params

# for websocket spot
def create_signature_v2(
    api_key: str,
    method: str,
    host: str,
    path: str,
    secret_key: str,
    get_params=None
) -> Dict[str, str]:
    """
    创建WebSocket接口签名
    """
    sorted_params: list = [
        ("accessKey", api_key),
        ("signatureMethod", "HmacSHA256"),
        ("signatureVersion", "2.1"),
        ("timestamp", datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"))
    ]

    if get_params:
        sorted_params.extend(list(get_params.items()))
        sorted_params = list(sorted(sorted_params))
    encode_params = urllib.parse.urlencode(sorted_params)
    
    host_name = urllib.parse.urlparse(host + path).hostname
    path_name = urllib.parse.urlparse(host + path).path

    payload: list = [method, host_name, path_name, encode_params]
    payload: str = "\n".join(payload)
    payload: str = payload.encode(encoding="UTF8")

    secret_key: str = secret_key.encode(encoding="UTF8")

    digest: bytes = hmac.new(secret_key, payload, digestmod=hashlib.sha256).digest()
    signature: bytes = base64.b64encode(digest)

    params: dict = dict(sorted_params)
    params["authType"] = "api"
    params["signature"] = signature.decode("UTF8")
    return params

def signature_huobi_aws(pParams, method, host_url, request_path, secret_key):
    sorted_params = sorted(pParams.items(), key=lambda d: d[0], reverse=False)
    encode_params = urllib.parse.urlencode(sorted_params)
    payload = [method, host_url, request_path, encode_params]
    payload = '\n'.join(payload)
    payload = payload.encode(encoding='UTF8')
    secret_key = secret_key.encode(encoding='UTF8')
    digest = hmac.new(secret_key, payload, digestmod=hashlib.sha256).digest()
    signature = base64.b64encode(digest)
    signature = signature.decode()
    return signature

def decode_msg_huobi(msg):
    if isinstance(msg, bytes):
        compressedstream = io.BytesIO(msg)
        gziper = gzip.GzipFile(fileobj=compressedstream)
        msg = json.loads(gziper.read().decode('utf-8'))
    elif isinstance(msg, str):
        msg = json.loads(msg)
    return msg

CONST_ERROR_INFO = {
    429: "Too Many Requests"
}


class Client(object):

    def __init__(self, api_key, secret_key, host=SPOT_REST_HOST, exch="pro"):
        self.__api_key = api_key
        self.__secret_key = secret_key
        self.__host = host
        self._exch = exch
        
        self.exchange_name = EXCHANGE_NAME

    def _get_url(self, endpoint):
        return self.__host + endpoint

    def _request(self, endpoint, method, params={}, auth=False):
        headers = {
            "Accept": "application/json",
            "Content-type": "application/json",
            'User-agent': 'Mozilla 5.10',
        }

        url_full = self._get_url(endpoint)
        ##########################################
        # 韩国站可以用pro的colo，需要额外加一个header
        if self._exch == "hbkr":
            headers.update({'CLOUD-EXCHANGE': '064B7FE487'})
        # 日本站的也可以用pro的colo，需要额外加一个header
        elif self._exch == "hbjp":
            if hasattr(self, '_api_key') and self._api_key in ['2b33c3cf-65be6192-e6650ace-dab4c45e6f', 'b4925cbf-bg5t6ygr6y-c9baea24-d659b']:
                headers.update({})
            else:
                headers.update({'CLOUD-EXCHANGE': '368B24B8A4'})
        elif self._exch == "hbsg":
            headers.update({'CLOUD-EXCHANGE': 'sgex'})
        ##########################################
        ##########################################

        if auth:
            if method == GET:
                params_get = create_signature(
                    api_key=self.__api_key,
                    method=GET,
                    host=self.__host,
                    path=endpoint,
                    secret_key=self.__secret_key,
                    get_params=params
                )
                data = urllib.parse.urlencode(params_get)
                response = requests.get(url_full, data, headers=headers, timeout=10)
            elif method == POST:
                params_post = create_signature(
                    api_key=self.__api_key,
                    method=POST,
                    host=self.__host,
                    path=endpoint,
                    secret_key=self.__secret_key,
                    get_params={}
                )
                data = json.dumps(params)
                url_full = url_full + f"?{urllib.parse.urlencode(params_post)}"
                
                response = requests.post(url_full, data, headers=headers, timeout=10)
            elif method == DELETE:
                response = requests.delete(url_full, data, headers=headers, timeout=10)
            else:
                raise Exception("method error " + str(method))
        else:
            data = urllib.parse.urlencode(params)
            if method == GET:
                response = requests.get(url_full, data, headers=headers, timeout=10)
            elif method == POST:
                response = requests.post(url_full, data, headers=headers, timeout=10)
            elif method == DELETE:
                response = requests.delete(url_full, data, headers=headers, timeout=10)
            else:
                raise Exception("method error " + str(method))
        ##########################################

        ##########################################
        if not str(response.status_code).startswith('2'):
            raise huobiException(response)
        try:
            return response.json()
        except ValueError:
            raise huobiRequestException('Invalid Response: %s' % response.text)
            
    
    
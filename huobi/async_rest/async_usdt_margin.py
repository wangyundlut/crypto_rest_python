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
import hmac
import hashlib
import time
from operator import itemgetter
from datetime import datetime, timedelta
import asyncio
from crypto_rest_python.async_rest_client import asyncRestClient, Request, Response
from aiohttp import ClientSession, ClientResponse

from pprint import pprint
from typing import Dict, List

from .consts import COIN_FUTURES_HOST, GET, POST, DELETE, EXCHANGE_NAME

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
        ("Timestamp", datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"))
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


class asyncHuobiUSDTMargin(asyncRestClient):

    def __init__(self, api_key, secret_key, host=COIN_FUTURES_HOST, exch="pro", loop: asyncio.AbstractEventLoop = None, session: ClientSession = None):
        asyncRestClient.__init__(self, loop, session)
        self.__api_key = api_key
        self.__secret_key = secret_key
        self.__host = host
        self._exch = exch
        
        self.exchange_name = EXCHANGE_NAME

    def _get_url(self, endpoint):
        return self.__host + endpoint

    def _get_header(self):
        headers = {
            "Accept": "application/json",
            "Content-type": "application/json",
            'User-agent': 'Mozilla 5.10',
        }
        return headers

    def test_cb(self, request):
        print(f"{datetime.now()} ===== call back sync =====")
        print(f"request: {request.base_url} {request.path} {request.params}")
        print(f"{request.response.json()}")

    def _request(self, endpoint, method, params={}, auth=False, cb=None, callback_method="sync"):
        headers = self._get_header()

        ##########################################
        # 韩国站可以用pro的colo，需要额外加一个header
        if self._exch == "hbkr":
            headers.update({'CLOUD-EXCHANGE': '064B7FE487'})
        # 日本站的也可以用pro的colo，需要额外加一个header
        elif self._exch == "hbjp":
            if hasattr(self, '_api_key') and self.__api_key in ['2b33c3cf-65be6192-e6650ace-dab4c45e6f', 'b4925cbf-bg5t6ygr6y-c9baea24-d659b']:
                headers.update({})
            else:
                headers.update({'CLOUD-EXCHANGE': '368B24B8A4'})
        elif self._exch == "hbsg":
            headers.update({'CLOUD-EXCHANGE': 'sgex'})
        ##########################################
        ##########################################

        if not cb:
            cb = self.test_cb

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
                self.request(
                    method="get",
                    base_url=self.__host,
                    path=f"{endpoint}?{data}",
                    callback_method=callback_method,
                    callback=cb,
                    params={},
                    headers=headers,
                    extra={}
                )
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
                
                self.request(
                    method="post",
                    base_url=self.__host,
                    path=f"{endpoint}?{urllib.parse.urlencode(params_post)}",
                    callback_method=callback_method,
                    callback=cb,
                    data=data,
                    headers=headers,
                    extra={}
                )
            elif method == DELETE:
                self.request(
                    method="delete",
                    base_url=self.__host,
                    path=f"{endpoint}?{urllib.parse.urlencode(params_post)}",
                    callback_method=callback_method,
                    callback=cb,
                    data=data,
                    headers=headers,
                    extra={}
                )
            else:
                raise Exception("method error " + str(method))
        else:
            data = urllib.parse.urlencode(params)
            if method == GET:
                self.request(
                    method="get",
                    base_url=self.__host,
                    path=f"{endpoint}?{data}",
                    callback_method=callback_method,
                    callback=cb,
                    params={},
                    headers=headers,
                    extra={}
                )
            elif method == POST:
                self.request(
                    method="post",
                    base_url=self.__host,
                    path=f"{endpoint}?{urllib.parse.urlencode(params_post)}",
                    callback_method=callback_method,
                    callback=cb,
                    data=data,
                    headers=headers,
                    extra={}
                )
            elif method == DELETE:
                self.request(
                    method="delete",
                    base_url=self.__host,
                    path=f"{endpoint}?{urllib.parse.urlencode(params_post)}",
                    callback_method=callback_method,
                    callback=cb,
                    data=data,
                    headers=headers,
                    extra={}
                )
            else:
                raise Exception("method error " + str(method))
        ##########################################

    # ===================
    # Base Data Service
    # ===================

    # ===================
    # Market Data Service
    # ===================

    # ====================
    # Account Data Service
    # ====================

    # =============
    # Trade Service
    # =============
    def trade_post_order(self, contract_code, price, volume, direction, order_price_type, client_order_id="", lever_rate=10, cb=None):
        params = {}
        params["contract_code"] = contract_code
        params["price"] = price
        params["volume"] = volume
        params["direction"] = direction
        params["order_price_type"] = order_price_type
        if client_order_id:
            params["client_order_id"] = client_order_id
        params["lever_rate"] = lever_rate
        return self._request("/linear-swap-api/v1/swap_cross_order", POST, params, auth=True, cb=cb)

    def trade_post_cancel_order(self, contract_code, order_id="", client_order_id="", cb=None):
        params = {}
        params["contract_code"] = contract_code
        if order_id:
            params["order_id"] = order_id
        elif client_order_id:
            params["client_order_id"] = client_order_id
        return self._request("/linear-swap-api/v1/swap_cross_cancel", POST, params, auth=True, cb=cb)








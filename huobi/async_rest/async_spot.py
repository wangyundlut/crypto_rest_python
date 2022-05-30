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

from .consts import SPOT_REST_HOST, GET, POST, DELETE, EXCHANGE_NAME

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


class asyncHuobiSpot(asyncRestClient):

    def __init__(self, api_key, secret_key, host=SPOT_REST_HOST, exch="pro", loop: asyncio.AbstractEventLoop = None, session: ClientSession = None):
        asyncRestClient.__init__(self, loop, session)
        self.__api_key = api_key
        self.__secret_key = secret_key
        self.__host = host
        self._exch = exch
        
        self.exchange_name = EXCHANGE_NAME

        # url: /v1/account/accounts return :"id": 10000001,"type": "spot"
        self.account_id_map = {}
        self.account_id_map_reverse = {}

        if api_key != "" and secret_key != "":
            result = self.account_get_id()
            return

    def save_account_id(self, request: Request):
        for li in request.response.json()["data"]:
            if li["state"] == "working":
                self.account_id_map[li["type"]] = li["id"]
                self.account_id_map_reverse[li["id"]] = li["type"]

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

    def get_account_type_from_account_id(self, account_id):
        if account_id in self.account_id_map_reverse:
            return self.account_id_map_reverse[account_id]
        return None

    def get_account_id_from_account_type(self, account_type):
        if account_type in self.account_id_map:
            return self.account_id_map[account_type]
        return None

    def account_get_id(self):
        params = {}
        return self._request("/v1/account/accounts", GET, params, auth=True, cb=self.save_account_id)

    # ===================
    # Base Data Service
    # ===================

    def common_timestamp(self):
        return self._request("/v1/common/timestamp", GET)

    # ===================
    # Market Data Service
    # ===================

    # ====================
    # Account Data Service
    # ====================

    # =============
    # Trade Service
    # =============
    def trade_post_order(self, symbol, type_, amount, price=None, 
        client_order_id: str="", 
        self_match_prevent: int=0, 
        stop_price: str="", 
        operator: str="",
        account_type: str="spot",
        cb=None
        ):

        """
        buy-market, sell-market, 
        buy-limit, sell-limit, 
        buy-ioc, sell-ioc, 
        buy-limit-maker, sell-limit-maker, 
        buy-stop-limit, sell-stop-limit, 
        buy-limit-fok, sell-limit-fok, 
        buy-stop-limit-fok, sell-stop-limit-fok
        """
        
        if account_type == "spot":
            acc_id = self.account_id_map["spot"]
            source = "spot-api"
        elif account_type == "margin":
            acc_id = self.account_id_map["margin"]
            source = "margin-api"
        elif account_type == "super-margin":
            acc_id = self.account_id_map["super-margin"]
            source = "super-margin-api"

        params = {
            "account-id": str(acc_id),
            "symbol": symbol,
            "type": type_,
            "amount": str(amount),

            "source": source,

            "self-match-prevent": self_match_prevent,
        }
        if price:
            params.update({"price": str(price)})
        if client_order_id:
            params.update({"client-order-id": str(client_order_id)})
        
        if stop_price:
            params.update({"stop-price": str(stop_price)})
        if operator:
            params.update({"operator": str(operator)})

        return self._request(f"/v1/order/orders/place", POST, params, auth=True, cb=cb)

    def trade_post_batch_order(self, post_order_list: List, cb=None):
        params = post_order_list
        for order in post_order_list:
            
            if order["account_type"] == "spot":
                acc_id = self.account_id_map["spot"]
                source = "spot-api"
            elif order["account_type"] == "margin":
                acc_id = self.account_id_map["margin"]
                source = "margin-api"
            elif order["account_type"] == "super-margin":
                acc_id = self.account_id_map["super-margin"]
                source = "super-margin-api"
            order["account-id"] =  str(acc_id)
            order["source"] = str(source)
        
        return self._request(f"/v1/order/batch-orders", POST, params, auth=True, cb=cb)
        
    def trade_post_cancel_order(self, order_id: str, symbol: str="", cb=None):
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._request(f"/v1/order/orders/{order_id}/submitcancel", POST, params, auth=True, cb=cb)

    def trade_post_cancel_order_cliordId(self, client_order_id: str="", cb=None):
        params = {}
        params["client-order-id"] = client_order_id
        return self._request(f"/v1/order/orders/submitCancelClientOrder", POST, params, auth=True, cb=cb)




    
    
            

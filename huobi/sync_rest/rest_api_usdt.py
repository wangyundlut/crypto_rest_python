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

from .consts import COIN_FUTURES_HOST, GET, POST, DELETE, EXCHANGE_NAME
from .client import Client
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

class huobiRestUSDT(Client):

    def __init__(self, api_key, secret_key, host=COIN_FUTURES_HOST, exch="pro"):
        super(huobiRestUSDT, self).__init__(api_key, secret_key, host, exch)

    # ===================
    # Market Data Service
    # ===================

    def market_get_contract_info(self, contract_code: str="", support_margin_mode: str="", pair: str="", contract_type: str="", business_type:str=""):
        params = {}
        if contract_code:
            params["contract_code"] = contract_code
        if pair:
            params["pair"] = pair
        if contract_type:
            params["contract_type"] = contract_type
        if support_margin_mode:
            params["support_margin_mode"] = support_margin_mode
        if business_type:
            params["business_type"] =business_type

        return self._request("/linear-swap-api/v1/swap_contract_info", GET, params)
    
    def market_get_bbo(self, contract_code="", business_type=""):
        params = {}
        if contract_code:
            params["contract_code"] = contract_code
        if business_type:
            params["business_type"] = business_type
        return self._request("/linear-swap-ex/market/bbo", GET, params)

    def market_get_ticker(self, contract_code:str):
        params = {}
        params["contract_code"] = contract_code
        return self._request("/linear-swap-ex/market/detail/merged", GET, params)

    # ====================
    # Asset Data Service
    # ====================
    def asset_balance_valuation(self, valuation_asset="USDT"):
        params = {}
        if valuation_asset:
            params["valuation_asset"] = valuation_asset
        return self._request("/linear-swap-api/v1/swap_balance_valuation", POST, params, auth=True)
    
    def asset_account(self, margin_account=""):
        params = {}
        if margin_account:
            params["margin_account"] = margin_account
        return self._request("/linear-swap-api/v1/swap_cross_account_info", POST, params, auth=True)

    def asset_position(self, contract_code="", pair="", contract_type=""):
        params = {}
        if contract_code:
            params["contract_code"] = contract_code
        if pair:
            params["pair"] = pair
        if contract_type:
            params["contract_type"] = contract_type
        return self._request("/linear-swap-api/v1/swap_cross_position_info", POST, params, auth=True)
        
    def asset_fee(self):
        params = {}
        return self._request("/linear-swap-api/v1/swap_fee", POST, params, auth=True)

    # ====================
    # Trade Data Service
    # ====================
    def trade_switch_position_mode(self, position_mode: str, margin_account: str="USDT"):
        # single_side, dual_side
        params = {}
        params["margin_account"] = margin_account
        params["position_mode"] = position_mode
        return self._request("/linear-swap-api/v1/swap_cross_switch_position_mode", POST, params, auth=True)

    def trade_get_order_info(self, order_id: str=None, client_order_id:str=None, contract_code: str=None):
        params = {}
        if order_id:
            params["order_id"] = order_id
        elif client_order_id:
            params["client_order_id"] = client_order_id
        if contract_code:
            params["contract_code"] = contract_code
        return self._request("/linear-swap-api/v1/swap_cross_order_info", POST, params, auth=True)

    def trade_post_order(self, contract_code, price, volume, direction, order_price_type, client_order_id="", lever_rate=10):
        params = {}
        params["contract_code"] = contract_code
        params["price"] = price
        params["volume"] = volume
        params["direction"] = direction
        params["order_price_type"] = order_price_type
        if client_order_id:
            params["client_order_id"] = client_order_id
        params["lever_rate"] = lever_rate
        return self._request("/linear-swap-api/v1/swap_cross_order", POST, params, auth=True)

    def trade_post_cancel_order(self, contract_code, order_id="", client_order_id=""):
        params = {}
        params["contract_code"] = contract_code
        if order_id:
            params["order_id"] = order_id
        elif client_order_id:
            params["client_order_id"] = client_order_id
        return self._request("/linear-swap-api/v1/swap_cross_cancel", POST, params, auth=True)

    def trade_get_openorders(self, contract_code: str=""):
        params = {}
        if contract_code:
            params["contract_code"] = contract_code
        return self._request("/linear-swap-api/v1/swap_cross_openorders", POST, params, auth=True)

    def trade_cancel_all(self, contract_code="", direction="", offset=""):
        params = {}
        if contract_code:
            params["contract_code"] = contract_code
        if direction:
            params["direction"] = direction
        if offset:
            params["offset"] = offset
        return self._request("/linear-swap-api/v1/swap_cross_cancelall", POST, params, auth=True)

    def trade_fill_history(self, contract_code, trade_type="0", create_date=90, page_index=1, page_size=50):
        # trade_type 0 for all, 17 for buy 18 for sell
        # create_date 90 means 90days
        # page_size 50, means one page 50 fills
        params = {}
        
        params["contract_code"] = contract_code
        params["trade_type"] = trade_type
        params["create_date"] = create_date
        params["page_index"] = page_index
        params["page_size"] = page_size
        return self._request("/linear-swap-api/v1/swap_cross_matchresults", POST, params, auth=True)
    

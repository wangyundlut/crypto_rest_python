import hmac
import hashlib
import time
from operator import itemgetter
from datetime import datetime, timedelta
import asyncio
from crypto_rest_python.async_rest_client import asyncRestClient, Request, Response
from aiohttp import ClientSession, ClientResponse
from .consts import (
    SPOT_URL
)

HOURS8 = 8

class asyncBinanceSpot(asyncRestClient):

    def __init__(self, api_key, api_secret, loop: asyncio.AbstractEventLoop = None, session: ClientSession = None):
        
        asyncRestClient.__init__(self, loop, session)

        self.API_KEY = api_key
        self.API_SECRET = api_secret

        # 添加base_url
        self.base_url = SPOT_URL

    def get_header(self):
        header = {'Accept': 'application/json',
                    'User-Agent': 'binance/python',
                    'X-MBX-APIKEY': self.API_KEY}
        return header

    def test_cb_sync(self, request: Request):
        
        print(f"{datetime.now()} ===== call back sync =====")
        print(f"request: {request.base_url} {request.path} {request.params}")
        print(f"{request.response.json()}")

    async def test_cb_async(self, request: Request):
        print(f"{datetime.now()} ===== call back async =====")
        print(f"request: {request.base_url} {request.path} {request.params}")
        print(f"{request.response.json()}")

    def _generate_signature(self, data):
        # 生成签名必须有排序
        ordered_data = self._order_params(data)
        query_string = '&'.join(["{}={}".format(d[0], d[1]) for d in ordered_data])
        m = hmac.new(self.API_SECRET.encode('utf-8'), query_string.encode('utf-8'), hashlib.sha256)
        return m.hexdigest()

    def _order_params(self, data):
        """Convert params to list with signature as last element
        signature always at last
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

    def _request_params(self, method: str, path: str, signed=False, params={}, cb=None, callback_method="sync"):
        """request.method == get"""
        
        # process call back
        if cb:
            callback = cb
        else:
            if callback_method == "sync":
                callback = self.test_cb_sync
            else:
                callback = self.test_cb_async
        
        extra_data = {"timeout": 10}

        if signed:
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)
        params = self._order_params(params)
        params_str = '&'.join('%s=%s' % (data[0], data[1]) for data in params)
        
        self.request(
            method="get",
            base_url=self.base_url,
            path=path,
            callback_method=callback_method,
            callback=callback,
            params=params_str,
            headers=self.get_header(),
            extra=extra_data
        )
        
        return 

    def _request_data(self, method: str, path: str, signed=False, data={}, cb=None, callback_method="sync"):
        """request.method == POST, PUT, 和 DELETE"""
        
        # process call back
        if cb:
            callback = cb
        else:
            if callback_method == "sync":
                callback = self.test_cb_sync
            else:
                callback = self.test_cb_async
        
        extra_data = {"timeout": 10}

        if signed:
            data['timestamp'] = int(time.time() * 1000)
            data['signature'] = self._generate_signature(data)
        data = self._order_params(data)
        
        self.request(
            method=method,
            base_url=self.base_url,
            path=path,
            callback_method=callback_method,
            callback=callback,
            data=data,
            headers=self.get_header(),
            extra=extra_data
        )
        return 

    ################### 钱包接口 ###################
    # 系统状态
    def wallet_get_systemStatus(self, cb=None, callback_method="sync"):
        path = "/sapi/v1/system/status"
        return self._request_params("get", path, signed=False, params={}, cb=cb, callback_method=callback_method)
    
    ################### 行情接口 ###################
    # 交易规范信息
    def market_exchangeInfo(self, symbol=None, cb=None, callback_method="sync"):
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._request_params("get", "/api/v3/exchangeInfo", signed=False, params=params, cb=cb, callback_method=callback_method)

    ################### 现货账户和交易接口 ###################
    # 账户信息 weight 10
    def spot_get_account(self, cb=None, callback_method="sync"):
        params = {}
        return self._request_params("get", "/api/v3/account", True, params, cb, callback_method=callback_method)    
    
    ################### 现货账户和交易接口 ###################
    def spot_post_order(self, 
        symbol, 
        side, 
        type_, 
        timeInForce=None, 
        quantity=None, 
        quoteOrderQty=None, 
        price=None, 
        newClientOrderId=None, 
        cb=None, 
        callback_method="sync"):

        data = {}
        data["symbol"] = symbol.upper()
        data["side"] = side.upper()
        data["type"] = type_.upper()
        if timeInForce:
            data["timeInForce"] = timeInForce.upper()
        if quantity:
            data["quantity"] = quantity
        if quoteOrderQty:
            data["quoteOrderQty"] = quoteOrderQty
        if price:
            data["price"] = price
        if newClientOrderId:
            data["newClientOrderId"] = newClientOrderId
    
        return self._request_data("post", "/api/v3/order", True, data, cb, callback_method=callback_method)    

    def spot_cancel_order(self, symbol, orderId=None, origClientOrderId=None, cb=None, callback_method="sync"):
        data = {}
        data["symbol"] = symbol.upper()
        if orderId:
            data["orderId"] = orderId
        elif origClientOrderId:
            data["origClientOrderId"] = origClientOrderId
    
        return self._request_data("delete", "/api/v3/order", True, data, cb, callback_method=callback_method)  

    def spot_get_order(self, symbol, orderId=None, origClientOrderId=None, cb=None, callback_method="sync"):
        data = {}
        data["symbol"] = symbol.upper()
        if orderId:
            data["orderId"] = orderId
        elif origClientOrderId:
            data["origClientOrderId"] = origClientOrderId
    
        return self._request_data("get", "/api/v3/order", True, data, cb, callback_method=callback_method)      
    

    

    
    
    
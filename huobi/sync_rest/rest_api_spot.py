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


class huobiRestSpot(Client):

    def __init__(self, api_key, secret_key, host=SPOT_REST_HOST, exch="pro"):
        super(huobiRestSpot, self).__init__(api_key, secret_key, host, exch)
        # url: /v1/account/accounts return :"id": 10000001,"type": "spot"
        self.account_id_map = {}
        self.account_id_map_reverse = {}

        
        if api_key != "" and secret_key != "":
            result = self.account_get_id()
            for li in result["data"]:
                if li["state"] == "working":
                    self.account_id_map[li["type"]] = li["id"]
                    self.account_id_map_reverse[li["id"]] = li["type"]

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
        return self._request("/v1/account/accounts", GET, params, auth=True)

    # ===================
    # Base Data Service
    # ===================

    def common_symbols(self, ts: int=0):
        params = {}
        if ts:
            params["ts"] = ts
        return self._request("/v2/settings/common/symbols", GET, params)
    
    def common_currencies(self, ts: int=0):
        params = {}
        if ts:
            params["ts"] = ts
        return self._request("/v2/settings/common/currencies", GET, params)

    def common_setting_currencies(self, ts: int=0):
        params = {}
        if ts:
            params["ts"] = ts
        return self._request("/v1/settings/common/currencys", GET, params)

    def common_setting_symbols(self, ts: int=0):
        params = {}
        if ts:
            params["ts"] = ts
        return self._request("/v1/settings/common/symbols", GET, params)

    def common_setting_market_symbols(self, symbols: str="", ts: int=0):
        params = {}
        if symbols:
            params["symbols"] = symbols
        if ts:
            params["ts"] = ts
        return self._request("/v1/settings/common/market-symbols", GET, params)

    def common_timestamp(self):
        return self._request("/v1/common/timestamp", GET)

    # ===================
    # Market Data Service
    # ===================

    def market_kline(self, symbol, period="1min", size=500):
        params = {}
        params["symbol"] = symbol
        params["period"] = period
        if size:
            params["size"] = size
        return self._request("/market/history/kline", GET, params)

    def market_ticker(self, symbol):
        params = {}
        params["symbol"] = symbol
        return self._request("/market/detail/merged", GET, params)
    
    def market_ticker_all(self):
        return self._request("/market/tickers", GET)

    def market_depth(self, symbol, type_: str="step0", depth: int=20):
        params = {}
        params["symbol"] = symbol
        params["type"] = type_
        if depth:
            params["depth"] = depth
        return self._request("/market/depth", GET, params)
    
    def market_trade(self, symbol):
        params = {}
        params["symbol"] = symbol
        return self._request("/market/trade", GET, params)
    
    def market_trade_history(self, symbol, size: int=500):
        params = {}
        params["symbol"] = symbol
        params["size"] = size
        return self._request("/market/history/trade", GET, params)
    
    # ====================
    # Account Data Service
    # ====================


    def account_get_balance(self, account_type: str=""):
        """
        spot, margin, otc, point, super-margin, investment, borrow
        """
        params = {}
        acc_id = self.get_account_id_from_account_type(account_type)
        return self._request(f"/v1/account/accounts/{acc_id}/balance", GET, params, auth=True)

    def account_get_valuation(self, account_type: str="", valuationCurrency: str="BTC"):
        """
        账户类型数据字典
        code	说明
        1	币币账户
        2	逐仓杠杆账户
        3	全仓杠杆账户
        4	交割合约账户
        5	法币账户
        6	矿池账户
        7	永续合约账户
        8	C2C出借账户
        9	C2C借款账户
        10	存币宝账户
        11	正向合约账户
        12	期权合约账户
        13	场外期权账户
        14	抵押借贷账户
        15	网格交易账户
        16	挖矿宝账户
        """
        params = {}
        if account_type:
            params["accountType"] = account_type
        params["valuationCurrency"] = valuationCurrency
        return self._request(f"/v2/account/valuation", GET, params, auth=True)
    
    def account_get_asset_valuation(self, accountType, valuationCurrency: str="", subUid: str=""):
        params = {}
        """
        accountType: spot, margin, otc, super-margin
        valuationCurrency: BTC CNY USD JPY...
        """
        params["accountType"] = accountType
        if valuationCurrency:
            params["valuationCurrency"] = valuationCurrency
        if subUid:
            params["subUid"]

        return self._request(f"/v2/account/asset-valuation", GET, params, auth=True)

    def account_post_transfer(self, ):
        params = {}
    
        return self._request(f"/v1/account/transfer", POST, params, auth=True)

    def account_post_transfer_futures(self, currency, amount, type_):
        """
        futures-to-pro
        pro-to-futures
        """
        params = {}
        params["currency"] = str(currency)
        params["amount"] = str(amount)
        params["type"] = str(type_)
        return self._request(f"/v1/futures/transfer", POST, params, auth=True)

    def account_post_transfer_usdt_margin(self, from_, to, currency, amount, margin_account):
        """
        futures-to-pro
        pro-to-futures
        """
        params = {}
        params["from"] = str(from_)
        params["to"] = str(to)
        params["currency"] = str(currency)
        params["amount"] = str(amount)
        params["margin-account"] = str(margin_account)

        return self._request(f"/v2/account/transfer", POST, params, auth=True)

    def account_get_uid(self):
        params = {}
        return self._request(f"/v2/user/uid", GET, params, auth=True)


    # =============
    # Trade Service
    # =============
    def trade_post_order(self, symbol, type_, amount, price=None, 
        client_order_id: str="", 
        self_match_prevent: int=0, 
        stop_price: str="", 
        operator: str="",
        account_type: str="spot",
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

        return self._request(f"/v1/order/orders/place", POST, params, auth=True)

    def trade_post_batch_order(self, post_order_list: List):
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
        
        return self._request(f"/v1/order/batch-orders", POST, params, auth=True)
        
    def trade_post_cancel_order(self, order_id: str, symbol: str=""):
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._request(f"/v1/order/orders/{order_id}/submitcancel", POST, params, auth=True)

    def trade_post_cancel_order_cliordId(self, client_order_id: str=""):
        params = {}
        params["client-order-id"] = client_order_id
        return self._request(f"/v1/order/orders/submitCancelClientOrder", POST, params, auth=True)

    def trade_post_cancel_order_after(self, timeout: int=10):
        """
        set order cancel after  like 10 seconds
        """
        params = {}
        params["timeout"] = str(timeout)
        return self._request(f"/v2/algo-orders/cancel-all-after", POST, params, auth=True)

    def trade_get_open_order(self, symbol: str="", side: str="", types: str="", from_: str="", direct: str="", size: str="", account_type="spot"):
        
        if account_type == "spot":
            acc_id = self.account_id_map["spot"]
            source = "spot-api"
        elif account_type == "margin":
            acc_id = self.account_id_map["margin"]
            source = "margin-api"
        elif account_type == "super-margin":
            acc_id = self.account_id_map["super-margin"]
            source = "super-margin-api"

        params = {}
        params["account-id"] = acc_id

        if symbol:
            params["symbol"] = symbol
        if side:
            params["side"] = side
        if types:
            params["types"] = types
        if from_:
            params["from"] = from_
        if direct:
            params["direct"] = direct
        if size:
            params["size"] = size
        return self._request(f"/v1/order/openOrders", GET, params, auth=True)
   
    def trade_post_batch_cancel_open_orders(self, symbol: str="", types: str="", side: str="", size: str="", account_type="spot"):
        
        if account_type == "spot":
            acc_id = self.account_id_map["spot"]
            source = "spot-api"
        elif account_type == "margin":
            acc_id = self.account_id_map["margin"]
            source = "margin-api"
        elif account_type == "super-margin":
            acc_id = self.account_id_map["super-margin"]
            source = "super-margin-api"

        params = {}
        params["account-id"] = acc_id
        if symbol:
            params["symbol"] = str(symbol)
        if types:
            params["types"] = str(types)
        if side:
            params["side"] = str(side)
        if size:
            params["size"] = str(size)
        return self._request(f"/v1/order/orders/batchCancelOpenOrders", POST, params, auth=True)

    def trade_post_batch_cancel(self, order_ids: List=[], client_order_ids: List=[]):
        params = {}
        if order_ids:
            params["order-ids"] = order_ids
        elif client_order_ids:
            params["client-order-ids"] = client_order_ids
        
        return self._request(f"/v1/order/orders/batchcancel", POST, params, auth=True)

    def trade_get_order_info(self, order_id):
        return self._request(f"/v1/order/orders/{order_id}", GET, {}, auth=True)

    def trade_get_order_info_in_client_order_id(self, client_order_id: str=""):
        params = {}
        params["clientOrderId"] = client_order_id
        return self._request(f"/v1/order/orders/getClientOrder", GET, params, auth=True)
    
    def trade_get_order_matchresults(self, order_id: str=""):
        params = {}
        return self._request(f"/v1/order/orders/{order_id}/matchresults", GET, params, auth=True)

    def trade_get_history_orders(self, symbol, states, types: str="", start_time: str="", end_time: str="", from_: str="", direct: str="", size: str="100"):

        params = {}
        params["symbol"] = symbol
        params["states"] = states
        if types:
            params["types"] = types
        if start_time:
            params["start-time"] = int(start_time)
        if end_time:
            params["end-time"] = int(end_time)
        if from_:
            params["from"] = from_
        if direct:
            params["direct"] = direct
        
        params["size"] = size
        return self._request(f"/v1/order/orders", GET, params, auth=True)

    def trade_get_2days_order(self, symbol, start_time: str="", end_time: str="", direct: str="", size: str="100"):
        # 经和运维确认，此接口1s/1次 非常严格 API文档上的并不准确
        params = {}
        params["symbol"] = symbol

        if start_time:
            params["start-time"] = int(start_time)
        if end_time:
            params["end-time"] = int(end_time)
        if direct:
            params["direct"] = direct
        
        params["size"] = size
        return self._request(f"/v1/order/history", GET, params, auth=True)

    def trade_get_order_match(self, symbol, types: str="", start_time: int=0, end_time: int=0, from_: str="", direct: str="", size: str="500"):
        params = {}
        params["symbol"] = symbol

        if types:
            params["types"] = types
        if start_time:
            params["start-time"] = int(start_time)
        if end_time:
            params["end-time"] = int(end_time)
        if from_:
            params["from"] = from_
        if direct:
            params["direct"] = direct

        params["size"] = size
        return self._request(f"/v1/order/matchresults", GET, params, auth=True)

    def trade_get_fee(self, symbols=[]):
        params = {}
        params["symbols"] = ",".join(symbols)

        return self._request(f"/v2/reference/transact-fee-rate", GET, params, auth=True)


    ##############################################################
    def spot_account_history(
            self, account_id: int, currency: str = None, transact_types: str = None,
            start_time: int = None, end_time: int = None, from_id: int = None,
            sort: str = 'asc', size: int = 500
    ):
        params = {
            'account-id': account_id,
            'sort': sort,
            'size': size
        }

        if currency:
            params['currency'] = currency
        if transact_types:
            params['transact-types'] = transact_types
        if start_time:
            params['start-time'] = int(start_time)
        if end_time:
            params['end-time'] = int(end_time)
        if from_id:
            params['from-id'] = from_id

        url = self._get_url(endpoint='/v1/account/history')
        return self.api_key_get_original(url=url, params=params)

    def subscription(self, etpName: str, value: float, currency: str):
        """
        ETP Subscription
        :param etpName: etpName	string	TRUE	杠杆ETP名称
        :param value:value	float	TRUE	申购金额（基于计价币种）
        :param currency:currency	string	TRUE	申购金额单位（计价币种）
        :return:
        名称	类型	是否必需	描述
        code	integer	TRUE	状态码
        message	string	FALSE	错误描述（如有）
        data	object	TRUE
        { transactId	long	TRUE	交易ID
        transactTime }	long	TRUE	交易时间（unix time in millisecond）
        """

        path = "/v2/etp/creation"
        params = {
            "etpName": etpName,
            "value": value,
            "currency": currency,
        }
        url = self._get_url(path)
        return self.api_key_post(url, params)

    def redemption(self, etpName: str, amount: float, currency: str):
        """
        :param etpName: 杠杆ETP名称
        :param amount: 赎回数量
        :param currency: 赎回币种（计价币种）, e.g. 'btc'
        :return:
        """
        path = "/v2/etp/redemption"
        params = {
            "etpName": etpName,
            "amount": amount,
            "currency": currency,
        }

        url = self._get_url(path)
        return self.api_key_post(url, params)

    def etp_transaction(self, transaction_id):
        path = "/v2/etp/transaction"
        params = {
            "transactId": transaction_id,
        }

        url = self._get_url(path)
        return self.api_key_get(url, params)

    def blockchain_withdraw(self, address: str, amount: float, currency: str, fee: float, chain: str = None) -> dict:
        """
        Transact currencies on blockchain.
        :param address: Target address to receive currency.
        :param amount: Amount of currencies to be transferred.
        :param currency: Target currency to transfer.
        :param fee: Fee to pay for the transaction.
        :param chain: Target chain to transfer, only need to be specified when transacting USDT.
        :return: ID of the transaction if the action is successful.
        """
        params = {
            'address': address,
            'amount': str(amount),
            'currency': currency,
            'fee': str(fee),
        }

        if currency in ('usdt', 'USDT'):
            if chain:
                params['chain'] = chain
            else:
                raise Exception('Please clarify target chain for withdrawing.')

        url = self._get_url(endpoint='/v1/dw/withdraw/api/create')
        return self.api_key_post(url=url, params=params)

    def blockchain_deposit_withdraw_history(
            self, _type: str, symbol: str = None,
            _from: str = None, size: int = 500, direction: str = 'prev'
    ) -> dict:
        """
        Query the deposit and withdraw history from blockchain.
        :param _type: deposit/withdraw.
        :param symbol: Symbol of the currency.
        :param _from: Start querying ID.
        :param size: Size of the page.
        :param direction: Direction of the paging.
        """
        params = {
            'type': _type,
        }

        if symbol:
            params['currency'] = symbol
        if _from:
            params['from'] = _from
        if size:
            params['size'] = size
        if direction:
            params['direct'] = direction

        url = self._get_url(endpoint='/v1/query/deposit-withdraw')

        return self.api_key_get(url=url, params=params)

    def blockchain_deposit_address(self, symbol: str) -> dict:
        """
        Query the legit deposit addresses.
        :param symbol: Currency to be deposited.
        :return:
        """
        params = {
            'currency': symbol
        }

        url = self._get_url(endpoint='/v2/account/deposit/address')

        return self.api_key_get(url=url, params=params)

    def blockchain_withdraw_address(
            self, symbol: str, chain: str = None,
            note: str = None, limit: int = 500, from_id: int = None
    ) -> dict:
        """
        Query the legit (whitelisted) withdraw addresses of parent account.
        :param symbol: Currency to be withdrawn.
        :param chain: Target chain. For example, USDT is on OMNI, ERC20, and TRC20.
        :param note: Label of the address.
        :param limit: Limit of each page, 500 by default.
        :param from_id: For pagination.
        :return:
        """
        params = {
            'limit': limit
        }
        if symbol:
            params['currency'] = symbol
        if chain:
            params['chain'] = chain
        if note:
            params['note'] = note
        if from_id:
            params['fromId'] = from_id

        url = self._get_url(endpoint='/v2/account/withdraw/address')

        return self.api_key_get(url=url, params=params)

    def account_withdraw_quota(self, currency):
        url = self._get_url(endpoint='/v2/account/withdraw/quota')

        return self.api_key_get(url=url, params={'currency': currency})

    def reference_currencies(self, currency: str = None, authorizedUser: bool = None) -> dict:
        params = {}
        if currency:
            params['currency'] = currency
        if authorizedUser is not None:
            params['authorizedUser'] = authorizedUser
        url = self._get_url(endpoint='/v2/reference/currencies')
        return self.http_get_request(url=url, params=params)

    # add by xiandong
    def contract_account_info(self, symbol=None):
        """获取用户账户信息
        """
        params = {}
        if symbol:
            params.update({"symbol": symbol})
        url = self._get_url("/v1/contract_account_info")
        return self.api_key_post(url, params)

    def contract_position_info(self, symbol=None):
        """获取用户账户信息
        """
        params = {}
        if symbol:
            params.update({"symbol": symbol})
        url = self._get_url("/v1/contract_position_info")
        return self.api_key_post(url, params)

   





    # ===
    # ETF
    # ===

    def swap_config(self, etf_name):
        params = {"etf_name": etf_name}
        url = self._get_url("/etf/swap/config")
        return self.http_get_request(url, params)

    def swap_in(self, etf_name, amount):
        params = {
            "etf_name": etf_name,
            "amount": amount
        }
        url = self._get_url("/etf/swap/in")
        return self.api_key_post(url, params)

    def swap_out(self, etf_name, amount):
        params = {
            "etf_name": etf_name,
            "amount": amount
        }
        url = self._get_url("/etf/swap/out")
        return self.api_key_post(url, params)

    def swap_list(self, etf_name, offset, limit=100):
        params = {
            "etf_name": etf_name,
            "offset": offset,
            "limit": limit
        }
        url = self._get_url("/etf/list")
        return self.api_key_get(url, params)

    # ============
    # Cross Margin 全仓杠杆
    # ============

    def cross_margin_transfer_in(self, currency, amount):
        """
        currency: 币种
        amount: 划转数量

        return:
        data: Transfer id
        """
        params = {
            "currency": currency,
            "amount": amount
        }
        url = self._get_url("/v1/cross-margin/transfer-in")
        #        print(self.api_key_post(url, params))
        return self.api_key_post(url, params)

    def cross_margin_transfer_out(self, currency, amount):
        """
        currency: 币种
        amount: 划转数量

        return
        data: Transfer id
        """
        params = {
            "currency": currency,
            "amount": amount
        }
        url = self._get_url("/v1/cross-margin/transfer-out")
        #        print(self.api_key_post(url, params))
        return self.api_key_post(url, params)

    def cross_margin_interest_rate(self):
        """
        return:
        currency: 币种
        interest_rate: 借贷利率
        """
        url = self._get_url("/v1/cross-margin/loan-info")
        #        print(self.api_key_get(url))
        return self.api_key_get(url)

    def cross_margin_order(self, currency, amount):
        params = {
            "currency": currency,
            "amount": amount
        }
        url = self._get_url("/v1/cross-margin/orders")
        #        print(self.api_key_post(url, params))
        return self.api_key_post(url, params)

    def cross_margin_repay(self, order_id, amount):
        params = {
            "amount": amount
        }
        url = self._get_url("/v1/cross-margin/orders/{}/repay".format(order_id))
        #        print(self.api_key_post(url, params))
        return self.api_key_post(url, params)

    def cross_margin_loan_orders(self, start_date=None, end_date=None, state=None, id_from=None, direct=None, size=100):
        """
        start_date: 查询开始日期，日期格式yyyy-mm-dd
        end_date: 查询结束日期，日期格式yyyy-mm-dd
        state: created 未放款，accrual 已放款，cleared 已还清，invalid 异常
        direct: prev 向前，时间（或ID）正序；next 向后，时间（或ID）倒序
        size: [10, 100]
        """
        params = {
            "size": size
        }
        if start_date:
            params.update({"start-date": start_date})
        if end_date:
            params.update({"end-date": end_date})
        if state:
            params.update({"state": state})
        if id_from:
            params.update({"from": id_from})
        if direct:
            params.update({"direct": direct})
        url = self._get_url("/v1/cross-margin/loan-orders")
        #        print(self.api_key_get(url, params))
        return self.api_key_get(url, params)

    def cross_margin_loan_orders1(self, currency=None, start_date=None, end_date=None, state=None, id_from=None,
                                  direct=None, size=100):
        """
        currency: 币种，比如btc
        start_date: 查询开始日期，日期格式yyyy-mm-dd
        end_date: 查询结束日期，日期格式yyyy-mm-dd
        state: created 未放款，accrual 已放款，cleared 已还清，invalid 异常
        direct: prev 向前，时间（或ID）正序；next 向后，时间（或ID）倒序
        size: [10, 100]
        """
        params = {
            "size": size
        }
        if currency:
            params.update({"currency": currency})
        if start_date:
            params.update({"start-date": start_date})
        if end_date:
            params.update({"end-date": end_date})
        if state:
            params.update({"state": state})
        if id_from:
            params.update({"from": id_from})
        if direct:
            params.update({"direct": direct})
        url = self._get_url("/v1/cross-margin/loan-orders")
        #        print(self.api_key_get(url, params))
        return self.api_key_get(url, params)

    def cross_margin_balance(self):
        url = self._get_url("/v1/cross-margin/accounts/balance")
        #        print(self.api_key_get(url).get('list',[]))
        # return self.api_key_get(url).get('list', [])
        res = self.api_key_get(url)
        if isinstance(res, list):
            return res
        elif isinstance(res, dict):
            return res.get('list', [])
        else:
            return {}

    def cross_margin_balance1(self):
        url = self._get_url("/v1/cross-margin/accounts/balance")
        #        print(self.api_key_get(url).get('list',[]))
        return self.api_key_get(url)

    # ======
    # Margin 逐仓杠杆
    # ======

    def margin_transfer_in(self, symbol, currency, amount):
        params = {
            "symbol": symbol,
            "currency": currency,
            "amount": amount
        }
        url = self._get_url("/v1/dw/transfer-in/margin")
        return self.api_key_post(url, params)

    def margin_transfer_out(self, symbol, currency, amount):
        params = {
            "symbol": symbol,
            "currency": currency,
            "amount": amount
        }
        url = self._get_url("/v1/dw/transfer-out/margin")
        return self.api_key_post(url, params)

    def margin_interest_rate(self, symbols=None):
        """
        param:
        symbols: 交易代码 (可多选，以逗号分隔)

        return:
        currency: 币种
        interest_rate: 借贷利率
        """
        params = {}
        if symbols:
            params.update(
                {
                    "symbols": symbols
                }
            )
            url = self._get_url("/v1/margin/loan-info")
            return self.api_key_get(url, params)
        else:
            url = self._get_url("/v1/margin/loan-info")
            return self.api_key_get(url)

    def margin_orders(self, symbol, currency, amount):
        params = {
            "symbol": symbol,
            "currency": currency,
            "amount": amount
        }
        url = self._get_url("/v1/margin/orders")
        return self.api_key_post(url, params)

    def margin_repay(self, order_id, amount):
        params = {
            "amount": amount
        }
        url = self._get_url("/v1/margin/orders/{}/repay".format(order_id))
        return self.api_key_post(url, params)

    def margin_loan_orders(
            self, symbol, start_date=None, end_date=None,
            states=None, id_from=None, direct=None, size=100):
        """
        states: created 未放款，accrual 已放款，cleared 已还清，invalid 异常
        """
        params = {
            "symbol": symbol,
            "size": size
        }
        if start_date:
            params.update({"start-date": start_date})
        if end_date:
            params.update({"end-date": end_date})
        if states:
            params.update({"states": states})
        if id_from:
            params.update({"from": id_from})
        if direct:
            params.update({"direct": direct})
        url = self._get_url("/v1/margin/loan-orders")
        return self.api_key_get(url, params)

    def margin_balance(self, symbol=None):
        params = {}
        if symbol:
            params.update(
                {
                    "symbol": symbol
                }
            )
        url = self._get_url("/v1/margin/accounts/balance")
        return self.api_key_get(url, params)

    # =============
    # Child Account
    # =============

    def get_accounts(self):
        """
        :return:
        """
        url = self._get_url("/v1/account/accounts")
        params = {}
        return self.api_key_get(url, params)

    def account_transfer(self, from_user_id, from_account_type, from_account_id, to_user_uid, to_account_type,
                         to_account_id, currency, amount):
        params = {
            "from-user": from_user_id,
            "from-account-type": from_account_type,
            "from-account": from_account_id,
            "to-user": to_user_uid,
            "to-account-type": to_account_type,
            "to-account": to_account_id,
            "currency": currency,
            "amount": amount,
        }
        url = self._get_url("/v1/account/transfer")
        return self.api_key_post(url, params)

    def subuser_transfer(self, sub_uid, currency, amount, transfer_type):
        params = {
            "sub-uid": sub_uid,
            "currency": currency,
            "amount": amount,
            "type": transfer_type
        }
        url = self._get_url("/v1/subuser/transfer")
        return self.api_key_post(url, params)

    def set_subuser_transferability(self, sub_uid, account_type, transferrable):
        params = {
            "subUids": sub_uid,
            "accountType": account_type,
            "transferrable": transferrable,
        }
        url = self._get_url("/v2/sub-user/transferability")
        return self.api_key_post(url, params)

    def aggregate_balance(self):
        url = self._get_url("/v1/subuser/aggregate-balance")
        return self.api_key_get(url)

    def sub_balance(self, sub_uid):
        url = self._get_url("/v1/account/accounts/{}".format(sub_uid))
        return self.api_key_get(url)

    # ===========
    # Stable Coin
    # ===========

    def get_stablecoin_quote(self, currency, amount, type):
        # url = self._get_url("/v1/stable-coin/quote")
        url = 'https://api.huobi.pro/v1/stable-coin/quote'
        params = {'currency': currency, 'amount': amount, 'type': type}
        return self.api_key_get(url, params)

    def transfer_stablecoin(self, quote_id):
        # url = self._get_url("/v1/stable-coin/exchange")
        url = 'https://api.huobi.pro/v1/stable-coin/exchange'
        params = {'quote-id': quote_id}
        return self.api_key_post(url, params)






    
    
            

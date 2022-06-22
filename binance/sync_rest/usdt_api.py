from pandas.core.base import NoNewAttributesMixin
from .client import Client
from .consts import (
    USDT_URL
)

# 对应binance u本位合约交易
class USDTAPI(Client):

    def __init__(self, api_key=None, api_secret=None, requests_params=None):
        Client.__init__(self, api_key, api_secret, requests_params)
        self.API_KEY = api_key
        self.API_SECRET = api_secret
        self.session = self._init_session()
        self._requests_params = requests_params
        self.response = None
        # 添加base_url
        self.base_url = USDT_URL
    
    ################### 行情接口 ###################
    # 以market + (method) + 接口为名字
    # 测试服务器联通性
    def market_get_ping(self):
        return self._request_api("get", "/fapi/v1/ping")
    
    def market_get_exchangeInfo(self):
        return self._request_api("get", "/fapi/v1/exchangeInfo")
    
    def market_kline(self, symbol, interval, startTime=None, endTime=None):
        params = {}
        params["symbol"] = symbol
        params['interval'] = interval
        if startTime:
            params['startTime'] = startTime
        if endTime:
            params['endTime'] = endTime

        return self._request_api("get", "/fapi/v1/klines", data=params)
    
    def market_fundingRate(self, symbol=None, startTime=None, endTime=None, limit=None):
        params = {}
        if symbol:
            params['symbol'] = symbol
        if startTime:
            params['startTime'] = startTime
        if endTime:
            params['endTime'] = endTime
        if limit:
            params['limit'] = limit
        return self._request_api("get", "/fapi/v1/fundingRate", data=params)
    
    def market_ticker(self, symbol=None):
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._request_api("get", "/fapi/v1/ticker/price", data=params)
    
    # 最新价格
    def market_bookTicker(self, symbol=None):
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._request_api("get", "/fapi/v1/ticker/bookTicker", data=params)

    ################### 账户和交易接口 ###################
    # 以trade+ (method) + 接口为名字
    # 划转
    # 获取划转历史 
    # 获取所有订单 权重5
    def trade_get_allorders(self, symbol='', orderId='', startTime='', endTime='', limit=1000):
        # 这个接口不接受startTime为0的查询
        # 查询结果包括startTime 和endTime的点
        # 因此 只能先定位
        params = {}
        if symbol:
            params['symbol'] = symbol
        if orderId:
            params['orderId'] = orderId
        if startTime:
            params['startTime'] = startTime
        if endTime:
            params['endTime'] = endTime
        params['limit'] = limit
        return self._request_api("get", "/fapi/v1/allOrders", True, data=params)

    # 更改持仓模式
    # 查询持仓模式
    def trade_get_positionSide(self):
        params = {}
        return self._request_api("get", "/fapi/v1/positionSide/dual", True, data=params)

    def trade_post_order(self, symbol, side, type_, timeInForce="GTC", quantity=0, price=0, newClientOrderId=None, ):
        # timeInForce : GTC IOC FOK
        params = {}
        params['symbol'] = symbol
        params['side'] = side
        params['type'] = type_
        if type_ == 'LIMIT':
            params['timeInForce'] = timeInForce
            params['quantity'] = quantity
            params['price'] = price
        if newClientOrderId:
            params["newClientOrderId"] = newClientOrderId
        return self._request_api("post", "/fapi/v1/order", True, data=params)

    def trade_post_order_test(self, symbol, side, type_, timeInForce="GTC", quantity=0, price=0):
        # timeInForce : GTC IOC FOK
        params = {}
        params['symbol'] = symbol
        params['side'] = side
        params['type'] = type_
        if type_ == 'LIMIT':
            params['timeInForce'] = timeInForce
            params['quantity'] = quantity
            params['price'] = price
        elif type_ == "MARKET":
            params['quantity'] = quantity
        return self._request_api("post", "/fapi/v1/order/test", True, data=params)
    
    def trade_get_order_info(self, symbol, orderId=None, origClientOrderId=None,):
        params = {}
        params['symbol'] = symbol
        if orderId:
            params["orderId"] = orderId
        elif origClientOrderId:
            params["origClientOrderId"] = origClientOrderId
        return self._request_api("get", "/fapi/v1/order", True, data=params)

    def trade_cancel_order(self, symbol, orderId=None, origClientOrderId=None,):
        params = {}
        params['symbol'] = symbol
        if orderId:
            params["orderId"] = orderId
        elif origClientOrderId:
            params["origClientOrderId"] = origClientOrderId
        return self._request_api("delete", "/fapi/v1/order", True, data=params)
    
    def trade_cancel_order_all(self, symbol):
        params = {}
        params['symbol'] = symbol
        return self._request_api("delete", "/fapi/v1/allOpenOrders", True, data=params)
    
    def trade_get_open_order(self, symbol, orderId):
        params = {}
        params['symbol'] = symbol
        params['orderId'] = orderId
        return self._request_api("get", "/fapi/v1/openOrder", True, data=params)

    def trade_get_open_order_all(self, symbol):
        params = {}
        params['symbol'] = symbol
        return self._request_api("get", "/fapi/v1/openOrders", True, data=params)
    # ...
    # 账户余额V2 weight 5
    def trade_get_balance(self):
        params = {}
        return self._request_api("get", "/fapi/v2/balance", True, data=params)

    # 账户信息V2  (持仓的情况在这里！！！) weight 5
    def trade_get_account(self):
        params = {}
        return self._request_api("get", "/fapi/v2/account", True, data=params)

    def trade_get_userTrades(self, symbol='', fromId='', startTime='', endTime='', limit=1000):
        params = {}
        if symbol:
            params['symbol'] = symbol
        if fromId:
            params['fromId'] = fromId
        if startTime:
            params['startTime'] = startTime
        if endTime:
            params['endTime'] = endTime
        params['limit'] = limit
        return self._request_api("get", "/fapi/v1/userTrades", True, data=params)
        
    # 用户持仓风险  (持仓的情况在这里！！！) weight 5 
    def trade_get_positionRisk(self, symbol=None):
        params = {}
        if symbol:
            params["symbol"] =symbol
        return self._request_api("get", "/fapi/v2/positionRisk", True, data=params)
    
    # 获取账户损益资金流水 weight 30
    def trade_get_income(self, symbol=None, incomeType=None, startTime=None, endTime=None, limit=1000, ):
        params = {}
        if symbol:
            params["symbol"] = symbol
        if incomeType:
            params["incomeType"] = incomeType
        if startTime:
            params["startTime"] = startTime
        if endTime:
            params["endTime"] = endTime
        if limit:
            params["limit"] = limit
        return self._request_api("get", "/fapi/v1/income", True, data=params)
        
    def websocket_get_listenKey(self):
        return self._request_api("post", "/fapi/v1/listenKey", False, data={})
    
    def websocket_extend_listenKey(self):
        return self._request_api("put", "/fapi/v1/listenKey", False, data={})
    
    def websocket_delete_listenKey(self):
        return self._request_api("delete", "/fapi/v1/listenKey", False, data={})
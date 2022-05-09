from .client import Client
from .consts import (
    SPOT_URL
)

class SpotAPI(Client):

    def __init__(self, api_key=None, api_secret=None, requests_params=None):
        Client.__init__(self, api_key, api_secret, requests_params)
        self.API_KEY = api_key
        self.API_SECRET = api_secret
        self.session = self._init_session()
        self._requests_params = requests_params
        self.response = None
        # 添加base_url
        self.base_url = SPOT_URL
    
    ################### 钱包接口 ###################
    # 系统状态
    def wallet_get_systemStatus(self):
        return self._request_api("get", "/wapi/v3/systemStatus.html")
    # 获取所有币信息
    def wallet_get_config(self):
        return self._request_api("get", "/sapi/v1/capital/config/getall")
    # 查询每日资产快照
    def wallet_get_accountSnapshot(self, accountType="SPOT"):
        params = {
            "type": accountType,
        }
        return self._request_api("get", "/sapi/v1/accountSnapshot", True, data=params)
    # 关闭站内划转
    # 开启站内划转
    # 提币SAPI
    # 提币
    # 获取充值历史
    # 获取提币历史
    # 获取充值地址
    # 账户状态
    # 账户API交易状态
    # 小额资产转换BNB历史
    # 小额资产转换
    # 资产利息记录
    # 上架资产详情
    # 交易手续费率查询
    # 用户万向划转
    # 查询用户万向划转历史
    ################### 子母账户接口 ###################

    ################### 行情接口 ###################
    def market_exchangeInfo(self):
        return self._request_api("get", "/api/v3/exchangeInfo")

    def market_kline(self, symbol, interval, startTime=None, endTime=None):
        params = {}
        params["symbol"] = symbol
        params['interval'] = interval
        if startTime:
            params['startTime'] = startTime
        if endTime:
            params['endTime'] = endTime

        return self._request_api("get", "/api/v3/klines", data=params)

    # 最新价格
    def market_ticker(self, symbol=None):
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._request_api("get", "/api/v3/ticker/price")
    
    # 最新价格
    def market_bookTicker(self, symbol=None):
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._request_api("get", "/api/v3/ticker/bookTicker", data=params)

    ################### 现货账户和交易接口 ###################
    # 账户信息 weight 10
    def spot_get_account(self):
        params = {}
        return self._request_api("get", "/api/v3/account", True, data=params)

    def spot_post_order(self, symbol, side, type_, timeInForce=None, quantity=None, quoteOrderQty=None, price=None, newClientOrderId=None):
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
    
        return self._request_api("post", "/api/v3/order", True, **{"data": data})    

    def spot_cancel_order(self, symbol, orderId=None, origClientOrderId=None):
        data = {}
        data["symbol"] = symbol.upper()
        if orderId:
            data["orderId"] = orderId
        elif origClientOrderId:
            data["origClientOrderId"] = origClientOrderId
    
        return self._request_api("delete", "/api/v3/order", True, **{"data": data})  

    def spot_get_allorders(self, symbol='', orderId='', startTime='', endTime='', limit=1000):
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
        return self._request_api("get", "/api/v3/allOrders", True, data=params)
    
    def spot_get_userTrades(self, symbol='', orderId='', fromId='', startTime='', endTime='', limit=1000):
        params = {}
        if symbol:
            params['symbol'] = symbol
        if orderId:
            params['orderId'] = orderId
        if fromId:
            params['fromID'] = fromId
        if startTime:
            params['startTime'] = startTime
        if endTime:
            params['endTime'] = endTime
        params['limit'] = limit
        return self._request_api("get", "/api/v3/myTrades", True, data=params)

    ################### 杠杆账户和交易接口 ###################
    # 全仓杠杆账户划转
    def lever_post_transfer(self, asset, amount, type_):
        # type_ 
        # 1:spot->margin 
        # 2:margin->spot
        params = {}
        params['asset'] = asset
        params['amount'] = amount
        params['type'] = type_
        
        return self._request_api("post", "/sapi/v1/margin/transfer", True, data=params)
    
    # 查询全仓杠杆交易对 
    def lever_get_all_pairs(self):
        params = {}
        
        return self._request_api("get", "/sapi/v1/margin/allPairs", True, data=params)
    
    # 杠杆账户下单
    def lever_post_order(self, symbol, side, type_, isIsolated=False, timeInForce=None, quantity=None, quoteOrderQty=None, price=None, newClientOrderId=None):
        data = {}
        data["symbol"] = symbol.upper()
        data["side"] = side.upper()
        data["type"] = type_.upper()
        if not isIsolated:
            data["isIsolated"] = "FALSE"
        else:
            data["isIsolated"] = "TRUE"

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
        return self._request_api("post", "/sapi/v1/margin/order", True, **{"data": data})
    
    # 杠杆账户撤销订单

    def lever_cancel_order(self, symbol, orderId=None, origClientOrderId=None, isIsolated=False):
        data = {}
        data["symbol"] = symbol.upper()

        if not isIsolated:
            data["isIsolated"] = "FALSE"
        else:
            data["isIsolated"] = "TRUE"

        if orderId:
            data["orderId"] = orderId
        elif origClientOrderId:
            data["origClientOrderId"] = origClientOrderId
    
        return self._request_api("delete", "/sapi/v1/margin/order", True, **{"data": data}) 

    def lever_cancel_symbol_order(self, symbol, isIsolated=False):
        data = {}
        data["symbol"] = symbol.upper()

        if not isIsolated:
            data["isIsolated"] = "FALSE"
        else:
            data["isIsolated"] = "TRUE"
    
        return self._request_api("delete", "/sapi/v1/margin/openOrders", True, **{"data": data})

    # 查询全仓杠杆账户详情 weight 1
    def lever_get_account(self):
        params = {}
        return self._request_api("get", "/sapi/v1/margin/account", True, data=params)
    
    # 查询杠杆逐仓账户信息 weight 1
    def lever_get_isolated_account(self, symbols=None):
        params = {}
        if symbols:
            params["symbols"] = symbols
        return self._request_api("get", "/sapi/v1/margin/isolated/account", True, data=params)

    # 获取利息历史
    def lever_get_interest_history(self, 
        asset=None,
        isolatedSymbol=None,
        startTime=None,
        endTime=None,
        current=None,
        size=None,
        archived=False,
        ):
        # 只是用startTime来更新，不用别的
        params = {}
        if asset:
            params["asset"] = asset
        if isolatedSymbol:
            params["isolatedSymbol"] = isolatedSymbol
        if startTime:
            params["startTime"] = startTime
        if endTime:
            params["endTime"] = endTime
        if current:
            params["current"] = current
        if size:
            params["size"] = size
        if archived:
            params["archived"] = archived
        return self._request_api("get", "/sapi/v1/margin/interestHistory", True, data=params)

    def lever_get_allorders(self, symbol='', isIsolated='', orderId='', startTime='', endTime='', limit=500):
        # 60次 每分钟 每个IP
        params = {}
        if symbol:
            params['symbol'] = symbol
        if isIsolated:
            params['isIsolated'] = isIsolated
        if orderId:
            params['orderId'] = orderId
        if startTime:
            params['startTime'] = startTime
        if endTime:
            params['endTime'] = endTime
        params['limit'] = limit
        return self._request_api("get", "/sapi/v1/margin/allOrders", True, data=params)
    
    def lever_get_userTrades(self, symbol='', isIsolated='',orderId='', fromId='', startTime='', endTime='', limit=1000):
        params = {}
        if symbol:
            params['symbol'] = symbol
        if isIsolated:
            params['isIsolated'] = isIsolated
        if orderId:
            params['orderId'] = orderId
        if fromId:
            params['fromID'] = fromId
        if startTime:
            params['startTime'] = startTime
        if endTime:
            params['endTime'] = endTime
        params['limit'] = limit
        return self._request_api("get", "/sapi/v1/margin/myTrades", True, data=params)

    def lever_isolated_post_transfer(self, asset, amount, transFrom, transTo):
        # type_ 
        # From to: SPOT  ISOLATED_MARGIN
        params = {}
        params['asset'] = asset
        params['amount'] = amount
        params['transFrom'] = transFrom
        params['transTo'] = transTo
        
        return self._request_api("post", "/sapi/v1/margin/isolated/transfer", True, data=params)
    
    # 获取所有逐仓杠杆交易对(USER_DATA)
    def lever_isolated_get_all_pairs(self):
        params = {}
        return self._request_api("get", "/sapi/v1/margin/isolated/allPairs", True, data=params)

    def lever_get_order_limit(self, isIsolated=False, symbol=None):
        params = {}
        if isIsolated:
            params["isIsolated"] = isIsolated
        if symbol:
            params["symbol"] = symbol
        return self._request_api("get", "/sapi/v1/margin/rateLimit/order", True, data=params)


    ################### 币安宝接口 ###################

    ################### 矿池接口 ###################

    ################### 合约接口 ###################
    def contract_futures_transfer(self, asset, amount, type_):
        # type_ 
        # 1 spot_account -> usdt_account
        # 2 usdt_account -> spot_account
        # 3 spot_account -> coin_account
        # 4 coin_account -> spot_account
        params = {}
        params['asset'] = asset
        params['amount'] = amount
        params['type'] = type_
        return self._request_api("post", "/sapi/v1/futures/transfer", True, data=params)
    ################### 杠杆代币接口 ###################

    ################### 币安挖矿接口 ###################

    def websocket_get_listenKey_spot(self):
        return self._request_api("post", "/api/v3/userDataStream", False, data={})
    
    def websocket_extend_listenKey_spot(self, listenKey):
        params = {}
        params['listenKey'] = listenKey
        return self._request_api("put", "/api/v3/userDataStream", False, data=params)
    
    def websocket_delete_listenKey_spot(self, listenKey):
        params = {}
        params['listenKey'] = listenKey
        return self._request_api("delete", "/api/v3/userDataStream", False, data=params)

    def websocket_get_listenKey_lever(self):
        return self._request_api("post", "/sapi/v1/userDataStream", False, data={})
    
    def websocket_extend_listenKey_lever(self, listenKey):
        params = {}
        params['listenKey'] = listenKey
        return self._request_api("put", "/sapi/v1/userDataStream", False, data=params)
    
    def websocket_delete_listenKey_lever(self, listenKey):
        params = {}
        params['listenKey'] = listenKey
        return self._request_api("delete", "/sapi/v1/userDataStream", False, data=params)
    
    def websocket_get_listenKey_lever_isolated(self, symbol):
        params = {}
        params['symbol'] = symbol
        return self._request_api("post", "/sapi/v1/userDataStream/isolated", False, data=params)
    
    def websocket_extend_listenKey_lever_isolated(self, symbol, listenKey):
        params = {}
        params['symbol'] = symbol
        params['listenKey'] = listenKey
        return self._request_api("put", "/sapi/v1/userDataStream/isolated", False, data=params)
    
    def websocket_delete_listenKey_lever_isolated(self, symbol, listenKey):
        params = {}
        params['symbol'] = symbol
        params['listenKey'] = listenKey
        return self._request_api("delete", "/sapi/v1/userDataStream/isolated", False, data=params)
    
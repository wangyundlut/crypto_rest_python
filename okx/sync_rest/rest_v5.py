
from datetime import datetime, timedelta
from decimal import Decimal
from math import ceil, floor

from .client import Client
from .consts import GET, POST

HOURS8 = 8

class okx_api_v5(Client):

    def __init__(self, api_key, api_secret_key, passphrase, use_server_time=False, test=False, first=False):
        # print(locals())
        Client.__init__(self, api_key, api_secret_key, passphrase, use_server_time, test, first)

    # -------------- 账户 ---------------------------
    def account_get_balance(self, ccy=None):
        params = {}
        if ccy:
            params['ccy'] = ccy
        return self._request_with_params(GET, '/api/v5/account/balance', params)

    def account_get_position(self, instType=None, instId=None, posId=None):
        params = {}
        if instType:
            params['instType'] = instType
        if instId:
            params['instId'] = instId
        if posId:
            params['posId'] = posId
        return self._request_with_params(GET, '/api/v5/account/positions', params)

    def account_get_bills(self, before='', after=''):
        # before 填入billId 获取更新的数据
        params = {}
        if before:
            params['before'] = before
        if after:
            params['after'] = after
        return self._request_with_params(GET, '/api/v5/account/bills', params) 

    def account_get_bills_archive(self, before='', after='', instType='', ccy='', type_=''):
        # before 填入billId 获取更新的数据
        params = {}
        if instType:
            params['instType'] = instType
        if ccy:
            params['ccy'] = ccy
        if type_:
            params["type"] = type_
        if before:
            params['before'] = before
        if after:
            params['after'] = after
        return self._request_with_params(GET, '/api/v5/account/bills-archive', params)   

    def account_get_config(self):
        return self._request_without_params(GET, '/api/v5/account/config')

    def account_set_position_mode(self, params: dict={}):
        if not params:
            params['posMode'] = 'long_short_mode'
        return self._request_with_params(POST, '/api/v5/account/set-position-mode', params)
    
    def account_get_max_size(self, instId, tdMode='cross'):
        params = {}
        params['instId'] = instId
        params['tdMode'] = tdMode
        return self._request_with_params(GET, '/api/v5/account/max-size', params)
    
    def account_get_interest_accrued(self):
        return self._request_without_params(GET, '/api/v5/account/interest-accrued')

    def account_set_leverage(self, lever, mgnMode, instId=None, ccy=None, posSide=None):
        params = {}
        params['lever'] = lever
        params['mgnMode'] = mgnMode
        if instId:
            params['instId'] = instId
        if ccy:
            params['ccy'] = instId
        if posSide:
            params['posSide'] = instId
        return self._request_with_params(POST, '/api/v5/account/set-leverage', params)
    
    # -------------- 资金 ---------------------------
    def asset_get_balances(self):
        return self._request_without_params(GET, '/api/v5/asset/balances')
    
    def asset_post_transfer(self, ccy, amt, from_, to, type_='0', instId=None, toInstId=None, subAcct=None):
        params = {}
        params['ccy'] = ccy
        params['amt'] = amt
        params['from'] = from_
        params['to'] = to
        if type_:
            params['type'] = type_
        if subAcct:
            params['subAcct'] = subAcct
        if instId:
            params['instID'] = instId
        if toInstId:
            params['toInstId'] = toInstId
        return self._request_with_params(POST, '/api/v5/asset/transfer', params)

    def asset_get_currencies(self):
        return self._request_without_params(GET, '/api/v5/asset/currencies')
    # -------------- 行情数据 ---------------------------
    def market_get_tickers(self, instType):
        # SPOT SWAP FUTURES OPTION
        params = {}
        params['instType'] = instType
        return self._request_with_params(GET, '/api/v5/market/tickers', params)

    def market_get_ticker(self, instId):
        params = {}
        params['instId'] = instId
        return self._request_with_params(GET, '/api/v5/market/ticker', params)
    
    def market_get_candles(self, instId, after=None, before=None, bar='1m', limit=100):
        # if you use before, you must use after together
        # you can use after only, but not before only
        # if you use before after together, the result will return before , not as the exchange says
        # after means get older data
        # before means get newer data
        params = {}
        params['instId'] = instId
        if after:
            params['after'] = str(after)

        if before:
            params['before'] = str(before)

        params['bar'] = bar
        params['limit'] = limit
        return self._request_with_params(GET, '/api/v5/market/candles', params)
    # -------------- 公共数据 ---------------------------
    def public_get_instruments(self, instType):
        params = {}
        params['instType'] = instType
        return self._request_with_params(GET, '/api/v5/public/instruments', params)

    def public_get_funding_rate_current(self, instId):
        params = {}
        params['instId'] = instId
        return self._request_with_params(GET, '/api/v5/public/funding-rate', params)

    def public_get_funding_rate_history(self, instId):
        params = {}
        params['instId'] = instId
        return self._request_with_params(GET, '/api/v5/public/funding-rate-history', params)

    def public_get_price_limit(self, instId):
        params = {}
        params['instId'] = instId
        return self._request_with_params(GET, '/api/v5/public/price-limit', params)

    def public_get_server_time(self):
        return self._request_without_params(GET, '/api/v5/public/time')

    # -------------- send order ---------------------------
    # for all the mode = 'cross', 
    def trade_post_order(self, instId, side, ordType, sz,  px=None, tdMode='cross'):
        params = {}
        params['instId'] = instId
        params['tdMode'] = tdMode
        params['side'] = side
        params['ordType'] = ordType
        params['sz'] = str(sz)

        if ordType != 'market':
            params['px'] = str(px)

        return self._request_with_params(POST, '/api/v5/trade/order', params)
    
    def trade_post_batch_order_net(self, params=[]):
        # 批量下单 
        return self._request_with_params(POST, '/api/v5/trade/batch-orders', params)


    def trade_post_cancel_order(self, instId, ordId=None, clOrdId=None):
        params = {}
        params['instId'] = instId
        if ordId:
            params['ordId'] = ordId
        if clOrdId:
            params['clOrdId'] = clOrdId
        return self._request_with_params(POST, '/api/v5/trade/cancel-order', params)

    def trade_post_cancel_batch_orders(self, params: list):
        return self._request_with_params(POST, '/api/v5/trade/cancel-batch-orders', params)

    def trade_post_amend_order(self, instId, ordId=None, clOrderId=None, newSz=None, newPx=None):
        params = {}
        params['instId'] = instId
        if ordId:
            params['ordId'] = ordId
        else:
            if clOrderId:
                params['clOrderId'] = clOrderId
            else:
                print("amend error must have ordId or clOrderId")
                return
        if (not newSz) and (not newPx):
            print(f"amend order must have newSz or newPx")
            return
        if newSz:
            params['newSz'] = newSz
        if newPx:
            params['newPx'] = newPx
        return self._request_with_params(POST, '/api/v5/trade/amend-order', params)


    def trade_get_order_info(self, instId, ordId=None, clOrdId=None):
        params = {}
        params['instId'] = instId
        if ordId:
            params['ordId'] = ordId
        elif clOrdId:
            params['clOrdId'] = ordId
        return self._request_with_params(GET, '/api/v5/trade/order', params)

    def trade_get_orders_pending(self, instType=None, uly=None, instId=None, ordType=None, state_=None, after=None, before=None, limit=100):
        params = {}
        
        if instType:
            params['instType'] = instType
        if uly:
            params['uly'] = uly
        if instId:
            params['instId'] = instId
        if ordType:
            params['ordType'] = ordType
        if state_:
            params['state'] = state_
        if after:
            params['after'] = after
        if before:
            params['before'] = before
        if limit:
            params['limit'] = limit
       
        return self._request_with_params(GET, '/api/v5/trade/orders-pending', params)

    def trade_get_order_history(self, instType, state='filled', before='', after=''):
        params = {}
        params['instType'] = instType
        params['state'] = state
        if before:
            params['before'] = before
        if after:
            params['after'] = after
        return self._request_with_params(GET, '/api/v5/trade/orders-history', params)
    
    def trade_get_order_history_archive(self, instType, instId='', state='', before='', after=''):
        params = {}
        params['instType'] = instType
        if instId:
            params['instId'] = instId
        if state:
            params['state'] = state
        if before:
            params['before'] = before
        if after:
            params['after'] = after
        return self._request_with_params(GET, '/api/v5/trade/orders-history-archive', params)
    
    def trade_get_trades_history(self, instType, before='', after='', instId=''):
        params = {}
        params['instType'] = instType
        if instId:
            params['instId'] = instId
        # careful use before, newer information will get different info
        if before:
            params['before'] = before
        # this is for asking for older data, billId 
        if after:
            params['after'] = after
        return self._request_with_params(GET, '/api/v5/trade/fills', params)
    
    def trade_get_trades_history_archive(self, instType, before='', after='', instId=''):
        params = {}
        params['instType'] = instType
        if instId:
            params['instId'] = instId
        # careful use before, newer information will get different info
        if before:
            params['before'] = before
        # this is for asking for older data, billId 
        if after:
            params['after'] = after
        return self._request_with_params(GET, '/api/v5/trade/fills-history', params)

    # -------------- 子账户 ---------------------------
    def subaccount_get_list(self, enable=None, subAcct=None, after=None, before=None, limit=None):
        params = {}
        if enable:
            params['enable'] = enable
        if subAcct:
            params['subAcct'] = subAcct
        if after:
            params['after'] = after
        if before:
            params['before'] = before
        if limit:
            params['limit'] = limit

        return self._request_with_params(GET, '/api/v5/users/subaccount/list', params)
    
    def subaccount_balances(self, subAcct):
        params = {}
        params['subAcct'] = subAcct
        return self._request_with_params(GET, '/api/v5/account/subaccount/balances', params)




    
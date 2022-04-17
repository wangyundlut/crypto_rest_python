import sys
sys.path.append('/application/3dots_exchange_api/')
sys.path.append('/application/crypto_tools/')

from Tools import logtool, dbMysql, noticeDingDing, dbMongo

key = "j-xCUQY_AvGcHgzFl7SAX-Rs3fK9pQSULDhumMGp"
secret = "TFqi2N-5IdJ_jl2fBWL3d815ZTJywHKQiMGTiNeL"

from client_with_sign import FtxClient
log = logtool().addHandler(name='ftxtest')

ftx = FtxClient(api_key=key, api_secret=secret, subaccount_name='test00')

# 测试limit order
# limitorder = ftx.place_order(market='AAVE-PERP', side='buy', price=2.2, size=1.0)
# log.info('limit order')
# log.info(limitorder)
# limit_order_info = ftx.get_orders(limitorder['id'])
# log.info('limit order info')
# log.info(limit_order_info)
# 测试market order
# marketorder = ftx.place_order(market='AAVE-PERP', side='buy', price=None, size=1.0, type='market')
# log.info('market order')
# log.info(marketorder)
# market 现货
marketorder = ftx.place_order(market='DOGE/USD', side='sell', price=None, size=9.992, type='market')
log.info('market spot order')
log.info(marketorder)

marketorder = ftx.place_order(market='DOGE-PERP', side='buy', price=None, size=10.0, type='market')
log.info('market future order')
log.info(marketorder)

# market_order_info = ftx.get_orders(marketorder['id'])
# log.info('market order info')
# log.info(market_order_info)


print(ftx.get_account_info())
print(ftx.get_balances())
print(ftx.get_positions())
print(ftx.list_markets())
print(ftx.cancel_orders('AAVE-PERP'))
print(ftx.get_open_orders())
import asyncio
import websockets
import json
from datetime import datetime, timedelta
import time

import yaml
import platform
import os
"""
该期权以比特币或以太币为定价单位，但相关价格也可以按美元显示。
美元价格是通过最新的期货价格（如果不存在到期日与之相同或更早的期货合约，则通过指数）来确定的。
同时交易平台还会显示期权价格的隐含波动率。

交易者以 10,000 美元的执行价格购买了 0.05(价格) 比特币的看涨期权。您有权用 10,000 美元购买 1 比特币。
假设到期日当天，比特币指数达到 12,500 美元，则到期（交割）价格为 12,500 美元。该期权将以 1 比特币 2500 美元的价格结算。
因此，在期权到期日，交易者的账户将记入 0.2 比特币（2,500/12,500）。
交易者的初始购买价格为 0.05 比特币，交易者的收益为 0.15 比特币。


"""



HOURS8 = 8
DERIBIT = 'deribit'
OPTION = 'option'
# WEBURL = 'wss://test.deribit.com/ws/api/v2'
WEBURL = 'wss://www.deribit.com/ws/api/v2/'

currencies = []
currencies_trade = {}
instrument_names = {}

def deribit_timestamp():
    #  in milliseconds since UNIX epoch
    now = int((datetime.utcnow() + timedelta(hours=HOURS8)).timestamp() * 1000)
    return now

def exch_to_local(time_exchange):
    # 交易所的时间 -> 本地的时间 int -> datetime
    time_local = datetime.utcfromtimestamp(int(time_exchange / 1000))
    time_local = time_local.replace(tzinfo=None)
    time_local = time_local + timedelta(hours=HOURS8)
    # time_local = CHINA_TZ.localize(time_local)
    return time_local

def local_to_exch(time_local):
    # 本地的时间 ->交易所的时间 datetime -> int
    # time.strptime会自动忽略毫秒，只取最小精度秒
    # time_local = datetime.now()
    time_utc = time_local - timedelta(hours=HOURS8)
    stamp_utc = int(time_utc.timestamp() * 1000)
    time_exchange = stamp_utc + HOURS8 * 3600 * 1000

    return time_exchange

def local_timestamp(time_local):
    # 本地时间 -> 数据库时间 datetime -> str
    return time_local.strftime("%Y-%m-%d %H:%M:%S")

class deribit_api_websocket:
    
    def __init__(self):
        pass
    
    def create_options_instruments_table(self):
        asyncio.get_event_loop().run_until_complete(self.get_currencies())
        for currency in currencies:
            instrument_names[currency] = []

        for currency in currencies:
            if currency in ['BTC', 'ETH']:
                continue
            table_name = f"{DERIBIT}_{OPTION}_{currency.replace('-', '_')}"
            self.create_option_kline_table(table_name)
            
        asyncio.get_event_loop().run_until_complete(self.get_last_trades_by_currency())
        asyncio.get_event_loop().run_until_complete(self.get_instrument_names())
        asyncio.get_event_loop().run_until_complete(self.get_klines())
    
    async def get_currencies(self):
        async with websockets.connect(WEBURL) as websocket:
            msg = \
                {
                    "jsonrpc" : "2.0",
                    # "id" : 7538,
                    "method" : "public/get_currencies",
                    "params" : {

                }
            }
            await websocket.send(json.dumps(msg))
            response = await websocket.recv()
            # do something with the response...
            d = json.loads(response)
            # print(d)
            for result in d['result']:
                currencies.append(result['currency'])

    async def get_last_trades_by_currency(self):
        async with websockets.connect(WEBURL) as websocket:
            for currency in currencies:
                msg = \
                    {
                        "jsonrpc" : "2.0",
                        "id" : 9290,
                        "method" : "public/get_last_trades_by_currency",
                        "params" : {
                            "currency" : currency,
                            "count" : 1
                        }
                    }
                await websocket.send(json.dumps(msg))
                response = await websocket.recv()
                # do something with the response...
                d = json.loads(response)
                # print(d)
                d = d['result']['trades'][0]
                currencies_trade[currency] = d['price']

    async def get_instrument_names(self):
        async with websockets.connect(WEBURL) as websocket:
            for currency in currencies:
                msg = \
                    {
                        "jsonrpc" : "2.0",
                        # "id" : 7617,
                        "method" : "public/get_instruments",
                        "params" : {
                            "currency" : currency,
                            "kind" : "option",
                            "expired" : False
                    }
                }
                await websocket.send(json.dumps(msg))
                response = await websocket.recv()
                # do something with the response...
                d = json.loads(response)
                # print(d)
                for result in d['result']:
                    instrument_names[result['base_currency']].append(result['instrument_name'])

    async def get_klines(self):
        async with websockets.connect(WEBURL) as websocket:
            cur = self.cur
            conn = self.conn
            te = datetime.now().replace(second=0, microsecond=0)
            for key, values in instrument_names.items():
                # 找到最近更新的小时
                sql = f"select instrument_id, datetime from {DERIBIT}_{OPTION}_{key.replace('-', '_')} " \
                        f" order by datetime desc limit 1"   
                cur.execute(sql)
                dateresult = cur.fetchall()
                # timestart for all
                tsall = dateresult[0][1] - timedelta(hours=3)
                sql = f"select instrument_id, datetime from {DERIBIT}_{OPTION}_{key.replace('-', '_')} " \
                        f"where datetime > '{tsall.strftime('%Y-%m-%d %H:%M:%S')}' order by datetime"   
                cur.execute(sql)
                datarecents = list(cur.fetchall())
                datasdict = {}
                for data in datarecents:
                    datasdict[data[0]] = data[1]

                klines = []
                for value in values:
                    print(f"{datetime.now()} {value} start")
                    # value='BTC-5MAR21-50000-C'
                    # 查询本地时间
                    if value in datasdict.keys():
                        ts = datasdict[value]
                    else:
                        ts = tsall
                    
                    now = datetime.now().replace(second=0, microsecond=0)

                    ts = ts + timedelta(minutes=1)
                    msg = \
                        {
                            "jsonrpc" : "2.0",
                            # "id" : 7617,
                            "method" : "public/get_tradingview_chart_data",
                            "params" : {
                                "instrument_name" : value,
                                "start_timestamp" : local_to_exch(ts),
                                "end_timestamp" : local_to_exch(te),
                                "resolution" : "1"
                        }
                    }
                    await websocket.send(json.dumps(msg))
                    response = await websocket.recv()
                    # do something with the response...
                    d = json.loads(response)
                    d = d['result']
                    # print(d)
                    
                    close_list = d['close']
                    # volume in quote currency
                    cost_list = d['cost']
                    high_list = d['high']
                    low_list = d['low']
                    open_list = d['open']
                    status = d['status']
                    ticks_list = d['ticks']
                    # volume in base currency
                    volume_list = d['volume']
                    
                    if status == 'no_data':
                        continue
                    
                    if status != 'ok':
                        print(f"status not ok: {status} {d}")

                    for i in range(len(close_list)):
                        if round(volume_list[i], 8) <= 0:
                            continue
                        # print(f"{value}  {exch_to_local(ticks_list[i])}")
                        kline = [value, 
                                exch_to_local(ticks_list[i]),
                                round(open_list[i], 8),
                                round(high_list[i], 8),
                                round(low_list[i], 8),
                                round(close_list[i], 8),
                                round(cost_list[i], 8),
                                round(cost_list[i] * currencies_trade[key], 2),
                                round(volume_list[i], 8),
                                ]
                        klines.append(kline)
                    print(f"{datetime.now()} {value} Done")
                    pass
                if klines:
                    # 插入数据 更新时间
                    db_klines = ((klines[i][0], klines[i][1], klines[i][2], klines[i][3], klines[i][4],
                                klines[i][5], klines[i][6], klines[i][7], klines[i][8]) for i in range(len(klines)))
                    sql = f"insert into {DERIBIT}_{OPTION}_{key.replace('-', '_')}(instrument_id, datetime, open, high, low, close, vol, vol_usd, vol_underlying) " \
                        f"values( %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                    cur.executemany(sql, db_klines)
                    conn.commit()





if __name__ == "__main__":
    testcls = deribit_api_websocket()
    testcls.create_options_instruments_table()


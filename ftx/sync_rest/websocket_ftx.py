# okex snapshot V3 BTC估值 
# okex snapshot V5 account position

import sys
sys.path.append('/application/3dots_exchange_api/')
sys.path.append('/application/crypto_tools/')

from Tools import logtool, dbMysql, noticeDingDing, dbMongo

import asyncio
from copy import deepcopy
import redis
import pandas as pd
from datetime import datetime, timedelta
from time import sleep
import time
import math
import yaml
import platform
import os
import json
from sqlalchemy import create_engine
import websockets
import hmac
import base64

yml_path = os.path.join("/","application", "account.yml")
f = open(yml_path)
yaml_data = yaml.full_load(f)
yaml_file = yaml_data

DBNAME = yaml_data['mysql_alan']['dbname']
CONS = 'okex_trade_'

log = logtool().addHandler()
ding = noticeDingDing(yaml_data['ding_info']['ding'])


def login_params(api_key, secret_key, name=None):
    ts = int(time.time() * 1000)
    login_params = {'op': 'login', 'args': {
        'key': api_key,
        'sign': hmac.new(
            secret_key.encode(), f'{ts}websocket_login'.encode(), 'sha256').hexdigest(),
        'time': ts,
        'subaccount': name,
    }}
    return login_params

class FtxWebsocket:

    websocketUrl = 'wss://ftx.com/ws/'
    
    def __init__(self):
        self.conn_pool = None
        self.load_redis_connection_pool()

    def load_redis_connection_pool(self):
        redis_key = 'redis_pro2'
        host = yaml_data[redis_key]['host']
        port = yaml_data[redis_key]['port']
        password = yaml_data[redis_key]['password']
        self.conn_pool = redis.ConnectionPool(host=host, port=port, password=password, decode_responses=True, max_connections=10)   

    def get_redis_connection(self):
        rc = redis.Redis(connection_pool=self.conn_pool)
        return rc
    

    async def private_with_login(self, ftx_account):
        

        apikey = yaml_file[ftx_account]['key']
        secretkey = yaml_file[ftx_account]['secret']
        accountname = yaml_file[ftx_account]['subaccount_name']

        while True:
            try:
                async with websockets.connect(self.websocketUrl) as ws:
                    
                    await ws.send(json.dumps({'op': 'ping'}))
                    res = await ws.recv()
                    print(f"send ping res {res}")

                    login_param = login_params(apikey, secretkey, accountname)
                    await ws.send(json.dumps(login_param))
  
                    channel = {'op': 'subscribe', 'channel': 'fills'}
                    await ws.send(json.dumps(channel))
                    channel = {'op': 'subscribe', 'channel': 'orders'}
                    await ws.send(json.dumps(channel))
                    # channel = {'op': 'subscribe', 'channel': 'ticker', 'market': 'BTC/USD'}
                    # channel = {'op': 'subscribe', 'channel': 'trades', 'market': 'BTC/USD'}
                    # channel = {'op': 'subscribe', 'channel': 'orderbook', 'market': 'BTC/USD'}
                    # await ws.send(json.dumps(channel))

                    while True:
                        try:
                            res = await asyncio.wait_for(ws.recv(), timeout=20)
                        except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed) as e:
                            try:
                                await ws.send(json.dumps({'op': 'ping'}))
                                res = await ws.recv()
                                print(f"{datetime.now()} {res}")
                                # channel = {'op': 'subscribe', 'channel': 'fills'}
                                # await ws.send(json.dumps(channel))
                                continue
                            except Exception as e:
                                print(f"error 正在重连 {e}")
                                break
                        res = json.loads(res)
                        print(res)
                        # print(res.keys())
                        if 'data' not in res.keys():
                            continue

                        # data = res['data']
                        # print(data)
                        # instId = res['market']
                        # print(instId)
                        # # read price
                        # if instId == 'BTC/USD':
                        #     #  update leg 1
                        #     print(f"{float(data['ask'])} {data}")
                            
                            
            except Exception as e:
                print(str(datetime.now()) + " 连接断开，正在重连……")
                continue
    

def main():
    loop = asyncio.get_event_loop()

    cls = FtxWebsocket()
    cls.load_redis_connection_pool()
    tasks = []
    account_list = [
        'ftx_test00',
        # 'ftx_main'
    ]
    for account in account_list:
        task = cls.private_with_login(account)
        tasks.append(task)
    
    loop.run_until_complete(asyncio.gather(*tasks))
    loop.close()

if __name__ == "__main__":
    main()
            




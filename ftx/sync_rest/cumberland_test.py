
import websockets
import asyncio
from uuid import uuid4
import json

# async def cert_3():
#     print("[CERT-3] Make an INDICATIVE_QUOTE_REQUEST for BTC_USD")
#     # conn = Connection.connect()
    
#     websocket = WebsocketConnection()
#     async with websocket.session.ws_connect(WebsocketConnection.connection_string()) as ws:
#         asyncio.ensure_future(websocket.process_messages(ws))
#         request = WebsocketConnection.indicative_quote_request("BTC_USD", 'USD', 10000, "cert-3")
#         await ws.send_str(json.dumps(request))
#         print(await websocket.take())
#         request = WebsocketConnection.indicative_quote_request("BTC_USD", 'BTC', 10, "cert-3")
#         await ws.send_str(json.dumps(request))
#         print(await websocket.take())
#         # add_result("cert_3", await websocket.take())
#     await websocket.session.close()

websocketPubUrl = "https://api-v00-cert.cumberlandmining.com:443/messaging"
async def test():
    async with websockets.connect(websocketPubUrl) as ws:
        print("[CERT-3] Make an INDICATIVE_QUOTE_REQUEST for BTC_USD")
        msg = {
                "messageType": "INDICATIVE_QUOTE_REQUEST",
                "ticker": "BTC_USD",
                "notional": {
                    "amount": 10000,
                    "currency": "USDT"
                },
                "counterpartyRequestId": f"cert-3-{uuid4()}"
            }
        await ws.send(json.dumps(msg))

    while True:
        try:
            res = await asyncio.wait_for(ws.recv(), timeout=30)
        except (asyncio.TimeoutError, websockets.exceptions.ConnectionClosed) as e:
            try:
                print("time out")
                continue

            except Exception as e:
                print("error")
                break
        print(res)
loop = asyncio.get_event_loop()
loop.run_until_complete(test())


import re
import urllib
import base64
import json
import zlib
import hashlib
import hmac
import sys
from copy import copy
from datetime import datetime
import pytz
from typing import Dict, List, Any

from .rest_client import RestClient
from .rest_client import Request


CHINA_TZ = pytz.timezone("Asia/Shanghai")

class HuobiSpot(RestClient):
    # REST_HOST = "https://api.huobipro.com"
    REST_HOST = "https://api.huobi.pro"
    def __init__(self):

        super().__init__()
        self.init(url_base=self.REST_HOST)
        self.proxies: dict = None

    def connect(
            self,
            key: str,
            secret: str,
    ) -> None:
        """
        Initialize connection to REST server.
        """
        self.key = key
        self.secret = secret
        self.host, _ = _split_url(self.REST_HOST)

    def sign(self, request: Request) -> Request:
        """
        Generate HUOBI signature.
        """
        request.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36"
        }
        # params_with_signature = create_signature(
        #     self.key,
        #     request.method,
        #     self.host,
        #     request.path,
        #     self.secret,
        #     request.params
        # )
        # 更新参数
        # request.params = params_with_signature

        # 这里修改 如果是POST方法，修改headers dict
        if request.method == "POST":
            request.headers["Content-Type"] = "application/json"

            if request.data:
                request.data = json.dumps(request.data)

        return request

    def spot_tickers(self):
        request = Request(
            method="GET",
            path="/market/tickers"
        )
        try:
            self.rest_request(request)

            # print(request.response['data'][0])
            # print(f" spot instruments done")
        except Exception as e:
            print(e)
        return request.response

    def spot_instruments(self):
        request = Request(
            method="GET",
            path="/v1/common/symbols"
        )
        try:
            self.rest_request(request)

            # print(request.response['data'][0])
            # print(f" spot instruments done")
        except Exception as e:
            print(e)

        return request.response

    def query_account(self):
        request = Request(
            method="GET",
            path="/v1/account/accounts",
        )
        try:
            self.rest_request(request)
            # print(request.response['data'][0])
            # print(f" spot account ")
        except Exception as e:
            print(e)

    def spot_kline(self, symbol):
        #
        params = {
            "symbol": symbol,
            "period": "1min",
            "size": 2000
        }

        # Get response from server
        request = Request(
            "GET",
            "/market/history/kline",
            params=params
        )
        try:
            self.rest_request(request)
            # print(request.response['data'][0])
            # print(f" spot kline")
        except Exception as e:
            print(e)
        return request.response


class HuobiFutures(RestClient):
    REST_HOST = "https://api.hbdm.com"
    # REST_HOST = "https://api.huobi.pro"
    def __init__(self):

        super().__init__()
        self.init(url_base=self.REST_HOST)
        self.proxies: dict = None

    def connect(
            self,
            key: str,
            secret: str,
    ) -> None:
        """
        Initialize connection to REST server.
        """
        self.key = key
        self.secret = secret
        self.host, _ = _split_url(self.REST_HOST)

    def sign(self, request: Request) -> Request:
        """
        Generate HUOBI signature.
        """
        request.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36"
        }
        # params_with_signature = create_signature(
        #     self.key,
        #     request.method,
        #     self.host,
        #     request.path,
        #     self.secret,
        #     request.params
        # )
        # # 更新参数
        # request.params = params_with_signature

        # 这里修改 如果是POST方法，修改headers dict
        if request.method == "POST":
            request.headers["Content-Type"] = "application/json"

            if request.data:
                request.data = json.dumps(request.data)

        return request

    def futures_instruments(self):
        request = Request(
            method="GET",
            path="/api/v1/contract_contract_info"
        )
        try:
            self.rest_request(request)

            # print(request.response['data'][0])
            # print(f"futures instruments  Done")
        except Exception as e:
            print(e)

        return request.response

    def query_account(self):
        request = Request(
            method="POST",
            path="/api/v1/contract_account_info",
        )
        try:
            self.rest_request(request)
            # print(request.response['data'][0])
            # print(f"futures account  Done")
        except Exception as e:
            print(e)

    def futures_kline(self, contract_code):
        #
        params = {
            "symbol": contract_code,
            "period": "1min",
            "size": 2000
        }

        # Get response from server
        request = Request(
            "GET",
            "/market/history/kline",
            params=params
        )
        try:
            self.rest_request(request)
            # print(request.response['data'][0])
            # print(f"futures kline done")
        except Exception as e:
            print(e)

        return request.response


class HuobiSwap(RestClient):
    REST_HOST = "https://api.hbdm.com"
    def __init__(self):

        super().__init__()
        self.init(url_base=self.REST_HOST)
        self.proxies: dict = None

    def connect(
            self,
            key: str,
            secret: str,
    ) -> None:
        """
        Initialize connection to REST server.
        """
        self.key = key
        self.secret = secret
        self.host, _ = _split_url(self.REST_HOST)

    def sign(self, request: Request) -> Request:
        """
        Generate HUOBI signature.
        """
        request.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36"
        }
        # params_with_signature = create_signature(
        #     self.key,
        #     request.method,
        #     self.host,
        #     request.path,
        #     self.secret,
        #     request.params
        # )
        # # 更新参数
        # request.params = params_with_signature

        # 这里修改 如果是POST方法，修改headers dict
        if request.method == "POST":
            request.headers["Content-Type"] = "application/json"

            if request.data:
                request.data = json.dumps(request.data)

        return request

    def swap_instruments(self):
        request = Request(
            method="GET",
            path="/swap-api/v1/swap_contract_info"
        )
        try:
            self.rest_request(request)

            # print(request.response['data'][0])
            # print(f"swap instruments  Done")
        except Exception as e:
            print(e)

        return request.response

    def swapu_instruments(self):
        request = Request(
            method="GET",
            path="/linear-swap-api/v1/swap_contract_info"
        )
        try:
            self.rest_request(request)

            # print(request.response['data'][0])
            # print(f"swap u instruments  Done")
        except Exception as e:
            print(e)

        return request.response

    def query_account(self):
        request = Request(
            method="POST",
            path="/swap-api/v1/swap_account_info",
        )
        try:
            self.rest_request(request)
            # print(request.response['data'][0])
            # print(f"swap account  Done")
        except Exception as e:
            print(e)

    def swap_kline(self, contract_code):
        #
        params = {
            "contract_code": contract_code,
            "period": "1min",
            "size": 2000
        }

        # Get response from server
        request = Request(
            "GET",
            "/swap-ex/market/history/kline",
            params=params
        )
        try:
            self.rest_request(request)
            # print(request.response['data'][0])
            # print(f"swap kline done")
        except Exception as e:
            print(e)

        return request.response

    def swapu_kline(self, contract_code):
        #
        params = {
            "contract_code": contract_code,
            "period": "1min",
            "size": 2000
        }

        # Get response from server
        request = Request(
            "GET",
            "/linear-swap-ex/market/history/kline",
            params=params
        )
        try:
            self.rest_request(request)
            # print(request.response['data'][0])
            # print(f"swap u kline done")
        except Exception as e:
            print(e)

        return request.response

    def swap_fee(self, contract_code):
        params = {
            "contract_code": contract_code,
        }
        request = Request(
            method="GET",
            path="/swap-api/v1/swap_historical_funding_rate",
            params=params,
        )
        try:
            self.rest_request(request)

            # print(request.response)
            # print(f"swap fee  Done")
        except Exception as e:
            print(e)

        return request.response

    def swapu_fee(self, contract_code):
        params = {
            "contract_code": contract_code,
        }
        request = Request(
            method="GET",
            path="/linear-swap-api/v1/swap_historical_funding_rate",
            params=params,
        )
        try:
            self.rest_request(request)

            # print(request.response)
            # print(f"swap u fee  Done")
        except Exception as e:
            print(e)

        return request.response


def _split_url(url):
    """
    将url拆分为host和path
    :return: host, path
    """
    result = re.match("\w+://([^/]*)(.*)", url)  # noqa
    if result:
        return result.group(1), result.group(2)


def create_signature(
    api_key,
    method,
    host,
    path,
    secret_key,
    get_params=None
) -> Dict[str, str]:
    """
    创建签名
    :param get_params: dict 使用GET方法时附带的额外参数(urlparams)
    :return:
    """
    sorted_params = [
        ("AccessKeyId", api_key),
        ("SignatureMethod", "HmacSHA256"),
        ("SignatureVersion", "2"),
        ("Timestamp", datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"))
    ]

    if get_params:
        sorted_params.extend(list(get_params.items()))
        sorted_params = list(sorted(sorted_params))
    encode_params = urllib.parse.urlencode(sorted_params)

    payload = [method, host, path, encode_params]
    payload = "\n".join(payload)
    payload = payload.encode(encoding="UTF8")

    secret_key = secret_key.encode(encoding="UTF8")

    digest = hmac.new(secret_key, payload, digestmod=hashlib.sha256).digest()
    signature = base64.b64encode(digest)

    params = dict(sorted_params)
    params["Signature"] = signature.decode("UTF8")
    return params


def create_signature_v2(
    api_key,
    method,
    host,
    path,
    secret_key,
    get_params=None
) -> Dict[str, str]:
    """
    创建签名
    :param get_params: dict 使用GET方法时附带的额外参数(urlparams)
    :return:
    """
    sorted_params = [
        ("accessKey", api_key),
        ("signatureMethod", "HmacSHA256"),
        ("signatureVersion", "2.1"),
        ("timestamp", datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"))
    ]

    if get_params:
        sorted_params.extend(list(get_params.items()))
        sorted_params = list(sorted(sorted_params))
    encode_params = urllib.parse.urlencode(sorted_params)

    payload = [method, host, path, encode_params]
    payload = "\n".join(payload)
    payload = payload.encode(encoding="UTF8")

    secret_key = secret_key.encode(encoding="UTF8")

    digest = hmac.new(secret_key, payload, digestmod=hashlib.sha256).digest()
    signature = base64.b64encode(digest)

    params = dict(sorted_params)
    params["authType"] = "api"
    params["signature"] = signature.decode("UTF8")
    return params


def generate_datetime(timestamp: float) -> datetime:
    """"""
    dt = datetime.fromtimestamp(timestamp)
    dt = CHINA_TZ.localize(dt)
    return dt





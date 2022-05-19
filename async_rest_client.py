import sys
import traceback
from datetime import datetime
from typing import Any, Callable, Optional, Union, Type
from types import TracebackType, coroutine
from threading import Thread
from asyncio import (
    get_event_loop,
    new_event_loop,
    set_event_loop,
    run_coroutine_threadsafe,
    AbstractEventLoop,
    Future
)
from json import loads

from aiohttp import ClientSession, ClientResponse, client_exceptions
import aiohttp


CALLBACK_TYPE = Callable[[dict, "Request"], None]
ON_FAILED_TYPE = Callable[[int, "Request"], None]
ON_ERROR_TYPE = Callable[[Type, Exception, TracebackType, "Request"], None]


class Request(object):
    """
    请求对象
    method: API的请求方法（GET, POST, PUT, DELETE, QUERY）
    path: API的请求路径（不包含根地址）
    callback: 请求成功的回调函数
    params: 请求表单的参数字典, 用于get请求,转换为请求地址
    data: 请求主体数据，如果传入字典会被自动转换为json,用于post请求
    headers: 请求头部的字典
    on_failed: 请求失败的回调函数
    on_error: 请求异常的回调函数
    extra: 任意其他数据（用于回调时获取） **extra 添加进session.get或其它
    """

    def __init__(
        self,
        method: str,
        base_url: str,
        path: str,
        params: dict,
        data: Union[dict, str, bytes],
        headers: dict,
        callback_method: str = "sync",
        callback: CALLBACK_TYPE = None,
        on_failed: ON_FAILED_TYPE = None,
        on_error: ON_ERROR_TYPE = None,
        extra: dict = {},
    ):
        """"""
        self.method: str = method
        self.base_url: str = base_url
        self.path: str = path
        self.callback_method = callback_method
        self.callback: CALLBACK_TYPE = callback
        self.params: dict = params
        self.data: Union[dict, str, bytes] = data
        self.headers: dict = headers

        self.on_failed: ON_FAILED_TYPE = on_failed
        self.on_error: ON_ERROR_TYPE = on_error
        self.extra: dict = extra

        self.response: "Response" = None


class Response:
    """结果对象"""

    def __init__(self, status_code: int, text: str, header: dict) -> None:
        """"""
        self.status_code: int = status_code
        self.text: str = text
        self.header: dict = header

    def json(self) -> dict:
        """获取字符串对应的JSON格式数据"""
        data = loads(self.text)
        return data


class asyncRestClient(object):
    """
    针对各类RestFul API的异步客户端
    * 重载sign方法来实现请求签名逻辑
    * 重载on_failed方法来实现请求失败的标准回调处理
    * 重载on_error方法来实现请求异常的标准回调处理
    """

    def __init__(self, loop: AbstractEventLoop = None, session: ClientSession = None):
        """"""
        self.loop: AbstractEventLoop = loop
        self.session: ClientSession = session

    def start(self) -> None:
        """启动客户端的事件循环"""
        if not self.loop:
            self.loop = new_event_loop()

        if not self.session:
            self.session = self.loop.run_until_complete(create_session(loop=self.loop))
        
        if not self.loop.is_running():
            start_event_loop(self.loop)
        
    def stop(self) -> None:
        """停止客户端的事件循环"""
        if self.loop and self.loop.is_running():
            self.loop.stop()

    def request(
        self,
        method: str,
        base_url: str,
        path: str,
        callback: CALLBACK_TYPE,
        callback_method: str = "sync",
        params: dict = None,
        data: Union[dict, str, bytes] = None,
        headers: dict = None,
        on_failed: ON_FAILED_TYPE = None,
        on_error: ON_ERROR_TYPE = None,
        extra: dict = {},
    ) -> Request:
        """添加新的请求任务，每个请求以new task的方式，no blocking，完成之后会有回调函数"""
        request: Request = Request(
            method,
            base_url,
            path,
            params,
            data,
            headers,
            callback_method,
            callback,
            on_failed,
            on_error,
            extra,
        )
    
        coro: coroutine = self._process_request(request)
        # self.loop.call_soon_threadsafe()
        run_coroutine_threadsafe(coro, self.loop)
        return request

    def on_failed(self, status_code: int, request: Request) -> None:
        """请求失败的默认回调"""
        print("RestClient on failed" + "-" * 10)
        print(str(request))

    def on_error(
        self,
        exception_type: type,
        exception_value: Exception,
        tb,
        request: Optional[Request],
    ) -> None:
        """请求触发异常的默认回调"""
        try:
            print("RestClient on error" + "-" * 10)
            print(self.exception_detail(exception_type, exception_value, tb, request))
        except Exception:
            traceback.print_exc()

    def exception_detail(
        self,
        exception_type: type,
        exception_value: Exception,
        tb,
        request: Optional[Request],
    ) -> None:
        """将异常信息转化生成字符串"""
        text = "[{}]: Unhandled RestClient Error:{}\n".format(
            datetime.now().isoformat(), exception_type
        )
        text += "request:{}\n".format(request)
        text += "Exception trace: \n"
        text += "".join(
            traceback.format_exception(exception_type, exception_value, tb)
        )
        return text

    async def _get_response(self, request: Request) -> Response:
        """发送请求到服务器，并返回处理结果对象"""

        url = request.base_url + request.path
        
        async with self.session.request(
            request.method,
            url,
            headers=request.headers,
            params=request.params,
            data=request.data,
            **request.extra
        ) as cr:
            text: str = await cr.text()
            status_code = cr.status
            header = dict(cr.headers)

            request.response = Response(status_code, text, header)
            return request.response
        
        # cr: ClientResponse = await self.session.request(
        #     request.method,
        #     url,
        #     headers=request.headers,
        #     params=request.params,
        #     data=request.data,
        #     **request.extra
        # )
        # text: str = await cr.text()
        # status_code = cr.status
        # header = dict(cr.headers)

        # request.response = Response(status_code, text, header)
        # return request.response

    async def _process_request(self, request: Request) -> None:
        """发送请求到服务器，并对返回进行后续处理 request请求"""
        try:
            
            response: Response = await self._get_response(request)
            request.response = response
            if request.callback_method == "sync":
                request.callback(request)
            else:
                await request.callback(request)
        except client_exceptions.ServerTimeoutError as timeout_error:
            request.on_failed(0, request)
        except Exception:
            t, v, tb = sys.exc_info()
            # 设置了专用异常回调
            if request.on_error:
                request.on_error(t, v, tb, request)
            # 否则使用全局异常回调
            else:
                self.on_error(t, v, tb, request)

async def create_session(loop: AbstractEventLoop):
    timeout = aiohttp.ClientTimeout(
            total=330, # 全部请求最终完成时间
            connect=2, # 从本机连接池里取出一个将要进行的请求的时间
            sock_connect=15, # 单个请求连接到服务器的时间
            sock_read=10 # 单个请求从服务器返回的时间
        )
    return ClientSession(loop=loop, timeout=timeout)

def start_event_loop(loop: AbstractEventLoop) -> None:
    """启动事件循环"""
    # 如果事件循环未运行，则创建后台线程来运行
    if not loop.is_running():
        thread = Thread(target=run_event_loop, args=(loop, ))
        # thread.daemon = True
        thread.start()

def run_event_loop(loop: AbstractEventLoop) -> None:
    """运行事件循环"""
    set_event_loop(loop)
    loop.run_forever()
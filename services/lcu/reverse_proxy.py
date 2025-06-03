# reverse_proxy.py

import ssl
from urllib.parse import urljoin

import requests
from requests.exceptions import RequestException


def generate_client_api_url(port: int, token: str) -> str:
    """
    生成 LCU API 的 base URL：
        https://riot:<token>@127.0.0.1:<port>
    这样后续的 requests 会自动带上 Basic Auth。
    """
    return f"https://riot:{token}@127.0.0.1:{port}"


class RP:
    """
    一个 WSGI 风格的反向代理 (Reverse Proxy)。它会把传入的 HTTP 请求透传到
    LCU 客户端 API，然后将 LCU 的响应再返回给原调用方。

    用法示例（以 WSGI 服务器为例）：
        from wsgiref.simple_server import make_server
        from reverse_proxy import RP

        rp_app = RP(port=你的LCULoginPort, token=你的LCUToken)
        server = make_server('127.0.0.1', 5000, rp_app)
        server.serve_forever()

    此时，访问 http://127.0.0.1:5000/<LCU 路径> 会被反向代理到
    https://riot:<token>@127.0.0.1:<port>/<LCU 路径>。
    """

    def __init__(self, port: int, token: str):
        """
        :param port: LCU 返回的本地端口号
        :param token: LCU 返回的 Basic Auth token
        """
        self.port = port
        self.token = token
        self.base_url = generate_client_api_url(port, token)

        # 使用 requests.Session 复用连接，关闭证书验证 (InsecureSkipVerify)
        self._session = requests.Session()
        self._session.verify = False  # 对应 Go 中 tls.Config{InsecureSkipVerify: true}

    def __call__(self, environ, start_response):
        """
        使 RP 实例可作为 WSGI 应用使用。会把传入的 WSGI environ 解析成 HTTP 请求，
        再用 requests 转发到 LCU，并将响应写回 WSGI start_response。
        """
        # 1. 从 WSGI environ 中提取请求方法、路径、查询字符串
        method = environ.get("REQUEST_METHOD", "GET")
        path = environ.get("PATH_INFO", "")
        query = environ.get("QUERY_STRING", "")
        # 构造完整的目标 URL
        # NOTE: urljoin 只会在 path 以 / 开头时拼接 base_url，否则可能丢失前缀
        # 所以，我们用简单的字符串拼接：
        if query:
            url = f"{self.base_url}{path}?{query}"
        else:
            url = f"{self.base_url}{path}"

        # 2. 收集要转发的 headers（除了 X-Forwarded-For，我们删掉它）
        forward_headers = {}
        for key, value in environ.items():
            if not key.startswith("HTTP_"):
                continue
            header_name = key[5:].replace("_", "-").title()
            if header_name.lower() == "x-forwarded-for":
                # 跳过它，等同于 Go 中的 `req.Header["X-Forwarded-For"] = nil`
                continue
            forward_headers[header_name] = value

        # 3. CONTENT_TYPE 和 CONTENT_LENGTH 也要单独处理
        if "CONTENT_TYPE" in environ:
            forward_headers["Content-Type"] = environ["CONTENT_TYPE"]
        if "CONTENT_LENGTH" in environ:
            forward_headers["Content-Length"] = environ["CONTENT_LENGTH"]

        # 4. 读取请求 body（如果有的话）
        try:
            length = int(environ.get("CONTENT_LENGTH", "0") or "0")
        except ValueError:
            length = 0

        if length > 0:
            body = environ["wsgi.input"].read(length)
        else:
            body = None

        # 5. 发起到 LCU 的请求
        try:
            resp = self._session.request(
                method=method,
                url=url,
                headers=forward_headers,
                data=body,
                timeout=30,
            )
        except RequestException as e:
            # 如果请求失败，返回 502 Bad Gateway
            status = "502 Bad Gateway"
            response_headers = [("Content-Type", "text/plain; charset=utf-8")]
            start_response(status, response_headers)
            return [f"Reverse proxy error: {e}".encode("utf-8")]

        # 6. 准备响应
        status = f"{resp.status_code} {resp.reason}"
        # WSGI 要求 headers 是 List[Tuple[str, str]]
        response_headers = []
        for k, v in resp.headers.items():
            # 某些头可能会被 WSGI 删减，比如 Transfer-Encoding: chunked
            # 这里只直接传递 LCU Response 中的所有头
            response_headers.append((k, v))

        start_response(status, response_headers)
        return [resp.content]


def new_rp(port: int, token: str) -> RP:
    """
    等价于 Go 中的 `NewRP(port int, token string) (*RP, error)`：
    返回一个反向代理 RP 实例。如果 URL 无法解析，这里直接抛异常。
    """
    # 在 Python 里，我们通过 requests 和简单的字符串拼接实现，不会出现 URL 解析错误。
    return RP(port, token)

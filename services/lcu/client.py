# client.py

import requests
import urllib3
from typing import Any, Optional

# 禁用 InsecureRequestWarning，因为我们在 LCU 通信中会跳过 TLS 验证
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 全局 Session，关闭证书验证，超时时间 30 秒
_session = requests.Session()
_session.verify = False  # 对应 Go 中 tls.Config{InsecureSkipVerify: true}
# 注意：requests 不支持全局 timeout，只能在每次请求时传入 timeout 参数

# 全局 client 对象，供 init_cli 初始化后使用
cli: Optional["Client"] = None


class Client:
    def __init__(self, port: int, token: str):
        """
        :param port: LCU 的端口号
        :param token: LCU 返回的 TLS/Basic Auth token
        """
        self.port = port
        self.auth_pwd = token
        self.base_url = self._fmt_client_api_url()

    def _fmt_client_api_url(self) -> str:
        """
        生成 LCU API 的 base_url。
        常见的格式是： https://riot:<token>@127.0.0.1:<port>
        这样后续 requests 会自动带上 Basic Auth 信息。
        """
        return f"https://riot:{self.auth_pwd}@127.0.0.1:{self.port}"

    def http_get(self, url: str) -> bytes:
        """
        等价于 Go 中的 httpGet(url string) ([]byte, error)
        """
        return self._req("GET", url, None)

    def http_post(self, url: str, body: Any) -> bytes:
        """
        等价于 Go 中的 httpPost(url string, body any) ([]byte, error)
        """
        return self._req("POST", url, body)

    def http_patch(self, url: str, body: Any) -> bytes:
        """
        等价于 Go 中的 httpPatch(url string, body any) ([]byte, error)
        """
        return self._req("PATCH", url, body)

    def http_delete(self, url: str) -> bytes:
        """
        等价于 Go 中的 httpDel(url string) ([]byte, error)
        """
        return self._req("DELETE", url, None)

    def _req(self, method: str, url: str, data: Any) -> bytes:
        """
        私有方法：统一执行 HTTP 请求，自动拼接 base_url，处理 JSON 序列化和响应。
        :param method: "GET", "POST", "PATCH", "DELETE"
        :param url:    相对于 base_url 的路径（例如 "/lol-summoner/v1/current-summoner"）
        :param data:   如果不为 None，则会被当成 JSON body 发送
        :return:       响应内容的 bytes；如有 HTTP 错误会抛出异常
        """
        full_url = self.base_url + url
        headers = {}
        try:
            if data is not None:
                # 发送 JSON body
                response = _session.request(
                    method,
                    full_url,
                    json=data,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
            else:
                # 不带 body
                response = _session.request(
                    method,
                    full_url,
                    timeout=30
                )
            # 如果状态码不是 2xx，则抛出 HTTPError
            response.raise_for_status()
            return response.content
        except Exception:
            # 上层调用可捕获并处理异常
            raise

def init_cli(port: int, token: str):
    """
    在全局范围内初始化一个 Client 实例，等价于 Go 中的 InitCli(port, token)。
    """
    global cli
    cli = Client(port, token)
    return cli

def new_client(port: int, token: str) -> Client:
    """
    返回一个新的 Client 实例，等价于 Go 中的 NewClient(port, token)。
    （但只有 init_cli 会写入全局 cli）
    """
    return Client(port, token)

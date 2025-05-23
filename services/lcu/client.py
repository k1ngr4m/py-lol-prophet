# client.py
import json
import time
from typing import Optional, Any, Dict
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class Client:
    _instance = None  # 单例实例

    def __init__(self, port: int, token: str):
        self.port = port
        self.auth_token = token
        self.base_url = self._generate_api_url()
        self.session = self._create_session()

    @classmethod
    def init_client(cls, port: int, token: str):
        cls._instance = cls(port, token)

    @classmethod
    def get_instance(cls):
        if not cls._instance:
            raise RuntimeError("Client not initialized")
        return cls._instance

    def _generate_api_url(self) -> str:
        return f"https://riot:{self.auth_token}@127.0.0.1:{self.port}"

    def _create_session(self) -> requests.Session:
        session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504])
        session.mount('https://', HTTPAdapter(max_retries=retries))
        session.verify = False  # 忽略SSL验证
        session.headers.update({
            "Accept": "application/json",
            "User-Agent": "hh-lol-prophet"
        })
        return session

    def _request(self, method: str, endpoint: str, data: Optional[Any] = None) -> Dict:
        url = f"{self.base_url}{endpoint}"
        kwargs = {"json": data} if data else {}

        try:
            resp = self.session.request(
                method=method,
                url=url,
                timeout=30,
                **kwargs
            )
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"HTTP request failed: {str(e)}")

    def http_get(self, endpoint: str) -> Dict:
        return self._request("GET", endpoint)

    def http_post(self, endpoint: str, data: Any) -> Dict:
        return self._request("POST", endpoint, data)

    def http_patch(self, endpoint: str, data: Any) -> Dict:
        return self._request("PATCH", endpoint, data)

    def http_delete(self, endpoint: str) -> Dict:
        return self._request("DELETE", endpoint)
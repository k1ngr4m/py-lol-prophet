import json
import requests
from typing import Optional, TypedDict
import global_conf.global_conf as global_vars
from conf.appConf import AppConf, Mode, CalcScoreConf, RateItemConf, HorseScoreConf


# 定义配置常量
CODE_OK = 0

# 全局变量
client = None
base_url = ""


# 类型定义
class Response(TypedDict):
    code: int
    msg: str
    data: dict

class CurrVersion(TypedDict):
    downloadUrl: str
    versionTag: str
    zipDownloadUrl: str


def init(url: str, _timeout_sec: int) -> None:
    """初始化 HTTP 客户端"""
    global client, base_url, timeout_sec
    base_url = url
    timeout_sec = _timeout_sec


def req(req_path: str, body: Optional[dict] = None) -> dict:
    """发送 HTTP POST 请求并处理响应"""
    url = base_url + req_path
    headers = {"Content-Type": "application/json"}

    try:
        # 发送请求
        response = requests.post(
            url,
            json=body,
            headers=headers,
            timeout=timeout_sec
        )

        # 检查 HTTP 状态码
        response.raise_for_status()

        # 解析 JSON 响应
        api_resp: Response = response.json()

        # 检查 API 响应码
        if api_resp["code"] != CODE_OK:
            raise Exception(f"API error {api_resp['code']}: {api_resp['msg']}")

        return api_resp["data"]

    except requests.exceptions.RequestException as e:
        raise Exception(f"Request failed: {str(e)}")
    except json.JSONDecodeError:
        raise Exception("Invalid JSON response")

def get_client_conf() -> CalcScoreConf:
    """获取客户端配置"""
    data = req("/v1/lol/client/getConf")

    # 将嵌套结构转换为模型实例
    try:
        # 转换列表字段
        if "KillRate" in data:
            data["KillRate"] = [RateItemConf(**item) for item in data["KillRate"]]

        if "HurtRate" in data:
            data["HurtRate"] = [RateItemConf(**item) for item in data["HurtRate"]]

        if "AssistRate" in data:
            data["AssistRate"] = [RateItemConf(**item) for item in data["AssistRate"]]

        # 转换元组字段
        if "Horse" in data:
            # 确保元组长度正确
            if len(data["Horse"]) != 6:
                raise ValueError("Horse tuple must have exactly 6 elements")
            data["Horse"] = tuple(HorseScoreConf(**item) for item in data["Horse"])

        # 创建配置实例
        return CalcScoreConf(**data)

    except Exception as e:
        raise Exception(f"Failed to parse client config: {str(e)}")

def get_curr_version() -> CurrVersion:
    """获取当前版本信息"""
    data = req("/v1/lol/getCurrVersion")
    return CurrVersion(
        downloadUrl=data.get("downloadUrl", ""),
        versionTag=data.get("versionTag", ""),
        zipDownloadUrl=data.get("zipDownloadUrl", "")
    )
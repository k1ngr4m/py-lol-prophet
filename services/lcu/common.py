"""
通用工具模块，对应原Go代码中的common.go
"""

import os
import sys
import hashlib
import uuid
import time
import json
import re
from typing import Any, List, Dict, Optional, TypeVar, Callable, Union
from services.lcu import adapt
from services.lcu.models.api import SummonerProfileData, Summoner
from services.lcu.windows import get_lol_client_api_info_adapt

# 常量定义
HTTP_SCHEME = "https"
WS_SCHEME = "wss"
AUTH_USERNAME = "riot"
HOST = "127.0.0.1"
T = TypeVar('T')


def is_file(path: str) -> bool:
    """
    检查路径是否为文件

    Args:
        path: 文件路径

    Returns:
        如果是文件则返回True，否则返回False
    """
    return os.path.isfile(path)


def is_dir(path: str) -> bool:
    """
    检查路径是否为目录

    Args:
        path: 目录路径

    Returns:
        如果是目录则返回True，否则返回False
    """
    return os.path.isdir(path)


def ensure_dir(path: str) -> bool:
    """
    确保目录存在，如果不存在则创建

    Args:
        path: 目录路径

    Returns:
        如果目录存在或创建成功则返回True，否则返回False
    """
    if is_dir(path):
        return True

    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception:
        return False


def get_mac() -> int:
    """
    获取MAC地址的数字表示

    Returns:
        MAC地址的数字表示，如果获取失败则返回0
    """
    import netifaces
    import re

    # 优先尝试物理网卡
    physical_interfaces = ['eth0', 'en0', 'en1', 'enp0s3', 'wlan0']

    for iface in physical_interfaces + netifaces.interfaces():
        try:
            addrs = netifaces.ifaddresses(iface)
            # 检查是否有链路层地址
            if netifaces.AF_LINK not in addrs:
                continue

            link_addrs = addrs[netifaces.AF_LINK]
            if not link_addrs:
                continue

            mac_str = link_addrs[0].get('addr', '')
            # 验证MAC地址格式
            if not mac_str or len(mac_str) < 12:
                continue

            # 清理MAC地址（移除分隔符）
            clean_mac = re.sub(r'[^0-9A-Fa-f]', '', mac_str)
            if len(clean_mac) != 12:  # 标准MAC是6字节=12字符
                continue

            mac_bytes = bytes.fromhex(clean_mac)

            # 跳过本地管理地址（第1字节第2位为1）
            if mac_bytes[0] & 0x02 == 0x02:
                continue

            # 补零到8字节并转为大端序整数
            padded_mac = mac_bytes.ljust(8, b'\x00')
            return int.from_bytes(padded_mac, 'big')

        except (KeyError, IndexError, ValueError):
            continue

    return 0


def in_array(item: T, array: List[T]) -> bool:
    """
    检查元素是否在数组中

    Args:
        item: 要检查的元素
        array: 数组

    Returns:
        如果元素在数组中则返回True，否则返回False
    """
    return item in array

def get_lol_client_api_info():
    return get_lol_client_api_info_adapt()


def compare_version(version1: str, version2: str) -> int:
    """
    比较两个版本号

    Args:
        version1: 第一个版本号
        version2: 第二个版本号

    Returns:
        如果version1 > version2返回1，如果version1 < version2返回-1，如果相等返回0
    """
    v1_parts = [int(x) for x in version1.split('.')]
    v2_parts = [int(x) for x in version2.split('.')]

    # 补齐版本号长度
    while len(v1_parts) < len(v2_parts):
        v1_parts.append(0)
    while len(v2_parts) < len(v1_parts):
        v2_parts.append(0)

    # 逐位比较
    for i in range(len(v1_parts)):
        if v1_parts[i] > v2_parts[i]:
            return 1
        elif v1_parts[i] < v2_parts[i]:
            return -1

    return 0


def generate_uuid() -> str:
    """
    生成UUID

    Returns:
        UUID字符串
    """
    return str(uuid.uuid4())


def md5(data: Union[str, bytes]) -> str:
    """
    计算MD5哈希

    Args:
        data: 要计算哈希的数据

    Returns:
        MD5哈希字符串
    """
    if isinstance(data, str):
        data = data.encode('utf-8')

    return hashlib.md5(data).hexdigest()


def sha256(data: Union[str, bytes]) -> str:
    """
    计算SHA256哈希

    Args:
        data: 要计算哈希的数据

    Returns:
        SHA256哈希字符串
    """
    if isinstance(data, str):
        data = data.encode('utf-8')

    return hashlib.sha256(data).hexdigest()


def json_encode(obj: Any) -> str:
    """
    将对象编码为JSON字符串

    Args:
        obj: 要编码的对象

    Returns:
        JSON字符串
    """
    return json.dumps(obj, ensure_ascii=False)


def json_decode(data: str) -> Any:
    """
    将JSON字符串解码为对象

    Args:
        data: JSON字符串

    Returns:
        解码后的对象
    """
    return json.loads(data)


def retry(attempts: int, delay: float, func: Callable, *args, **kwargs) -> Any:
    """
    重试执行函数

    Args:
        attempts: 尝试次数
        delay: 重试延迟（秒）
        func: 要执行的函数
        *args: 函数参数
        **kwargs: 函数关键字参数

    Returns:
        函数执行结果

    Raises:
        最后一次执行的异常
    """
    last_exception = None
    for i in range(attempts):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if i < attempts - 1:
                time.sleep(delay)

    if last_exception:
        raise last_exception
    return None



def generate_client_api_url(port: int, token: str) -> str:
    """生成 LCU API 访问地址"""
    return f"{HTTP_SCHEME}://{AUTH_USERNAME}:{token}@{HOST}:{port}"

def generate_client_ws_url(port: int) -> str:
    """生成 LCU WebSocket 地址"""
    return f"{WS_SCHEME}://{HOST}:{port}"

class LolProcessError(Exception):
    """与英雄联盟进程相关的错误"""

class ErrLolProcessNotFound(LolProcessError):
    """当未找到英雄联盟进程时引发的错误"""
    def __init__(self):
        super().__init__("未找到lol进程")


def convert_curr_summoner_to_summoner(curr_summoner: SummonerProfileData) -> Summoner:
    """将 SummonerProfileData 转换为 Summoner 对象"""
    # 从 lol 字典中提取等级信息，并转换为整数
    summoner_level = 0
    if curr_summoner.lol and 'Level' in curr_summoner.lol:
        try:
            summoner_level = int(curr_summoner.lol['Level'])
        except (ValueError, TypeError):
            # 转换失败时使用默认值 0
            pass

    return Summoner(
        account_id=curr_summoner.summoner_id,
        game_name=curr_summoner.game_name,
        tag_line=curr_summoner.game_tag,
        display_name=curr_summoner.name,
        internal_name=curr_summoner.name,
        name_change_flag=False,
        percent_complete_for_next_level=0,
        privacy=None,
        profile_icon_id=curr_summoner.icon,
        puuid=curr_summoner.puuid,
        reroll_points=None,
        summoner_id=curr_summoner.summoner_id,
        summoner_level=summoner_level,
        unnamed=False,
        xp_since_last_level=0,
        xp_until_next_level=0
    )
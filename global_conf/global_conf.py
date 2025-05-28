"""
全局配置模块，对应原Go代码中的global.go
"""

import os
import json
import hashlib
import logging
import threading
import time
import uuid
from typing import Dict, List, Tuple, Callable, Optional, Any, Union
from dataclasses import dataclass, field
from contextlib import contextmanager

# 全局常量
ENV_KEY_MODE = "HH_LOL_PROPHET_MODE"
LOG_WRITER_CLEANUP_KEY = "log_writer"
ZAP_LOGGER_CLEANUP_KEY = "zap_logger"
OTEL_CLEANUP_KEY = "otel"
DEFAULT_TZ = "Asia/Shanghai"


# 模式枚举
class Mode:
    DEBUG = "debug"
    RELEASE = "release"


@dataclass
class HorseScoreConf:
    score: float
    name: str


@dataclass
class RateItemConf:
    limit: float
    score_conf: List[List[float]]


@dataclass
class CalcScoreConf:
    enabled: bool = True
    game_min_duration: int = 900
    allow_queue_id_list: List[int] = field(default_factory=lambda: [430, 420, 450, 440, 1700])
    first_blood: Tuple[float, float] = (10, 5)
    penta_kills: Tuple[float] = (20,)
    quadra_kills: Tuple[float] = (10,)
    triple_kills: Tuple[float] = (5,)
    join_team_rate_rank: Tuple[float, float, float, float] = (10, 5, 5, 10)
    gold_earned_rank: Tuple[float, float, float, float] = (10, 5, 5, 10)
    hurt_rank: Tuple[float, float] = (10, 5)
    money2hurt_rate_rank: Tuple[float, float] = (10, 5)
    vision_score_rank: Tuple[float, float] = (10, 5)
    minions_killed: List[List[float]] = field(default_factory=lambda: [[10, 20], [9, 10], [8, 5]])
    kill_rate: List[RateItemConf] = field(default_factory=lambda: [
        RateItemConf(limit=50, score_conf=[[15, 40], [10, 20], [5, 10]]),
        RateItemConf(limit=40, score_conf=[[15, 20], [10, 10], [5, 5]])
    ])
    hurt_rate: List[RateItemConf] = field(default_factory=lambda: [
        RateItemConf(limit=40, score_conf=[[15, 40], [10, 20], [5, 10]]),
        RateItemConf(limit=30, score_conf=[[15, 20], [10, 10], [5, 5]])
    ])
    assist_rate: List[RateItemConf] = field(default_factory=lambda: [
        RateItemConf(limit=50, score_conf=[[20, 30], [18, 25], [15, 20], [10, 10], [5, 5]]),
        RateItemConf(limit=40, score_conf=[[20, 15], [15, 10], [10, 5], [5, 3]])
    ])
    adjust_kda: Tuple[float, float] = (2, 5)
    horse: List[HorseScoreConf] = field(default_factory=lambda: [
        HorseScoreConf(score=180, name="通天代"),
        HorseScoreConf(score=150, name="小代"),
        HorseScoreConf(score=125, name="上等马"),
        HorseScoreConf(score=105, name="中等马"),
        HorseScoreConf(score=95, name="下等马"),
        HorseScoreConf(score=0.0001, name="牛马")
    ])
    merge_msg: bool = False


@dataclass
class AppConf:
    calc_score: CalcScoreConf = field(default_factory=CalcScoreConf)
    mode: str = Mode.RELEASE
    app_name: str = "hh-lol-prophet"

    class LogConf:
        level: str = "info"

    class OtlpConf:
        endpoint_url: str = ""
        token: str = ""

    class BuffApi:
        url: str = ""
        timeout: int = 10

    log: LogConf = field(default_factory=LogConf)
    otlp: OtlpConf = field(default_factory=OtlpConf)
    buff_api: BuffApi = field(default_factory=BuffApi)


@dataclass
class ClientUserConf:
    AutoAcceptGame: bool = True
    AutoPickChampID: int = 0
    AutoBanChampID: int = 0
    AutoSendTeamHorse: bool = True
    ShouldSendSelfHorse: bool = True
    HorseNameConf: List[str] = field(default_factory=lambda: ["通天代", "小代", "上等马", "中等马", "下等马", "牛马"])
    ChooseSendHorseMsg: List[bool] = field(default_factory=lambda: [True, True, True, True, True, True])
    ChooseChampSendMsgDelaySec: int = 3
    ShouldInGameSaveMsgToClipBoard: bool = True
    ShouldAutoOpenBrowser: Optional[bool] = True


@dataclass
class UserInfo:
    mac_hash: str = ""
    summoner: Any = None


@dataclass
class AppInfo:
    version: str = ""
    commit: str = ""
    build_time: str = ""
    build_user: str = ""


# 全局变量
DEFAULT_CLIENT_USER_CONF = ClientUserConf()
DEFAULT_APP_CONF = AppConf()

user_info = UserInfo()
conf_lock = threading.Lock()
Conf = AppConf()
ClientUserConf = ClientUserConf()
Logger = logging.getLogger("hh-lol-prophet")
Cleanups = {}
AppBuildInfo = AppInfo()

# 数据库连接
SqliteDB = None


def set_user_mac(user_mac_hash: str) -> None:
    """设置用户MAC地址哈希"""
    with conf_lock:
        global user_info
        user_info.mac_hash = user_mac_hash


def set_curr_summoner(summoner: Any) -> None:
    """设置当前召唤师信息"""
    with conf_lock:
        global user_info
        user_info.summoner = summoner


def get_user_info() -> UserInfo:
    """获取用户信息"""
    with conf_lock:
        return user_info


def cleanup() -> None:
    """清理资源"""
    import contextlib

    for name, cleanup_func in Cleanups.items():
        if name == LOG_WRITER_CLEANUP_KEY:
            continue
        with contextlib.suppress(Exception):
            cleanup_func()

    if LOG_WRITER_CLEANUP_KEY in Cleanups:
        with contextlib.suppress(Exception):
            Cleanups[LOG_WRITER_CLEANUP_KEY]()


def is_dev_mode() -> bool:
    """是否为开发模式"""
    return get_env() == Mode.DEBUG


def is_prod_mode() -> bool:
    """是否为生产模式"""
    return not is_dev_mode()


def get_env() -> str:
    """获取当前环境模式"""
    return Conf.mode


def get_env_mode() -> str:
    """获取环境变量中的模式设置"""
    return os.environ.get(ENV_KEY_MODE, "")


def is_env_mode_dev() -> bool:
    """环境变量中是否为开发模式"""
    return get_env_mode() == Mode.DEBUG


def get_score_conf() -> CalcScoreConf:
    """获取评分配置"""
    with conf_lock:
        return Conf.calc_score


def set_score_conf(score_conf: CalcScoreConf) -> None:
    """设置评分配置"""
    with conf_lock:
        Conf.calc_score = score_conf


def get_client_user_conf() -> ClientUserConf:
    """获取客户端用户配置"""
    with conf_lock:
        return ClientUserConf


def set_client_user_conf(cfg: dict) -> ClientUserConf:
    """设置客户端用户配置"""
    with conf_lock:
        global ClientUserConf

        if "AutoAcceptGame" in cfg and cfg["AutoAcceptGame"] is not None:
            ClientUserConf.AutoAcceptGame = cfg["AutoAcceptGame"]

        if "AutoPickChampID" in cfg and cfg["AutoPickChampID"] is not None:
            ClientUserConf.AutoPickChampID = cfg["AutoPickChampID"]

        if "AutoBanChampID" in cfg and cfg["AutoBanChampID"] is not None:
            ClientUserConf.AutoBanChampID = cfg["AutoBanChampID"]

        if "AutoSendTeamHorse" in cfg and cfg["AutoSendTeamHorse"] is not None:
            ClientUserConf.AutoSendTeamHorse = cfg["AutoSendTeamHorse"]

        if "ShouldSendSelfHorse" in cfg and cfg["ShouldSendSelfHorse"] is not None:
            ClientUserConf.ShouldSendSelfHorse = cfg["ShouldSendSelfHorse"]

        if "HorseNameConf" in cfg and cfg["HorseNameConf"] is not None:
            ClientUserConf.HorseNameConf = cfg["HorseNameConf"]

        if "ChooseSendHorseMsg" in cfg and cfg["ChooseSendHorseMsg"] is not None:
            ClientUserConf.ChooseSendHorseMsg = cfg["ChooseSendHorseMsg"]

        if "ChooseChampSendMsgDelaySec" in cfg and cfg["ChooseChampSendMsgDelaySec"] is not None:
            ClientUserConf.ChooseChampSendMsgDelaySec = cfg["ChooseChampSendMsgDelaySec"]

        if "ShouldInGameSaveMsgToClipBoard" in cfg and cfg["ShouldInGameSaveMsgToClipBoard"] is not None:
            ClientUserConf.ShouldInGameSaveMsgToClipBoard = cfg["ShouldInGameSaveMsgToClipBoard"]

        if "ShouldAutoOpenBrowser" in cfg and cfg["ShouldAutoOpenBrowser"] is not None:
            ClientUserConf.ShouldAutoOpenBrowser = cfg["ShouldAutoOpenBrowser"]

        return ClientUserConf


def set_app_info(info: AppInfo) -> None:
    """设置应用信息"""
    global AppBuildInfo
    AppBuildInfo = info


def set_cleanup(name: str, fn: Callable) -> None:
    """设置清理函数"""
    global Cleanups
    Cleanups[name] = fn

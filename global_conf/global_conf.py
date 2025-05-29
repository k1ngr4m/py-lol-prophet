"""
全局配置模块
"""
import contextlib
import os
import json
import hashlib
import logging
import threading
import time
import uuid
from typing import Dict, List, Tuple, Callable, Optional, Any, Union
from dataclasses import dataclass, field
from contextlib import contextmanager, AbstractContextManager
from conf import appConf, client
from services.lcu.models.api import SummonerProfileData
import threading


@dataclass
class AppInfo:
    version: str = ""
    commit: str = ""
    build_time: str = ""
    build_user: str = ""

@dataclass
class UserInfo:
    mac_hash: str = ""
    summoner: SummonerProfileData = None

# 全局常量
ENV_KEY_MODE = "PROPHET_MODE"

ZAP_LOGGER_CLEANUP_KEY = "zap_logger"
LOG_WRITER_CLEANUP_KEY = "log_writer"
OTEL_CLEANUP_KEY = "otel"

cleanups_mu : threading.Lock = threading.Lock()
DEFAULT_SHOULD_AUTO_OPEN_BROWSER_CFG : bool = True
DEFAULT_CLIENT_USER_CONF : client.ClientUserConf = client.ClientUserConf(
    AutoAcceptGame=True,
    AutoPickChampID=0,
    AutoBanChampID=0,
    AutoSendTeamHorse=True,
    ShouldSendSelfHorse=True,
    HorseNameConf=["通天代", "小代", "上等马", "中等马", "下等马", "牛马"],
    ChooseSendHorseMsg=[True, True, True, True, True, True],
    ChooseChampSendMsgDelaySec=3,
    ShouldInGameSaveMsgToClipBoard=True,
    ShouldAutoOpenBrowser=DEFAULT_SHOULD_AUTO_OPEN_BROWSER_CFG
)
DEFAULT_APP_CONF : appConf.AppConf = appConf.AppConf(
    BuffApi=appConf.BuffApi(),
    CalcScore=appConf.CalcScoreConf(
        Enabled=True,
        GameMinDuration=900,
        AllowQueueIDList=[430, 420, 450, 440, 1700],
        FirstBlood=(10, 5),
        PentaKills=(20,),
        QuadraKills=(10,),
        TripleKills=(5,),
        JoinTeamRateRank=(10, 5, 5, 10),
        GoldEarnedRank=(10, 5, 5, 10),
        HurtRank=(10, 5),
        Money2hurtRateRank=(10, 5),
        VisionScoreRank=(10, 5),
        MinionsKilled=[
            (10, 20),
            (9, 10),
            (8, 5),
        ],
        KillRate=[
            appConf.RateItemConf(
                Limit=50,
                ScoreConf=[
                    (15, 40),
                    (10, 20),
                    (5, 10),
                ]
            ),
            appConf.RateItemConf(
                Limit=40,
                ScoreConf=[
                    (15, 20),
                    (10, 10),
                    (5, 5),
                ]
            ),
        ],
        HurtRate=[
            appConf.RateItemConf(
                Limit=40,
                ScoreConf=[
                    (15, 40),
                    (10, 20),
                    (5, 10),
                ]
            ),
            appConf.RateItemConf(
                Limit=30,
                ScoreConf=[
                    (15, 20),
                    (10, 10),
                    (5, 5),
                ]
            ),
        ],
        AssistRate=[
            appConf.RateItemConf(
                Limit=50,
                ScoreConf=[
                    (20, 30),
                    (18, 25),
                    (15, 20),
                    (10, 10),
                    (5, 5),
                ]
            ),
            appConf.RateItemConf(
                Limit=40,
                ScoreConf=[
                    (20, 15),
                    (15, 10),
                    (10, 5),
                    (5, 3),
                ]
            ),
        ],
        AdjustKDA=(2, 5),
        Horse=(
            appConf.HorseScoreConf(Score=180, Name="通天代"),
            appConf.HorseScoreConf(Score=150, Name="小代"),
            appConf.HorseScoreConf(Score=125, Name="上等马"),
            appConf.HorseScoreConf(Score=105, Name="中等马"),
            appConf.HorseScoreConf(Score=95, Name="下等马"),
            appConf.HorseScoreConf(Score=0.0001, Name="牛马"),
        ),
        MergeMsg=False
    )
)

user_info: UserInfo = UserInfo()
conf_mu: threading.Lock = threading.Lock()
Conf: appConf.AppConf = appConf.AppConf(
    BuffApi=appConf.BuffApi(),
    CalcScore=appConf.CalcScoreConf(
        Enabled=True,
        GameMinDuration=900,
        AllowQueueIDList=[430, 420, 450, 440, 1700],
        FirstBlood=(10, 5),
        PentaKills=(20,),
        QuadraKills=(10,),
        TripleKills=(5,),
        JoinTeamRateRank=(10, 5, 5, 10),
        GoldEarnedRank=(10, 5, 5, 10),
        HurtRank=(10, 5),
        Money2hurtRateRank=(10, 5),
        VisionScoreRank=(10, 5),
        MinionsKilled=[
            (10, 20),
            (9, 10),
            (8, 5),
        ],
        KillRate=[
            appConf.RateItemConf(
                Limit=50,
                ScoreConf=[
                    (15, 40),
                    (10, 20),
                    (5, 10),
                ]
            ),
            appConf.RateItemConf(
                Limit=40,
                ScoreConf=[
                    (15, 20),
                    (10, 10),
                    (5, 5),
                ]
            ),
        ],
        HurtRate=[
            appConf.RateItemConf(
                Limit=40,
                ScoreConf=[
                    (15, 40),
                    (10, 20),
                    (5, 10),
                ]
            ),
            appConf.RateItemConf(
                Limit=30,
                ScoreConf=[
                    (15, 20),
                    (10, 10),
                    (5, 5),
                ]
            ),
        ],
        AssistRate=[
            appConf.RateItemConf(
                Limit=50,
                ScoreConf=[
                    (20, 30),
                    (18, 25),
                    (15, 20),
                    (10, 10),
                    (5, 5),
                ]
            ),
            appConf.RateItemConf(
                Limit=40,
                ScoreConf=[
                    (20, 15),
                    (15, 10),
                    (10, 5),
                    (5, 3),
                ]
            ),
        ],
        AdjustKDA=(2, 5),
        Horse=(
            appConf.HorseScoreConf(Score=180, Name="通天代"),
            appConf.HorseScoreConf(Score=150, Name="小代"),
            appConf.HorseScoreConf(Score=125, Name="上等马"),
            appConf.HorseScoreConf(Score=105, Name="中等马"),
            appConf.HorseScoreConf(Score=95, Name="下等马"),
            appConf.HorseScoreConf(Score=0.0001, Name="牛马"),
        ),
        MergeMsg=False
    )
)  # 使用默认构造

ClientUserConf: client.ClientUserConf = client.ClientUserConf()  # 使用默认构造
Logger: Optional[Any] = None  # 类型为zap.SugaredLogger的等效物
Cleanups: Dict[str, Callable[[contextlib.AbstractContextManager], Optional[Exception]]] = {}
AppBuildInfo: AppInfo = AppInfo()

SqliteDB = None


def set_user_mac(user_mac_hash: str) -> None:
    """设置用户MAC地址哈希"""
    with conf_mu:
        global user_info
        user_info.mac_hash = user_mac_hash


def set_curr_summoner(summoner: Any) -> None:
    """设置当前召唤师信息"""
    with conf_mu:
        global user_info
        user_info.summoner = summoner


def get_user_info() -> UserInfo:
    """获取用户信息"""
    with conf_mu:
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
    return get_env() == appConf.Mode.DEBUG


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
    return get_env_mode() == appConf.Mode.DEBUG


def get_score_conf() -> appConf.CalcScoreConf:
    """获取评分配置"""
    with conf_mu:
        return Conf.calc_score


def set_score_conf(score_conf: appConf.CalcScoreConf) -> None:
    """设置评分配置"""
    with conf_mu:
        Conf.calc_score = score_conf


def get_client_user_conf() -> ClientUserConf:
    """获取客户端用户配置"""
    with conf_mu:
        return ClientUserConf


def set_client_user_conf(cfg: dict) -> ClientUserConf:
    """设置客户端用户配置"""
    with conf_mu:
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
    with cleanups_mu:
        global Cleanups
        Cleanups[name] = fn


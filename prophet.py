import threading
import re
import time
from enum import Enum
from typing import Optional, Callable, Any

from option import ApplyOption, WithDebug, WithProd
from services.lcu import common, client
from services.lcu.client import Client
from services.lcu.models.api import SummonerProfileData
from services.lcu import reverse_proxy
from services.lcu.reverse_proxy import RP
from api import Api
import global_conf.global_conf as global_vars
import services.logger.logger as logger


class CancellationContext:
    def __init__(self):
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    @property
    def cancelled(self) -> bool:
        return self._cancelled

class GameState(str, Enum):
    NONE = "none"
    CHAMP_SELECT = "champSelect"
    READY_CHECK = "ReadyCheck"
    IN_GAME = "inGame"
    OTHER = "other"
    MATCHMAKING = "Matchmaking"

class Options:
    def __init__(self,
                 debug: bool = False,
                 enable_pprof: bool = True,
                 http_addr: str = "127.0.0.1:4396"):
        self.debug = debug
        self.enable_pprof = enable_pprof
        self.http_addr = http_addr

default_opts = Options()
allow_origin_regex = re.compile(r".+?\.buffge\.com(:\d+)?$")


# 3. Prophet 对应的 Python 类
class Prophet:
    def __init__(self,
                 ctx: Optional[Any] = None,
                 opts: Optional[Options] = None,
                 http_srv: Optional[Any] = None,
                 lcu_port: int = 0,
                 lcu_token: str = "",
                 lcu_active: bool = False,
                 curr_summoner: Optional[SummonerProfileData] = None,
                 cancel: Optional[Callable[[], None]] = None,
                 api: Optional[Api] = None,
                 lock: Optional[threading.Lock] = None,
                 game_state: GameState = GameState.NONE,
                 lcu_rp: Optional[RP] = None):
        self.ctx = ctx
        self.opts = opts if opts is not None else default_opts
        self.http_srv = http_srv
        self.lcu_port = lcu_port
        self.lcu_token = lcu_token
        self.lcu_active = lcu_active
        self.curr_summoner = curr_summoner
        self.cancel = cancel
        self.api = api
        self.lock = lock if lock is not None else threading.Lock()
        self.game_state = game_state
        self.lcu_rp = lcu_rp

    def is_lcu_active(self) -> bool:
        return self.lcu_active

    def init_lcu_client(self, port: int, token: str):
        client.init_cli(port, token)

    def init_lcu_rp(self, port: int, token: str) -> Optional[Exception]:
        try:
            rp = reverse_proxy.new_rp(port, token)
            self.lcu_rp = rp
            return None
        except Exception as e:
            return e

    def monitor_start(self):
        while True:
            if not self.is_lcu_active():
                try:
                    # 获取 LCU 信息
                    port, token = common.get_lol_client_api_info()
                except Exception as err:
                    # 如果不是 "LOL 未运行" 错误，就打印警告
                    if not isinstance(err, common.ErrLolProcessNotFound):
                        logger.warning("获取 LCU info 失败: %s", err)
                    time.sleep(1)
                    continue

                # 初始化 LCU client
                self.init_lcu_client(port, token)

                # 初始化 RP
                err = self.init_lcu_rp(port, token)
                if err:
                    logger.debug("初始化 LCU RP 失败: %s", err)

                # 初始化游戏流程监控（略去实现）
                try:
                    self.init_game_flow_monitor(port, token)
                except Exception as err:
                    logger.debug("游戏流程监视器 err: %s", err)

                # 清空当前召唤师
                global_vars.set_curr_summoner(None)  # 如果有实现，取消注释
                self.lcu_active = False
                self.curr_summoner = None

            time.sleep(1)

    def init_game_flow_monitor(self, port: int, token: str):
        # 占位方法，你可以稍后补充实现
        pass

def new_prophet(*apply_options: ApplyOption) -> Prophet:
    ctx = CancellationContext()
    cancel = ctx.cancel

    p = Prophet(
        ctx=ctx,
        cancel=cancel,
        lock=threading.Lock(),
        opts=default_opts,
        game_state=GameState.NONE
    )

    if global_vars.is_dev_mode():
        apply_options = (*apply_options, WithDebug())
    else:
        apply_options = (*apply_options, WithProd())

    p.api = Api(p)

    for fn in apply_options:
        fn(p.opts)

    return p


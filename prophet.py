import threading
import re
import time
import base64
import json
import ssl
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import Optional, Callable, Any

import version
from option import ApplyOption, WithDebug, WithProd
from services.lcu import common, client
from services.lcu.models.api import SummonerProfileData, ChampSelectSessionInfo
from services.lcu import reverse_proxy
from services.lcu import api
from services.lcu.api import ChampSelectPatchType, pick_champion, pre_pick_champion, ban_champion
from services.lcu.models.lol import GameFlow as LolGameFlow
from services.lcu.reverse_proxy import RP
from api import Api
import global_conf.global_conf as global_vars
import services.logger.logger as logger
import websocket
from services.lcu.ws import SUBSCRIBE_ALL_EVENT_MSG, ON_JSON_API_EVENT_PREFIX_LEN, WS_EVT_GAME_FLOW_CHANGED, WS_EVT_CHAMP_SELECT_UPDATE_SESSION
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from routes import register_routes
import subprocess
import webbrowser
import asyncio
import signal
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from pyinstrument.middleware import ProfilerMiddleware
from starlette.middleware import Middleware


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
        self.lcu_client = None
        self.curr_summoner = curr_summoner
        self.cancel = cancel
        self.api = api
        self.lock = lock if lock is not None else threading.Lock()
        self.game_state = game_state
        self.lcu_rp = lcu_rp

    # 以下方法需要在 Prophet 中定义或已有：
    def champion_select_start(self):
        pass

    def calc_enemy_team_score(self):
        pass

    def accept_game(self):
        pass

    def is_lcu_active(self) -> bool:
        return self.lcu_active

    def init_lcu_client(self, port: int, token: str):
        self.lcu_client = client.init_cli(port, token)

    def init_lcu_rp(self, port: int, token: str) -> Optional[Exception]:
        try:
            rp = reverse_proxy.new_rp(port, token)
            self.lcu_rp = rp
            return None
        except Exception as e:
            return e

    def monitor_start(self):
        thread_name = threading.current_thread().name
        logger.debug(f"[{thread_name}] 监控线程启动")
        while True:
            if not self.is_lcu_active():
                try:
                    # 获取 LCU 信息
                    port, token = common.get_lol_client_api_info()
                    logger.info(f"[{thread_name}] <UNK>, port: {port}, token: {token}")
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

                # 初始化游戏流程监控
                try:
                    self.init_game_flow_monitor(port, token)
                except Exception as err:
                    logger.debug("游戏流程监视器 err: %s", err)

                # 清空当前召唤师
                global_vars.set_curr_summoner(None)  # 如果有实现，取消注释
                self.lcu_active = False
                self.curr_summoner = None

            time.sleep(1)

    def init_game_flow_monitor(self, port: int, auth_pwd: str) -> Exception or None:
        """
        等价于 Go 的：
            func (p *Prophet) initGameFlowMonitor(port int, authPwd string) error { ... }
        """
        # 1. 构造 WebSocket URL 与 Header（跳过 TLS 校验）
        raw_url = common.generate_client_ws_url(port)  # 需要自行实现
        auth_secret = base64.b64encode(f"{common.AUTH_USERNAME}:{auth_pwd}".encode()).decode()
        headers = {"Authorization": f"Basic {auth_secret}"}

        try:
            # websocket.create_connection 会返回一个 WebSocket 对象
            ws = websocket.create_connection(
                raw_url,
                header=headers,
                sslopt={"cert_reqs": ssl.CERT_NONE}
            )
        except Exception as e:
            return e

        logger.debug(f"connect to lcu {raw_url}")

        # 2. 重试获取当前召唤师信息（最多 5 次，每次间隔 1 秒）
        for attempt in range(5):
            try:
                curr_summoner = api.get_summoner_profile(self.lcu_client)
                self.curr_summoner = curr_summoner
                break
            except Exception:
                time.sleep(1)
        else:
            return Exception("获取当前召唤师信息失败")

        # 3. 将当前召唤师信息写入全局，并标记 LCU 已激活
        global_vars.set_curr_summoner(self.curr_summoner)  # 如果有实现，取消注释
        self.lcu_active = True

        # 4. 订阅所有事件
        try:
            # Go: c.WriteMessage(websocket.TextMessage, lcu.SubscribeAllEventMsg)
            ws.send(SUBSCRIBE_ALL_EVENT_MSG, opcode=websocket.ABNF.OPCODE_TEXT)
        except Exception as e:
            return e

        # 5. 持续读取消息并分发
        while True:
            try:
                message = ws.recv()
            except Exception as e:
                logger.debug("lol事件监控读取消息失败: %s", e)
                return e

            # 只处理文本消息，且长度要大于前缀长度 + 1
            if not isinstance(message, str) or len(message) < ON_JSON_API_EVENT_PREFIX_LEN + 1:
                continue

            # 消息体：去掉前缀和末尾换行符，再做 JSON 解析
            try:
                raw = message[ON_JSON_API_EVENT_PREFIX_LEN : -1]
                msg_obj = json.loads(raw)
            except Exception:
                continue

            uri = msg_obj.get("uri")
            data = msg_obj.get("data")

            # 分发：游戏流程变化
            if uri == WS_EVT_GAME_FLOW_CHANGED:
                try:
                    game_flow = LolGameFlow(data)
                except Exception as e:
                    logger.error("<UNK> LCU <UNK>: %s", e)
                    # 如果结构体解析失败，也可以先忽略
                    continue
                self.on_game_flow_update(game_flow)

            # 分发：抢/选人阶段更新
            elif uri == WS_EVT_CHAMP_SELECT_UPDATE_SESSION:
                try:
                    session_info = ChampSelectSessionInfo()
                except Exception as e:
                    logger.debug("champSelectUpdateSessionEvt 解析结构体失败: %s", e)
                    continue
                # 用一个单独线程去处理此事件，避免阻塞
                threading.Thread(
                    target=lambda: self.on_champ_select_session_update(session_info),
                    daemon=True
                ).start()

            # 其它事件可以按需继续添加 elif 分支

        # （循环退出时会走到这里，但通常不会到达）
        # ws.close()  # 如果需要在某个条件下退出循环并关闭 WebSocket，可放在循环外
        # return None

    def update_game_state(self, new_state):
        """
        用于更新内部的游戏状态字段，并做必要的状态变更逻辑。
        你可以在此处添加一些公共的进入/退出某个状态时的处理。
        """
        self.game_state = new_state
        logger.info(f"GameState updated to {new_state}")

    def on_game_flow_update(self, game_flow):
        """
        等价于 Go 中：
            func (p *Prophet) onGameFlowUpdate(gameFlow models.GameFlow) { ... }
        """
        game_flow = game_flow.value
        logger.info("切换状态: %s", game_flow)


        # 进入英雄选择阶段
        if game_flow == LolGameFlow.CHAMP_SELECT:
            logger.info("进入英雄选择阶段,正在计算用户分数")
            self.update_game_state(GameState.CHAMP_SELECT)
            threading.Thread(target=self.champion_select_start, daemon=True).start()

        # 无状态
        elif game_flow == LolGameFlow.NONE:
            self.update_game_state(GameState.NONE)

        # 匹配中
        elif game_flow == LolGameFlow.MATCHMAKING:
            self.update_game_state(GameState.MATCHMAKING)

        # 游戏进行中
        elif game_flow == LolGameFlow.IN_PROGRESS:
            self.update_game_state(GameState.IN_GAME)
            threading.Thread(target=self.calc_enemy_team_score, daemon=True).start()

        # 等待接受对局
        elif game_flow == LolGameFlow.READY_CHECK:
            self.update_game_state(GameState.READY_CHECK)
            client_cfg = global_vars.get_client_user_conf()  # 按实际路径和函数名修改
            if client_cfg.auto_accept_game:
                threading.Thread(target=self.accept_game, daemon=True).start()

        # 其他任意情况
        else:
            self.update_game_state(GameState.OTHER)

    def on_champ_select_session_update(self, session_info: ChampSelectSessionInfo) -> Optional[Exception]:
        user_pick_action_id = None
        user_ban_action_id = None
        pick_champion_id = 0
        is_self_pick = False
        is_self_ban = False
        pick_is_in_progress = False
        ban_is_in_progress = False

        ally_pre_pick_champion_ids = set()

        if not session_info.actions:
            return None

        for actions in session_info.actions:
            for action in actions:
                if action.is_ally_action and action.type == ChampSelectPatchType.PICK and action.champion_id > 0:
                    ally_pre_pick_champion_ids.add(action.champion_id)

                if action.actor_cell_id != session_info.local_player_cell_id:
                    continue

                if action.type == ChampSelectPatchType.PICK:
                    is_self_pick = True
                    user_pick_action_id = action.id
                    pick_champion_id = action.champion_id
                    pick_is_in_progress = action.is_in_progress
                elif action.type == ChampSelectPatchType.BAN:
                    is_self_ban = True
                    user_ban_action_id = action.id
                    ban_is_in_progress = action.is_in_progress

                break  # 只处理一个匹配的 action（等价于 Go 的 break）

        client_cfg = global_vars.get_client_user_conf()

        if getattr(client_cfg, 'auto_pick_champ_id', 0) > 0 and is_self_pick:
            champ_id = client_cfg.auto_pick_champ_id
            if pick_is_in_progress:
                try:
                    pick_champion(champ_id, user_pick_action_id)
                except Exception as e:
                    logger.warning(f"自动锁定失败: {e}")
                    # elif pick_champion_id == 0:
                try:
                    pre_pick_champion(champ_id, user_pick_action_id)
                except Exception as e:
                    logger.warning(f"预选英雄失败: {e}")

                    if getattr(client_cfg, 'auto_ban_champ_id', 0) > 0 and is_self_ban and ban_is_in_progress:
                        champ_id = client_cfg.auto_ban_champ_id
                    if champ_id not in ally_pre_pick_champion_ids:
                        try:
                            ban_champion(champ_id, user_ban_action_id)
                        except Exception as e:
                            logger.warning(f"自动禁用失败: {e}")

        return None

    def capture_start_message(self):
        logger.info(global_vars.Conf.app_name + "已启动")

    def init_gin(self):
        # 确保 api 已初始化
        if self.api is None:
            raise RuntimeError("Api instance is not initialized")

        # 1. 根据 debug 标志创建 FastAPI 应用
        debug = bool(self.opts.debug)
        app = FastAPI(debug=debug)
        middleware_list = []
        # 2. 如果 enable_pprof 为 True，预留挂载 Profiling 中间件的入口
        if self.opts.enable_pprof:
            try:
                middleware_list.append(
                    Middleware(
                        ProfilerMiddleware,
                        server_timing_header=True,
                        profiler_output_dir="./profiles"
                    )
                )
                logger.info("已启用 PyInstrument 性能分析中间件")
            except ImportError:
                logger.warning("PyInstrument 未安装，请运行 'pip install pyinstrument' 启用性能分析")

        # 3. 配置 CORS
        cors_kwargs = {
            "allow_methods": ["*"],
            "allow_headers": ["*"],
            "expose_headers": ["*"],
            "allow_credentials": True,
            "max_age": 12 * 60 * 60,  # 12 小时，单位为秒
        }

        if global_vars.is_dev_mode():
            cors_kwargs["allow_origins"] = ["*"]
        else:
            cors_kwargs["allow_origin_regex"] = allow_origin_regex.pattern

        app.add_middleware(CORSMiddleware, **cors_kwargs)


        @app.middleware("http")
        async def recovery_and_log(request: Request, call_next):
            try:
                response = await call_next(request)
                return response
            except Exception as exc:
                logger.error("Unhandled exception in request:", exc_info=exc)
                from fastapi.responses import PlainTextResponse
                return PlainTextResponse("Internal Server Error", status_code=500)

        # 5. 注册路由
        register_routes(app, self.api)

        # 6. 创建并保存 Uvicorn 服务器实例（未运行）
        host_str, port_str = self.opts.http_addr.split(":")
        host = host_str.strip()
        port = int(port_str.strip())

        uvicorn_config = uvicorn.Config(
            app,
            host=host,
            port=port,
            log_level="debug" if debug else "info",
        )
        server = uvicorn.Server(uvicorn_config)

        # 7. 将 app 与 server 保存在实例属性中
        self.app = app
        self.http_srv = server

    def init_web_view(self):
        """
        初始化 WebView 界面（在浏览器中打开应用界面）
        """
        try:
            # 获取客户端配置
            client_cfg = global_vars.get_client_user_conf()

            # 获取基础 URL
            index_url = global_vars.Conf.web_view.IndexUrl
            default_url = f"{index_url}?version={version.APP_VERSION}"
            website_url = default_url
                # 检查是否应自动打开浏览器
            should_auto_open = getattr(client_cfg, 'should_auto_open_browser', True)
            if not should_auto_open:
                logger.info(f"自动打开浏览器选项已关闭，手动打开请访问 {website_url}")
                return

            # 尝试使用跨平台方式打开浏览器
            try:
                # 方法1: 使用 Python 内置的 webbrowser 模块
                webbrowser.open(website_url, new=2)
                logger.info(f"界面已在浏览器中打开，若未打开请手动访问 {website_url}")
            except Exception:
                # 方法2: 使用 Windows 命令（兼容原始 Go 代码）
                try:
                    subprocess.run(["cmd", "/c", "start", website_url],
                                  shell=True,
                                  check=True)
                    logger.info(f"界面已在浏览器中打开，若未打开请手动访问 {website_url}")
                except Exception as e:
                    logger.error(f"无法打开浏览器: {e}")
                    logger.info(f"请手动访问: {website_url}")

        except Exception as e:
            logger.error(f"初始化 WebView 时出错: {e}")

    async def notify_quit(self):
        """
        等待程序退出信号，管理服务器生命周期
        """
        # 创建事件循环
        loop = asyncio.get_running_loop()
        interrupt_event = asyncio.Event()

        # # 设置中断信号处理
        # interrupt_event = asyncio.Event()
        # for sig in (signal.SIGINT, signal.SIGTERM):
        #     loop.add_signal_handler(sig, interrupt_event.set)

        # Windows 专用信号处理
        def signal_handler(sig, frame):
            logger.info("收到 Ctrl+C 信号")
            interrupt_event.set()

        signal.signal(signal.SIGINT, signal_handler)

        # 创建线程池用于运行阻塞操作
        with ThreadPoolExecutor(max_workers=2) as executor:
            # 任务1: 运行HTTP服务器
            server_task = loop.run_in_executor(
                executor,
                self.http_srv.run
            )

            # 任务2: 监听中断信号
            async def watch_interrupt():
                await interrupt_event.wait()
                logger.info("收到退出信号，正在关闭服务器...")

                # 调用停止方法
                await self.stop()

                # 关闭服务器
                with suppress(Exception):
                    await self.http_srv.shutdown()

            interrupt_task = asyncio.create_task(watch_interrupt())

            # 任务3: 监听上下文取消
            async def watch_context():
                while not self.ctx.cancelled:
                    await asyncio.sleep(0.1)
                logger.info("上下文已取消，正在关闭服务器...")
                interrupt_event.set()

            context_task = asyncio.create_task(watch_context())

            # 等待所有任务完成
            done, pending = await asyncio.wait(
                [server_task, interrupt_task, context_task],
                return_when=asyncio.FIRST_COMPLETED
            )

            # 取消未完成的任务
            for task in pending:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task

            # 检查是否有错误
            for task in done:
                if task.exception():
                    logger.error(f"任务异常: {task.exception()}")
                    return task.exception()

        return None

    async def stop(self):
        """停止服务，清理资源"""
        logger.info("正在停止服务...")

        # 清理 LCU 连接
        if hasattr(self, 'lcu_ws') and self.lcu_ws:
            with suppress(Exception):
                self.lcu_ws.close()
                self.lcu_ws = None

        # 清理其他资源
        # ...

        # 标记上下文为已取消
        self.ctx.cancel()
        logger.info("服务已停止")

    def run(self):
        # 启动后台线程
        threading.Thread(target=self.monitor_start, name="MonitorThread", daemon=True).start()
        threading.Thread(target=self.capture_start_message, daemon=True).start()

        # 初始化 Web 接口服务
        self.init_gin()

        # 初始化 WebView（界面服务）
        threading.Thread(target=self.init_web_view, daemon=True).start()

        logger.info(
            f"{global_vars.Conf.app_name} 已启动 v{version.APP_VERSION} -- {global_vars.Conf.website_title}"
        )

        return asyncio.run(self.notify_quit())


def new_prophet(*apply_options: ApplyOption) -> Prophet:
    ctx = CancellationContext()
    cancel = ctx.cancel

    # 创建 Prophet 实例
    p = Prophet(
        ctx=ctx,
        cancel=cancel,
        lock=threading.Lock(),
        opts=default_opts,
        game_state=GameState.NONE
    )

    # 设置开发/生产模式
    if global_vars.is_dev_mode():
        apply_options = (*apply_options, WithDebug())
    else:
        apply_options = (*apply_options, WithProd())

    # 应用选项
    for fn in apply_options:
        fn(p.opts)

    # 关键：在返回之前创建并设置 Api 实例
    p.api = Api(p)  # 确保 Api 被正确初始化

    return p


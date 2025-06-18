"""
初始化模块，对应原Go代码中的init.go
"""

import os
import queue
import sys
import json
import logging
import hashlib
import binascii
import threading
import time
import sqlite3
from contextlib import contextmanager
from typing import Dict, Any, Optional

import requests

from dotenv import load_dotenv
import global_conf.global_conf as global_vars
from conf import client
from conf.appConf import AppConf, Mode
from conf.client import valid_client_user_conf
from services.buffApi import update
from services.db.models.config import INIT_LOCAL_CLIENT_SQL, dataclass_json_encoder
from services.lcu import common
from pkg.os.admin.admin import must_run_with_admin
from bootstrap.windows import init_console_adapt
import services.logger.logger as logger
import version as version
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from conf.appConf import GET_REMOTE_CONF_API
from contextlib import contextmanager
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
# from opentelemetry.exporter.otlp.proto.grpc.log_exporter import OTLPLogExporter
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.resources import Resource, ResourceDetector
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION


DEFAULT_TZ = "Asia/Shanghai"
ENV_FILE = ".env"
ENV_LOCAL_FILE = ".env.local"
LOCAL_CONF_FILE = "./config.json"

def init_conf():
    """初始化配置"""
    # 加载环境变量
    load_dotenv(ENV_FILE)
    if os.path.exists(ENV_LOCAL_FILE):
        load_dotenv(ENV_LOCAL_FILE, override=True)

    global_vars.Conf = global_vars.DEFAULT_APP_CONF
    global_vars.ClientUserConf = global_vars.DEFAULT_CLIENT_USER_CONF

    # 设置环境模式
    env_mode = global_vars.is_env_mode_dev()
    if env_mode:
        global_vars.Conf.mode = Mode.DEBUG

    remote_conf_queue = queue.Queue(maxsize=1)

    # 启动远程配置获取线程
    def fetch_remote_config():
        try:
            # 开发模式直接返回 None
            if global_vars.Conf.mode == "debug":
                remote_conf_queue.put(None)
                return

            # 获取远程配置
            remote_conf = get_remote_conf()
            if remote_conf:
                # 保存到本地文件
                with open(LOCAL_CONF_FILE, "w", encoding="utf-8") as f:
                    json.dump(remote_conf.dict(by_alias=True), f, ensure_ascii=False, indent=2)
            remote_conf_queue.put(remote_conf)
        except Exception as e:
            logging.error(f"Error fetching remote config: {str(e)}")
            remote_conf_queue.put(None)

    threading.Thread(target=fetch_remote_config, daemon=True).start()

    # 初始化客户端配置
    try:
        init_client_conf()
    except Exception as e:
        logging.critical(f"本地配置错误, 请删除 {client.SQLITE_DB_PATH} 文件后重启, 错误信息: {str(e)}")
        sys.exit(1)

    # 获取远程配置结果
    remote_conf = remote_conf_queue.get()

    # 处理配置
    if remote_conf is None:
        # 尝试加载本地配置
        if os.path.exists(LOCAL_CONF_FILE):
            try:
                with open(LOCAL_CONF_FILE, "r", encoding="utf-8") as f:
                    local_conf_data = json.load(f)
                    global_vars.Conf = AppConf.parse_obj(local_conf_data)
            except Exception as e:
                logging.error(f"本地配置错误: {str(e)}")
                # 保持默认配置
    else:
        # 使用远程配置
        global_vars.Conf = remote_conf

    # 最终配置验证
    # if not valid_client_user_conf(global_vars.ClientUserConf):
    #     logging.error("客户端配置验证失败，使用默认配置")
    #     global_vars.ClientUserConf = global_vars.DEFAULT_CLIENT_USER_CONF


    # 设置应用信息
    # global_vars.set_app_info(global_vars.AppInfo(
    #     version=version.APP_VERSION,
    #     commit=version.COMMIT,
    #     build_time=version.BUILD_TIME,
    #     build_user=version.BUILD_USER
    # ))


def get_remote_conf():
    """
    从远程服务器获取应用配置

    Args:
        remote_conf_api: 远程配置 API 的 URL

    Returns:
        AppConf: 解析后的应用配置对象

    Raises:
        ValueError: 如果无法解析配置或配置无效
        RequestException: 如果请求失败
    """
    try:
        # 发送 GET 请求，设置 2 秒超时
        response = requests.get(GET_REMOTE_CONF_API, timeout=2)
        response.raise_for_status()  # 检查 HTTP 错误状态码

        # 解析响应为 JSON
        response_data = response.json()

        # 检查响应结构是否符合预期
        if 'code' not in response_data or 'data' not in response_data:
            raise ValueError("Invalid API response structure")

        # 检查 API 返回码（假设 0 表示成功）
        if response_data['code'] != 0:
            raise ValueError(f"API returned non-zero code: {response_data['code']}")

        # 解析嵌套的配置数据
        config_data = response_data['data']

        # 如果 data 是字符串，需要再次解析
        if isinstance(config_data, str):
            try:
                config_data = json.loads(config_data)
            except json.JSONDecodeError:
                raise ValueError("Failed to parse nested JSON in 'data' field")

        # 创建配置对象
        app_conf = AppConf(**config_data)

        # 验证配置是否有效
        if not app_conf.app_name:
            raise ValueError("Invalid configuration: app_name is empty")

        return app_conf

    # except Timeout:
    #     raise RequestException("Request to remote config API timed out")
    # except json.JSONDecodeError as e:
    #     raise ValueError(f"Failed to parse API response JSON: {str(e)}")
    # except RequestException as e:
    #     raise RequestException(f"HTTP request failed: {str(e)}")
    except Exception as e:
        raise e


def init_client_conf():
    """
    初始化客户端配置
    1. 检查 SQLite 数据库文件是否存在
    2. 不存在则创建数据库并初始化默认配置
    3. 存在则从数据库读取配置并验证
    """
    db_path = client.SQLITE_DB_PATH

    # 配置数据库日志
    if global_vars.is_dev_mode():
        db_logger = logging.getLogger('sqlalchemy.engine')
        db_logger.setLevel(logging.INFO)
    else:
        db_logger = logging.getLogger('sqlalchemy.engine')
        db_logger.setLevel(logging.WARNING)

    try:
        # 检查数据库文件是否存在
        if not os.path.exists(db_path):
            # 创建新数据库和配置
            engine = create_engine(f"sqlite:///{db_path}")

            # 创建 config 表
            with engine.connect() as conn:
                # 执行前两条DDL语句
                for stmt in INIT_LOCAL_CLIENT_SQL[:2]:
                    conn.execute(text(stmt))
                conn.commit()

            # 插入默认配置
            # default_conf_json = json.dumps(global_vars.DEFAULT_CLIENT_USER_CONF)
            default_conf_json = json.dumps(
                global_vars.DEFAULT_CLIENT_USER_CONF,
                default=dataclass_json_encoder,  # 使用自定义编码器
                ensure_ascii=False  # 允许非ASCII字符（如中文）
            )
            print(default_conf_json)
            with engine.connect() as conn:
                conn.execute(text("""
                                  INSERT INTO config (k, v)
                                  VALUES (:key, :value)
                                  """), {"key": "localClient", "value": default_conf_json})
                conn.commit()

            # 设置全局配置
            global_vars.CLIENT_USER_CONF = global_vars.DEFAULT_CLIENT_USER_CONF

        else:
            # 打开现有数据库
            engine = create_engine(f"sqlite:///{db_path}")

            # 查询配置
            with engine.connect() as conn:
                result = conn.execute(text("""
                                           SELECT v
                                           FROM config
                                           WHERE k = :key
                                           """), {"key": "localClient"}).fetchone()

                if not result:
                    raise ValueError("Configuration key not found in database")

                # 解析并验证配置
                config_data = json.loads(result[0])
                # if not valid_client_user_conf(config_data):
                #     raise ValueError("Invalid configuration format")

                # 设置全局配置
                global_vars.CLIENT_USER_CONF = config_data

        # 保存数据库引擎到全局
        global_vars.SqliteDB = engine
        return True

    except (SQLAlchemyError, ValueError, json.JSONDecodeError) as e:
        logging.critical(f"Configuration initialization failed: {str(e)}")
        if not os.path.exists(db_path):
            logging.critical("Please try deleting the configuration file and retrying")
        return False

# def init_db() -> Optional[Exception]:
#     """
#     初始化数据库
#
#     Returns:
#         如果发生错误则返回异常，否则返回None
#     """
#     try:
#         # 获取数据库路径
#         app_data_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "hh-lol-prophet")
#         os.makedirs(app_data_dir, exist_ok=True)
#         db_path = os.path.join(app_data_dir, "config.db")
#
#         # 检查数据库文件是否存在
#         if not os.path.exists(db_path):
#             # 创建数据库
#             conn = sqlite3.connect(db_path)
#             cursor = conn.cursor()
#
#             # 创建配置表
#             cursor.execute('''
#             CREATE TABLE IF NOT EXISTS config (
#                 k TEXT PRIMARY KEY,
#                 v TEXT NOT NULL
#             )
#             ''')
#
#             # 插入默认配置
#             client_conf_json = json.dumps(global_vars.DEFAULT_CLIENT_USER_CONF.__dict__)
#             cursor.execute("INSERT INTO config (k, v) VALUES (?, ?)",
#                            ("local_client_conf", client_conf_json))
#
#             conn.commit()
#             conn.close()
#
#             # 使用默认配置
#             global_vars.ClientUserConf = global_vars.DEFAULT_CLIENT_USER_CONF
#         else:
#             # 读取配置
#             conn = sqlite3.connect(db_path)
#             cursor = conn.cursor()
#
#             # 查询配置
#             cursor.execute("SELECT v FROM config WHERE k = ?", ("local_client_conf",))
#             result = cursor.fetchone()
#
#             if result:
#                 # 解析配置
#                 try:
#                     client_conf_dict = json.loads(result[0])
#                     client_conf = global_vars.ClientUserConf
#
#                     # 更新配置
#                     for key, value in client_conf_dict.items():
#                         if hasattr(client_conf, key):
#                             setattr(client_conf, key, value)
#
#                     global_vars.ClientUserConf = client_conf
#                 except json.JSONDecodeError:
#                     return Exception("本地配置解析错误")
#
#             conn.close()
#
#         # 创建数据库连接类
#         class SqliteDB:
#             def __init__(self, db_path):
#                 self.db_path = db_path
#                 self.conn = None
#
#             @contextmanager
#             def connection(self):
#                 conn = sqlite3.connect(self.db_path)
#                 try:
#                     yield conn
#                 finally:
#                     conn.close()
#
#             def execute(self, sql, params=None):
#                 with self.connection() as conn:
#                     cursor = conn.cursor()
#                     if params:
#                         cursor.execute(sql, params)
#                     else:
#                         cursor.execute(sql)
#                     conn.commit()
#                     return cursor
#
#             def query(self, sql, params=None):
#                 with self.connection() as conn:
#                     cursor = conn.cursor()
#                     if params:
#                         cursor.execute(sql, params)
#                     else:
#                         cursor.execute(sql)
#                     return cursor.fetchall()
#
#         # 设置数据库连接
#         global_vars.SqliteDB = SqliteDB(db_path)
#
#         return None
#     except Exception as e:
#         return e


def init_log(app_name: str):
    """
    初始化日志

    Args:
        app_name: 应用名称
    """
    # 获取日志级别
    log_level = logging.DEBUG if global_vars.is_dev_mode() else logging.INFO

    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 创建日志处理器
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # 设置日志记录器
    global_vars.Logger = logging.getLogger(app_name)
    global_vars.Logger.setLevel(log_level)
    global_vars.Logger.addHandler(handler)

    # 如果是生产模式，添加文件处理器
    if global_vars.is_prod_mode():
        # 获取日志文件路径
        log_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "hh-lol-prophet", "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"{app_name}.log")

        # 创建文件处理器
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        global_vars.Logger.addHandler(file_handler)

        # 设置清理函数
        def cleanup_log():
            for handler in global_vars.Logger.handlers:
                handler.close()
                global_vars.Logger.removeHandler(handler)

        global_vars.set_cleanup(global_vars.LOG_WRITER_CLEANUP_KEY, cleanup_log)


def init_user_info():
    """初始化用户信息"""
    # 获取MAC地址
    mac = common.get_mac()

    # 计算MAC地址哈希
    mac_bytes = mac.to_bytes(8, byteorder='little')
    mac_hash = hashlib.sha256(mac_bytes).hexdigest()
    # 设置用户MAC地址哈希
    global_vars.set_user_mac(mac_hash)


def init_api(buff_api_cfg):
    """
    初始化API

    Args:
        buff_api_cfg: API配置
    """
    update.init(buff_api_cfg.Timeout, buff_api_cfg.Timeout)


def init_lib() -> Optional[Exception]:
    """
    初始化库

    Returns:
        如果发生错误则返回异常，否则返回None
    """
    # 设置时区
    os.environ["TZ"] = DEFAULT_TZ

    return None


def init_console():
    """初始化控制台"""
    init_console_adapt()


def init_global():
    """初始化全局设置"""
    # 这里原Go代码中是启动自动重载配置的功能
    # 由于该功能已被废弃，这里不实现
    pass



def new_resource(mode, app_name, user_info):
    # 创建自定义属性
    custom_attributes = {
        ResourceAttributes.SERVICE_NAME: app_name,
        ResourceAttributes.SERVICE_VERSION: version.APP_VERSION,
        "buff.userMac": user_info.mac_hash,
        "buff.commitID": version.COMMIT,
        "buff.mode": mode
    }

    # 合并默认资源和自定义属性
    return Resource.create(custom_attributes).merge(Resource.get_empty())

def init_otel(mode, app_name, log_conf, otlp_cfg, user_info):
    try:
        # 创建资源
        res = new_resource(mode, app_name, user_info)

        # 创建日志提供者
        logger_provider = new_logger_provider(res, log_conf, otlp_cfg)

        # 注册清理函数
        global_vars.set_cleanup("otel_cleanup", lambda: logger_provider.shutdown())

        # 设置全局日志提供者
        set_logger_provider(logger_provider)

        # 初始化日志检测
        LoggingInstrumentor().instrument(
            set_logging_format=True,
            log_level=log_conf.Level
        )

        return None
    except Exception as e:
        return e


def new_logger_provider(resource, log_conf, otlp_cfg):
    # 创建 OTLP 导出器
    exporter = OTLPLogExporter(
        endpoint=otlp_cfg.EndpointUrl,
        insecure=otlp_cfg.Token
    )

    # 创建日志提供者
    logger_provider = LoggerProvider(
        resource=resource,
    )

    # 添加批处理处理器
    logger_provider.add_log_record_processor(
        BatchLogRecordProcessor(exporter)
    )

    return logger_provider


def init_app() -> Optional[Exception]:
    """
    初始化应用

    Returns:
        如果发生错误则返回异常，否则返回None
    """
    try:
        # 检查管理员权限
        must_run_with_admin()

        # 初始化配置
        init_conf()

        # 初始化用户信息
        init_user_info()

        cfg = global_vars.Conf

        # 初始化日志
        init_log(cfg.app_name)

        # 初始化控制台
        init_console()

        # 初始化库
        if err := init_lib():
            return err

        # 初始化API
        init_api(global_vars.Conf.buff_api)

        # 初始化全局设置
        init_global()

        return None
    except Exception as e:
        return e

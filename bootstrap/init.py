"""
初始化模块，对应原Go代码中的init.go
"""

import os
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

import global_conf.global_conf as global_vars
from conf import client
from conf.client import valid_client_user_conf
from services.lcu import common
from pkg.os.admin.admin import must_run_with_admin
from bootstrap.windows import init_console_adapt
import services.logger.logger as logger
import version as version
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError


def init_conf():
    """初始化配置"""
    # 设置默认配置
    global_vars.Conf = global_vars.DEFAULT_APP_CONF
    global_vars.ClientUserConf = global_vars.DEFAULT_CLIENT_USER_CONF

    # 设置环境模式
    env_mode = global_vars.get_env_mode()
    if env_mode:
        global_vars.Conf.mode = env_mode

    # 设置应用信息
    global_vars.set_app_info(global_vars.AppInfo(
        version=version.APP_VERSION,
        commit=version.COMMIT,
        build_time=version.BUILD_TIME,
        build_user=version.BUILD_USER
    ))

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
                conn.execute(text("""
                                  CREATE TABLE config
                                  (
                                      id  INTEGER PRIMARY KEY AUTOINCREMENT,
                                      k   TEXT NOT NULL UNIQUE,
                                      val TEXT NOT NULL
                                  )
                                  """))
                conn.commit()

            # 插入默认配置
            default_conf_json = json.dumps(global_vars.DEFAULT_CLIENT_USER_CONF)
            with engine.connect() as conn:
                conn.execute(text("""
                                  INSERT INTO config (k, val)
                                  VALUES (:key, :value)
                                  """), {"key": "local_client_conf", "value": default_conf_json})
                conn.commit()

            # 设置全局配置
            global_vars.CLIENT_USER_CONF = global_vars.DEFAULT_CLIENT_USER_CONF

        else:
            # 打开现有数据库
            engine = create_engine(f"sqlite:///{db_path}")

            # 查询配置
            with engine.connect() as conn:
                result = conn.execute(text("""
                                           SELECT val
                                           FROM config
                                           WHERE k = :key
                                           """), {"key": "local_client_conf"}).fetchone()

                if not result:
                    raise ValueError("Configuration key not found in database")

                # 解析并验证配置
                config_data = json.loads(result[0])
                if not valid_client_user_conf(config_data):
                    raise ValueError("Invalid configuration format")

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

def init_db() -> Optional[Exception]:
    """
    初始化数据库

    Returns:
        如果发生错误则返回异常，否则返回None
    """
    try:
        # 获取数据库路径
        app_data_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "hh-lol-prophet")
        os.makedirs(app_data_dir, exist_ok=True)
        db_path = os.path.join(app_data_dir, "config.db")

        # 检查数据库文件是否存在
        if not os.path.exists(db_path):
            # 创建数据库
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 创建配置表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS config (
                k TEXT PRIMARY KEY,
                v TEXT NOT NULL
            )
            ''')

            # 插入默认配置
            client_conf_json = json.dumps(global_vars.DEFAULT_CLIENT_USER_CONF.__dict__)
            cursor.execute("INSERT INTO config (k, v) VALUES (?, ?)",
                           ("local_client_conf", client_conf_json))

            conn.commit()
            conn.close()

            # 使用默认配置
            global_vars.ClientUserConf = global_vars.DEFAULT_CLIENT_USER_CONF
        else:
            # 读取配置
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # 查询配置
            cursor.execute("SELECT v FROM config WHERE k = ?", ("local_client_conf",))
            result = cursor.fetchone()

            if result:
                # 解析配置
                try:
                    client_conf_dict = json.loads(result[0])
                    client_conf = global_vars.ClientUserConf

                    # 更新配置
                    for key, value in client_conf_dict.items():
                        if hasattr(client_conf, key):
                            setattr(client_conf, key, value)

                    global_vars.ClientUserConf = client_conf
                except json.JSONDecodeError:
                    return Exception("本地配置解析错误")

            conn.close()

        # 创建数据库连接类
        class SqliteDB:
            def __init__(self, db_path):
                self.db_path = db_path
                self.conn = None

            @contextmanager
            def connection(self):
                conn = sqlite3.connect(self.db_path)
                try:
                    yield conn
                finally:
                    conn.close()

            def execute(self, sql, params=None):
                with self.connection() as conn:
                    cursor = conn.cursor()
                    if params:
                        cursor.execute(sql, params)
                    else:
                        cursor.execute(sql)
                    conn.commit()
                    return cursor

            def query(self, sql, params=None):
                with self.connection() as conn:
                    cursor = conn.cursor()
                    if params:
                        cursor.execute(sql, params)
                    else:
                        cursor.execute(sql)
                    return cursor.fetchall()

        # 设置数据库连接
        global_vars.SqliteDB = SqliteDB(db_path)

        return None
    except Exception as e:
        return e


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
    # 这里需要实现API的初始化
    # 由于原Go代码中的API实现较为复杂，这里先留空
    pass


def init_lib() -> Optional[Exception]:
    """
    初始化库

    Returns:
        如果发生错误则返回异常，否则返回None
    """
    # 设置时区
    os.environ["TZ"] = global_vars.DEFAULT_TZ

    return None


def init_console():
    """初始化控制台"""
    init_console_adapt()


def init_global():
    """初始化全局设置"""
    # 这里原Go代码中是启动自动重载配置的功能
    # 由于该功能已被废弃，这里不实现
    pass


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

        # 初始化日志
        init_log(global_vars.Conf.app_name)

        # 初始化控制台
        init_console()

        # 初始化库
        if err := init_lib():
            return err

        # 初始化API
        init_api(global_vars.Conf.buff_api)

        # 初始化数据库
        if err := init_db():
            return err

        # 初始化全局设置
        init_global()

        return None
    except Exception as e:
        return e

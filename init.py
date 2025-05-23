import os
import json
import logging
import sqlite3
import threading
import hashlib
import struct
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

from global_conf.global_conf import (
    GlobalConf,
    DefaultAppConf,
    DefaultClientUserConf,
    set_cleanup,
    set_user_mac,
    get_user_info
)

DEFAULT_TZ = "Asia/Shanghai"
ENV_FILE = ".env"
ENV_LOCAL_FILE = ".env.local"
LOCAL_CONF_FILE = "config.json"
SQLITE_DB_PATH = "config.db"
REMOTE_CONF_URL = "https://example.com/conf"  # Replace with actual URL

def get_mac():
    return 123456789012345

def get_remote_conf():
    try:
        response = requests.get(REMOTE_CONF_URL, timeout=2)
        if response.status_code != 200:
            return None
        data = response.json()
        if data.get("code") != 0 or not data.get("data"):
            return None
        conf = data["data"]
        if not conf.get("AppName"):
            return None
        return conf
    except Exception as e:
        logging.error(f"获取远程配置失败: {e}")
        return None

def init_conf():
    load_dotenv(ENV_FILE)
    if os.path.exists(ENV_LOCAL_FILE):
        load_dotenv(dotenv_path=ENV_LOCAL_FILE, override=True)

    remote_conf_result = {}

    def load_remote():
        try:
            if os.getenv("ENV_MODE") == "dev":
                remote_conf_result["conf"] = None
            else:
                conf = get_remote_conf()
                if conf:
                    with open(LOCAL_CONF_FILE, "w", encoding="utf-8") as f:
                        json.dump(conf, f)
                remote_conf_result["conf"] = conf
        except Exception:
            remote_conf_result["conf"] = None

    thread = threading.Thread(target=load_remote)
    thread.start()

    GlobalConf.conf = DefaultAppConf.copy()

    if not init_client_conf():
        raise RuntimeError(f"本地配置错误，请删除 {SQLITE_DB_PATH} 文件后重启")

    thread.join()
    remote_conf = remote_conf_result.get("conf")

    if remote_conf:
        GlobalConf.conf = remote_conf
    else:
        if os.path.exists(LOCAL_CONF_FILE):
            with open(LOCAL_CONF_FILE, encoding="utf-8") as f:
                GlobalConf.conf.update(json.load(f))
        else:
            raise RuntimeError("无法加载配置文件")

def init_client_conf():
    try:
        create_new = not os.path.exists(SQLITE_DB_PATH)
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        if create_new:
            cursor.execute("CREATE TABLE IF NOT EXISTS config (k TEXT PRIMARY KEY, v TEXT)")
            value = json.dumps(DefaultClientUserConf)
            cursor.execute("INSERT INTO config (k, v) VALUES (?, ?)", ("client_conf", value))
            conn.commit()
            GlobalConf.client_user_conf = DefaultClientUserConf
        else:
            cursor.execute("SELECT v FROM config WHERE k = ?", ("client_conf",))
            row = cursor.fetchone()
            if not row:
                return False
            conf_data = json.loads(row[0])
            GlobalConf.client_user_conf = conf_data
        GlobalConf.sqlite_db = conn
        return True
    except Exception as e:
        logging.error(f"初始化配置数据库失败: {e}")
        return False

def init_user_info():
    mac_bytes = struct.pack("<Q", get_mac())
    hash_bytes = hashlib.sha256(mac_bytes).digest()
    set_user_mac(hash_bytes.hex())

def init_log(app_name):
    log_level = logging.DEBUG
    logging.basicConfig(
        format='%(asctime)s %(levelname)s %(message)s',
        level=log_level
    )
    if os.getenv("ENV_MODE") == "prod":
        log_file = open("app.log", "a")
        handler = logging.StreamHandler(log_file)
        logging.getLogger().addHandler(handler)
        set_cleanup("log_writer", log_file.close)

def init_app():
    init_conf()
    init_user_info()
    cfg = GlobalConf.conf
    init_log(cfg.get("AppName", "LCU"))
    return True

import logging
from dataclasses import is_dataclass, asdict

from sqlalchemy import Column, Integer, String, create_engine, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
import json
import global_conf.global_conf as global_vars

# 声明基类
Base = declarative_base()

# 常量定义
LOCAL_CLIENT_CONF_KEY = "localClient"
INIT_LOCAL_CLIENT_SQL = [
    # 第一条语句：创建表
    """
    CREATE TABLE config
    (
        id INTEGER     NOT NULL
            CONSTRAINT config_pk
                PRIMARY KEY AUTOINCREMENT,
        k  VARCHAR(32) NOT NULL,
        v  TEXT        NOT NULL
    );
    """,

    # 第二条语句：创建唯一索引
    """
    CREATE UNIQUE INDEX config_k_uindex
        ON config (k);
    """,

    # 第三条语句：插入初始数据（使用参数占位符）
    """
    INSERT INTO config (k, v)
    VALUES (:key, :value);
    """
]

def dataclass_json_encoder(obj):
    """将 dataclass 对象转换为字典"""
    if is_dataclass(obj):
        return asdict(obj)
    # 处理其他不可序列化类型
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
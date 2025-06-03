from dataclasses import is_dataclass, asdict

import global_conf.global_conf as global_vars
import contextvars
from typing import Optional
from sqlalchemy import Column, Integer, String, UniqueConstraint
from sqlalchemy.orm import Session
from sqlalchemy import (
    Column,
    BigInteger,
    String,
    text,
    select,
    update as sqlalchemy_update,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base


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


class Config(Base):
    __tablename__ = 'config'

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column('k', String(32), nullable=False)
    val = Column('v', String, nullable=False)

    __table_args__ = (
        UniqueConstraint('k', name='config_k_uindex'),
    )

    def update(self, key: str, value: str) -> bool:
        """更新配置项"""
        global session
        try:
            # 获取数据库会话
            session = Session(global_vars.SqliteDB)

            # 查询并更新配置
            config = session.query(Config).filter(Config.key == key).first()
            if config:
                config.val = value
            else:
                new_config = Config(key=key, val=value)
                session.add(new_config)

            session.commit()
            return True
        except Exception as e:
            print(f"更新配置失败: {e}")
            return False
        finally:
            session.close()

    @classmethod
    def get_config(cls, key: str) -> Optional['Config']:
        """获取配置项"""
        global session
        try:
            session = Session(global_vars.SqliteDB)
            return session.query(Config).filter(Config.key == key).first()
        except Exception as e:
            print(f"查询配置失败: {e}")
            return None
        finally:
            session.close()


# 初始化数据库表（如果不存在）
def init_db():
    try:
        # 创建所有表
        Base.metadata.create_all(global_vars.SqliteDB)
        print("数据库表初始化完成")
    except Exception as e:
        print(f"数据库初始化失败: {e}")
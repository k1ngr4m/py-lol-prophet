
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
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.sdk.resources import Resource, ResourceDetector
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.sdk.resources import SERVICE_NAME, SERVICE_VERSION
import global_conf.global_conf as global_conf


def main():
    # 注册清理函数
    import atexit
    atexit.register(global_conf.cleanup)

    # 启动检查更新线程
    import threading
    # threading.Thread(target=check_update).start()

    # 创建并运行Prophet
    prophet = new_prophet()
    err = prophet.run()
    if err:
        print(f"运行失败:{err}")
        sys.exit(1)
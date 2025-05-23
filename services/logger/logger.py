"""
日志模块，对应原Go代码中的log.go
"""

import os
import sys
import logging
import logging.handlers
from typing import Optional, TextIO

# 配置日志格式
def setup_logger(name: str, level: int = logging.INFO, 
                log_file: Optional[str] = None, 
                console_output: bool = True) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        log_file: 日志文件路径，如果为None则不记录到文件
        console_output: 是否输出到控制台
        
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 添加文件处理器
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # 添加控制台处理器
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger

class ConcurrentWriter:
    """线程安全的写入器，对应原Go代码中的ConcurrentWriter"""
    
    def __init__(self, writer: TextIO):
        self.writer = writer
        self.closed = False
    
    def write(self, data: str) -> int:
        """写入数据"""
        if self.closed:
            return 0
        return self.writer.write(data)
    
    def flush(self) -> None:
        """刷新缓冲区"""
        if not self.closed:
            self.writer.flush()
    
    def close(self) -> None:
        """关闭写入器"""
        if not self.closed:
            self.writer.flush()
            self.closed = True

# 日志级别映射
def log_level_to_python(level: str) -> int:
    """将字符串日志级别转换为Python日志级别"""
    level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL
    }
    return level_map.get(level.lower(), logging.INFO)

# 日志函数别名，方便从原Go代码迁移
def debug(msg: str, *args, **kwargs) -> None:
    """Debug级别日志"""
    from global_conf.global_conf import Logger
    Logger.debug(msg, *args, **kwargs)

def info(msg: str, *args, **kwargs) -> None:
    """Info级别日志"""
    from global_conf.global_conf import Logger
    Logger.info(msg, *args, **kwargs)

def warning(msg: str, *args, **kwargs) -> None:
    """Warning级别日志"""
    from global_conf.global_conf import Logger
    Logger.warning(msg, *args, **kwargs)

def error(msg: str, *args, **kwargs) -> None:
    """Error级别日志"""
    from global_conf.global_conf import Logger
    Logger.error(msg, *args, **kwargs)

def critical(msg: str, *args, **kwargs) -> None:
    """Critical级别日志"""
    from global_conf.global_conf import Logger
    Logger.critical(msg, *args, **kwargs)

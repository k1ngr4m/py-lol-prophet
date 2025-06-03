from typing import Callable, Optional
from dataclasses import dataclass

# 定义选项应用函数类型
ApplyOption = Callable[['Options'], None]

@dataclass
class Options:
    """配置选项类"""
    debug: bool = False
    enable_pprof: bool = False
    http_addr: str = ""
    # 可以在此添加其他配置字段


def WithEnablePprof(enable_pprof: bool) -> ApplyOption:
    """启用性能分析选项

    :param enable_pprof: 是否启用性能分析
    :return: 应用函数
    """

    def apply(o: Options):
        o.enable_pprof = enable_pprof

    return apply


def WithHttpAddr(http_addr: str) -> ApplyOption:
    """设置HTTP服务器地址选项

    :param http_addr: HTTP服务器地址 (例如 "127.0.0.1:8080")
    :return: 应用函数
    """

    def apply(o: Options):
        o.http_addr = http_addr

    return apply


def WithDebug() -> ApplyOption:
    """启用调试模式选项

    :return: 应用函数
    """

    def apply(o: Options):
        o.debug = True

    return apply


def WithProd() -> ApplyOption:
    """启用生产模式选项

    :return: 应用函数
    """

    def apply(o: Options):
        o.debug = False

    return apply


def WithDebugPprof() -> ApplyOption:
    """组合选项：同时启用调试模式和性能分析

    :return: 应用函数
    """

    def apply(o: Options):
        o.debug = True
        o.enable_pprof = True

    return apply
import time
from typing import Callable, Any


def retry_fetch(func: Callable[..., Any], *args, attempts: int = 5, delay: float = 0.01, logger=None, **kwargs) -> Any:
    """
    通用的重试工具：
    - func: 要调用的函数
    - args, kwargs: 传给 func 的参数
    - attempts: 最多尝试次数
    - delay: 每次失败后 Sleep 多久（秒）
    - logger: 如果传入 logger，在最后一次仍失败时打 debug 日志
    返回：func 的返回值（成功时）；全部 attempts 都失败后返回 None
    """
    for i in range(attempts):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if i < attempts - 1:
                time.sleep(delay)
            else:
                if logger:
                    logger.debug(f"重试 {func.__name__} 仍失败：args={args}, kwargs={kwargs}, error={e}")
    return None
# 全局限流器 (使用tenacity实现)
import threading
import time


class TokenBucketLimiter:
    """
    令牌桶限流器实现 (与Go的rate.Limiter类似)

    参数:
        rate_per_sec: 每秒允许的请求数量
        burst: 桶的容量（最大突发请求数）
    """

    def __init__(self, rate_per_sec: float, burst: int):
        self.rate = rate_per_sec  # 每秒令牌生成速率
        self.capacity = burst  # 桶的最大容量
        self.tokens = burst  # 当前令牌数量
        self.last_refill = time.monotonic()  # 上次填充时间
        self.lock = threading.Lock()  # 线程安全锁

    def wait(self):
        """等待直到获取一个令牌"""
        with self.lock:
            # 计算并添加新生成的令牌
            now = time.monotonic()
            elapsed = now - self.last_refill
            new_tokens = elapsed * self.rate

            if new_tokens > 0:
                self.tokens = min(self.tokens + new_tokens, self.capacity)
                self.last_refill = now

            # 如果桶中有令牌，立即消耗一个
            if self.tokens >= 1:
                self.tokens -= 1
                return

            # 计算需要等待的时间
            deficit = 1 - self.tokens
            wait_time = deficit / self.rate

            # 更新令牌状态
            self.tokens = 0
            self.last_refill = now + wait_time

        # 等待所需的时间
        time.sleep(wait_time)


query_game_summary_limiter = TokenBucketLimiter(rate_per_sec=50.0, burst=50)
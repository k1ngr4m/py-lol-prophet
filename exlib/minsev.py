from opentelemetry.sdk._logs import LogRecordProcessor
from opentelemetry.sdk._logs.export import LogExporter
from opentelemetry._logs import SeverityNumber


class MinSeverityProcessor(LogRecordProcessor):
    """
    最小严重性日志处理器
    对应 Go 的 minsev 处理器

    只记录达到或超过指定严重性级别的日志
    """

    def __init__(self, min_severity: SeverityNumber):
        """
        初始化处理器

        Args:
            min_severity: 最小严重性级别
        """
        self.min_severity = min_severity

    def emit(self, log_record):
        """
        发出日志记录（如果达到最小严重性）
        """
        # 检查日志记录的严重性是否达到或超过最小级别
        if log_record.severity_number >= self.min_severity:
            # 在这里处理或转发日志记录
            # 例如：发送到导出器、控制台等
            # 实际实现会根据您的日志导出配置
            pass
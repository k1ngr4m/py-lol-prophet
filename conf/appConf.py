from enum import Enum
from pydantic import BaseModel, Field, validator
from typing import List, Tuple, Optional, Literal
from exlib.minsev import MinSeverityProcessor as minsev  # 假设有对应的 Python OpenTelemetry 实现
from opentelemetry._logs import SeverityNumber

from pydantic import BaseModel, Field
from typing import List, Tuple, Optional, Literal
import os

# 常量定义
GET_REMOTE_CONF_API = "https://lol.buffge.com/api/v1/getAppConf"

class Mode(str, Enum):
    DEBUG = "debug"
    PROD = "prod"

# 日志级别映射
log_level_map_severity = {
    "trace": SeverityNumber.TRACE,
    "debug": SeverityNumber.DEBUG,
    "info": SeverityNumber.INFO,
    "warn": SeverityNumber.WARN,
    "error": SeverityNumber.ERROR,
    "fatal": SeverityNumber.FATAL,
}

def log_level_to_otel(level_str: str) -> SeverityNumber:
    """将日志级别字符串转换为 OpenTelemetry 严重级别"""
    return log_level_map_severity.get(level_str.lower(), SeverityNumber.INFO)


# 子模型定义
class LogConf(BaseModel):
    Level: str = Field(default="info", json_schema_extra={"env": "logLevel"})


class OtlpConf(BaseModel):
    EndpointUrl: str = Field(default="https://otlp-gateway-prod-ap-southeast-1.grafana.net/otlp")
    Token: str = Field(
        default="ODE5OTIyOmdsY19leUp2SWpvaU16QXdOekkzSWl3aWJpSTZJbk4wWVdOckxUZ3hPVGt5TWkxdmRHeHdMWGR5YVhSbExXOTBiSEF0ZEc5clpXNHRNaUlzSW1zaU9pSTVORVl5TVdsS1pHdG9NVmN3VXpaaE1HczNhakZwYm1jaUxDSnRJanA3SW5JaU9pSndjbTlrTFdGd0xYTnZkWFJvWldGemRDMHhJbjE5")


class BuffApi(BaseModel):
    Url: str = Field(default="https://k2-api.buffge.com:40012/prod/lol", json_schema_extra={"env": "buffApiUrl"})
    Timeout: int = Field(default=5)


class WebViewConf(BaseModel):
    IndexUrl: str = Field(default="https://lol.buffge.com/dev/client")


class RateItemConf(BaseModel):
    Limit: float  # >30%
    ScoreConf: List[Tuple[float, float]]  # [ [最低人头限制,加分数] ]


class HorseScoreConf(BaseModel):
    Score: float
    Name: str


class CalcScoreConf(BaseModel):
    Enabled: bool = Field(default=False)
    GameMinDuration: int = Field(default=900)  # 允许计算战绩的最低游戏时长
    AllowQueueIDList: List[int] = Field(default_factory=list)  # 允许计算战绩的queueID
    FirstBlood: Tuple[float, float]  # [击杀+,助攻+]
    PentaKills: Tuple[float]  # 五杀
    QuadraKills: Tuple[float]  # 四杀
    TripleKills: Tuple[float]  # 三杀
    JoinTeamRateRank: Tuple[float, float, float, float]  # 参团率排名
    GoldEarnedRank: Tuple[float, float, float, float]  # 打钱排名
    HurtRank: Tuple[float, float]  # 伤害排名
    Money2hurtRateRank: Tuple[float, float]  # 金钱转换伤害比排名
    VisionScoreRank: Tuple[float, float]  # 视野得分排名
    MinionsKilled: List[Tuple[float, float]]  # 补兵 [ [补兵数,加分数] ]
    KillRate: List[RateItemConf]  # 人头占比
    HurtRate: List[RateItemConf]  # 伤害占比
    AssistRate: List[RateItemConf]  # 助攻占比
    AdjustKDA: Tuple[float, float]  # kda
    Horse: Tuple[
        HorseScoreConf,
        HorseScoreConf,
        HorseScoreConf,
        HorseScoreConf,
        HorseScoreConf,
        HorseScoreConf
    ]  # 马匹名称
    MergeMsg: bool = Field(default=False)  # 是否合并消息为一条


# 主配置模型
class AppConf(BaseModel):
    Mode: Mode = Field(default="prod", json_schema_extra={"env": "PROPHET_MODE"})
    Log: LogConf = Field(default_factory=LogConf)
    BuffApi: BuffApi()
    CalcScore: CalcScoreConf()
    AppName: str = Field(default="lol对局先知")
    WebsiteTitle: str = Field(default="lol.buffge.com")
    AdaptChatWebsiteTitle: str = Field(default="lol.buffge点康姆")
    ProjectUrl: str = Field(default="github.com/real-web-world/hh-lol-prophet")
    Otlp: OtlpConf = Field(default_factory=OtlpConf)
    WebView: WebViewConf = Field(default_factory=WebViewConf)

    class Config:
        # 允许使用字段名别名
        populate_by_name = True
        # 环境变量前缀
        env_prefix = "PROPHET_"

    @classmethod
    def from_json_file(cls, path: str):
        """从JSON文件加载配置"""
        with open(path, "r", encoding="utf-8") as f:
            return cls.model_validate_json(f.read())
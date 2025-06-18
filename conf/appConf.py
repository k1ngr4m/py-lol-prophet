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
    AllowQueueIDList: List[int] = Field(default=([430, 420, 450, 440, 1700]))  # 允许计算战绩的queueID
    FirstBlood: Tuple[float, float] = Field(default=(10,5)) # [击杀+,助攻+]
    PentaKills: Tuple[float] = Field(default=(20,))
    QuadraKills: Tuple[float] = Field(default=(10,)) # 四杀
    TripleKills: Tuple[float] = Field(default=(5,))  # 三杀
    JoinTeamRateRank: Tuple[float, float, float, float] = Field(default=(10,5,5,10))  # 参团率排名
    GoldEarnedRank: Tuple[float, float, float, float] = Field(default=(10,5,5,10)) # 打钱排名
    HurtRank: Tuple[float, float] = Field(default=(10,5)) # 伤害排名
    Money2hurtRateRank: Tuple[float, float] = Field(default=(10,5)) # 金钱转换伤害比排名
    VisionScoreRank: Tuple[float, float] = Field(default=(10,5))  # 视野得分排名
    MinionsKilled: List[Tuple[float, float]] = Field(default=[
            (10, 20),
            (9, 10),
            (8, 5),
        ]) # 补兵 [ [补兵数,加分数] ]
    KillRate: List[RateItemConf] = Field(default=[RateItemConf(
                Limit=50,
                ScoreConf=[
                    (15, 40),
                    (10, 20),
                    (5, 10),]),RateItemConf(
                Limit=40,
                ScoreConf=[
                    (15, 20),
                    (10, 10),
                    (5, 5),])]) # 人头占比
    HurtRate: List[RateItemConf] = Field(default=[RateItemConf(
                Limit=50,
                ScoreConf=[
                    (15, 40),
                    (10, 20),
                    (5, 10),]),RateItemConf(
                Limit=40,
                ScoreConf=[
                    (15, 20),
                    (10, 10),
                    (5, 5),])]) # 伤害占比
    AssistRate: List[RateItemConf] = Field(default=[RateItemConf(
                Limit=50,
                ScoreConf=[
                    (15, 40),
                    (10, 20),
                    (5, 10),]),RateItemConf(
                Limit=40,
                ScoreConf=[
                    (15, 20),
                    (10, 10),
                    (5, 5),])]) # 助攻占比
    AdjustKDA: Tuple[float, float] =Field(default=(2,5))  # kda
    Horse: Tuple[
        HorseScoreConf,
        HorseScoreConf,
        HorseScoreConf,
        HorseScoreConf,
        HorseScoreConf,
        HorseScoreConf
    ] = Field(default=(HorseScoreConf(Score=180, Name="通天代"),
            HorseScoreConf(Score=150, Name="小代"),
            HorseScoreConf(Score=125, Name="上等马"),
            HorseScoreConf(Score=105, Name="中等马"),
            HorseScoreConf(Score=95, Name="下等马"),
            HorseScoreConf(Score=0.0001, Name="牛马"),)) # 马匹名称
    MergeMsg: bool = Field(default=False)  # 是否合并消息为一条


# 主配置模型
class AppConf(BaseModel):
    mode: Mode = Field(default="prod", json_schema_extra={"env": "PROPHET_MODE"})
    log: LogConf = Field(default_factory=LogConf)
    buff_api: BuffApi = Field(default_factory=BuffApi)
    calc_score: CalcScoreConf = Field(default_factory=CalcScoreConf)
    app_name: str = Field(default="lol对局先知")
    website_title: str = Field(default="lol.buffge.com")
    adapt_Chat_website_title: str = Field(default="lol.buffge点康姆")
    project_url: str = Field(default="github.com/real-web-world/hh-lol-prophet")
    otlp: OtlpConf = Field(default_factory=OtlpConf)
    web_view: WebViewConf = Field(default_factory=WebViewConf)

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
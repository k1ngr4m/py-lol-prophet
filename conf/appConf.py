from enum import Enum
from pydantic import BaseModel, Field, validator
from typing import List, Tuple, Optional, Literal
from exlib.minsev import MinSeverityProcessor as minsev  # 假设有对应的 Python OpenTelemetry 实现
from opentelemetry._logs import SeverityNumber

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

class WebViewConf(BaseModel):
    """WebView 配置"""
    index_url: str = Field(
        "https://lol.buffge.com/dev/client",
        alias="indexUrl",
        description="WebView 首页 URL"
    )

class LogConf(BaseModel):
    """日志配置"""
    level: str = Field(
        "info",
        alias="level",
        description="日志级别 (trace, debug, info, warn, error, fatal)"
    )

class OtlpConf(BaseModel):
    """OpenTelemetry 配置"""
    endpoint_url: str = Field(
        "https://otlp-gateway-prod-ap-southeast-1.grafana.net/otlp",
        alias="endpointUrl",
        description="OTLP 端点 URL"
    )
    token: str = Field(
        "ODE5OTIyOmdsY19leUp2SWpvaU16QXdOekkzSWl3aWJpSTZJbk4wWVdOckxUZ3hPVGt5TWkxdmRHeHdMWGR5YVhSbExXOTBiSEF0ZEc5clpXNHRNaUlzSW1zaU9pSTVORVl5TVdsS1pHdG9NVmN3VXpaaE1HczNhakZwYm1jaUxDSnRJanA3SW5JaU9pSndjbTlrTFdGd0xYTnZkWFJvWldGemRDMHhJbjE5",
        alias="token",
        description="OTLP 认证令牌"
    )

class BuffApi(BaseModel):
    """Buff API 配置"""
    url: str = Field(
        "https://k2-api.buffge.com:40012/prod/lol",
        alias="url",
        description="Buff API 基础 URL"
    )
    timeout: int = Field(
        5,
        alias="timeout",
        description="API 请求超时时间（秒）"
    )

class HorseScoreConf(BaseModel):
    """马匹评分配置"""
    score: float = Field(
        ...,
        alias="score",
        description="马匹分数"
    )
    name: str = Field(
        ...,
        alias="name",
        description="马匹名称"
    )

class RateItemConf(BaseModel):
    """评分项目配置"""
    limit: float = Field(
        ...,
        alias="limit",
        description="评分限制（例如 >30%）"
    )
    score_conf: List[Tuple[float, float]] = Field(
        ...,
        alias="scoreConf",
        description="评分配置 [[最低限制, 加分数]]"
    )

class CalcScoreConf(BaseModel):
    """分数计算配置"""
    enabled: bool = Field(
        False,
        alias="enabled",
        description="是否启用分数计算"
    )
    game_min_duration: int = Field(
        900,
        alias="gameMinDuration",
        description="允许计算战绩的最低游戏时长（秒）"
    )
    allow_queue_id_list: List[int] = Field(
        [],
        alias="allowQueueIDList",
        description="允许计算战绩的队列 ID 列表"
    )
    first_blood: Tuple[float, float] = Field(
        ...,
        alias="firstBlood",
        description="一血评分 [击杀+, 助攻+]"
    )
    penta_kills: Tuple[float] = Field(
        ...,
        alias="pentaKills",
        description="五杀评分"
    )
    quadra_kills: Tuple[float] = Field(
        ...,
        alias="quadraKills",
        description="四杀评分"
    )
    triple_kills: Tuple[float] = Field(
        ...,
        alias="tripleKills",
        description="三杀评分"
    )
    join_team_rate: Tuple[float, float, float, float] = Field(
        ...,
        alias="joinTeamRate",
        description="参团率排名评分"
    )
    gold_earned: Tuple[float, float, float, float] = Field(
        ...,
        alias="goldEarned",
        description="打钱排名评分"
    )
    hurt_rank: Tuple[float, float] = Field(
        ...,
        alias="hurtRank",
        description="伤害排名评分"
    )
    money2hurt_rate_rank: Tuple[float, float] = Field(
        ...,
        alias="money2HurtRateRank",
        description="金钱转换伤害比排名评分"
    )
    vision_score_rank: Tuple[float, float] = Field(
        ...,
        alias="visionScoreRank",
        description="视野得分排名评分"
    )
    minions_killed: List[Tuple[float, float]] = Field(
        ...,
        alias="minionsKilled",
        description="补兵评分 [[补兵数, 加分数]]"
    )
    kill_rate: List[RateItemConf] = Field(
        ...,
        alias="killRate",
        description="人头占比评分配置"
    )
    hurt_rate: List[RateItemConf] = Field(
        ...,
        alias="hurtRate",
        description="伤害占比评分配置"
    )
    assist_rate: List[RateItemConf] = Field(
        ...,
        alias="assistRate",
        description="助攻占比评分配置"
    )
    adjust_kda: Tuple[float, float] = Field(
        ...,
        alias="adjustKDA",
        description="KDA 调整评分"
    )
    horse: Tuple[
        HorseScoreConf, HorseScoreConf, HorseScoreConf,
        HorseScoreConf, HorseScoreConf, HorseScoreConf
    ] = Field(
        ...,
        alias="horse",
        description="马匹评分配置（固定6个）"
    )
    merge_msg: bool = Field(
        False,
        alias="mergeMsg",
        description="是否合并消息为一条"
    )

class AppConf(BaseModel):
    """应用主配置"""
    mode: Mode = Field(
        Mode.PROD,
        alias="mode",
        description="运行模式 (debug/prod)"
    )
    log: LogConf = Field(
        ...,
        alias="log",
        description="日志配置"
    )
    buff_api: BuffApi = Field(
        ...,
        alias="buffApi",
        description="Buff API 配置"
    )
    calc_score: CalcScoreConf = Field(
        ...,
        alias="calcScore",
        description="分数计算配置"
    )
    app_name: str = Field(
        "lol对局先知",
        alias="appName",
        description="应用名称"
    )
    website_title: str = Field(
        "lol.buffge.com",
        alias="websiteTitle",
        description="网站标题"
    )
    adapt_chat_website_title: str = Field(
        "lol.buffge点康姆",
        alias="adaptChatWebsiteTitle",
        description="适配聊天窗口的网站标题"
    )
    project_url: str = Field(
        "github.com/real-web-world/hh-lol-prophet",
        alias="projectUrl",
        description="项目 URL"
    )
    otlp: OtlpConf = Field(
        ...,
        alias="otlp",
        description="OpenTelemetry 配置"
    )
    web_view: WebViewConf = Field(
        ...,
        alias="webView",
        description="WebView 配置"
    )

    # 自定义验证器示例
    @validator("app_name")
    def app_name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("App name cannot be empty")
        return v

# # 默认配置实例（可选）
# DEFAULT_APP_CONF = AppConf(
#     log=LogConf(),
#     buff_api=BuffApi(),
#     calc_score=CalcScoreConf(
#         first_blood=(0, 0),
#         penta_kills=(0,),
#         quadra_kills=(0,),
#         triple_kills=(0,),
#         join_team_rate=(0, 0, 0, 0),
#         gold_earned=(0, 0, 0, 0),
#         hurt_rank=(0, 0),
#         money2hurt_rate_rank=(0, 0),
#         vision_score_rank=(0, 0),
#         minions_killed=[],
#         kill_rate=[],
#         hurt_rate=[],
#         assist_rate=[],
#         adjust_kda=(0, 0),
#         horse=(
#             HorseScoreConf(score=0, name=""),
#             HorseScoreConf(score=0, name=""),
#             HorseScoreConf(score=0, name=""),
#             HorseScoreConf(score=0, name=""),
#             HorseScoreConf(score=0, name=""),
#             HorseScoreConf(score=0, name=""),
#         )
#     ),
#     otlp=OtlpConf(),
#     web_view=WebViewConf()
# )
import logging
from dataclasses import field

SQLITE_DB_PATH = "./prophet.db"

from pydantic import BaseModel, validator, conlist
from typing import Optional, List
import json

class ClientUserConf(BaseModel):
    AutoAcceptGame: bool = True
    AutoPickChampID: int = 0
    AutoBanChampID: int = 0
    AutoSendTeamHorse: bool = True
    ShouldSendSelfHorse: bool = True
    HorseNameConf: List[str] = field(default_factory=lambda: ["通天代", "小代", "上等马", "中等马", "下等马", "牛马"])
    ChooseSendHorseMsg: List[bool] = field(default_factory=lambda: [True, True, True, True, True, True])
    ChooseChampSendMsgDelaySec: int = 3
    ShouldInGameSaveMsgToClipBoard: bool = True
    ShouldAutoOpenBrowser: Optional[bool] = True

    @validator('HorseNameConf', each_item=True)
    def check_horse_name_not_empty(cls, v):
        """验证马匹名称不为空"""
        if not v.strip():
            raise ValueError("Horse name cannot be empty")
        return v


class UpdateClientUserConfReq(BaseModel):
    """
    更新客户端配置请求模型
    对应 Go 的 UpdateClientUserConfReq 结构
    """
    AutoAcceptGame: Optional[bool] = None
    AutoPickChampID: Optional[int] = None
    AutoBanChampID: Optional[int] = None
    AutoSendTeamHorse: Optional[bool] = None
    ShouldSendSelfHorse: Optional[bool] = None
    HorseNameConf: Optional[conlist(str)] = None
    ChooseSendHorseMsg: Optional[conlist(bool)] = None
    ChooseChampSendMsgDelaySec: Optional[int] = None
    ShouldInGameSaveMsgToClipBoard: Optional[bool] = None
    ShouldAutoOpenBrowser: Optional[bool] = None


class BadConfigError(Exception):
    pass


def valid_client_user_conf(conf: "ClientUserConf") -> None:
    for name in conf.conf:
        if not name.strip():
            raise BadConfigError("错误的配置")


# 默认配置实例
DEFAULT_CLIENT_CONF = ClientUserConf()

# 使用示例
if __name__ == "__main__":
    # 创建默认配置
    default_conf = ClientUserConf()
    print("Default Config:", default_conf.json(indent=2))

    # 验证配置
    print("Is valid:", valid_client_user_conf(default_conf))

    # 测试无效配置
    invalid_conf = ClientUserConf(
        HorseNameConf=["", "Valid", "Names", "Here", "But", "FirstEmpty"]
    )
    print("Is invalid valid?", valid_client_user_conf(invalid_conf))  # 应该返回 False

    # 更新配置请求
    update_req = UpdateClientUserConfReq(
        AutoAcceptGame=True,
        ChooseChampSendMsgDelaySec=5
    )
    print("Update Request:", update_req.json(indent=2))

    # 应用更新
    updated_conf = default_conf.copy(update=update_req.dict(exclude_unset=True))
    print("Updated Config:", updated_conf.json(indent=2))
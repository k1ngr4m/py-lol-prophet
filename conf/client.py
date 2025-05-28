import logging

SQLITE_DB_PATH = "prophet.db"

from pydantic import BaseModel, validator, conlist
from typing import Optional, List
import json

class ClientUserConf(BaseModel):
    """
    客户端用户配置模型
    对应 Go 的 ClientUserConf 结构
    """
    auto_accept_game: bool = False
    auto_pick_champ_id: int = 0
    auto_ban_champ_id: int = 0
    auto_send_team_horse: bool = False
    should_send_self_horse: bool = False
    horse_name_conf: conlist(str, min_items=6, max_items=6) = ["马匹1", "马匹2", "马匹3", "马匹4", "马匹5", "马匹6"]
    choose_send_horse_msg: conlist(bool, min_items=6, max_items=6) = [True, True, True, True, True, True]
    choose_champ_send_msg_delay_sec: int = 0
    should_in_game_save_msg_to_clip_board: bool = False
    should_auto_open_browser: Optional[bool] = None

    @validator('horse_name_conf', each_item=True)
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
    auto_accept_game: Optional[bool] = None
    auto_pick_champ_id: Optional[int] = None
    auto_ban_champ_id: Optional[int] = None
    auto_send_team_horse: Optional[bool] = None
    should_send_self_horse: Optional[bool] = None
    horse_name_conf: Optional[conlist(str, min_items=6, max_items=6)] = None
    choose_send_horse_msg: Optional[conlist(bool, min_items=6, max_items=6)] = None
    choose_champ_send_msg_delay_sec: Optional[int] = None
    should_in_game_save_msg_to_clip_board: Optional[bool] = None
    should_auto_open_browser: Optional[bool] = None



def valid_client_user_conf(conf: ClientUserConf) -> bool:
    """
    验证客户端配置是否有效
    对应 Go 的 ValidClientUserConf 函数

    Args:
        conf: ClientUserConf 实例

    Returns:
        bool: 配置是否有效
    """
    try:
        # 使用 Pydantic 验证
        conf.validate(conf.dict())
        return True
    except Exception as e:
        logging.error(f"Invalid configuration: {str(e)}")
        return False


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
        horse_name_conf=["", "Valid", "Names", "Here", "But", "FirstEmpty"]
    )
    print("Is invalid valid?", valid_client_user_conf(invalid_conf))  # 应该返回 False

    # 更新配置请求
    update_req = UpdateClientUserConfReq(
        auto_accept_game=True,
        choose_champ_send_msg_delay_sec=5
    )
    print("Update Request:", update_req.json(indent=2))

    # 应用更新
    updated_conf = default_conf.copy(update=update_req.dict(exclude_unset=True))
    print("Updated Config:", updated_conf.json(indent=2))
from typing import Optional
import services.logger.logger as logger
from services.lcu.client import Client

def get_summoner_profile():
    pass


# 消息类型
JOINED_ROOM_MSG = "joined_room"

# 会话消息类型
class ConversationMsgType:
    SYSTEM = "system"

# 选人阶段动作类型
class ChampSelectPatchType:
    PICK = "pick"
    BAN = "ban"

# 在线状态
class Availability:
    OFFLINE = "offline"  # 离线

def champ_select_patch_action(
    champion_id: int,
    action_id: int,
    patch_type: Optional[str] = None,
    completed: Optional[bool] = None
) -> Optional[Exception]:
    """
    向 LCU 发送 PATCH 请求以修改当前选人/禁用状态。
    """
    payload = {
        "championId": champion_id,
    }
    if patch_type is not None:
        payload["type"] = patch_type
    if completed is not None:
        payload["completed"] = completed

    try:
        Client.http_patch(f"/lol-champ-select/v1/session/actions/{action_id}", payload)
        return None
    except Exception as e:
        logger.warning(f"champ_select_patch_action failed: {e}")
        return e


def pre_pick_champion(champion_id: int, action_id: int) -> Optional[Exception]:
    """
    预选英雄（不需要设置 type/completed）
    """
    return champ_select_patch_action(champion_id, action_id)


def pick_champion(champion_id: int, action_id: int) -> Optional[Exception]:
    """
    锁定英雄，需设置 type 和 completed
    """
    return champ_select_patch_action(
        champion_id,
        action_id,
        patch_type=ChampSelectPatchType.PICK,
        completed=True
    )


def ban_champion(champion_id: int, action_id: int) -> Optional[Exception]:
    """
    禁用英雄，需设置 type 和 completed
    """
    return champ_select_patch_action(
        champion_id,
        action_id,
        patch_type=ChampSelectPatchType.BAN,
        completed=True
    )
import json
import urllib
from typing import Optional
import services.logger.logger as logger
from services.lcu.client import Client
from services.lcu.models.api import Summoner
import requests
import os

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


def query_summoner_by_name(name: str, client: Client) -> Optional[Summoner]:
    """
    通过召唤师名称查询用户信息

    Args:
        name: 召唤师名称
        client: 已初始化的 Client 实例

    Returns:
        Summoner 对象或 None（如果查询失败）
    """
    try:
        # 编码查询参数
        encoded_name = urllib.parse.quote(name)
        url = f"/lol-summoner/v1/summoners?name={encoded_name}"

        # 发送 HTTP GET 请求
        response_data = client.http_get(url)
        if not response_data:
            logger.error(f"搜索用户失败: 空响应")
            return None

        # 解析 JSON 响应
        summoner_data = json.loads(response_data)

        # 检查错误响应
        if "errorCode" in summoner_data and summoner_data["errorCode"]:
            error_msg = summoner_data.get("message", "未知错误")
            logger.error(f"搜索用户失败: {error_msg}")
            return None

        # 转换为 Summoner 对象
        return Summoner(
            account_id=summoner_data.get("accountId"),
            game_name=summoner_data.get("gameName"),
            tag_line=summoner_data.get("tagLine"),
            display_name=summoner_data.get("displayName"),
            internal_name=summoner_data.get("internalName"),
            name_change_flag=summoner_data.get("nameChangeFlag", False),
            percent_complete_for_next_level=summoner_data.get("percentCompleteForNextLevel", 0),
            privacy=summoner_data.get("privacy"),
            profile_icon_id=summoner_data.get("profileIconId"),
            puuid=summoner_data.get("puuid"),
            reroll_points=summoner_data.get("rerollPoints"),
            summoner_id=summoner_data.get("summonerId"),
            summoner_level=summoner_data.get("summonerLevel", 0),
            unnamed=summoner_data.get("unnamed", False),
            xp_since_last_level=summoner_data.get("xpSinceLastLevel", 0),
            xp_until_next_level=summoner_data.get("xpUntilNextLevel", 0)
        )

    except json.JSONDecodeError as e:
        logger.error(f"解析用户信息失败: {e}")
        return None
    except Exception as e:
        logger.error(f"搜索用户时发生未知错误: {e}", exc_info=True)
        return None
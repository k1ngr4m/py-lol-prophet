import json
import string
import threading
import time
import urllib
from typing import Optional, Any
import services.logger.logger as logger
from exlib.token_bucket import TokenBucketLimiter
# from exlib.token_bucket import query_game_summary_limiter
from services.lcu.client import Client, cli
from services.lcu.models.api import Summoner, GameSummary, CurrSummoner, GameListResp, SummonerProfileData, \
    UpdateSummonerProfileData
import requests
import os
import json
from typing import Optional
from tenacity import retry, wait_fixed, stop_after_attempt
from urllib.parse import urlencode

# 消息类型
JOINED_ROOM_MSG = "joined_room"

query_game_summary_limiter = TokenBucketLimiter(rate_per_sec=50.0, burst=50)

def get_curr_summoner() -> Optional[CurrSummoner]:
    pass

def list_games_by_summonerID(summonerID: int, begin, limit: int) -> Optional[GameListResp]:
    pass






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
        cli.http_patch(f"/lol-champ-select/v1/session/actions/{action_id}", payload)
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

def list_games_by_puuid(puuid: str, begin: int, limit: int, client: Client) -> Optional[dict]:
    """
    获取指定PUUID的比赛记录

    Args:
        puuid: 玩家唯一标识符
        begin: 起始索引
        limit: 获取数量
        client: client

    Returns:
        GameListResp格式的字典，或None(失败时)
    """
    # 构建查询参数
    params = {
        'begIndex': begin,
        'endIndex': begin + limit
    }
    query_str = urlencode(params)

    # 构建URL
    path = f"/lol-match-history/v1/products/lol/{puuid}/matches?{query_str}"

    try:
        # 发送HTTP GET请求
        response = client.http_get(path)

        data = response.decode('utf-8')
        json_data = json.loads(data)

        return json_data

    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: puuid={puuid}, error={str(e)}")
        return None
    except Exception as e:
        logger.error(f"获取比赛记录异常: puuid={puuid}, error={str(e)}")
        return None



@retry(wait=wait_fixed(0.01), stop=stop_after_attempt(5))
def query_game_summary(game_id: int, client: Client) -> Optional[Any]:
    """查询对局详情信息"""
    try:
        # 等待限流器 (如果有)
        if query_game_summary_limiter:
            query_game_summary_limiter.wait()

        # 发送API请求
        url = f"/lol-match-history/v1/games/{game_id}"
        response = client.http_get(url)
        data = response.decode('utf-8')
        json_data = json.loads(data)

        # 转换为模型对象
        return GameSummary.from_dict(json_data)

    except json.JSONDecodeError as e:
        logger.debug(f"JSON解析失败: game_id={game_id}, error={str(e)}")
        return None
    except Exception as e:
        logger.debug(f"查询对局详情异常: game_id={game_id}, error={str(e)}")
        return None


# 更新玩家信息
def update_summoner_profile(
        client: Client,
        update_data: UpdateSummonerProfileData
) -> SummonerProfileData:
    try:
        url = f"/lol-chat/v1/me"

        response = client._req("PUT", "/lol-chat/v1/me", update_data.__dict__)
        data = response.decode('utf-8')
        json_data = json.loads(data)
        profile_data = SummonerProfileData(**json_data)

        # 检查错误响应
        if profile_data.code != 0:
            raise Exception(f"更新用户信息请求失败: {profile_data.msg}")

        return profile_data
    except Exception as e:
        print(f"更新用户信息失败: {e}")
        raise

# 获取玩家简介信息
def get_summoner_profile(client: Client) -> SummonerProfileData:
    data = UpdateSummonerProfileData()
    return update_summoner_profile(client, data)
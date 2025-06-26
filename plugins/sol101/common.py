import concurrent.futures
import threading
import time
from datetime import datetime, timedelta
from typing import List, Tuple, Any, Optional, Union

from exlib.common import retry_fetch
from services.lcu.api import list_games_by_puuid, query_game_summary
from services.lcu.client import Client
from services.lcu.game_score import UserScore, ScoreWithReason, ScoreOption, new_score_with_reason
import services.logger.logger as logger
import global_conf.global_conf as global_vars
from services.lcu.models.api import GameSummary, Participant
from typing import Dict, List, Optional, Tuple

from services.lcu.models.lol import Lane, ChampionRole

def get_user_game_history_list(summoner: Any, client: Client):
    """根据召唤师信息计算用户游戏得分"""
    # 1. 初始化用户得分对象
    summoner_id = summoner.summoner_id
    summoner_name = f"{summoner.game_name}#{summoner.tag_line}"

    # 2. 获取战绩列表
    try:
        game_list = list_game_history(summoner.puuid, client)
    except Exception as e:
        logger.error(f"获取用户战绩失败: summoner_id={summoner_id}, error={str(e)}")
        return 0
    return game_list

def list_game_history(puuid: str, client: Client) -> List[Any]:
    """获取用户战绩列表并过滤"""
    # 获取全局配置
    score_cfg = global_vars.get_score_conf()
    limit = 10

    # 调用API获取战绩列表
    try:
        resp = list_games_by_puuid(puuid, 0, limit, client)
    except Exception as e:
        logger.error(f"查询用户战绩失败: puuid={puuid}, error={str(e)}")
        return []

    # 暂时不用过滤
    # # 准备过滤条件
    # allow_queue_ids = set(score_cfg.AllowQueueIDList)
    # min_duration = score_cfg.GameMinDuration
    #
    # # 过滤符合条件的对局
    filtered_games = []
    # # for game_item in resp.games.games:
    for game_item in resp['games']['games']:
    #     queue_id = int(game_item['queueId'])
    #     game_duration = game_item['gameDuration']
    #
    #     # 检查队列ID和游戏时长
    #     if queue_id not in allow_queue_ids:
    #         continue
    #     if game_duration < min_duration:
    #         continue
    #
        filtered_games.append(game_item)
    #
    # # 反转列表使对局按时间从旧到新排序
    filtered_games.reverse()

    return filtered_games



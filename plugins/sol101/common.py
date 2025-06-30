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


def get_user_game_history_list(summoner: Any, client: Client, begin: int = 0, limit: int = 10):
    """根据召唤师信息获取用户游戏历史(支持分页)"""
    summoner_id = summoner.summoner_id
    summoner_name = f"{summoner.game_name}#{summoner.tag_line}"

    try:
        game_list = list_game_history(summoner.puuid, begin, limit, client)
    except Exception as e:
        logger.error(f"获取用户战绩失败: summoner_id={summoner_id}, error={str(e)}")
        return []
    return game_list

def list_game_history(puuid: str, begin: int, limit: int, client: Client) -> List[Any]:
    """获取用户战绩列表(支持分页)"""
    try:
        resp = list_games_by_puuid(puuid, begin, limit, client)
        if not resp:
            return []
        return resp['games']['games']
    except Exception as e:
        logger.error(f"查询用户战绩失败: puuid={puuid}, error={str(e)}")
        return []


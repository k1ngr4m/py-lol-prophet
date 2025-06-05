import concurrent.futures
import threading
import time
from datetime import datetime, timedelta
from typing import List, Tuple, Any, Optional, Union

from services.lcu.api import list_games_by_puuid, query_game_summary
from services.lcu.client import Client
from services.lcu.game_score import UserScore, ScoreWithReason, ScoreOption, new_score_with_reason
import services.logger.logger as logger
import global_conf.global_conf as global_vars
from services.lcu.models.api import GameSummary, Participant
from typing import Dict, List, Optional, Tuple

from services.lcu.models.lol import Lane, ChampionRole

# 假设的默认分数
DEFAULT_SCORE = 100.0


def get_user_score(summoner: Any, client: Client) -> UserScore:
    """根据召唤师信息计算用户游戏得分"""
    # 1. 初始化用户得分对象
    summoner_id = summoner.summoner_id
    summoner_name = f"{summoner.game_name}#{summoner.tag_line}"
    user_score = UserScore(
        summoner_id=summoner_id,
        summoner_name=summoner_name,
        score=DEFAULT_SCORE,
        curr_kda=[]
    )

    # 2. 获取战绩列表
    try:
        game_list = list_game_history(summoner.puuid, client)
    except Exception as e:
        logger.error(f"获取用户战绩失败: summoner_id={summoner_id}, error={str(e)}")
        return user_score

    # 3. 构建KDA列表（从旧到新）
    curr_kda_list = [None] * len(game_list)
    for i, game_info in enumerate(game_list):
        idx = len(game_list) - 1 - i  # 逆序存储
        participant = game_info['participants'][0]
        curr_kda_list[idx] = (
            participant['stats']['kills'],
            participant['stats']['deaths'],
            participant['stats']['assists']
        )
    user_score.curr_kda = curr_kda_list

    # 4. 并发获取对局详情
    game_summaries = []
    lock = threading.Lock()

    def fetch_game_summary(game_info):
        for attempt in range(5):
            try:
                return query_game_summary(game_info['gameId'], client)
            except Exception as e:
                time.sleep(0.01)  # 10ms延迟重试
        logger.debug(f"获取游戏详情失败: game_id={game_info['gameId']}")
        return None

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetch_game_summary, game_info) for game_info in game_list]
        for future in concurrent.futures.as_completed(futures):
            game_summary = future.result()
            if game_summary:
                with lock:
                    game_summaries.append(game_summary)

    # 5. 计算每局得分并分类
    now_time = datetime.now()
    curr_time_scores = []
    other_scores = []

    for summary in game_summaries:
        try:
            score_value = calc_user_game_score(summoner_id, summary)
        except Exception as e:
            print(e)
            logger.debug(f"计算得分失败: game_id={summary['gameId']}, error={str(e)}")
            return user_score  # 遇到错误直接返回默认分数

        # 判断是否在5小时内的对局
        game_time = summary.game_creation_date
        if now_time - game_time < timedelta(hours=5):
            curr_time_scores.append(score_value[0].score)
        else:
            other_scores.append(score_value[0].score)

    # 6. 计算加权得分
    total_games = len(game_summaries)
    if total_games == 0:
        return user_score  # 无对局保持默认分

    # 计算各部分平均分
    total_avg = sum(curr_time_scores + other_scores) / total_games
    curr_avg = sum(curr_time_scores) / len(curr_time_scores) if curr_time_scores else total_avg
    other_avg = sum(other_scores) / len(other_scores) if other_scores else total_avg

    # 应用权重计算最终得分 (近期80% + 历史20%)
    weighted_score = 0.8 * curr_avg + 0.2 * other_avg
    user_score.score = weighted_score

    return user_score


def list_game_history(puuid: str, client: Client) -> List[Any]:
    """获取用户战绩列表并过滤"""
    # 获取全局配置
    score_cfg = global_vars.get_score_conf()
    limit = 50

    # 调用API获取战绩列表
    try:
        resp = list_games_by_puuid(puuid, 0, limit, client)
    except Exception as e:
        logger.error(f"查询用户战绩失败: puuid={puuid}, error={str(e)}")
        return []

    # 准备过滤条件
    allow_queue_ids = set(score_cfg.AllowQueueIDList)
    min_duration = score_cfg.GameMinDuration

    # 过滤符合条件的对局
    filtered_games = []
    # for game_item in resp.games.games:
    for game_item in resp['games']['games']:
        queue_id = int(game_item['queueId'])
        game_duration = game_item['gameDuration']

        # 检查队列ID和游戏时长
        if queue_id not in allow_queue_ids:
            continue
        if game_duration < min_duration:
            continue

        filtered_games.append(game_item)

    # 反转列表使对局按时间从旧到新排序
    filtered_games.reverse()

    return filtered_games


def calc_user_game_score(summoner_id: int, game_summary: 'GameSummary') -> Union[
    Tuple[None, Exception], Tuple[ScoreWithReason, None]]:
    calc_score_conf = global_vars.get_score_conf()
    game_score = new_score_with_reason(DEFAULT_SCORE)

    # 查找用户参与者ID
    user_participant_id = 0
    for identity in game_summary.participant_identities:
        if identity.player.summoner_id == summoner_id:
            user_participant_id = identity.participant_id
            break

    if user_participant_id == 0:
        return None, Exception("获取用户位置失败")

    # 识别用户队伍并映射参与者
    user_team_id = None
    member_participant_ids = []
    id_to_participant: Dict[int, 'Participant'] = {}

    for participant in game_summary.participants:
        id_to_participant[participant.participant_id] = participant
        if participant.participant_id == user_participant_id:
            user_team_id = participant.team_id

    if user_team_id is None:
        return None, Exception("获取用户队伍id失败")

    for participant in game_summary.participants:
        if participant.team_id == user_team_id:
            member_participant_ids.append(participant.participant_id)

    # 计算队伍总数据
    total_kill = 0
    total_death = 0
    total_assist = 0
    total_hurt = 0
    total_money = 0

    for participant in game_summary.participants:
        if participant.team_id != user_team_id:
            continue
        stats = participant.stats
        total_kill += stats['kills']
        total_death += stats['deaths']
        total_assist += stats['assists']
        total_hurt += stats['totalDamageDealtToChampions']
        total_money += stats['goldEarned']

    # 获取用户数据并判断是否辅助
    user_participant = id_to_participant[user_participant_id]
    timeline = user_participant.timeline
    is_support_role = (
            timeline['lane'] == Lane.LaneBottom and
            timeline['role'] == ChampionRole.ChampionRoleSupport
    )

    # 一血击杀/助攻
    stats = user_participant.stats
    if stats['firstBloodKill']:
        game_score.add(calc_score_conf.FirstBlood[0], ScoreOption.ScoreOptionFirstBloodKill)
    elif stats['firstBloodAssist']:
        game_score.add(calc_score_conf.FirstBlood[1], ScoreOption.ScoreOptionFirstBloodAssist)

    # 多杀判定
    if stats['pentaKills'] > 0:
        game_score.add(calc_score_conf.PentaKills[0], ScoreOption.ScoreOptionPentaKills)
    elif stats['quadraKills'] > 0:
        game_score.add(calc_score_conf.QuadraKills[0], ScoreOption.ScoreOptionQuadraKills)
    elif stats['tripleKills'] > 0:
        game_score.add(calc_score_conf.TripleKills[0], ScoreOption.ScoreOptionTripleKills)

    # 参团率排名
    if total_kill > 0:
        user_kill_contribution = stats['kills'] + stats['assists']
        user_join_rate = user_kill_contribution / total_kill

        # 获取队伍成员参团率列表
        member_rates = [
            (p.stats['kills'] + p.stats['assists']) / total_kill
            for p in game_summary.participants
            if p.participant_id in member_participant_ids
        ]

        rank = 1
        for rate in member_rates:
            if rate > user_join_rate:
                rank += 1

        if rank == 1:
            game_score.add(calc_score_conf.JoinTeamRateRank[0], ScoreOption.ScoreOptionJoinTeamRateRank)
        elif rank == 2:
            game_score.add(calc_score_conf.JoinTeamRateRank[1], ScoreOption.ScoreOptionJoinTeamRateRank)
        elif rank == 4:
            game_score.add(-calc_score_conf.JoinTeamRateRank[2], ScoreOption.ScoreOptionJoinTeamRateRank)
        elif rank == 5:
            game_score.add(-calc_score_conf.JoinTeamRateRank[3], ScoreOption.ScoreOptionJoinTeamRateRank)

    # 金钱排名
    if total_money > 0:
        user_money = stats['goldEarned']
        member_moneys = [
            p.stats['goldEarned']
            for p in game_summary.participants
            if p.participant_id in member_participant_ids
        ]

        rank = 1
        for money in member_moneys:
            if money > user_money:
                rank += 1

        if rank == 1:
            game_score.add(calc_score_conf.GoldEarnedRank[0], ScoreOption.ScoreOptionGoldEarnedRank)
        elif rank == 2:
            game_score.add(calc_score_conf.GoldEarnedRank[1], ScoreOption.ScoreOptionGoldEarnedRank)
        elif rank == 4 and not is_support_role:
            game_score.add(-calc_score_conf.GoldEarnedRank[2], ScoreOption.ScoreOptionGoldEarnedRank)
        elif rank == 5 and not is_support_role:
            game_score.add(-calc_score_conf.GoldEarnedRank[3], ScoreOption.ScoreOptionGoldEarnedRank)

    # 伤害排名
    if total_hurt > 0:
        user_hurt = stats['totalDamageDealtToChampions']
        member_hurts = [
            p.stats['totalDamageDealtToChampions']
            for p in game_summary.participants
            if p.participant_id in member_participant_ids
        ]

        rank = 1
        for hurt in member_hurts:
            if hurt > user_hurt:
                rank += 1

        if rank == 1:
            game_score.add(calc_score_conf.HurtRank[0], ScoreOption.ScoreOptionHurtRank)
        elif rank == 2:
            game_score.add(calc_score_conf.HurtRank[1], ScoreOption.ScoreOptionHurtRank)

    # 金钱转化率
    if total_money > 0 and total_hurt > 0:
        user_money2hurt = stats['totalDamageDealtToChampions'] / stats['goldEarned']
        member_rates = [
            p.stats['totalDamageDealtToChampions'] / p.stats['goldEarned']
            for p in game_summary.participants
            if p.participant_id in member_participant_ids
        ]

        rank = 1
        for rate in member_rates:
            if rate > user_money2hurt:
                rank += 1

        if rank == 1:
            game_score.add(calc_score_conf.Money2hurtRateRank[0], ScoreOption.ScoreOptionMoney2hurtRateRank)
        elif rank == 2:
            game_score.add(calc_score_conf.Money2hurtRateRank[1], ScoreOption.ScoreOptionMoney2hurtRateRank)

    # 视野得分排名
    user_vision = stats['visionScore']
    member_visions = [
        p.stats['visionScore']
        for p in game_summary.participants
        if p.participant_id in member_participant_ids
    ]

    rank = 1
    for vision in member_visions:
        if vision > user_vision:
            rank += 1

    if rank == 1:
        game_score.add(calc_score_conf.VisionScoreRank[0], ScoreOption.ScoreOptionVisionScoreRank)
    elif rank == 2:
        game_score.add(calc_score_conf.VisionScoreRank[1], ScoreOption.ScoreOptionVisionScoreRank)

    # 补兵评分
    total_minions = stats['totalMinionsKilled']
    game_minutes = game_summary.game_duration // 60
    if game_minutes > 0:
        cs_per_min = total_minions / game_minutes
        for limit in calc_score_conf.MinionsKilled:
            if cs_per_min >= limit[0]:
                game_score.add(limit[1], ScoreOption.ScoreOptionMinionsKilled)
                break

    # 人头占比评分
    if total_kill > 0:
        user_kill_rate = stats['kills'] / total_kill
        for conf in calc_score_conf.KillRate:
            if user_kill_rate > conf.Limit:
                for limit_conf in conf.ScoreConf:
                    if stats['kills'] > limit_conf[0]:
                        game_score.add(limit_conf[1], ScoreOption.ScoreOptionKillRate)
                        break
                break

    # 伤害占比评分
    if total_hurt > 0:
        user_hurt_rate = stats['totalDamageDealtToChampions'] / total_hurt
        for conf in calc_score_conf.HurtRate:
            if user_hurt_rate > conf.Limit:
                for limit_conf in conf.ScoreConf:
                    if stats['kills'] > limit_conf[0]:
                        game_score.add(limit_conf[1], ScoreOption.ScoreOptionHurtRate)
                        break
                break

    # 助攻占比评分
    if total_assist > 0:
        user_assist_rate = stats['assists'] / total_assist
        for conf in calc_score_conf.AssistRate:
            if user_assist_rate > conf.Limit:
                for limit_conf in conf.ScoreConf:
                    if stats['kills'] > limit_conf[0]:
                        game_score.add(limit_conf[1], ScoreOption.ScoreOptionAssistRate)
                        break
                break

    # KDA调整
    user_join_rate = (stats['kills'] + stats['assists']) / total_kill if total_kill > 0 else 1.0
    deaths = stats['deaths'] if stats['deaths'] > 0 else 1

    kda_ratio = (stats['kills'] + stats['assists']) / deaths
    kill_diff = (stats['kills'] - stats['deaths']) / calc_score_conf.AdjustKDA[1]
    adjust_value = (kda_ratio - calc_score_conf.AdjustKDA[0] + kill_diff) * user_join_rate

    game_score.add(adjust_value, ScoreOption.ScoreOptionKDAAdjust)

    return game_score, None

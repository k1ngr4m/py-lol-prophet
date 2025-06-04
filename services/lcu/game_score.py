"""
游戏评分模块，对应原Go代码中的gameScore.go
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple




@dataclass
class ScoreOption:
    """评分选项"""
    ScoreOptionFirstBloodKill = "一血击杀"
    ScoreOptionFirstBloodAssist = "一血助攻"
    ScoreOptionPentaKills = "五杀"
    ScoreOptionQuadraKills = "四杀"
    ScoreOptionTripleKills = "三杀"
    ScoreOptionJoinTeamRateRank = "参团率排名"
    ScoreOptionGoldEarnedRank = "打钱排名"
    ScoreOptionHurtRank = "伤害排名"
    ScoreOptionMoney2hurtRateRank = "金钱转换率排名"
    ScoreOptionVisionScoreRank = "视野得分排名"
    ScoreOptionMinionsKilled = "补兵"
    ScoreOptionKillRate = "击杀占比"
    ScoreOptionHurtRate = "伤害占比"
    ScoreOptionAssistRate = "助攻占比"
    ScoreOptionKDAAdjust = "KDA调整"

class GameScore:
    """游戏评分"""
    
    def __init__(self):
        self.score = 0.0
        self.reasons = {}
    
    def add(self, value: float, reason: str) -> None:
        """
        添加评分
        
        Args:
            value: 评分值
            reason: 评分原因
        """
        self.score += value
        if reason in self.reasons:
            self.reasons[reason] += value
        else:
            self.reasons[reason] = value
    
    def value(self) -> float:
        """
        获取总评分
        
        Returns:
            总评分
        """
        return self.score
    
    def reasons_to_string(self) -> str:
        """
        获取评分原因字符串
        
        Returns:
            评分原因字符串
        """
        result = []
        for reason, value in self.reasons.items():
            result.append(f"{reason}: {value:.2f}")
        return ", ".join(result)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            字典表示
        """
        return {
            "score": self.score,
            "reasons": self.reasons
        }

def calc_game_score(game_summary: Dict[str, Any], user_participant_id: int, 
                    calc_score_conf: Any) -> Tuple[Optional[GameScore], Optional[str]]:
    """
    计算游戏评分
    
    Args:
        game_summary: 游戏摘要数据
        user_participant_id: 用户参与者ID
        calc_score_conf: 评分配置
        
    Returns:
        游戏评分和错误信息的元组
    """
    from services.lcu.common import in_array
    
    # 检查游戏时长
    if game_summary.get("gameDuration", 0) < calc_score_conf.game_min_duration:
        return None, "游戏时长不足"
    
    # 检查游戏模式
    if not in_array(game_summary.get("queueId", 0), calc_score_conf.allow_queue_id_list):
        return None, "不支持的游戏模式"
    
    # 查找用户参与者
    user_participant = None
    for participant in game_summary.get("participants", []):
        if participant.get("participantId") == user_participant_id:
            user_participant = participant
            break
    
    if not user_participant:
        return None, "找不到用户参与者数据"
    
    # 获取用户队伍ID
    user_team_id = user_participant.get("teamId", 0)
    
    # 查找队友参与者ID列表
    member_participant_id_list = []
    for participant in game_summary.get("participants", []):
        if participant.get("teamId") == user_team_id and participant.get("participantId") != user_participant_id:
            member_participant_id_list.append(participant.get("participantId"))
    
    # 计算队伍总击杀、总助攻和总伤害
    total_kill = 0
    total_assist = 0
    total_damage = 0
    
    for participant in game_summary.get("participants", []):
        if participant.get("teamId") == user_team_id:
            stats = participant.get("stats", {})
            total_kill += stats.get("kills", 0)
            total_assist += stats.get("assists", 0)
            total_damage += stats.get("totalDamageDealtToChampions", 0)
    
    # 创建游戏评分对象
    game_score = GameScore()
    
    # 获取用户统计数据
    user_stats = user_participant.get("stats", {})
    
    # 首杀加分
    if user_stats.get("firstBloodKill", False):
        game_score.add(calc_score_conf.first_blood[0], ScoreOption.FIRST_BLOOD)
    elif user_stats.get("firstBloodAssist", False):
        game_score.add(calc_score_conf.first_blood[1], ScoreOption.FIRST_BLOOD)
    
    # 五杀加分
    if user_stats.get("pentaKills", 0) > 0:
        game_score.add(calc_score_conf.penta_kills[0], ScoreOption.PENTA_KILL)
    
    # 四杀加分
    if user_stats.get("quadraKills", 0) > 0:
        game_score.add(calc_score_conf.quadra_kills[0], ScoreOption.QUADRA_KILL)
    
    # 三杀加分
    if user_stats.get("tripleKills", 0) > 0:
        game_score.add(calc_score_conf.triple_kills[0], ScoreOption.TRIPLE_KILL)
    
    # 补刀加分
    minions_killed = user_stats.get("totalMinionsKilled", 0) + user_stats.get("neutralMinionsKilled", 0)
    for minion_conf in calc_score_conf.minions_killed:
        if minions_killed >= minion_conf[0]:
            game_score.add(minion_conf[1], ScoreOption.MINIONS_KILLED)
            break
    
    # 参团率排名加分
    if total_kill > 0:
        member_join_team_kill_rates = []
        for participant in game_summary.get("participants", []):
            if participant.get("participantId") in member_participant_id_list:
                stats = participant.get("stats", {})
                rate = (stats.get("assists", 0) + stats.get("kills", 0)) / total_kill
                member_join_team_kill_rates.append(rate)
        
        user_join_team_kill_rate = (user_stats.get("assists", 0) + user_stats.get("kills", 0)) / total_kill
        member_join_team_kill_rates.sort(reverse=True)
        
        # 根据排名加分
        for i, rate in enumerate(member_join_team_kill_rates):
            if user_join_team_kill_rate > rate:
                if i < len(calc_score_conf.join_team_rate_rank):
                    game_score.add(calc_score_conf.join_team_rate_rank[i], ScoreOption.JOIN_TEAM_RATE_RANK)
                break
    
    # 经济排名加分
    member_money = []
    for participant in game_summary.get("participants", []):
        if participant.get("participantId") in member_participant_id_list:
            stats = participant.get("stats", {})
            member_money.append(stats.get("goldEarned", 0))
    
    user_money = user_stats.get("goldEarned", 0)
    member_money.sort(reverse=True)
    
    # 根据排名加分
    for i, money in enumerate(member_money):
        if user_money > money:
            if i < len(calc_score_conf.gold_earned_rank):
                game_score.add(calc_score_conf.gold_earned_rank[i], ScoreOption.GOLD_EARNED_RANK)
            break
    
    # 伤害排名加分
    member_hurt = []
    for participant in game_summary.get("participants", []):
        if participant.get("participantId") in member_participant_id_list:
            stats = participant.get("stats", {})
            member_hurt.append(stats.get("totalDamageDealtToChampions", 0))
    
    user_hurt = user_stats.get("totalDamageDealtToChampions", 0)
    member_hurt.sort(reverse=True)
    
    # 根据排名加分
    for i, hurt in enumerate(member_hurt):
        if user_hurt > hurt:
            if i < len(calc_score_conf.hurt_rank):
                game_score.add(calc_score_conf.hurt_rank[i], ScoreOption.HURT_RANK)
            break
    
    # 金钱转换率排名加分
    member_money2hurt_rate = []
    for participant in game_summary.get("participants", []):
        if participant.get("participantId") in member_participant_id_list:
            stats = participant.get("stats", {})
            if stats.get("goldEarned", 0) > 0:
                rate = stats.get("totalDamageDealtToChampions", 0) / stats.get("goldEarned", 1)
                member_money2hurt_rate.append(rate)
    
    user_money2hurt_rate = 0
    if user_stats.get("goldEarned", 0) > 0:
        user_money2hurt_rate = user_stats.get("totalDamageDealtToChampions", 0) / user_stats.get("goldEarned", 1)
    
    member_money2hurt_rate.sort(reverse=True)
    
    # 根据排名加分
    for i, rate in enumerate(member_money2hurt_rate):
        if user_money2hurt_rate > rate:
            if i < len(calc_score_conf.money2hurt_rate_rank):
                game_score.add(calc_score_conf.money2hurt_rate_rank[i], ScoreOption.MONEY2HURT_RATE_RANK)
            break
    
    # 视野得分排名加分
    member_vision_score = []
    for participant in game_summary.get("participants", []):
        if participant.get("participantId") in member_participant_id_list:
            stats = participant.get("stats", {})
            member_vision_score.append(stats.get("visionScore", 0))
    
    user_vision_score = user_stats.get("visionScore", 0)
    member_vision_score.sort(reverse=True)
    
    # 根据排名加分
    for i, score in enumerate(member_vision_score):
        if user_vision_score > score:
            if i < len(calc_score_conf.vision_score_rank):
                game_score.add(calc_score_conf.vision_score_rank[i], ScoreOption.VISION_SCORE_RANK)
            break
    
    # 击杀占比加分
    if total_kill > 0:
        user_kill_rate = user_stats.get("kills", 0) / total_kill
        
        for rate_item in calc_score_conf.kill_rate:
            if user_kill_rate > rate_item.limit / 100.0:
                for limit_conf in rate_item.score_conf:
                    if user_stats.get("kills", 0) > limit_conf[0]:
                        game_score.add(limit_conf[1], ScoreOption.KILL_RATE)
                        break
                break
    
    # 伤害占比加分
    if total_damage > 0:
        user_hurt_rate = user_stats.get("totalDamageDealtToChampions", 0) / total_damage
        
        for rate_item in calc_score_conf.hurt_rate:
            if user_hurt_rate > rate_item.limit / 100.0:
                for limit_conf in rate_item.score_conf:
                    if user_stats.get("kills", 0) > limit_conf[0]:
                        game_score.add(limit_conf[1], ScoreOption.HURT_RATE)
                        break
                break
    
    # 助攻占比加分
    if total_assist > 0:
        user_assist_rate = user_stats.get("assists", 0) / total_assist
        
        for rate_item in calc_score_conf.assist_rate:
            if user_assist_rate > rate_item.limit / 100.0:
                for limit_conf in rate_item.score_conf:
                    if user_stats.get("kills", 0) > limit_conf[0]:
                        game_score.add(limit_conf[1], ScoreOption.ASSIST_RATE)
                        break
                break
    
    # KDA调整
    user_join_team_kill_rate = 1.0
    if total_kill > 0:
        user_join_team_kill_rate = (user_stats.get("assists", 0) + user_stats.get("kills", 0)) / total_kill
    
    user_death_times = user_stats.get("deaths", 0)
    if user_death_times == 0:
        user_death_times = 1
    
    adjust_val = ((user_stats.get("kills", 0) + user_stats.get("assists", 0)) / user_death_times - 
                 calc_score_conf.adjust_kda[0] + 
                 (user_stats.get("kills", 0) - user_stats.get("deaths", 0)) / calc_score_conf.adjust_kda[1]) * user_join_team_kill_rate
    
    game_score.add(adjust_val, ScoreOption.KDA_ADJUST)
    
    return game_score, None

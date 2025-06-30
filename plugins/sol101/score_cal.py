import pytz

from plugins.sol101.config.championName_zh import championName_zh
from datetime import datetime
import services.logger.logger as logger
from plugins.sol101.config.itemList import item_name
from plugins.sol101.config.game_data_champs import game_data_champs_dict

# 保留特定的键值对
def get_filtered_data(data, summoner_id, summoner_allName):
    filtered_participants = []
    def filter_participant(participant, participantIdentities):
        stats = participant.get("stats", {})
        return {
            "assists": stats["assists"],
            "champLevel": stats["champLevel"],
            "championId": participant["championId"],
            "championName": str(get_champion_name_by_id(participant["championId"])),
            "deaths": stats["deaths"],
            "firstBloodKill": stats["firstBloodKill"],
            "goldEarned": stats["goldEarned"],
            "item0": replace_itemName(stats["item0"]),
            "item1": replace_itemName(stats["item1"]),
            "item2": replace_itemName(stats["item2"]),
            "item3": replace_itemName(stats["item3"]),
            "item4": replace_itemName(stats["item4"]),
            "item5": replace_itemName(stats["item5"]),
            "item6": replace_itemName(stats["item6"]),
            "kills": stats["kills"],
            "magicDamageDealtToChampions": stats["magicDamageDealtToChampions"],
            "magicDamageTaken": stats.get("magicDamageTaken",-1),
            "participantId": stats["participantId"],
            "physicalDamageDealtToChampions": stats["physicalDamageDealtToChampions"],
            "physicalDamageTaken": stats["physicalDamageTaken"],
            "placement": stats.get("placement", -1),
            "profileIcon": stats.get("profileIcon", "none"),
            "riotIdGameName": participantIdentities["gameName"],
            "riotIdTagline": participantIdentities["tagLine"],
            "role": stats.get("role","none"),
            "summonerId": str(participantIdentities["summonerId"]),
            "summonerLevel": participantIdentities.get("summonerLevel", -1),
            "summonerName": participantIdentities["summonerName"],
            "teamEarlySurrendered": stats["teamEarlySurrendered"],
            "teamId": participant["teamId"],
            "teamPosition": stats.get("teamPosition", "none"),
            "timePlayed": stats.get("timePlayed", "-1"),
            "totalDamageDealt": stats["totalDamageDealt"],
            "totalDamageDealtToChampions": stats["totalDamageDealtToChampions"],
            "totalDamageShieldedOnTeammates": stats.get("totalDamageShieldedOnTeammates", -1),
            "totalDamageTaken": stats["totalDamageTaken"],
            "totalHeal": stats["totalHeal"],
            "totalHealsOnTeammates": stats.get("totalHealsOnTeammates", -1),
            "totalMinionsKilled": stats["totalMinionsKilled"],
            "totalTimeSpentDead": stats.get("totalTimeSpentDead", -1),
            "trueDamageDealtToChampions": stats["trueDamageDealtToChampions"],
            "trueDamageTaken": stats["trueDamageTaken"],
            "win": stats["win"],
            "challenges": calculate_participant_scores(participant, data),
            "summonerAllName": str(participantIdentities["gameName"]) + "#" + str(participantIdentities["tagLine"]),
            "isSearched": 1
        }
    for participant in data["participants"]:
        participantIdentities = data["participantIdentities"][0]["player"]
        filtered_participant = filter_participant(participant, participantIdentities)
        if filtered_participant:
            filtered_participants.append(filtered_participant)

    # print(filtered_participants)

    filtered_data = {
        "endOfGameResult": data["endOfGameResult"],
        "gameCreation": timestamp_to_datetime(data["gameCreation"]),
        "gameDuration": round(int(data["gameDuration"]) / 60, 2),
        "gameEndTimestamp": timestamp_to_datetime(cal_endTime(data["gameCreation"], data["gameDuration"])),
        "gameId": str(data['gameId']),
        "gameMode": data["gameMode"],
        "gameStartTimestamp": timestamp_to_datetime(data["gameCreation"]),
        "dayOfWeek": get_chinese_day_of_week(data["gameCreation"]),
        "gameVersion": format_game_version(data["gameVersion"]),
        "participants": filtered_participants,
    }
    # logger.debug(filtered_data)

    return filtered_data


def calculate_participant_scores(participant, data):
    stats = participant.get("stats", {})

    # 从participant和data中提取所需的属性
    game_duration = round(int(data["gameDuration"]) / 60, 2)

    kda = cal_kda(int(stats["kills"]), int(stats["deaths"]), int(stats["assists"]))

    total_damage = stats["totalDamageDealtToChampions"]
    damage_per_minute = cal_per_minute(total_damage, game_duration)

    total_damage_taken = stats["totalDamageTaken"]
    damage_taken_per_minute = cal_per_minute(total_damage_taken, game_duration)

    gold_earned = stats["goldEarned"]
    gold_per_minute = cal_per_minute(gold_earned, game_duration)

    damage_conversion_rate = round(total_damage / gold_earned, 4)

    # 返回计算后的属性值
    return {
        "damageConversionRate": damage_conversion_rate,  # 伤害转化率
        "damagePerMinute": damage_per_minute,
        "damageTakenPerMinute": damage_taken_per_minute,  # 分均承受伤害
        "goldPerMinute": gold_per_minute,  # 分均经济
        "kda": kda,  # kda
    }

def cal_endTime(start_time, game_duration):
    end_time = start_time + game_duration * 1000
    return end_time

def timestamp_to_datetime(timestamp):
    # 将毫秒级时间戳转换为秒级
    timestamp_seconds = timestamp / 1000.0
    # 将时间戳转换为带有时区信息的 datetime 对象（UTC 时间）
    dt_utc = datetime.utcfromtimestamp(timestamp_seconds)

    # 创建时区对象
    tz_utc = pytz.timezone('UTC')
    tz_beijing = pytz.timezone('Asia/Shanghai')  # 北京时间所在时区

    # 使用 replace 方法将 UTC 时间对象的时区信息替换为北京时间的时区信息
    dt_beijing = tz_utc.localize(dt_utc).astimezone(tz_beijing)

    # 格式化为传统的时间格式
    traditional_format = dt_beijing.strftime('%Y-%m-%d %H:%M:%S')
    return traditional_format


def format_game_version(input_string):
    parts = input_string.split('.')
    # 取出前两个元素，并用点号连接起来
    return '.'.join(parts[:2])


def get_chinese_day_of_week(timestamp):
    # 映射英文星期几到中文的字典
    translation = {
        'Monday': '星期一',
        'Tuesday': '星期二',
        'Wednesday': '星期三',
        'Thursday': '星期四',
        'Friday': '星期五',
        'Saturday': '星期六',
        'Sunday': '星期日'
    }

    # 将毫秒级时间戳转换为秒级
    timestamp_seconds = timestamp / 1000.0
    # 将时间戳转换为带有时区信息的 datetime 对象（UTC 时间）
    dt_utc = datetime.utcfromtimestamp(timestamp_seconds)

    # 创建时区对象
    tz_utc = pytz.timezone('UTC')
    tz_beijing = pytz.timezone('Asia/Shanghai')  # 北京时间所在时区

    # 使用 replace 方法将 UTC 时间对象的时区信息替换为北京时间的时区信息
    dt_beijing = tz_utc.localize(dt_utc).astimezone(tz_beijing)

    # 将日期时间转换为英文星期几
    english_day_of_week = dt_beijing.strftime('%A')

    # 返回对应的中文星期几，如果在字典中找不到对应的值，则返回原始的英文星期几
    return translation.get(english_day_of_week, english_day_of_week)


def cal_kda(kill, death, assists):
    if death == 0:
        return round((kill + assists) / (death + 1), 2)
    else:
        return round((kill + assists) / death, 2)


def cal_per_minute(totalValue, totalTime):
    return round(totalValue / totalTime, 2)


def replace_itemName(item_num):
    # 确保 item_num 是字符串
    item_num_str = str(item_num)

    # 先检查键是否存在
    if item_num_str in item_name:
        return item_name[item_num_str].get('name', item_num_str)
    else:
        # 处理不存在的键，可以返回默认值或记录错误
        return item_num_str  # 或者返回 "Unknown Item" 等其他默认值

def find_min_max_values(min_max_values_list, game_mode, game_version, attribute):
    """
    从min_max_values_list中查找指定游戏模式和版本下属性的最小最大值
    :param min_max_values_list: 包含最小最大值的列表
    :param game_mode: 游戏模式
    :param game_version: 游戏版本
    :param attribute: 要查找的属性名称
    :return: 返回该属性的最小值和最大值，如果找不到则返回None, None
    """
    for item in min_max_values_list:
        if item['gameMode'] == game_mode and item['gameVersion'] == game_version:
            return item.get(attribute + '_min'), item.get(attribute + '_max')
    return None, None

def calculate_role_score(role, kda=None, damage_per_minute=None, damage_taken_per_minute=None,
                         gold_per_minute=None, damage_conversion_rate=None, total_heals_on_teammates=None,
                         game_mode='ARAM', game_version='1.0', min_max_values_list=None):
    """
    根据角色类型计算综合得分
    :param role: 角色类型 ('carry', 'tank', 'support')
    :param kda: 杀死/死亡/助攻比率
    :param damage_per_minute: 每分钟造成的伤害
    :param damage_taken_per_minute: 每分钟承受的伤害
    :param gold_per_minute: 每分钟获得的金币
    :param damage_conversion_rate: 伤害转化率
    :param total_heals_on_teammates: 对队友的总治疗量
    :param game_mode: 游戏模式，默认为 'ARAM'
    :param game_version: 游戏版本，默认为 '1.0'
    :param min_max_values_list: 包含最小最大值的列表
    :return: 综合得分
    """
    # 定义不同角色类型的默认权重
    weights = {
        'carry': {
            'kda': 10,
            'damagePerMinute': 40,
            'damageConversionRate': 50,
        },
        'tank': {
            'kda': 10,
            'damageTakenPerMinute': 60,
            'goldPerMinute': 30,
        },
        'support': {
            'kda': 30,
            'totalHealsOnTeammates': 70,
        }
    }

    # 处理特殊情况：CHERRY模式下的权重调整
    if game_mode == 'CHERRY':
        if role == 'carry':
            weights[role]['kda'] = 5
            weights[role]['damagePerMinute'] = 25
            weights[role]['damageConversionRate'] = 70
        elif role == 'tank':
            weights[role]['kda'] = 15
            weights[role]['damageTakenPerMinute'] = 85
            weights[role].pop('goldPerMinute', None)

    # 计算综合得分
    score = 0
    attributes = {
        'kda': kda,
        'damagePerMinute': damage_per_minute,
        'damageTakenPerMinute': damage_taken_per_minute,
        'goldPerMinute': gold_per_minute,
        'damageConversionRate': damage_conversion_rate,
        'totalHealsOnTeammates': total_heals_on_teammates
    }

    for attribute, weight in weights.get(role, {}).items():
        if attributes[attribute] is not None:
            value = attributes[attribute]
            min_val, max_val = find_min_max_values(min_max_values_list, game_mode, game_version, attribute)
            score += calculate_single_score(value, min_val, max_val, weight)

    return round(score, 2)

def calculate_total_score(carry_score, tank_score, support_score, game_mode, game_version, min_max_values_list):
    """
    计算综合得分并确定英雄分类
    :param carry_score: Carry角色的得分
    :param tank_score: Tank角色的得分
    :param support_score: Support角色的得分
    :param game_mode: 游戏模式
    :param game_version: 游戏版本
    :param min_max_values_list: 包含最小最大值的列表
    :return: 综合得分和英雄分类
    """
    # 确定最高得分及其对应的角色分类
    scores = {'Carry': carry_score, 'Tank': tank_score, 'Support': support_score}
    champion_classification = max(scores, key=scores.get)
    max_score = scores[champion_classification]

    # 根据最高得分的角色分类设置权重
    weight_dict = {
        'Carry': {'x': 100, 'y': 64, 'z': 33},
        'Tank': {'x': 64, 'y': 100, 'z': 33},
        'Support': {'x': 60, 'y': 60, 'z': 80}
    }

    weights = weight_dict[champion_classification]

    # 查找每个角色得分的最小最大值
    carry_score_min, carry_score_max = find_min_max_values(min_max_values_list, game_mode, game_version, 'carryScore')
    tank_score_min, tank_score_max = find_min_max_values(min_max_values_list, game_mode, game_version, 'tankScore')
    support_score_min, support_score_max = find_min_max_values(min_max_values_list, game_mode, game_version, 'supportScore')

    # 计算综合得分
    total_score = round(
        calculate_single_score(carry_score, carry_score_min, carry_score_max, weights['x']) +
        calculate_single_score(tank_score, tank_score_min, tank_score_max, weights['y']) +
        calculate_single_score(support_score, support_score_min, support_score_max, weights['z']), 2)

    return total_score, champion_classification


def calculate_single_score(value, min_val, max_val, factor):
    """
    根据给定的值、最小值、最大值和权重计算单项得分
    :param value: 当前统计值
    :param min_val: 统计值的最小值
    :param max_val: 统计值的最大值
    :param factor: 该项得分在总分中的权重
    :return: 单项得分
    """
    if max_val is not None and min_val is not None and max_val != min_val:
        return abs(value - min_val) / abs(max_val - min_val) * factor
    return 0


def get_champion_name_by_id(champ_id):
    """
    根据 champId 获取对应的英雄名称

    参数:
        game_data_champs_dict: 包含英雄数据的字典
        champ_id: 要查找的英雄ID (字符串或数字)

    返回:
        如果找到则返回英雄名称，否则返回 None
    """
    # 确保champ_id是字符串类型，方便比较
    champ_id_str = str(champ_id)

    # 遍历data列表中的每个英雄字典
    for champion in game_data_champs_dict.get("data", []):
        if champion.get("champId") == champ_id_str:
            return champion.get("title")

    return None  # 如果没有找到匹配的champId

if __name__ == '__main__':
    print(str(get_champion_name_by_id(1)))

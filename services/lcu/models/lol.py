from enum import Enum
from typing import Any


# ---------- 游戏模式 ----------
class GameMode(str, Enum):
    NONE = ""
    CLASSIC = "CLASSIC"      # 经典模式
    ARAM = "ARAM"            # 大乱斗
    TFT = "TFT"              # 云顶之弈
    URF = "URF"              # 无限火力
    CUSTOM = "PRACTICETOOL"  # 自定义
    CHERRY = "CHERRY"        # 斗魂竞技场

# ---------- 队列模式 ----------
class GameQueueType(str, Enum):
    NORMAL = "NORMAL"                  # 匹配
    RANKED_SOLO = "RANKED_SOLO_5x5"    # 单双排
    RANKED_FLEX = "RANKED_FLEX_SR"     # 组排
    ARAM_UNRANKED = "ARAM_UNRANKED_5x5"# 大乱斗5v5
    URF = "URF"                        # 无限火力
    BOT = "BOT"                        # 人机
    CUSTOM = "PRACTICETOOL"            # 自定义

# ---------- 游戏状态 ----------
class GameStatus(str, Enum):
    IN_QUEUE = "inQueue"                        # 队列中
    IN_GAME = "inGame"                          # 游戏中
    CHAMPION_SELECT = "championSelect"          # 英雄选择中
    OUT_OF_GAME = "outOfGame"                   # 退出游戏中
    HOST_NORMAL = "hosting_NORMAL"              # 匹配组队中-队长
    HOST_RANK_SOLO = "hosting_RANKED_SOLO_5x5" # 单排组队中-队长
    HOST_RANK_FLEX = "hosting_RANKED_FLEX_SR"  # 组排组队中-队长
    HOST_ARAM = "hosting_ARAM_UNRANKED_5x5"    # 大乱斗5v5组队中-队长
    HOST_URF = "hosting_URF"                    # 无限火力组队中-队长
    HOST_BOT = "hosting_BOT"                    # 人机组队中-队长

# ---------- 游戏流程 ----------
class GameFlow(str, Enum):
    CHAMP_SELECT = "ChampSelect"   # 英雄选择中
    READY_CHECK = "ReadyCheck"     # 等待接受对局
    IN_PROGRESS = "InProgress"     # 进行中
    MATCHMAKING = "Matchmaking"    # 匹配中
    NONE = "None"                  # 无

# ---------- 排位等级 ----------
class RankTier(str, Enum):
    IRON = "IRON"            # 黑铁
    BRONZE = "BRONZE"        # 青铜
    SILVER = "SILVER"        # 白银
    GOLD = "GOLD"            # 黄金
    PLATINUM = "PLATINUM"    # 白金
    DIAMOND = "DIAMOND"      # 钻石
    MASTER = "MASTER"        # 大师
    GRANDMASTER = "GRANDMASTER" # 宗师
    CHALLENGER = "CHALLENGER"   # 王者

# ---------- 游戏类型 ----------
class GameType(str, Enum):
    MATCHED_GAME = "MATCHED_GAME"  # 匹配

# ---------- 游戏队列 ID ----------
NORMAL_QUEUE_ID = 430     # 匹配
RANK_SOLO_QUEUE_ID = 420  # 单排
RANK_FLEX_QUEUE_ID = 440  # 组排
ARAM_QUEUE_ID = 450       # 大乱斗
URF_QUEUE_ID = 900        # 无限火力
BOT_SIMPLE_QUEUE_ID = 830 # 人机入门
BOT_NOVICE_QUEUE_ID = 840 # 人机新手
BOT_NORMAL_QUEUE_ID = 850 # 人机一般
CHEERY_QUEUE_ID = 1700    # 斗魂竞技场

# ---------- 地图 ID ----------
class MapID(int, Enum):
    MAP_ID_CLASSIC = 11  # 经典模式召唤师峡谷
    MAP_ID_ARAM = 12     # 极地大乱斗
    MAP_ID_CHEERY = 30   # 斗魂竞技场

# ---------- 队伍 ID ----------
class TeamID(int, Enum):
    TEAM_ID_NONE = 0     # 未知
    TEAM_ID_BLUE = 100   # 蓝色方
    TEAM_ID_RED = 200    # 红色方

TEAM_ID_STR_NONE = ""   # 未知
TEAM_ID_STR_BLUE = "100"# 蓝色方
TEAM_ID_STR_RED = "200" # 红色方

# ---------- 大区 ID ----------
PLATFORM_ID_DX1 = "HN1"  # 艾欧尼亚
PLATFORM_ID_DX2 = "HN2"  # 祖安

# ---------- 召唤师技能 ----------
SPELL_PINGZHANG = 21  # 屏障
SPELL_SHANXIAN = 4    # 闪现

# ---------- 位置 ----------
class Lane(str, Enum):
    LaneTop = "TOP"         # 上路
    LaneJungle = "JUNGLE"   # 打野
    LaneMiddle = "MIDDLE"   # 中路
    LaneBottom = "BOTTOM"   # 下路

# ---------- 英雄角色 ----------
class ChampionRole(str, Enum):
    ChampionRoleSolo = "SOLE"          # 单人路
    ChampionRoleSupport = "DUO_SUPPORT"  # 辅助
    ChampionRoleADC = "DUO_CARRY"      # ADC
    ChampionRoleNone = "NONE"          # 无，一般打野

# ---------- 游戏大区 ----------
PLATFORM_ID_HN1 = "HN1"  # 大区：艾欧尼亚

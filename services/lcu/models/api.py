from dataclasses import dataclass, field
from typing import List, Optional, Any, Union
from datetime import datetime

from services.lcu.models.lol import GameMode, GameType, MapID, TeamID, Lane, ChampionRole


@dataclass
class PerMinDeltas:
    ten: float = field(metadata={"json": "0-10"})
    twenty: float = field(metadata={"json": "10-20"})
    thirty: Optional[float] = field(default=None, metadata={"json": "20-30"})
    forty: Optional[float] = field(default=None, metadata={"json": "30-40"})
    fifty: Optional[float] = field(default=None, metadata={"json": "40-50"})
    sixty: Optional[float] = field(default=None, metadata={"json": "50-60"})


@dataclass
class CommonResp:
    error_code: Optional[str] = None
    http_status: Optional[int] = None
    message: Optional[str] = None


@dataclass
class RerollPoints:
    current_points: int
    max_rolls: int
    number_of_rolls: int
    points_cost_to_roll: int
    points_to_reroll: int


@dataclass
class CurrSummoner:
    account_id: int
    display_name: str
    internal_name: str
    name_change_flag: bool
    percent_complete_for_next_level: int
    profile_icon_id: int
    puuid: str
    reroll_points: RerollPoints
    summoner_id: int
    game_name: str
    tag_line: str
    summoner_level: int
    unnamed: bool
    xp_since_last_level: int
    xp_until_next_level: int


@dataclass
class ParticipantPlayer:
    account_id: int = None
    current_account_id: int = None
    current_platform_id: str = None
    match_history_uri: str = None
    platform_id: str = None
    profile_icon: int = None
    summoner_id: int = None
    summoner_name: str = None
    game_name: Optional[str] = None
    puuid: Optional[str] = None
    tag_line: Optional[str] = None

@dataclass
class Stats:
    assists: int
    caused_early_surrender: bool
    champ_level: int
    combat_player_score: int
    damage_dealt_to_objectives: int
    damage_dealt_to_turrets: int
    damage_self_mitigated: int
    deaths: int
    double_kills: int
    early_surrender_accomplice: bool
    first_blood_assist: bool
    first_blood_kill: bool
    first_inhibitor_assist: bool
    first_inhibitor_kill: bool
    first_tower_assist: bool
    first_tower_kill: bool
    game_ended_in_early_surrender: bool
    game_ended_in_surrender: bool
    gold_earned: int
    gold_spent: int
    inhibitor_kills: int
    item0: int
    item1: int
    item2: int
    item3: int
    item4: int
    item5: int
    item6: int
    killing_sprees: int
    kills: int
    largest_critical_strike: int
    largest_killing_spree: int
    largest_multi_kill: int
    longest_time_spent_living: int
    magic_damage_dealt: int
    magic_damage_dealt_to_champions: int
    magical_damage_taken: int
    neutral_minions_killed: int
    neutral_minions_killed_enemy_jungle: int
    neutral_minions_killed_team_jungle: int
    objective_player_score: int
    participant_id: int
    penta_kills: int
    perk0: int
    perk0_var1: int
    perk0_var2: int
    perk0_var3: int
    perk1: int
    perk1_var1: int
    perk1_var2: int
    perk1_var3: int
    perk2: int
    perk2_var1: int
    perk2_var2: int
    perk2_var3: int
    perk3: int
    perk3_var1: int
    perk3_var2: int
    perk3_var3: int
    perk4: int
    perk4_var1: int
    perk4_var2: int
    perk4_var3: int
    perk5: int
    perk5_var1: int
    perk5_var2: int
    perk5_var3: int
    perk_primary_style: int
    perk_sub_style: int
    physical_damage_dealt: int
    physical_damage_dealt_to_champions: int
    physical_damage_taken: int
    player_score0: int
    player_score1: int
    player_score2: int
    player_score3: int
    player_score4: int
    player_score5: int
    player_score6: int
    player_score7: int
    player_score8: int
    player_score9: int
    quadra_kills: int
    sight_wards_bought_in_game: int
    team_early_surrendered: bool
    time_ccing_others: int
    total_damage_dealt: int
    total_damage_dealt_to_champions: int
    total_damage_taken: int
    total_heal: int
    total_minions_killed: int
    total_player_score: int
    total_score_rank: int
    total_time_crowd_control_dealt: int
    total_units_healed: int
    triple_kills: int
    true_damage_dealt: int
    true_damage_dealt_to_champions: int
    true_damage_taken: int
    turret_kills: int
    unreal_kills: int
    vision_score: int
    vision_wards_bought_in_game: int
    wards_killed: int
    wards_placed: int
    win: bool

@dataclass
class CreepsPerMinDeltas:
    zero_to_ten: float
    ten_to_twenty: float

@dataclass
class CsDiffPerMinDeltas:
    zero_to_ten: float
    ten_to_twenty: float

@dataclass
class DamageTakenDiffPerMinDeltas:
    zero_to_ten: float
    ten_to_twenty: float

@dataclass
class DamageTakenPerMinDeltas:
    zero_to_ten: float
    ten_to_twenty: float

@dataclass
class GoldPerMinDeltas:
    zero_to_ten: float
    ten_to_twenty: float

@dataclass
class XpDiffPerMinDeltas:
    zero_to_ten: float
    ten_to_twenty: float

@dataclass
class XpPerMinDeltas:
    zero_to_ten: float
    ten_to_twenty: float

@dataclass
class Timeline:
    creeps_per_min_deltas: CreepsPerMinDeltas
    cs_diff_per_min_deltas: CsDiffPerMinDeltas
    damage_taken_diff_per_min_deltas: DamageTakenDiffPerMinDeltas
    damage_taken_per_min_deltas: DamageTakenPerMinDeltas
    gold_per_min_deltas: GoldPerMinDeltas
    lane: Lane
    participant_id: int
    role: ChampionRole
    xp_diff_per_min_deltas: XpDiffPerMinDeltas
    xp_per_min_deltas: XpPerMinDeltas

@dataclass
class Participant:
    champion_id: int = 0
    highest_achieved_season_tier: str = ''
    participant_id: int = 0
    spell1_id: int = 0
    spell2_id: int = 0
    stats: Stats = None
    team_id: TeamID = 0
    timeline: Timeline = None
    # stats and timeline fields omitted for brevity
    # they should be modeled similarly to PerMinDeltas and ParticipantPlayer
    @classmethod
    def from_dict(cls, data: dict):
        # 转换timeline字典为Timeline实例
        timeline_data = data.get('timeline', {})
        timeline = Timeline(**timeline_data) if timeline_data else None

        return cls(
            champion_id=data.get('champion_id', 0),
            highest_achieved_season_tier=data.get('highest_achieved_season_tier', ''),
            participant_id=data.get('participant_id', 0),
            spell1_id=data.get('spell1_id', 0),
            spell2_id=data.get('spell2_id', 0),
            stats=data.get('stats'),
            team_id=data.get('team_id', TeamID(0)),
            timeline=timeline
        )

@dataclass
class ParticipantIdentity:
    participant_id: int = 0
    player: ParticipantPlayer = field(default_factory=ParticipantPlayer)

@dataclass
class GameInfo:
    game_creation: int
    game_creation_date: datetime
    game_duration: int
    game_id: int
    game_mode: str
    game_type: str
    game_version: str
    map_id: int
    participant_identities: List[ParticipantIdentity]
    participants: List[Participant]
    platform_id: str
    queue_id: int
    season_id: int
    teams: List[Any]


@dataclass
class GameList:
    game_begin_date: str
    game_count: int
    game_end_date: str
    game_index_begin: int
    game_index_end: int
    games: List[GameInfo]


@dataclass()
class GameListResp(CommonResp):
    account_id: int = None
    games: GameList = None

@dataclass
class Conversation:
    game_name: str
    game_tag: str
    id: str
    inviter_id: str
    is_muted: bool
    last_message: Any
    name: str
    password: str
    pid: str
    target_region: str
    type: str
    unread_message_count: int


@dataclass
class ConversationMsg:
    body: str
    from_id: str
    from_pid: str
    from_summoner_id: int
    id: str
    is_historical: bool
    timestamp: datetime
    type: str


@dataclass
class Summoner(CommonResp):
    account_id: int = None
    game_name: str = None
    tag_line: str = None
    display_name: str = None
    internal_name: str = None
    name_change_flag: bool = None
    percent_complete_for_next_level: int = None
    privacy: str = None
    profile_icon_id: int = None
    puuid: str = None
    reroll_points: RerollPoints = None
    summoner_id: int = None
    summoner_level: int = None
    unnamed: bool = None
    xp_since_last_level: int = None
    xp_until_next_level: int = None


@dataclass
class SummonerProfileData(CommonResp):
    availability: str = None
    game_name: str = None
    game_tag: str = None
    icon: int = None
    id: str = None
    last_seen_online_timestamp: Optional[Any] = None
    lol: dict = None  # should be modeled with a nested class if structure is used
    name: str = None
    obfuscated_summoner_id: int = None
    patchline: str = None
    pid: str = None
    platform_id: str = None
    product: str = None
    product_name: str = None
    puuid: str = None
    status_message: str = None
    summary: str = None
    summoner_id: int = None
    time: int = None

    # 更新数据模型
@dataclass
class UpdateSummonerProfileData:
    availability: Optional[str] = None

# 玩家简介数据模型
@dataclass
class SummonerProfileData(CommonResp):
    availability: Optional[str] = None
    gameName: Optional[str] = None
    gameTag: Optional[str] = None
    icon: Optional[int] = None
    id: Optional[str] = None
    lastSeenOnlineTimestamp: Optional[Any] = None
    lol: Optional[dict] = None
    name: Optional[str] = None
    obfuscatedSummonerId: Optional[int] = None
    patchline: Optional[str] = None
    pid: Optional[str] = None
    platformId: Optional[str] = None
    product: Optional[str] = None
    productName: Optional[str] = None
    puuid: Optional[str] = None
    statusMessage: Optional[str] = None
    summary: Optional[str] = None
    summonerId: Optional[int] = None
    time: Optional[int] = None

@dataclass
class ChampSelectAction:
    actor_cell_id: int
    champion_id: int
    completed: bool
    id: int
    is_ally_action: bool
    is_in_progress: bool
    pick_turn: int
    type: str  # ChampSelectPatchType, modeled as string


@dataclass
class ChampSelectSessionInfo(CommonResp):
    actions: List[List[ChampSelectAction]] = None
    local_player_cell_id: int = None



@dataclass
class TeamBan:
    champion_id: int = 0
    pick_turn: int = 0

@dataclass
class Team:
    team_id: int = 0
    win: str = ""
    bans: List[TeamBan] = field(default_factory=list)
    baron_kills: int = 0
    dominion_victory_score: int = 0
    dragon_kills: int = 0
    first_baron: bool = False
    first_blood: bool = False
    first_dragon: bool = False
    first_inhibitor: bool = False
    first_tower: bool = False
    inhibitor_kills: int = 0
    rift_herald_kills: int = 0
    tower_kills: int = 0
    vilemaw_kills: int = 0

@dataclass
class GameSummary(CommonResp):
    game_creation: int = 0
    game_creation_date: datetime = None
    game_duration: int = 0
    game_id: int = 0
    game_mode: str = GameMode.CLASSIC
    game_type: str = GameType.MATCHED_GAME
    game_version: str = ""
    map_id: int = MapID.MAP_ID_CLASSIC
    participant_identities: List[ParticipantIdentity] = field(default_factory=list)
    participants: List[Participant] = field(default_factory=list)
    platform_id: str = ""
    queue_id: int = 0
    season_id: int = 0
    teams: List[Team] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> 'GameSummary':
        """从字典创建GameSummary对象"""
        # 创建基本对象
        summary = cls()

        # 设置公共响应字段
        summary.error_code = data.get("errorCode", "")
        summary.message = data.get("message", "")

        # 设置游戏基本信息
        summary.game_creation = data.get("gameCreation", 0)
        summary.game_duration = data.get("gameDuration", 0)
        summary.game_id = data.get("gameId", 0)
        summary.game_mode = data.get("gameMode", GameMode.CLASSIC)
        summary.game_type = data.get("gameType", GameType.MATCHED_GAME)
        summary.game_version = data.get("gameVersion", "")
        summary.map_id = data.get("mapId", MapID.MAP_ID_CLASSIC)
        summary.platform_id = data.get("platformId", "")
        summary.queue_id = data.get("queueId", 0)
        summary.season_id = data.get("seasonId", 0)

        # 转换时间戳为datetime对象
        if "gameCreation" in data:
            # 游戏创建时间通常是毫秒级时间戳
            summary.game_creation_date = datetime.fromtimestamp(data["gameCreation"] / 1000)

        # 解析参与者身份信息
        for pi_data in data.get("participantIdentities", []):
            pi = ParticipantIdentity()
            pi.participant_id = pi_data.get("participantId", 0)

            # 解析玩家信息
            player_data = pi_data.get("player", {})
            pi.player = ParticipantPlayer(
                summoner_id=player_data.get("summonerId", 0),
                summoner_name=player_data.get("summonerName", ""),
                puuid=player_data.get("puuid", ""),
                account_id=player_data.get("accountId", ""),
                current_platform_id=player_data.get("currentPlatformId", ""),
                platform_id=player_data.get("platformId", ""),
                current_account_id=player_data.get("accountId", ""),
                match_history_uri=player_data.get("matchHistoryUri", ""),
                profile_icon=player_data.get("profileIcon", 0),
            )
            summary.participant_identities.append(pi)

        # 解析参与者信息
        for p_data in data.get("participants", []):
            p = Participant()
            p.participant_id = p_data.get("participantId", 0)
            p.team_id = p_data.get("teamId", 0)
            p.champion_id = p_data.get("championId", 0)
            p.spell1_id = p_data.get("spell1Id", 0)
            p.spell2_id = p_data.get("spell2Id", 0)
            p.stats = p_data.get("stats", {})
            p.timeline = p_data.get("timeline", {})
            summary.participants.append(p)

        # 解析队伍信息
        for t_data in data.get("teams", []):
            t = Team()
            t.team_id = t_data.get("teamId", 0)
            t.win = t_data.get("win", "")
            t.baron_kills = t_data.get("baronKills", 0)
            t.dominion_victory_score = t_data.get("dominionVictoryScore", 0)
            t.dragon_kills = t_data.get("dragonKills", 0)
            t.first_baron = t_data.get("firstBaron", False)
            t.first_blood = t_data.get("firstBlood", False)
            t.first_dragon = t_data.get("firstDargon", False)  # 注意：Go代码中拼写为firstDargon
            t.first_inhibitor = t_data.get("firstInhibitor", False)
            t.first_tower = t_data.get("firstTower", False)
            t.inhibitor_kills = t_data.get("inhibitorKills", 0)
            t.rift_herald_kills = t_data.get("riftHeraldKills", 0)
            t.tower_kills = t_data.get("towerKills", 0)
            t.vilemaw_kills = t_data.get("vilemawKills", 0)

            # 解析禁用英雄信息
            for ban_data in t_data.get("bans", []):
                ban = TeamBan(
                    champion_id=ban_data.get("championId", 0),
                    pick_turn=ban_data.get("pickTurn", 0)
                )
                t.bans.append(ban)

            summary.teams.append(t)

        return summary

    def find_participant_by_summoner_id(self, summoner_id: int) -> Optional[Participant]:
        """通过召唤师ID查找参与者信息"""
        # 首先在participantIdentities中查找participant_id
        participant_id = None
        for identity in self.participant_identities:
            if identity.player.summoner_id == summoner_id:
                participant_id = identity.participant_id
                break

        if participant_id is None:
            return None

        # 在participants中查找对应的参与者
        for participant in self.participants:
            if participant.participant_id == participant_id:
                return participant

        return None
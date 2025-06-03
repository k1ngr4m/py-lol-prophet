from dataclasses import dataclass, field
from typing import List, Optional, Any, Union
from datetime import datetime


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
    account_id: int
    current_account_id: int
    current_platform_id: str
    match_history_uri: str
    platform_id: str
    profile_icon: int
    summoner_id: int
    summoner_name: str
    game_name: Optional[str] = None
    puuid: Optional[str] = None
    tag_line: Optional[str] = None


@dataclass
class Participant:
    champion_id: int
    highest_achieved_season_tier: str
    participant_id: int
    spell1_id: int
    spell2_id: int
    # stats and timeline fields omitted for brevity
    # they should be modeled similarly to PerMinDeltas and ParticipantPlayer


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
    participant_identities: List[dict]
    participants: List[dict]
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

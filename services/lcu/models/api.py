from dataclasses import dataclass, field
from typing import Any, Optional

@dataclass
class LolData:
    champion_id: str
    companion_id: str
    damage_skin_id: str
    game_queue_type: str
    game_status: str
    icon_override: str
    legendary_mastery_score: str
    level: str
    map_id: str
    map_skin_id: str
    puuid: str
    ranked_league_division: str
    ranked_league_queue: str
    ranked_league_tier: str
    ranked_losses: str
    ranked_prev_season_division: str
    ranked_prev_season_tier: str
    ranked_split_reward_level: str
    ranked_wins: str
    regalia: str
    skin_variant: str
    skinname: str

@dataclass
class SummonerProfileData:
    availability: str
    game_name: str
    game_tag: str
    icon: int
    id: str
    last_seen_online_timestamp: Optional[Any]  # 可能是 null 或时间戳
    lol: LolData
    name: str
    obfuscated_summoner_id: int
    patchline: str
    pid: str
    platform_id: str
    product: str
    product_name: str
    puuid: str
    status_message: str
    summary: str
    summoner_id: int
    time: int


from typing import Dict


class Api:
    def __init__(self, prophet: 'Prophet'):
        self.p = prophet  # 用字符串避免循环导入

class SummonerNameReq:
    def __init__(self, summoner_name: str = ""):
        self.summoner_name = summoner_name

    def to_dict(self) -> Dict[str, str]:
        """转换为字典，用于JSON序列化"""
        return {"summonerName": self.summoner_name}

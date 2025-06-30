import time

from fastapi import HTTPException, Request
import json
from typing import Any, Dict, Optional

import global_conf.global_conf as global_vars
from plugins.sol101.common import get_user_game_history_list, list_game_history
from plugins.sol101.update_db import update_summoner_data_to_db
from services.db.models import config
from services.lcu import common
from services.lcu import api
from app import get_user_score
from services.lcu.client import cli
from services.lcu.models.api import Summoner
from plugins.sol101.score_cal import get_filtered_data


class Api:
    def __init__(self, prophet: Any):
        self.prophet = prophet

    async def ProphetActiveMid(self):
        """检查LCU是否激活的中间件"""
        if not self.prophet.is_lcu_active():
            raise HTTPException(status_code=400, detail="请检查lol客户端是否已启动")
        return True

    async def QueryHorseBySummonerName(self, request: Request):
        data = await request.json()
        summoner_name = data.get("summonerName", "").strip()

        # 确保 prophet 已初始化 LCU 客户端
        if not hasattr(self.prophet, 'lcu_client') or self.prophet.lcu_client is None:
            raise HTTPException(status_code=500, detail="LCU 客户端未初始化")

        # 获取召唤师信息
        if not summoner_name:
            if not self.prophet.curr_summoner:
                raise HTTPException(status_code=500, detail="系统错误")
            summoner = common.convert_curr_summoner_to_summoner(self.prophet.curr_summoner)
        else:
            # 使用 prophet 的 lcu_client 实例
            summoner_info = api.query_summoner_by_name(summoner_name, self.prophet.lcu_client)
            if not summoner_info or summoner_info.summoner_id <= 0:
                raise HTTPException(status_code=404, detail="未查询到召唤师")
            summoner = summoner_info

        # 计算用户分数（假设已实现）
        score_info = get_user_score(summoner,self.prophet.lcu_client)
        score_cfg = global_vars.get_score_conf()
        client_user_cfg = global_vars.get_client_user_conf()

        # 确定马匹等级
        horse = ""
        for i, v in enumerate(score_cfg.Horse):
            if score_info.score >= v.Score:
                horse = client_user_cfg.HorseNameConf[i]
                break

        return {
            "score": score_info.score,
            # "currKDA": score_info.curr_kda,
            "horse": horse
        }

    async def GetSummonerInfoByName(self, request: Request):
        data = await request.json()
        summoner_name = data.get("name", "").strip()
        summoner_info = api.query_summoner_by_name(summoner_name, self.prophet.lcu_client)
        return {
            "code": 0,
            "msg": "success",
            "data": summoner_info.__dict__
        }
    async def GetCurrSummoner(self, request: Request):
        if not self.prophet.curr_summoner:
            for attempt in range(5):
                try:
                    curr_summoner = api.get_summoner_profile(self.prophet.lcu_client)
                    self.prophet.curr_summoner = curr_summoner
                    break
                except Exception:
                    time.sleep(1)

        summoner_name = self.prophet.curr_summoner.gameName
        tag_line = self.prophet.curr_summoner.gameTag
        summoner_all_name = summoner_name + "#" + tag_line
        return {
            "code": 0,
            "msg": "success",
            "data":{
                "summonerName": summoner_all_name
            }
        }

    async def CopyHorseMsgToClipBoard(self, request: Request):
        # 剪贴板功能实现（此处简化）
        return {"code": 0, "msg": "success"}

    async def GetAllConf(self, request: Request):
        return global_vars.get_client_user_conf().__dict__

    async def UpdateClientConf(self, request: Request):
        data = await request.json()
        updated_conf = global_vars.set_client_user_conf(data)

        # 保存到数据库
        conf_str = json.dumps(updated_conf.__dict__)
        m = config.Config()
        if not m.update(config.LOCAL_CLIENT_CONF_KEY, conf_str):
            raise HTTPException(status_code=500, detail="配置更新失败")

        return {"code": 0, "msg": "success"}

    async def DevHand(self, request: Request):
        return {"buffge": 23456}

    async def GetAppInfo(self, request: Request):
        return global_vars.AppBuildInfo.__dict__

    async def GetLcuAuthInfo(self, request: Request):
        try:
            port, token = common.get_lol_client_api_info()
            return {"port": port, "token": token}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def LcuProxy(self, request: Request):
        if not self.prophet.lcu_rp:
            raise HTTPException(status_code=500, detail="反向代理未初始化")

        # 处理代理请求
        full_path = request.path_params.get("full_path", "")
        return await self.prophet.lcu_rp.proxy_request(request, full_path)

    # 辅助方法
    # def get_user_score(self, summoner: Summoner) -> Any:
    #     """计算用户分数（需根据业务逻辑实现）"""
    #
    #     # 示例返回对象
    #     class ScoreInfo:
    #         def __init__(self, score, curr_kda):
    #             self.score = score
    #             self.curr_kda = curr_kda
    #
    #     return ScoreInfo(score=150, curr_kda="5/2/8")

    async def QuerySummonerMatchesList(self, request):
        data = await request.json()
        summoner_name = data.get("name", "").strip()
        page = int(data.get("page", 1))  # 默认第一页
        page_size = int(data.get("limit", 10))  # 默认每页10条

        if page < 1:
            page = 1
        if page_size < 1 or page_size > 200:  # 限制每页最多100条
            page_size = 10

        # 确保 prophet 已初始化 LCU 客户端
        if not hasattr(self.prophet, 'lcu_client') or self.prophet.lcu_client is None:
            raise HTTPException(status_code=500, detail="LCU 客户端未初始化")

        # 获取召唤师信息
        if not summoner_name:
            if not self.prophet.curr_summoner:
                raise HTTPException(status_code=500, detail="系统错误")
            summoner = common.convert_curr_summoner_to_summoner(self.prophet.curr_summoner)
        else:
            # 使用 prophet 的 lcu_client 实例
            summoner_info = api.query_summoner_by_name(summoner_name, self.prophet.lcu_client)
            if not summoner_info or summoner_info.summoner_id <= 0:
                raise HTTPException(status_code=404, detail="未查询到召唤师")
            summoner = summoner_info

        # 计算分页参数
        begin = (page - 1) * page_size
        limit = page_size

        # 直接获取分页后的游戏历史
        resp = list_game_history(summoner.puuid, begin, limit, self.prophet.lcu_client)
        if not resp:
            return {
                "code": 0,
                "msg": "success",
                "data": {
                    "items": [],
                    "total": 0,
                    "page": page,
                    "page_size": page_size,
                    "has_more": False
                }
            }

        # 处理游戏数据
        game_list = resp
        # 反转列表使对局按时间从旧到新排序
        # game_list.reverse()

        summoner_id = summoner.account_id
        filtered_data = [get_filtered_data(game, summoner_id, summoner_name)
                         for game in game_list
                         if int(game.get("gameDuration", 0)) > 260]

        if filtered_data:
            update_summoner_data_to_db(filtered_data)

        # 由于LCU API没有直接返回总条数，我们通过判断返回数量是否等于请求数量来推测是否有更多数据
        has_more = len(game_list) == page_size

        return {
            "code": 0,
            "msg": "success",
            "data": {
                "items": game_list,
                "page": page,
                "page_size": len(game_list),
                "has_more": has_more
            }
        }

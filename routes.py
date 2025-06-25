from fastapi import Request, APIRouter, Depends, FastAPI

from api import Api


def register_routes(app: FastAPI, api: Api):
    # 1. “test” 路由，支持所有 HTTP 方法
    @app.api_route(
        "/test",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )
    async def test_handler(request: Request):
        if request.method == "OPTIONS":
            return {"status": "OK"}
        return await api.DevHand(request)

    # 2. 创建 /v1 路由组
    v1 = APIRouter(prefix="/v1")

    @v1.get(
        "/getCurrSummoner"
    )
    async def get_curr_summoner(request: Request):
        return await api.GetCurrSummoner(request)

    @v1.post(
        "/summoner/queryByName/info",
        dependencies=[Depends(api.ProphetActiveMid)],
    )
    async def get_summoner_info(request: Request):
        return await api.GetSummonerInfoByName(request)

    # 2.1 查询用户马匹信息（带中间件 ProphetActiveMid）
    @v1.post(
        "/horse/queryBySummonerName",
        dependencies=[Depends(api.ProphetActiveMid)],
    )
    async def query_horse_by_summoner(request: Request):
        return await api.QueryHorseBySummonerName(request)

    # 2.2 获取所有配置
    @v1.post("/config/getAll")
    async def get_all_conf(request: Request):
        return await api.GetAllConf(request)

    # 2.3 更新配置
    @v1.post("/config/update")
    async def update_client_conf(request: Request):
        return await api.UpdateClientConf(request)

    # 2.4 获取 LCU 认证信息
    @v1.post("/lcu/getAuthInfo")
    async def get_lcu_auth_info(request: Request):
        return await api.GetLcuAuthInfo(request)

    # 2.5 获取 App 信息
    @v1.post("/app/getInfo")
    async def get_app_info(request: Request):
        return await api.GetAppInfo(request)

    # 2.6 复制马匹信息到剪切板
    @v1.post("/horse/copyHorseMsgToClipBoard")
    async def copy_horse_msg(request: Request):
        return await api.CopyHorseMsgToClipBoard(request)

    # 2.7 LCU Proxy（支持所有 HTTP 方法，使用 Catch‐all 路径参数）
    @v1.api_route(
        "/lcu/proxy/{full_path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    )
    async def lcu_proxy_handler(request: Request, full_path: str):
        # 如果 api.LcuProxy 需要知道原始请求的路径，可以从 `full_path` 里取
        # 也可以直接把 Request 对象传进去，让后端自己从 request.url.path 里解析
        return await api.LcuProxy(request)

    # 最后把 v1 注册到主应用
    app.include_router(v1)
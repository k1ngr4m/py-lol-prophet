from routes import register_routes
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from api import Api

class Prophet:

    def init_fastapi(self):

        app = FastAPI()
        api = Api()  # 实例化你的 API 类
        # 5. 注册路由
        register_routes(app, self.api)
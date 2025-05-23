"""
路由模块，对应原Go代码中的routes.go
"""

from flask import Flask, request, jsonify, send_from_directory
import os
import json
from typing import Dict, Any, Callable


class Router:
    """路由管理器"""

    def __init__(self, app: Flask):
        """
        初始化路由管理器

        Args:
            app: Flask应用实例
        """
        self.app = app
        self.routes = {}

    def register_routes(self):
        """注册所有路由"""
        # API路由
        self.app.route('/api/version')(self.handle_version)
        self.app.route('/api/config', methods=['GET'])(self.handle_get_config)
        self.app.route('/api/config', methods=['POST'])(self.handle_update_config)
        self.app.route('/api/game/accept', methods=['POST'])(self.handle_accept_game)
        self.app.route('/api/game/score', methods=['GET'])(self.handle_get_game_score)

        # 静态文件路由
        @self.app.route('/')
        def index():
            return send_from_directory(self.get_static_dir(), 'index.html')

        @self.app.route('/<path:path>')
        def static_files(path):
            return send_from_directory(self.get_static_dir(), path)

    def get_static_dir(self) -> str:
        """获取静态文件目录"""
        # 获取当前脚本所在目录
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 静态文件目录
        static_dir = os.path.join(current_dir, '..', 'static')
        return os.path.abspath(static_dir)

    def set_handler(self, route: str, handler: Callable):
        """
        设置路由处理器

        Args:
            route: 路由路径
            handler: 处理函数
        """
        self.routes[route] = handler

    def handle_version(self):
        """处理版本请求"""
        import version
        return jsonify({
            'version': version.APP_VERSION,
            'commit': version.COMMIT,
            'buildTime': version.BUILD_TIME
        })

    def handle_get_config(self):
        """处理获取配置请求"""
        from global_conf.global_conf import get_client_user_conf
        config = get_client_user_conf()
        return jsonify(config.__dict__)

    def handle_update_config(self):
        """处理更新配置请求"""
        from global_conf.global_conf import set_client_user_conf
        try:
            config = request.json
            updated_config = set_client_user_conf(config)
            return jsonify({
                'status': 'success',
                'data': updated_config.__dict__
            })
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 400

    def handle_accept_game(self):
        """处理接受游戏请求"""
        if 'accept_game' in self.routes:
            result = self.routes['accept_game']()
            return jsonify({
                'status': 'success',
                'data': result
            })
        return jsonify({
            'status': 'error',
            'message': '功能未实现'
        }), 501

    def handle_get_game_score(self):
        """处理获取游戏评分请求"""
        if 'get_game_score' in self.routes:
            result = self.routes['get_game_score']()
            return jsonify({
                'status': 'success',
                'data': result
            })
        return jsonify({
            'status': 'error',
            'message': '功能未实现'
        }), 501

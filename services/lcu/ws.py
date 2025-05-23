"""
WebSocket模块，对应原Go代码中的ws.go
"""

import asyncio
import json
import logging
import threading
import time
import websockets
from typing import Dict, List, Any, Callable, Optional, Union

class WebSocketServer:
    """WebSocket服务器实现"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8080):
        self.host = host
        self.port = port
        self.clients = set()
        self.server = None
        self.running = False
        self.logger = logging.getLogger("WebSocketServer")
    
    async def handler(self, websocket, path):
        """处理WebSocket连接"""
        self.clients.add(websocket)
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    # 处理消息
                    response = {"status": "ok", "message": "received"}
                    await websocket.send(json.dumps(response))
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({"status": "error", "message": "Invalid JSON"}))
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.remove(websocket)
    
    async def broadcast(self, message: Union[str, Dict, List]):
        """向所有客户端广播消息"""
        if isinstance(message, (dict, list)):
            message = json.dumps(message)
        
        if not self.clients:
            return
            
        await asyncio.gather(
            *[client.send(message) for client in self.clients],
            return_exceptions=True
        )
    
    async def start_server(self):
        """启动WebSocket服务器"""
        self.server = await websockets.serve(self.handler, self.host, self.port)
        self.running = True
        self.logger.info(f"WebSocket服务器已启动: ws://{self.host}:{self.port}")
        await self.server.wait_closed()
    
    def start(self):
        """在新线程中启动服务器"""
        def run_server():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.start_server())
        
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        return thread
    
    def stop(self):
        """停止WebSocket服务器"""
        if self.server:
            self.server.close()
            self.running = False
            self.logger.info("WebSocket服务器已停止")

class WebSocketClient:
    """WebSocket客户端实现"""
    
    def __init__(self, url: str):
        self.url = url
        self.websocket = None
        self.connected = False
        self.running = False
        self.message_handlers = []
        self.logger = logging.getLogger("WebSocketClient")
    
    def add_message_handler(self, handler: Callable[[str], None]):
        """添加消息处理器"""
        self.message_handlers.append(handler)
    
    async def connect(self):
        """连接到WebSocket服务器"""
        try:
            self.websocket = await websockets.connect(self.url)
            self.connected = True
            self.logger.info(f"已连接到WebSocket服务器: {self.url}")
            return True
        except Exception as e:
            self.logger.error(f"连接WebSocket服务器失败: {e}")
            return False
    
    async def disconnect(self):
        """断开与WebSocket服务器的连接"""
        if self.websocket:
            await self.websocket.close()
            self.connected = False
            self.logger.info("已断开与WebSocket服务器的连接")
    
    async def send(self, message: Union[str, Dict, List]):
        """发送消息到服务器"""
        if not self.connected:
            self.logger.error("未连接到WebSocket服务器")
            return False
        
        try:
            if isinstance(message, (dict, list)):
                message = json.dumps(message)
            
            await self.websocket.send(message)
            return True
        except Exception as e:
            self.logger.error(f"发送消息失败: {e}")
            return False
    
    async def receive_loop(self):
        """接收消息循环"""
        if not self.connected:
            return
        
        self.running = True
        try:
            while self.running and self.connected:
                try:
                    message = await self.websocket.recv()
                    for handler in self.message_handlers:
                        try:
                            handler(message)
                        except Exception as e:
                            self.logger.error(f"处理消息时出错: {e}")
                except websockets.exceptions.ConnectionClosed:
                    self.connected = False
                    self.logger.info("WebSocket连接已关闭")
                    break
        finally:
            self.running = False
    
    def start_receiving(self):
        """在新线程中启动接收循环"""
        def run_client():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.connect())
            if self.connected:
                loop.run_until_complete(self.receive_loop())
        
        thread = threading.Thread(target=run_client, daemon=True)
        thread.start()
        return thread
    
    def stop(self):
        """停止客户端"""
        self.running = False
        
        async def close():
            await self.disconnect()
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(close())

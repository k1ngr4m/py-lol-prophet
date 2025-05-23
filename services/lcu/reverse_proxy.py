"""
反向代理模块，对应原Go代码中的reverseProxy.go
"""

import http.server
import socketserver
import urllib.request
import urllib.error
import urllib.parse
import threading
from typing import Dict, Optional, Tuple, Callable

class ReverseProxyHandler(http.server.BaseHTTPRequestHandler):
    """反向代理处理器"""
    
    # 目标服务器URL
    target_url = ""
    
    # 请求处理器
    request_handler = None
    
    # 响应处理器
    response_handler = None
    
    def do_GET(self):
        """处理GET请求"""
        self._handle_request("GET")
    
    def do_POST(self):
        """处理POST请求"""
        self._handle_request("POST")
    
    def do_PUT(self):
        """处理PUT请求"""
        self._handle_request("PUT")
    
    def do_DELETE(self):
        """处理DELETE请求"""
        self._handle_request("DELETE")
    
    def do_OPTIONS(self):
        """处理OPTIONS请求"""
        self._handle_request("OPTIONS")
    
    def _handle_request(self, method: str):
        """处理HTTP请求"""
        target = self.target_url + self.path
        
        # 读取请求内容
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else None
        
        # 构建请求
        headers = {}
        for key, value in self.headers.items():
            if key.lower() not in ('host', 'content-length'):
                headers[key] = value
        
        # 调用请求处理器
        if self.request_handler:
            target, method, headers, body = self.request_handler(target, method, headers, body)
        
        # 创建请求
        req = urllib.request.Request(
            url=target,
            data=body,
            headers=headers,
            method=method
        )
        
        try:
            # 发送请求
            with urllib.request.urlopen(req) as response:
                # 获取响应
                status_code = response.status
                response_headers = response.headers
                response_body = response.read()
                
                # 调用响应处理器
                if self.response_handler:
                    status_code, response_headers, response_body = self.response_handler(
                        status_code, dict(response_headers), response_body
                    )
                
                # 发送响应
                self.send_response(status_code)
                
                # 设置响应头
                for key, value in response_headers.items():
                    if key.lower() not in ('server', 'date', 'transfer-encoding'):
                        self.send_header(key, value)
                
                self.end_headers()
                
                # 发送响应体
                if response_body:
                    self.wfile.write(response_body)
                
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            for key, value in e.headers.items():
                if key.lower() not in ('server', 'date', 'transfer-encoding'):
                    self.send_header(key, value)
            self.end_headers()
            if e.fp:
                self.wfile.write(e.fp.read())
        
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode('utf-8'))
    
    def log_message(self, format, *args):
        """重写日志方法，避免输出到控制台"""
        pass

class ReverseProxy:
    """反向代理服务器"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8000, target_url: str = ""):
        """
        初始化反向代理服务器
        
        Args:
            host: 监听主机
            port: 监听端口
            target_url: 目标服务器URL
        """
        self.host = host
        self.port = port
        self.target_url = target_url
        self.server = None
        self.server_thread = None
        
        # 创建处理器类
        handler_class = type('CustomReverseProxyHandler', (ReverseProxyHandler,), {
            'target_url': target_url,
            'request_handler': None,
            'response_handler': None
        })
        
        self.handler_class = handler_class
    
    def set_request_handler(self, handler: Callable[[str, str, Dict, Optional[bytes]], Tuple[str, str, Dict, Optional[bytes]]]):
        """
        设置请求处理器
        
        Args:
            handler: 请求处理函数，接收(target_url, method, headers, body)，返回修改后的值
        """
        self.handler_class.request_handler = handler
    
    def set_response_handler(self, handler: Callable[[int, Dict, bytes], Tuple[int, Dict, bytes]]):
        """
        设置响应处理器
        
        Args:
            handler: 响应处理函数，接收(status_code, headers, body)，返回修改后的值
        """
        self.handler_class.response_handler = handler
    
    def start(self):
        """启动反向代理服务器"""
        if self.server:
            return
        
        self.server = socketserver.ThreadingTCPServer((self.host, self.port), self.handler_class)
        
        def run_server():
            self.server.serve_forever()
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
    
    def stop(self):
        """停止反向代理服务器"""
        if self.server:
            self.server.shutdown()
            self.server = None
            self.server_thread = None

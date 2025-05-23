import argparse
import http.server
import logging
import ssl
import threading
import time
import urllib.request
import urllib.error
import urllib.parse

from http.client import HTTPSConnection
from urllib.parse import urlparse, parse_qs

# 模拟 lcu.GetLolClientApiInfo()
def get_lol_client_api_info():
    # 实际应替换为真实逻辑，例如通过扫描进程或文件读取端口与 token
    return 2999, "your-lcu-token"

class LCUProxyHandler(http.server.BaseHTTPRequestHandler):
    proxy_url = ""
    client_context = ssl._create_unverified_context()

    def do_GET(self):
        try:
            parsed = urllib.parse.urlparse(self.path)
            url = f"{self.proxy_url}{parsed.path}?{parsed.query}"

            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, context=self.client_context) as resp:
                self.send_response(resp.status)
                for key, value in resp.getheaders():
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(resp.read())
        except Exception as e:
            self.send_error(500, f"Internal error: {e}")

    def do_POST(self):
        self.do_METHOD("POST")

    def do_PUT(self):
        self.do_METHOD("PUT")

    def do_DELETE(self):
        self.do_METHOD("DELETE")

    def do_METHOD(self, method):
        try:
            parsed = urllib.parse.urlparse(self.path)
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length) if length else None
            url = f"{self.proxy_url}{parsed.path}?{parsed.query}"

            req = urllib.request.Request(url, data=body, headers=self.headers, method=method)
            with urllib.request.urlopen(req, context=self.client_context) as resp:
                self.send_response(resp.status)
                for key, value in resp.getheaders():
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(resp.read())
        except Exception as e:
            self.send_error(500, f"Internal error: {e}")

def run_server(port):
    server_address = ('', port)
    handler_class = LCUProxyHandler
    httpd = http.server.HTTPServer(server_address, handler_class)

    def update_proxy_url():
        while True:
            try:
                lcu_port, lcu_token = get_lol_client_api_info()
                new_proxy_url = f"https://riot:{lcu_token}@127.0.0.1:{lcu_port}"
                if handler_class.proxy_url != new_proxy_url:
                    handler_class.proxy_url = new_proxy_url
                    logging.info(f"Updated LCU proxy URL: {new_proxy_url}")
            except Exception:
                pass
            time.sleep(3)

    threading.Thread(target=update_proxy_url, daemon=True).start()
    logging.info(f"Listening on :{port}")
    httpd.serve_forever()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8098, help='LCU 代理端口')
    args = parser.parse_args()
    run_server(args.port)

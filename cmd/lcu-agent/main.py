import argparse
import http.server
import logging
import ssl
import threading
import time
import urllib.request
import urllib.error
import urllib.parse
from services.lcu.windows import get_lol_client_api_info
from http.client import HTTPSConnection
from urllib.parse import urlparse, parse_qs


class LCUProxyHandler(http.server.BaseHTTPRequestHandler):
    proxy_url = ""
    client_context = ssl._create_unverified_context()

    def do_GET(self):
        self.handle_request("GET")

    def do_POST(self):
        self.handle_request("POST")

    def do_PUT(self):
        self.handle_request("PUT")

    def do_DELETE(self):
        self.handle_request("DELETE")

    def do_PATCH(self):
        self.handle_request("PATCH")

    def handle_request(self, method):
        try:
            parsed = urllib.parse.urlparse(self.path)
            url = f"{self.proxy_url}{parsed.path}?{parsed.query}"

            # 处理headers
            headers = {k: v for k, v in self.headers.items() if k.lower() != 'host'}

            # 处理body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length) if content_length > 0 else None

            req = urllib.request.Request(
                url,
                data=body,
                headers=headers,
                method=method
            )

            with urllib.request.urlopen(req, context=self.client_context) as resp:
                self.send_response(resp.status)
                # 复制所有响应头
                for key, value in resp.headers.items():
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(resp.read())

        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            for key, value in e.headers.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_error(500, f"Internal error: {str(e)}")
            logging.exception("Proxy error")

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

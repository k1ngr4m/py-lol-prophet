from wsgiref.simple_server import make_server

from services.lcu import common, reverse_proxy
from services.lcu.reverse_proxy import RP

def main():
    port, token = common.get_lol_client_api_info()
    rp_app = reverse_proxy.new_rp(port, token)
    server = make_server('0.0.0.0', 7777, rp_app)
    server.serve_forever()

if __name__ == "__main__":
    main()
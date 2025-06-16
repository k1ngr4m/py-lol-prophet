from wsgiref.simple_server import make_server
from services.lcu import common
from services.lcu.reverse_proxy import RP

try:
    # 获取LCU客户端的端口和认证令牌
    port, token = common.get_lol_client_api_info()
    print(f"LCU API 端口: {port}, 令牌: {token[:8]}...")  # 只显示令牌前8位

    # 创建反向代理应用
    rp_app = RP(port=port, token=token)

    # 在0.0.0.0地址(所有可用网络接口)上启动服务器，监听7777端口
    server = make_server('0.0.0.0', 7777, rp_app)
    print("反向代理服务器已启动，监听端口7777")
    print("访问 http://localhost:7777/lol-summoner/v1/current-summoner 测试")

    # 启动服务器，开始接受请求
    server.serve_forever()

except Exception as e:
    print(f"发生错误: {str(e)}")
    import traceback

    traceback.print_exc()  # 打印详细的错误堆栈信息
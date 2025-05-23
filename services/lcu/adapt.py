# import platform
#
# def get_lol_client_api_info():
#     """跨平台获取 LCU 客户端端口与令牌"""
#     if platform.system().lower() == "windows":
#         return get_lol_client_api_info_windows()
#     else:
#         return get_lol_client_api_info_adapt()

import platform

def get_lol_client_api_info_adapt():
    """Linux/macOS 适配器：默认不支持，返回空值"""
    if platform.system().lower() == "windows":
        raise RuntimeError("此适配器仅用于非 Windows 系统")
    return 0, "", None

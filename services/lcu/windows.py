# windows.py
import re
from typing import Tuple

import psutil

from services.lcu.common import LolProcessNotFoundError
from pkg.windows.process.process import Process, ProcessNotFound

# LOL_UX_PROCESS_NAME = "LeagueClientUx.exe"
# COMMANDLINE_REGEX = re.compile(r'--remoting-auth-token=([\w-]+).*?--app-port=(\d+)')
#
# def get_lol_client_info() -> Tuple[int, str]:
#     for proc in psutil.process_iter(['name', 'cmdline']):
#         try:
#             if proc.info['name'] == LOL_UX_PROCESS_NAME:
#                 cmdline = ' '.join(proc.info['cmdline'])
#                 match = COMMANDLINE_REGEX.search(cmdline)
#                 if match:
#                     return int(match.group(2)), match.group(1)
#         except (psutil.NoSuchProcess, psutil.AccessDenied):
#             continue
#     raise LolProcessNotFoundError("未找到LOL进程")
#
# # 兼容旧版本调用
# GetLolClientApiInfoAdapt = get_lol_client_info
# GetLolClientApiInfoV3 = get_lol_client_info


LOL_UX_PROCESS_NAME = "LeagueClientUx.exe"
COMMANDLINE_REG = re.compile(r'--remoting-auth-token=([^"]+).*?--app-port=(\d+)')


def get_lol_client_api_info():
    return get_lol_client_api_info_v3()


def get_lol_client_api_info_v3():
    try:
        cmdline = Process.get_process_command(LOL_UX_PROCESS_NAME)
    except ProcessNotFound:
        raise LolProcessNotFound()

    match = COMMANDLINE_REG.search(cmdline)
    if not match or len(match.groups()) < 2:
        raise LolProcessNotFound()

    return int(match.group(2)), match.group(1)


class LolProcessNotFound(Exception):
    pass

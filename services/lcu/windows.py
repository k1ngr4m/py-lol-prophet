# windows.py
import re
from typing import Tuple

import psutil

from services.lcu.common import LolProcessNotFoundError

LOL_UX_PROCESS_NAME = "LeagueClientUx.exe"
COMMANDLINE_REGEX = re.compile(r'--remoting-auth-token=([\w-]+).*?--app-port=(\d+)')

def get_lol_client_info() -> Tuple[int, str]:
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            if proc.info['name'] == LOL_UX_PROCESS_NAME:
                cmdline = ' '.join(proc.info['cmdline'])
                match = COMMANDLINE_REGEX.search(cmdline)
                if match:
                    return int(match.group(2)), match.group(1)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    raise LolProcessNotFoundError("未找到LOL进程")

# 兼容旧版本调用
GetLolClientApiInfoAdapt = get_lol_client_info
GetLolClientApiInfoV3 = get_lol_client_info
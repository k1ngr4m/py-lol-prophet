# windows.py
import re
from typing import Tuple

import psutil

from pkg.windows.process.process import Process, ProcessNotFound


LOL_UX_PROCESS_NAME = "LeagueClientUx.exe"
COMMANDLINE_REG = re.compile(r'--remoting-auth-token=(\S+).*?--app-port=(\d+)')


def get_lol_client_api_info_adapt():
    return get_lol_client_api_info_v3()


def get_lol_client_api_info_v3():
    try:
        cmdline = Process.get_process_command(LOL_UX_PROCESS_NAME)
    except ProcessNotFound:
        raise LolProcessNotFound()

    match = COMMANDLINE_REG.search(cmdline)
    if not match or len(match.groups()) < 2:
        raise LolProcessNotFound()
    port = int(match.group(2))
    token = match.group(1)
    return port, token


class LolProcessNotFound(Exception):
    pass

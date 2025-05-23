"""
Windows平台特定功能模块，对应原Go代码中的windows.go
"""

import os
import sys
import ctypes
from ctypes import wintypes

# Windows常量定义
ENABLE_QUICK_EDIT_MODE = 0x0040
ENABLE_EXTENDED_FLAGS = 0x0080


def init_console_adapt():
    """
    初始化控制台适配，禁用快速编辑模式
    对应原Go代码中的initConsoleAdapt函数
    """
    if os.name != 'nt':
        return

    try:
        # 获取标准输入句柄
        stdin_handle = ctypes.windll.kernel32.GetStdHandle(-10)  # STD_INPUT_HANDLE

        # 获取当前控制台模式
        console_mode = wintypes.DWORD()
        ctypes.windll.kernel32.GetConsoleMode(stdin_handle, ctypes.byref(console_mode))

        # 修改控制台模式：禁用快速编辑模式，启用扩展标志
        new_mode = (console_mode.value & ~ENABLE_QUICK_EDIT_MODE) | ENABLE_EXTENDED_FLAGS
        ctypes.windll.kernel32.SetConsoleMode(stdin_handle, new_mode)
    except Exception as e:
        print(f"初始化控制台适配失败: {e}")

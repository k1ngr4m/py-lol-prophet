"""
用户32 API模块，对应原Go代码中的user32.go
"""

import ctypes
from ctypes import wintypes
import os

# 只在Windows平台上加载user32.dll
if os.name == 'nt':
    user32 = ctypes.windll.user32
    
    # 定义Windows API函数
    def find_window(class_name, window_name):
        """查找窗口，对应FindWindowW"""
        return user32.FindWindowW(
            None if class_name is None else ctypes.c_wchar_p(class_name),
            None if window_name is None else ctypes.c_wchar_p(window_name)
        )
    
    def get_window_rect(hwnd):
        """获取窗口矩形，对应GetWindowRect"""
        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        return rect
    
    def set_foreground_window(hwnd):
        """设置前台窗口，对应SetForegroundWindow"""
        return user32.SetForegroundWindow(hwnd)
    
    def show_window(hwnd, cmd_show):
        """显示窗口，对应ShowWindow"""
        return user32.ShowWindow(hwnd, cmd_show)
    
    # 窗口显示状态常量
    SW_HIDE = 0
    SW_NORMAL = 1
    SW_MINIMIZE = 6
    SW_MAXIMIZE = 3
    SW_SHOW = 5
    SW_RESTORE = 9
else:
    # 非Windows平台提供空实现
    def find_window(class_name, window_name):
        return 0
    
    def get_window_rect(hwnd):
        class DummyRect:
            def __init__(self):
                self.left = 0
                self.top = 0
                self.right = 0
                self.bottom = 0
        return DummyRect()
    
    def set_foreground_window(hwnd):
        return False
    
    def show_window(hwnd, cmd_show):
        return False
    
    # 窗口显示状态常量
    SW_HIDE = 0
    SW_NORMAL = 1
    SW_MINIMIZE = 6
    SW_MAXIMIZE = 3
    SW_SHOW = 5
    SW_RESTORE = 9

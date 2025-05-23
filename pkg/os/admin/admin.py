"""
管理员权限模块，对应原Go代码中的admin.go
"""

import os
import sys
import ctypes

def is_admin() -> bool:
    """
    检查当前进程是否具有管理员权限
    
    Returns:
        如果具有管理员权限则返回True，否则返回False
    """
    if os.name == 'nt':
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    else:
        # 在Unix/Linux系统上，检查是否为root用户
        return os.geteuid() == 0

def must_run_with_admin():
    """
    确保程序以管理员权限运行，如果没有则尝试提升权限
    对应原Go代码中的MustRunWithAdmin函数
    """
    if not is_admin():
        if os.name == 'nt':
            # 在Windows上，尝试以管理员权限重新启动程序
            ctypes.windll.shell32.ShellExecuteW(
                None, 
                "runas", 
                sys.executable, 
                " ".join(sys.argv), 
                None, 
                1  # SW_SHOWNORMAL
            )
            sys.exit(0)
        else:
            print("此程序需要管理员权限运行")
            sys.exit(1)

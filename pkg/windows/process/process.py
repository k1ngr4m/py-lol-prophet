"""
进程管理模块，对应原Go代码中的process.go
"""

import os
import sys
import subprocess
import psutil
import time
from typing import List, Optional, Tuple


def get_process_by_name(name: str) -> List[psutil.Process]:
    """
    根据进程名称获取进程列表

    Args:
        name: 进程名称

    Returns:
        匹配的进程列表
    """
    result = []
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if proc.info['name'].lower() == name.lower():
                result.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return result


def kill_process_by_name(name: str) -> int:
    """
    根据进程名称终止进程

    Args:
        name: 进程名称

    Returns:
        终止的进程数量
    """
    count = 0
    for proc in get_process_by_name(name):
        try:
            proc.terminate()
            count += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return count


def is_process_running(name: str) -> bool:
    """
    检查指定名称的进程是否正在运行

    Args:
        name: 进程名称

    Returns:
        如果进程正在运行则返回True，否则返回False
    """
    return len(get_process_by_name(name)) > 0


def get_process_path(pid: int) -> Optional[str]:
    """
    获取进程的可执行文件路径

    Args:
        pid: 进程ID

    Returns:
        进程可执行文件的路径，如果找不到则返回None
    """
    try:
        process = psutil.Process(pid)
        return process.exe()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return None


def execute_command(command: List[str], cwd: Optional[str] = None) -> Tuple[int, str, str]:
    """
    执行命令并返回结果

    Args:
        command: 命令及参数列表
        cwd: 工作目录

    Returns:
        返回码、标准输出和标准错误的元组
    """
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            text=True
        )
        stdout, stderr = process.communicate()
        return process.returncode, stdout, stderr
    except Exception as e:
        return -1, "", str(e)


def start_process(command: List[str], cwd: Optional[str] = None) -> Optional[subprocess.Popen]:
    """
    启动进程但不等待其完成

    Args:
        command: 命令及参数列表
        cwd: 工作目录

    Returns:
        启动的进程对象，如果启动失败则返回None
    """
    try:
        # 在Windows上使用CREATE_NO_WINDOW标志
        if os.name == 'nt':
            CREATE_NO_WINDOW = 0x08000000
            process = subprocess.Popen(
                command,
                cwd=cwd,
                creationflags=CREATE_NO_WINDOW
            )
        else:
            process = subprocess.Popen(
                command,
                cwd=cwd
            )
        return process
    except Exception:
        return None

"""
主程序入口，对应原Go代码中的main.go
"""

import os
import sys
import time
import argparse
import logging
import shutil
import subprocess
from typing import Optional

import version as version
import global_conf.global_conf as global_conf
from bootstrap.init import init_app
from prophet import Prophet, new_prophet
import services.logger.logger as logger
import services.lcu.common as common
from services.buffApi import update

# 进程名称常量
PROC_NAME = "hh-lol-prophet.exe"
PROC_NEW_NAME = "hh-lol-prophet_new.exe"


def flag_init():
    """
    初始化命令行参数
    对应原Go代码中的flagInit函数
    """
    # 创建参数解析器
    parser = argparse.ArgumentParser(description="HH-LOL-Prophet")
    parser.add_argument("-v", "--version", action="store_true", help="展示版本信息")
    parser.add_argument("-u", "--update", action="store_true", help="是否是更新")
    parser.add_argument("--delUpgradeBin", action="store_true", help="是否删除升级程序")

    # 解析参数
    args = parser.parse_args()

    # 处理版本参数
    if args.version:
        print(f"当前版本:{version.APP_VERSION},commitID:{version.COMMIT},构建时间:{version.BUILD_TIME}")
        sys.exit(0)

    # 处理更新参数
    if args.update:
        err = self_update()
        if err:
            print(f"selfUpdate failed, {err}")
        return
    else:
        err = must_run_with_main()
        if err:
            sys.exit(-1)

    # 处理删除升级程序参数
    if args.delUpgradeBin:
        # 在新线程中删除升级程序
        import threading
        threading.Thread(target=remove_upgrade_bin_file).start()


def must_run_with_main() -> Optional[Exception]:
    """
    确保程序以主进程运行
    对应原Go代码中的mustRunWithMain函数

    Returns:
        如果发生错误则返回异常，否则返回None
    """
    try:
        # 获取可执行文件路径
        bin_path = sys.executable

        # 获取文件名
        bin_file_name = os.path.basename(bin_path)

        # 检查是否为新进程
        if bin_file_name == PROC_NEW_NAME:
            return Exception("当前是更新进程，禁止执行")

        return None
    except Exception as e:
        return e


def main():
    # 初始化命令行参数
    flag_init()

    # 初始化应用
    err = init_app()
    if err:
        print(f"初始化应用失败:{err}")
        sys.exit(1)

    # 注册清理函数
    import atexit
    atexit.register(global_conf.cleanup)

    # 启动检查更新线程
    import threading
    # threading.Thread(target=check_update).start()

    # 创建并运行Prophet
    prophet = new_prophet()
    err = prophet.run()
    if err:
        print(f"运行失败:{err}")
        sys.exit(1)


def remove_upgrade_bin_file() -> Optional[Exception]:
    """
    删除升级程序文件
    对应原Go代码中的removeUpgradeBinFile函数

    Returns:
        如果发生错误则返回异常，否则返回None
    """
    try:
        # 获取可执行文件路径
        bin_new_path = sys.executable

        # 检查是否为主进程
        if os.path.basename(bin_new_path) != PROC_NAME:
            return Exception("当前不是主进程 禁止执行")

        # 获取目录路径
        dir_path = os.path.dirname(os.path.abspath(bin_new_path))

        # 构建新程序路径
        bin_new_full_path = os.path.join(dir_path, PROC_NEW_NAME)

        # 删除文件
        if os.path.exists(bin_new_full_path):
            os.remove(bin_new_full_path)

        return None
    except Exception as e:
        return e


def check_update() -> Optional[Exception]:
    """
    检查更新
    对应原Go代码中的checkUpdate函数

    Returns:
        如果发生错误则返回异常，否则返回None
    """
    try:
        # 开发模式不检查更新
        if global_conf.is_dev_mode():
            return None

        # 获取当前版本信息
        # 这里需要实现获取版本信息的功能
        # 由于原Go代码中的实现依赖于API，这里先模拟
        update_info = update.get_curr_version()

        # 检查版本信息
        if not update_info["versionTag"] or not update_info["downloadUrl"]:
            return None

        # 解析版本号
        version_str = update_info["versionTag"].lstrip("v")

        # 比较版本
        if common.compare_version(version_str, version.APP_VERSION) <= 0:
            # 已是最新版本
            return None

        # 提示更新
        print("检测到更新,两秒后将更新或按回车立即更新")

        # 创建定时器和输入监听
        import threading
        import select

        # 创建事件
        done_event = threading.Event()

        # 创建输入监听线程
        def input_listener():
            input()
            done_event.set()

        input_thread = threading.Thread(target=input_listener)
        input_thread.daemon = True
        input_thread.start()

        # 等待用户输入或超时
        done_event.wait(timeout=2)

        # 下载新版本
        import requests
        import tempfile

        # 获取可执行文件路径
        bin_path = sys.executable
        dir_path = os.path.dirname(os.path.abspath(bin_path))
        bin_new_full_path = os.path.join(dir_path, PROC_NEW_NAME)

        # 下载文件
        response = requests.get(update_info["downloadUrl"], stream=True)
        if response.status_code != 200:
            return Exception("下载更新文件失败")

        # 保存文件
        with open(bin_new_full_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # 设置文件权限
        os.chmod(bin_new_full_path, 0o755)

        # 启动更新进程
        if os.name == 'nt':
            subprocess.Popen(
                ["cmd.exe", "/C", "start", bin_new_full_path, "-u", "true"],
                shell=True
            )
        else:
            subprocess.Popen([bin_new_full_path, "-u", "true"])

        # 退出当前进程
        sys.exit(0)

    except Exception as e:
        logger.error(f"检查更新失败: {e}")
        return e


def self_update() -> Optional[Exception]:
    """
    自我更新
    对应原Go代码中的selfUpdate函数

    Returns:
        如果发生错误则返回异常，否则返回None
    """
    try:
        # 获取可执行文件路径
        bin_new_path = sys.executable

        # 获取目录路径
        dir_path = os.path.dirname(os.path.abspath(bin_new_path))

        # 获取文件名
        bin_new_file_name = os.path.basename(bin_new_path)

        # 检查是否为新进程
        if bin_new_file_name != PROC_NEW_NAME:
            return None

        # 构建主程序路径
        bin_full_path = os.path.join(dir_path, PROC_NAME)

        # 检查主程序是否存在
        if not os.path.exists(bin_full_path):
            return Exception("二进制文件不存在")

        # 复制新程序到主程序
        try:
            shutil.copy2(bin_new_path, bin_full_path)
        except Exception as e:
            logger.error(f"更新失败: {e}")
            return Exception("更新失败")

        # 启动主程序
        if os.name == 'nt':
            subprocess.Popen(
                ["cmd.exe", "/C", "start", bin_full_path, "--delUpgradeBin", "true"],
                shell=True
            )
        else:
            subprocess.Popen([bin_full_path, "--delUpgradeBin", "true"])

        # 退出当前进程
        sys.exit(0)

        return None
    except Exception as e:
        return e


if __name__ == "__main__":
    main()

import argparse
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

PROC_NAME = "hh-lol-prophet.exe"
PROC_NEW_NAME = "hh-lol-prophet_new.exe"
APP_VERSION = "1.0.0"  # 示例版本
COMMIT_ID = "abcdef"
BUILD_TIME = "2025-05-23"

logging.basicConfig(level=logging.INFO)

def show_version():
    print(f"当前版本: {APP_VERSION}, commitID: {COMMIT_ID}, 构建时间: {BUILD_TIME}")

def remove_upgrade_bin_file():
    current_path = Path(sys.executable)
    if current_path.name != PROC_NAME:
        raise RuntimeError("当前不是主进程 禁止执行")
    upgrade_path = current_path.with_name(PROC_NEW_NAME)
    if upgrade_path.exists():
        upgrade_path.unlink()

def compare_versions(v1, v2):
    return (tuple(map(int, v1.split('.'))) > tuple(map(int, v2.split('.')))) - \
           (tuple(map(int, v1.split('.'))) < tuple(map(int, v2.split('.'))))

def check_update():
    # 模拟从远程获取更新信息
    update_info = {
        "VersionTag": "v1.0.1",
        "DownloadUrl": "https://example.com/hh-lol-prophet_new.exe"
    }

    version = update_info["VersionTag"].lstrip("v")
    if compare_versions(version, APP_VERSION) <= 0:
        return

    logging.info("检测到更新, 两秒后将更新或按回车立即更新")

    update_ready = threading.Event()
    def wait_for_enter():
        input()
        update_ready.set()

    threading.Thread(target=wait_for_enter).start()
    time.sleep(2)
    update_ready.set()

    # 下载新版本
    bin_new_path = Path(sys.executable).with_name(PROC_NEW_NAME)
    with urllib.request.urlopen(update_info["DownloadUrl"]) as response, open(bin_new_path, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)

    subprocess.Popen(["cmd.exe", "/C", "start", str(bin_new_path), "-u", "true"])
    sys.exit(0)

def self_update():
    bin_new_path = Path(sys.executable)
    if bin_new_path.name != PROC_NEW_NAME:
        return

    bin_path = bin_new_path.with_name(PROC_NAME)
    if not bin_path.exists():
        raise FileNotFoundError("目标文件不存在")

    with open(bin_new_path, 'rb') as src, open(bin_path, 'wb') as dst:
        shutil.copyfileobj(src, dst)

    subprocess.Popen(["cmd.exe", "/C", "start", str(bin_path), "-delUpgradeBin", "true"])
    sys.exit(0)

def main_program():
    logging.info("初始化应用成功")
    # 启动主逻辑（示例）
    logging.info("运行主程序中...")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", action="store_true", help="展示版本信息")
    parser.add_argument("-u", action="store_true", help="是否是更新")
    parser.add_argument("-delUpgradeBin", action="store_true", help="是否删除升级程序")
    args = parser.parse_args()

    if args.v:
        show_version()
        sys.exit(0)

    if args.u:
        try:
            self_update()
        except Exception as e:
            logging.error("更新失败: %s", e)
        sys.exit(0)

    if args.delUpgradeBin:
        threading.Thread(target=remove_upgrade_bin_file).start()

    if Path(sys.executable).name == PROC_NEW_NAME:
        sys.exit(-1)

    try:
        check_update()
    except Exception as e:
        logging.error("检查更新失败: %s", e)

    main_program()

if __name__ == "__main__":
    main()

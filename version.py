from global_conf.global_conf import set_app_info, AppInfo

APP_VERSION = "0.3.0"
COMMIT = "dev"
BUILD_TIME = ""
BUILD_USER = ""

# 初始化设置应用信息
set_app_info(AppInfo(
    Version=APP_VERSION,
    Commit=COMMIT,
    BuildUser=BUILD_USER,
    BuildTime=BUILD_TIME
))
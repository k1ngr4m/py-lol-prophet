# from global_conf.global_conf import set_app_info, AppInfo
#
# APP_VERSION = "0.3.0"
# COMMIT = "dev"
# BUILD_TIME = ""
# BUILD_USER = ""
#
# # 初始化设置应用信息
# set_app_info(AppInfo(
#     Version=APP_VERSION,
#     Commit=COMMIT,
#     BuildUser=BUILD_USER,
#     BuildTime=BUILD_TIME
# ))

"""
版本信息模块，对应原Go代码中的version.go
"""
import global_conf.global_conf as global_vars

# 应用版本信息
APP_VERSION = "0.3.0"  # 对应原Go代码中的APPVersion
COMMIT = "dev"     # 对应原Go代码中的Commit
BUILD_TIME = "" # 对应原Go代码中的BuildTime
BUILD_USER = ""

global_vars.set_app_info(global_vars.AppInfo(
        version=APP_VERSION,
        commit=COMMIT,
        build_time=BUILD_TIME,
        build_user=BUILD_USER
    )
)
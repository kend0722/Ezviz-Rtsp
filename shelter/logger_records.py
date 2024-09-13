"""
摄像头遮挡日志设置
"""
import logging
import os
from logging.handlers import RotatingFileHandler
# import colorlog
import sys

# 日志设置
def logger_seting():
    '''
    日志级别等级排序：critical > error > warning > info > debug
    debug : 打印全部的日志( notset 等同于 debug )
    info : 打印 info, warning, error, critical 级别的日志
    warning : 打印 warning, error, critical 级别的日志
    error : 打印 error, critical 级别的日志
    critical : 打印 critical 级别

    # https://www.cnblogs.com/Zhouzg-2018/p/10247358.html
    # https://www.cnblogs.com/luckywh/p/15088688.html
    # https://blog.csdn.net/weixin_35663151/article/details/112895277
    # https://www.jb51.net/article/230596.htm
    # https://www.ngui.cc/article/show-505978.html?action=onClick
    # https://94e.cn/info/5236
    '''
    # 日志颜色,只在控制台显示
    log_colors_config = {
        'INFO': 'blue',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red',
    }

    logger = logging.getLogger("shelter")
    logger.setLevel(logging.DEBUG)  # 日志先会过这一层，和这层等级相同，或比他高的，才能进来，才能进行下列操作
    logger.propagate = False  # 传播，向父类或根类传播
    logger.handlers.clear()  # 每次创建handler时先清空handler

    if not os.path.exists(r"/ltb_test/logger_client/"):
        os.makedirs(r"/ltb_test/logger_client/")


    ## 保存文件_debug信息
    handler_debug = RotatingFileHandler(
        "/ltb_test/logger_client/logger_shelter.log", mode='a',
        encoding='utf8')  # 创建处理器，保存文件 ,maxBytes=100 , backupCount=3,
    handler_debug.maxBytes = 1024 * 1024 * 5  # 文件最大
    handler_debug.backupCount = 5  # 最多保留
    formatter = logging.Formatter('%(asctime)s -%(filename)s -%(levelname)s -%(message)s')  # 输出格式
    handler_debug.setFormatter(formatter)  # 设置输出格式
    handler_debug.setLevel(logging.DEBUG)
    #     debug会保存大于或等于这个级别的日志，为了让debug只显示debug信息，可以添加过滤器过滤
    def filter_log_fun(record):  # 过滤器方法
        if record.levelname in ["DEBUG", "INFO"]:
            return True
        return False

    logging_filter = logging.Filter()
    logging_filter.filter = filter_log_fun
    handler_debug.addFilter(logging_filter)

    # 屏幕展示
    # console = logging.StreamHandler()  # 创建处理器，输出屏幕
    # formatter = colorlog.ColoredFormatter(  # 控制台颜色显示
    #     fmt='%(log_color)s %(asctime)s -%(name)s -%(filename)s -%(levelname)s -%(message)s',
    #     log_colors=log_colors_config)
    # console.setFormatter(formatter)  # 设置输出格式
    # console.setLevel(logging.INFO)

    # 添加控制器
    # logger.addHandler(handler_err)  # 添加
    # logger.addHandler(handler_warn)  # 添加
    logger.addHandler(handler_debug)  # 添加
    # logger.addHandler(console)  # 添加
    return logger

logger = logger_seting() #全局变量
logger.info("shelter日志加载成功")
import os
import logging
from logging.config import dictConfig

import yaml


def logger_seting(logger_type='root'):
    """
    读取日志配置文件logger_setting.yaml
    根据输入的日志类型创建并返回一个日志
    输入的类型需要与配置文件中一致
    """
    yaml_path = "\\".join(os.path.abspath(__file__).split('\\')[:-2] + ["logging.yaml"])
    with open(file=yaml_path, mode='r', encoding='utf-8') as f:
        logging_yaml = yaml.load(stream=f, Loader=yaml.FullLoader)
    handlers = logging_yaml['handlers']
    for key, value in handlers.items():
        if 'filename' in value:
            log_path = (os.path.split(value['filename'])[0])
            if not os.path.exists(log_path):
                os.makedirs(log_path)
    dictConfig(config=logging_yaml)
    logger = logging.getLogger(logger_type)
    return logger

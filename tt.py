import logging
from logging.handlers import TimedRotatingFileHandler
 
logger = logging.getLogger()  # 获取Logger对象
logger.setLevel(logging.INFO) #设置等级
handler = TimedRotatingFileHandler(f'{floder_path}/output', when="midnight", interval=1)
handler.suffix = "_%Y_%m_%d.log"  #设置的后缀名 例如我的是output 那分割后就会输出output._年_月_日.log
formatter = logging.Formatter('%(asctime)s %(funcName)s  %(threadName)s %(message)s') #设置输出格式
handler.setFormatter(formatter)
logger.addHandler(handler)
 
if __name__ == '__main__':
    logging.basicConfig(filename=f'{floder_path}/{name}.log', level=logging.INFO,format='%(asctime)s %(funcName)s %(threadName)s %(message)s')
    info_logger = logging.getLogger()  # 获取Logger对象

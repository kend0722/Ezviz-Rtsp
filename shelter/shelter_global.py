
import socket
from multiprocessing import Queue


IMG_QUEUE = Queue()  # 图片传送队列
LOGGER_QUEUE = Queue()  # 日志队列
INTERACTION_QUEUE = Queue()  # 获取控制队列
SHELTER_SCENE_IP = socket.gethostbyname(socket.getfqdn(socket.gethostname()))
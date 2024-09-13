import os
from multiprocessing import Queue
IMG_QUEUE = Queue()  # 图片队列
RESULTS_SAVE_ROOT = "/".join(os.path.abspath(__file__).split('/')[:-3] + ["results"])  # 结果图保存位置
# CLIENT_PATH = "/".join(os.path.abspath(__file__).split('/')[:-2])  # client的文件夹位置
CLIENT_PATH = "\\".join(os.path.abspath(__file__).split('\\')[:-2])
# CLIENT_PATH ='f:\\Rtsp'   # ['f:\\Rtsp\\manage\\manage_global.py']
# print(11111, CLIENT_PATH)

# if __file__ == '__main__':
#     CLIENT_PATH = "\\".join(os.path.abspath(__file__).split('\\')[:-2])
#     print(11111, CLIENT_PATH)
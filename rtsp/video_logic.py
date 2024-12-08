'''
read_video.py, 读取到的图片放到相应的队列中，由各个算法自己去做相似度对比
'''
from multiprocessing import Queue
import time
import cv2
import numpy as np
import datetime
# from _utils._conf import ConfJson
from read_video import write_video_task
from get_video_url import *
import threading
from compare_images import cmp_abs
from video_global import Algorithm_Images, Video_Images
# from _utils._comm import ManageComm
from PIL import Image
import io
import base64

class CaptureThread():
    '''采集视频流线程'''
    def __init__(self, deviceSerial):
        self.deviceSerial = deviceSerial  # 以设备序列号作为一个采集视频的线程
        self.before_frame = None   # 前一张图的占位符
        self.frame_queue_input = Queue()  # 流入口
        self.frame_queue_output = Queue()   # # 流出口
        
    def run(self):
        '''
        采图的逻辑：
        根据接口，获取到视频流地址 -> 然后每帧的图像放到队列中 ->  相似度处理后 -> 由各个算法去处理
        '''
        # 读取视频, 每个摄像头分配一个线程，用来采集图像
        
        rtmp_url = get_video_with_url_online(self.deviceSerial)['data']['url']   # 获取地址
        write_video_task(self.frame_queue_input, rtmp_url)   # 这里会一直采集图像，放到队列中
        
    def get_frame(self):
        while True:
            frame = self.frame_queue_input.get()
            # print('get frame from queue')
            self.frame_queue_output.put(frame)
            Video_Images[self.deviceSerial] = self.frame_queue_output   # 将采集到的图像放到相应设备队列中
            # print('Video_Images.key', self.deviceSerial)
        
class CompareThread():
    # # 相似度处理：比较图像，将相似度对比后的图像放到相应的设备队列中
    def __init__(self, deviceSerial):
        self.deviceSerial = deviceSerial
        self.manageComm = ManageComm()
        # self.conf_json =  ConfJson()
        self.ip = "127.0.0.1"
        self.port = 5001
        # self.frame_queue = Queue()
    def run(self):
        while True:
            try:
                # 从设备图像队列中获取图像
                image1 = Video_Images[self.deviceSerial].get()
                # 获取采集到的视频流
                if image1 is not None :
                    image2 = Video_Images[self.deviceSerial].get()
                    time_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                    # 比较图像,这里直接先搞成连续的比较
                    is_similar = cmp_abs(image1, image2)
                    if is_similar:
                        # print('相似度图类型：', type(image2))  # <class 'numpy.ndarray'>
                        quality = 75 # 图片质量
                        encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
                        img_encode = cv2.imencode('.jpg', image2, encode_params)[1]
                        str_img_encode = img_encode.tostring()  # 图片字节流
                        # with open('test.jpg', 'wb') as f:
                        #     f.write(str_img_encode)
                        # 将字节流进一步转化为base64编码的字符串：
                        # print(type(str_img_encode),11111)   # byte
                        # 图片字节流转换为base64编码的字符串
                        byte_img_base64 = base64.b64encode(str_img_encode).decode('utf-8')  # byte
                        # print(type(byte_img_base64),22222)  # str
                        send = {'name':time_str, 'frame': byte_img_base64}
                    else:
                        send = {'name':time_str, 'frame': "SIMILAR"}
                        # send = {'name':time_str, 'frame': byte_img_base64}
                    # self.frame_queue.put(send)  # 相似就打一个相似的标签
                    # print(f"相似度处理完成， 发送到算法进程：")
                    self.manageComm.send_http(ip=self.ip, port=self.port, route='/images', send_json=send)
                    time.sleep(0.1)
                    # 通过http发送到算法进程：
                    # Algorithm_Images[self.deviceSerial] = self.frame_queue
            except Exception as e:
                # print("相似度错误！",e)
                time.sleep(0.2)
            

class Video_Logic():
    
    def __init__(self, deviceSerial):
        self.deviceSerial = deviceSerial
    """
    根据接口，获取到视频流地址 -> 然后每帧的图像放到队列中 ->  相似度处理后 -> 由各个算法去处理
    """
    def run(self):
        # 采集视频流
        capture_thread = CaptureThread(self.deviceSerial)
        for i in range(1):
            # 采集视频流
            threading.Thread(target=capture_thread.run).start()
            # 图像放到对应的设备队列中
            threading.Thread(target=capture_thread.get_frame).start()
            
        # 相似度处理
        compare_thread = CompareThread(self.deviceSerial)
        compare_thread.run()
        # Algorithm_Images[self.deviceSerial] : dict() # 将处理后的图像放到相应设备的队列中
        # 算法处理， 算法根据对应的设备id获取图像
        # algorithm_thread = AlgorithmThread(self.deviceSerial)
        # algorithm_thread.run()
        # 将处理后的图像放到相应的队列中
        # Algorithm_Images[self.deviceSerial] = algorithm_thread.frame_queue
    
class ManageComm(object):
    """
    统一交互接口
    send_http：只发送，不需要返回
    """

    @staticmethod
    def send_http(ip, port, route, send_json):
        url = f'http://{ip}:{port}/{route}'
        try:
            # headers = {'Connection': 'close'}
            requests.post(url=url, json=send_json, timeout=5)
            return True
        except Exception as err:
            print("send_http_{}_{}_{}_{}".format(ip, port, route, err))
            return False


if __name__ == '__main__':
    deviceSerial = 'K26430757'
    video_logic = Video_Logic(deviceSerial)
    video_logic.run()
    # ->>算法>>Algorithm_Images[self.deviceSerial]

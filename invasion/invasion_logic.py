from multiprocessing import Queue
import time
import cv2
import numpy as np
import sys

import torch
from invasion_global import IMG_QUEUE
# print(sys.path)
from invasion.invasion_events import Invasion_Events
from rtsp.video_global import Algorithm_Images   # 根据摄像头存放图片
from invasion_web import InvasionApplication
from invasion_function import yolov5Thread
import threading
from multiprocessing.pool import ThreadPool
import datetime
import base64

from yolov5.yolov_model import DetectMultiBackend
"""
算法管理：
1. 图片接收，分配
2. 算法结果接收
3. 总管理类
"""

class ReadThread():
    """
    图片分配线程，线程池分配
    """
    def __init__(self,parent,deviceSerial):
        super(ReadThread, self).__init__()
        # print("启动图片分配线程")
        self.deviceSerial = deviceSerial
        self.parent = parent
        self.operation_queue = self.parent.operation_queue   # 
        self.cur_index = 0
        self.pool = ThreadPool(processes=20)

    def run(self):
        # print('图片分配线程启动*')
        while True:
            try:
                if IMG_QUEUE.qsize() > 1:
                    get_dict = IMG_QUEUE.get()   # send = {'name':time_str, 'frame': image2}
                    # print('获取图片成功！', datetime.datetime.now())
                    self.pool.apply_async(self.operation, args=(get_dict,))
            except Exception as e:
                print("获取图像失败！", e)
                time.sleep(0.2)

    def operation(self, get_dict):
        """
        线程池分配处理图片
        :param get_dict: {'name':time_str, 'frame': image}  # 字节流字符串
        判断【myyolov5算法-摄像头是否开启】不开启则发送关闭结果，开启则往下
        判断【图片是否相似】相似则发送想搜结果，不相似则往下
        判断【图片是否正常】异常则发送异常结果，正常则往下
        发送图片，均分给各个模型
        """
        # print("enter----------------------------------------------")
        cam_id = self.deviceSerial
        name = get_dict["name"]
        img = get_dict["frame"]
        # switch = self.parent.algorithm_switch.get(cam_id, False)
        switch = True  # 先默认是True
        if not switch:
            self.operation_queue.put(['区域入侵', cam_id, name, img, "CLOSE"])
            return
        if img == "SIMILAR":
            self.operation_queue.put(['区域入侵', cam_id, name, img, "SIMILAR"])
            print(f'key={cam_id} name={name} 区域入侵图片相似被过滤 {datetime.datetime.now()}')
        elif img == "ERROR":
            self.operation_queue.put(['区域入侵', cam_id, name, img, "ERROR"])
        else:
            try:
                # print(f'区域入侵图片长度={len(img)},{type(img)} key={cam_id} name={name} {datetime.datetime.now()}')
                # 解码Base64字符串为字节流
                img_encode = img.encode(encoding='utf-8')
                img_encode = base64.b64decode(img_encode)
                # 字节流转numpy array
                byte_img = np.fromstring(img_encode, np.uint8)
                img = cv2.imdecode(byte_img, cv2.IMREAD_COLOR)  # 通道数
                # thread_id = self.cur_index % int(self.parent.algorithm_num)
                thread_id = 0
                self.parent.thread_dict[thread_id]["queue"].put([cam_id, name, img])
                # print(f'key={cam_id} name={name}区域入侵图片解码成功 img_shape={img.shape}, {datetime.datetime.now()}')
                # self.cur_index += 1
            except Exception as e:
                self.operation_queue.put([self.parent.manage_type, cam_id, name, img, "ERROR"])
                print(f'key={cam_id} name={name} 区域入侵图片解码失败 {datetime.datetime.now(), e}')
                import traceback
                traceback.print_exc()
                return


class InvasionManage(object):
    """
    区域入侵算法总管理类，用于各线程的启动，区域入侵进程的主要入口
    """

    def __init__(self, manage_type, yolov5_type, weights_path, device, algorithm_num):
        super(InvasionManage, self).__init__()
        self.manage_type = manage_type
        self.non_max_suppression_nm = 32 if yolov5_type == "yolov5_seg" else 0
        self.weights_path = weights_path
        self.device = device
        self.algorithm_num = algorithm_num   # 1
        # self.conf_json = ConfJson()
        # self.ip = socket.gethostbyname(socket.getfqdn(socket.gethostname()))
        # self.port = 0  # 由于算法等都是动态，所以port需要动态分配，最开始是0，分配好后马上占用
        self.algorithm_kwargs = dict()  # 算法参数 {"C01JK027":{"roi":[],"iou":1,},...}
        self.algorithm_switch = dict()  # 算法开关 {"C01JK027":True,...}
        # 算法暂时没什么用，后续如果改CPU/GPU，数量等可修改，主要是roi_switch，在camera模块实现
        self.thread_dict = dict()  # 以模型为颗粒度，各模型一个检测线程，thread_dict用于存检测线程  # 算法多线程
        self.operation_queue = Queue()  # 操作队列，用于处理算法的开关，结果处理等
        
        
    def server_operation(self):
        """启动区域入侵算法服务，用于接收请求"""
        app = InvasionApplication()
        self.port = 5001
        app.run(host='127.0.0.1', port=self.port)
        
    def run(self):
        deviceSerial = "K26430757"
        # 图片传输队列
        try:
            print('invasion算法总启动')
            device = torch.device('cuda')
            weights = "F:\Rtsp\models\weights\person_number_detect_V03.pt"
            self.model = DetectMultiBackend(weights, device)
            print("model 加载成功！")
            # self.server_operation()
            threading.Thread(target=self.server_operation).start()
            
            print('invasion图像分配服务启动')
            read_images = ReadThread(self, deviceSerial)
            # read_images.run()
            threading.Thread(target=read_images.run).start()
            
            # invasion算法总启动
            for i in range(int(self.algorithm_num)):
                self.thread_dict[i] = dict()
                print(f'区域入侵算法线程{i}启动')
                self.thread_dict[i]["queue"] = Queue()    # [cam_id, name, img]
                self.thread_dict[i]["thread"] = yolov5Thread(i, self, self.model)
                self.thread_dict[i]["thread"].start()
                
        # 事件處理啓動
            invasion_events = Invasion_Events(self,deviceSerial)
            threading.Thread(target=invasion_events.run).start()
        
        # # 结果处理线程
        # self.results_thread = ResultsThread(self)
        # self.results_thread.start()
        except Exception as e:
            print(f"Error line number: {sys.exc_info()[2].tb_lineno}")
            print(f'区域入侵算法启动失败，{e}')
            
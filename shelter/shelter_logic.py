import base64
import json
import datetime
import threading
import time
import traceback
from multiprocessing import Queue
from multiprocessing.pool import ThreadPool

import cv2
import os
import numpy as np
import json
import requests
import base64
import urllib3
import M2Crypto
import time
import datetime
import socket
from shelter_global import IMG_QUEUE, LOGGER_QUEUE, SHELTER_SCENE_IP, INTERACTION_QUEUE
from shelter_function import ShelterThread
from shelter_web import ShelterApplication
# from shelter_socket_server import start_scoket_server

from _utils import ConfJson, find_port, ManageComm
from logger_records import logger


class InteractionThread(threading.Thread):
    """
    交互函数，负责与算法服务器管理端进行交互
    """

    def __init__(self, parent):
        super(InteractionThread, self).__init__()
        self.parent = parent

    def run(self):
        """
        接口一致。数据由 shelter_web 通过INTERACTION_QUEUE发送过来，各详细操作说明如下
        如果不符合规矩[interaction_type]直接丢弃
        if interaction_type == "update_algorithm" 更新shelter算法各摄像头的算法信息
        elif interaction_type == "update_switch" 更新shelter算法各摄像头的启动信息
        elif interaction_type == "update_sence" 更新shelter算法信息
        """
        while True:
            interaction_dict = INTERACTION_QUEUE.get()
            interaction_type = interaction_dict.get("interaction_type", "")
            if interaction_type == "":
                continue
            elif interaction_type == "update_algorithm":
                self.parent.algorithm_kwargs = interaction_dict.get("algorithm_kwargs", dict())
            elif interaction_type == "update_switch":
                for cam_id, value in interaction_dict.get("algorithm_switch", dict()).items():
                    self.parent.algorithm_switch[cam_id] = value
            elif interaction_type == "update_sence":
                self.parent.algorithm_info = interaction_dict.get("algorithm_info", dict())
            elif interaction_type == "shelter_from":
                camera_list = interaction_dict.get("camera_ids")
                IMG_QUEUE.put(camera_list)
                # print(f"put IMG_QUEUE {camera_list} {IMG_QUEUE.qsize()} ", flush=True)
                print(f"put IMG_QUEUE {IMG_QUEUE.qsize()} ", flush=True)


class ReadThread(threading.Thread):
    """
    图片分配线程，线程池分配
    """

    def __init__(self, parent):
        super(ReadThread, self).__init__()
        self.parent = parent
        self.operation_queue = self.parent.operation_queue
        self.cur_index = 0
        self.pool = ThreadPool(processes=200)

    def run(self):
        while True:
            camera_list = IMG_QUEUE.get()
            # print(f"get camera_list, {camera_list}", flush=True)
            try:
                for camera in camera_list:
                    # print(camera, flush=True)
                    img1_path = os.path.join("/haikui/3d_test_server/results/obj_motion", camera, "post.jpg")
                    # print(img1_path, flush=True)
                    if os.path.exists(img1_path):
                        # img1 = cv2.imdecode(np.fromfile(img1_path, dtype=np.uint8), -1)
                        thread_id = self.cur_index % self.parent.algorithm_num
                        # self.parent.thread_dict[thread_id]["queue"].put([camera, img1, img1_path])
                        self.parent.thread_dict[thread_id]["queue"].put([camera, img1_path])
                        # print("put shelter algorithm", flush=True)
                        self.cur_index += 1
            except Exception as err:
                import traceback
                traceback.print_exc()
                print(err)


class ResultsThread(threading.Thread):
    """
    结果处理线程，获取图片数据，发送给管理端，线程池发送提速
    """

    def __init__(self, parent):
        super(ResultsThread, self).__init__()
        self.parent = parent
        self.pool = ThreadPool(processes=20)

    def run(self):
        ip = socket.gethostbyname(socket.getfqdn(socket.gethostname()))
        port = ConfJson()["manage"]["port"]
        while True:
            type_, cam_id, name, original_path, results = self.parent.operation_queue.get()
            self.pool.apply_async(self.operation, args=(ip, port, cam_id, name, original_path, results))

    def operation(self, ip, port, cam_id, name, original_path, results):
        send_json = {
            "results_type": self.parent.manage_type,
            "cam_id": cam_id,
            "name": name,
            "original_path": original_path,
            "results": results,
        }
        # if results['illegal']:
        print("shelter_send_json", ip, port, send_json, flush=True)
        ManageComm().send_http(ip, port, "resutls", send_json)


class Shelter_manage(object):
    """
    摄像头遮挡的总管理类
    """

    def __init__(self, manage_type):
        super(Shelter_manage, self).__init__()
        self.algorithm_num = 1
        # print(algorithm_num, 'algorithm_num', algorithm_num)
        self.manage_type = manage_type
        self.thread_dict = dict()  # 以摄像头遮挡线程为单位，存放每个线程对应信息
        self.conf_json = ConfJson()  # 初始化读取本地json

        self.ip = socket.gethostbyname(socket.getfqdn(socket.gethostname()))
        self.port = 0  # 由于算法等都是动态，所以port需要动态分配，最开始是0，分配好后马上占用
        self.operation_queue = Queue()  # 存放结果数据
        self.algorithm_kwargs = dict()  # 算法参数 {"C01JK027":{"roi":[],"iou":1,},...}
        self.algorithm_switch = dict()  # 算法开关 {"C01JK027":True,...}
        self.algorithm_info = dict()  # 场景参数 {'摄像头遮挡': {'num': 2, 'device': 'cuda:0', 'roi_switch': 0,...},...}
        self.thread_dict = dict()  # 以模型为颗粒度，各模型一个检测线程，thread_dict用于存检测线程
        self.results_thread = None  # 结果处理线程
        self.interaction_thread = None  # 交互线程
        self.image_thread = dict()  # 传图线程
        self.shelter_server_thread = None  # 服务器线程
        self.heartbeat_thread = None  # 连接管理端

    def run(self):
        # 日志写入线程
        self.write_logger_thread = threading.Thread(target=self.write_logger_fun)
        self.write_logger_thread.start()

        # 交互线程
        self.interaction_thread = InteractionThread(self)
        self.interaction_thread.start()
        # 结果处理线程
        self.results_thread = ResultsThread(self)
        self.results_thread.start()

        # 图片传输队列
        self.image_thread = ReadThread(self)
        self.image_thread.start()
        for i in range(self.algorithm_num):
            self.thread_dict[i] = dict()
            self.thread_dict[i]["queue"] = Queue()
            self.thread_dict[i]["thread"] = ShelterThread(i, self)
            self.thread_dict[i]["thread"].start()

        # 摄像头遮挡进程httpserver线程
        self.shelter_server_thread = threading.Thread(target=self.shelter_server_operation)
        self.shelter_server_thread.start()
        self.wait_server()

        # 启动心跳线程
        self.heartbeat_thread = threading.Thread(target=self.heartbeat_opeartion, args=(self.ip, self.port))
        self.heartbeat_thread.start()

    def write_logger_fun(self):
        """
        日志处理线程
        """
        while True:
            try:
                logger_data = LOGGER_QUEUE.get()
                if logger_data == -1:
                    break
            except Exception:
                break
            logger.info(logger_data)

    def shelter_server_operation(self):
        """
        function: web端通讯开启
        """
        try:
            app = ShelterApplication()  # web端
            self.port = find_port()
            app.run(host=SHELTER_SCENE_IP, port=self.port)
            LOGGER_QUEUE.put(f"application{SHELTER_SCENE_IP}:{self.port}")
        except Exception as err:
            print(traceback.format_exc())

    def heartbeat_opeartion(self, socket_ip, socket_port):
        """
        心跳线程，用于判断摄像头遮挡的在线情况
        """
        manage_ip = socket.gethostbyname(socket.getfqdn(socket.gethostname()))
        manage_port = self.conf_json["manage"]["port"]
        while True:
            interaction_dict = {
                "interaction_type": "heartbeat",
                "type": self.manage_type,
                "ip": self.ip,
                "port": self.port,
                "socket_ip": socket_ip,
                "socket_port": socket_port
            }
            ManageComm().send_http(manage_ip, manage_port, "interaction", interaction_dict)
            time.sleep(1)

    def wait_server(self):
        """
        确保shelter httpserver获取到空端口
        """
        while True:
            time.sleep(0.05)
            if self.port != 0:
                break

import copy
import operator
import os
import gc
import subprocess
import threading
import time
import socket

import psutil
# from apscheduler.schedulers.background import BackgroundScheduler
# from _utils._conf import ConfJson
from manage_global import CLIENT_PATH
from manage_web import ManageApplication


class mainManage(object):
    """
    总管理类，用于各线程、进程的启动，算法服务器的主要入口
    """

    def __init__(self):
        super(mainManage, self).__init__()
        # self.ip = "127.0.0.1"  # 获取本机ip
        # self.port = 5000
        # self.static_port = self.conf_json["manage"]["static_port"]  # 固定端口号
        # 摄像头
        # self.capture_interval = dict()  # 采图间隔，默认2秒
        # self.camera_info = dict()  # 所有摄像头的采图信息 {"C01JK027":{"camera_type":"dahua","cam_info":{"ip":"",...}}}
        # self.camera_responsible = []  # 负责采集的摄像头id ["C01JK027","C01JK028",...]
        # self.camera_results = []  # 需要返回结果图片的摄像头id ["C01JK027","C01JK028",...]
        # 算法
        # self.algorithm_info = dict()  # 各算法启动信息 {"物品占道":{},"安全帽":{"num":2,"device":"cuda:0",...}}
        # self.algorithm_kwargs = dict()  # 各算法参数 {"物品占道":{"C01JK027":{"roi":[],"iou":1,},...}}
        # self.algorithm_switch = dict()  # 各算法开关 {"物品占道":{"C01JK027":True}}
       
        # # 刪除旧结果图。定期删除过期结果图
        # self.del_thread = threading.Thread(target=del_former)
        # self.del_thread.start()

        # 开启服务器
        # self.manage_application = None
        # # self.server_opeartion()
        # self.server_thread = threading.Thread(target=self.server_opeartion)
        # self.server_thread.start()

        # 启动摄像头采图进程，摄像头采图进程连接上后，心跳线程自动发送具体采图信息
        self.capture_opearion()
        time.sleep(2)
        
        # # 启动算法进程
        print("manage start!")
        self.start_algorithm_process("区域入侵")

        # # 定时任务：删除根目录下的原图
        # scheduler = BackgroundScheduler()
        # scheduler.add_job(self.crontab_remove_original_images, 'interval', hours=1)
        # scheduler.start()

        # # 垃圾收集清理线程
        # garbage_collection_thread = threading.Thread(target=self.garbage_deal)
        # garbage_collection_thread.start()

    # def garbage_deal(self):
    #     """
    #     每隔2min，进行一次垃圾清理
    #     垃圾回收开始时，所有线程都将被挂起，故慎用
    #     """
    #     print("client enter garbage release!")
    #     while True:
    #         time.sleep(60 * 2)
    #         unreached_count = gc.collect()
    #         # print("client_unreached_count:", unreached_count)

    # 视频流不存图
    # def crontab_remove_original_images(self):
    #     """
    #     定时任务：删除根目录下的原图
    #     """
    #     now_time = time.time()
    #     for camera_dir in os.listdir('/ltb_test/imgs'):
    #         camera_dir_path = os.path.join('/ltb_test/imgs', camera_dir)
    #         mtime = time.localtime(os.path.getmtime(camera_dir_path))
    #         if now_time - time.mktime(mtime) > 3600 * 24:  # 文件修改日期在24小时之前
    #             subprocess.run(f'rm -rf {camera_dir_path}', shell=True)
    def server_opeartion(self):
            """启动算法服务器管理端的web"""
            self.manage_application = ManageApplication()
            self.manage_application.run(host=self.ip, port=self.port)

    def capture_opearion(self):
        """
        启动rtmp视频流进程
        """
        time.sleep(2)
        run_str = "conda activate yolov5_seg & python -u "
        software = "rtsp"
        run_py = os.path.join(CLIENT_PATH, software, software + "_run.py")
        run_str += run_py
        # run_str += " --type camera"
        print('摄像头采图进程', run_str)
        pro = subprocess.Popen(run_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)  # 启动一个新的进程
        # stdout=subprocess.PIPE表示将进程的输出重定向到管道
        stdout_thread = threading.Thread(target=self.stdout_operation, args=(software, pro))  # 打印各个进程的输出
        stdout_thread.start()
        # 打印错误信息
        sub_stderr = threading.Thread(target=self.sub_stderr_thread_fun, args=(software, pro))
        sub_stderr.start()
    
    def start_algorithm_process(self, start_key):
        """
        根据算法启动信息启动算法
        """
        print("客户端管理进程，启动算法:", start_key)
        if start_key == "区域入侵":
            run_str = "conda activate yolov5_seg & python -u "
            software = "invasion"
            run_py = os.path.join(CLIENT_PATH, software, software + "_run.py")
            run_str += run_py
            run_str += " --type {}".format(start_key)
            run_str += " --yolov5 {}".format("yolov5_seg")
            run_str += " --num {}".format(1)
            run_str += ' --weights {}'.format("../models/weights/person_number_detect_V03.pt")
            run_str += " --device {}".format('cuda:0')
            print('run_py', run_str)
            pro = subprocess.Popen(run_str, shell=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            stdout_thread = threading.Thread(target=self.stdout_operation, args=(software, pro))
            stdout_thread.start()
            print('区域入侵进程启动成功')
            # 打印错误信息
            sub_stderr = threading.Thread(target=self.sub_stderr_thread_fun, args=(software, pro))
            sub_stderr.start()
            return pro
        elif start_key == '摄像头遮挡':
            run_str = "python "
            algorithm = "algorithm"
            software = "shelter"
            run_py = os.path.join(CLIENT_PATH, f'{algorithm}/{software}', software + "_run.py")
            run_str += run_py
            run_str += " --type {}".format(start_key)
            # run_str += " --num {}".format(self.algorithm_info.get(start_key, {}).get('num', 10))
            print('run_str', run_str)
            pro = subprocess.Popen(run_str, shell=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            stdout_thread = threading.Thread(target=self.stdout_operation, args=(software, pro))
            stdout_thread.start()
            return pro
        else:
            return False

    @staticmethod
    def stdout_operation(algorithm, pro):
        """
        打印各进程的输出信息
        """
        for line in iter(pro.stdout.readline, b''):
            try:
                out_str = str(line, encoding="utf-8")
            except UnicodeDecodeError:
                try:
                    out_str = str(line, encoding="gbk")
                except UnicodeDecodeError:
                    print(algorithm, line)
                    continue
            print(algorithm, out_str[:-2])

    @staticmethod
    def sub_stderr_thread_fun(algorithm, pro):
        '''打印错误信息'''
        while True:
            for line in iter(pro.stderr.readline, b''):
                try:
                    out_str = str(line, encoding="utf-8")
                except UnicodeDecodeError as err:
                    out_str = str(line, encoding="gbk")
                if "size_with_stride larger than model origin size" in out_str:
                    print("算法进程异常信息：",algorithm, out_str[:-1])
                    
    @staticmethod
    def kill_algorithm_process(pro):
        """
        杀死算法进程
        """
        pid = pro.pid
        pid_list = [pid] + [p.pid for p in psutil.Process(pid).children(recursive=True)]
        for pid in pid_list:
            try:
                psutil.Process(pid).kill()
            except:
                pass

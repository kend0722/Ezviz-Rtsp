import datetime
import cv2
import threading
import numpy as np
import socket
import socketserver
import re
import struct
import pickle
import base64
import random
import time
from invasion_global import IMG_QUEUE,LOGGER_QUEUE


class MyTCPHandler(socketserver.BaseRequestHandler):
    '''
    有外部的客户端连接本地开启的服务器后，会生成这个线程。这个线程专门用来处理外部连接的客户端
    一个客户端连接成功就开启一个线程
    '''

    def __init__(self, request, client_address, server, *args, **kwargs):
        super().__init__(request, client_address, server)

    # 可以传递参数
    @classmethod
    def Creator(cls, *args, **kwargs):
        def _HandlerCreator(request, client_address, server):
            cls(request, client_address, server, *args, **kwargs)
        return _HandlerCreator

    def handle(self):
        '''处理连接的方法'''
        while True:
            try:
                recv_data = self.request.recv(1024 * 1024 * 20)
            except Exception as err: #接收异常，退出
                break
            if recv_data == b"": #接收到空字节，退出
                break
            self.data_operation(recv_data)
        self.request.close()  # 关闭socket连接
        self.RECV_BUF = b""  # 清空接收缓存

    def cmp_abs(self, img, img_before, threshold=0.9, kernel=np.ones((7, 7), np.uint8), iterations=1):
        """
        图片相似度对比，使用cv2.absdiff做基础对比
        :param img: 现在的图片cv2格式，bgr
        :param img_before: 以前的图片，如果是空则传字符串
        :param threshold: 相似度阈值
        :param kernel: 腐蚀运算核
        :param iterations: 腐蚀次数
        :return: True图片不相似，False图片相似
        """
        if isinstance(img_before, str):
            return True
        if isinstance(img, np.ndarray) and isinstance(img_before, np.ndarray):
            if img.shape == img_before.shape:
                dif = cv2.absdiff(img, img_before)
                dif_erode_mean = 1 - cv2.erode(dif, kernel, iterations=iterations).mean()
                return False if dif_erode_mean >= threshold else True
                # return True if dif_erode_mean >= threshold else True
        return True

    def data_analysis(self,recv_data):
        '''数据解析'''
        self.RECV_BUF += recv_data
        analysis_list = []
        while True:
            before_process_data_len = len(self.RECV_BUF)  # 处理之前的数据
            if len(self.RECV_BUF) >= 33:  # 长度信息，标签+内容
                data_len = self.RECV_BUF[:33]  # 获取长度信息，标签+内容
                data_len_lab_h = data_len[:14]
                data_len_lab_l = data_len[-15:]
                data_len_lab_h_id = data_len[9:13]
                data_len_lab_l_id = data_len[-5:-1]
                if re.findall(b"<tcp_len_.+>", data_len_lab_h) and re.findall(b"</tcp_len_.+>", data_len_lab_l) \
                        and data_len_lab_h_id == data_len_lab_l_id:  # 判断数据长度标签是否正确，并且id相等
                    data_len = struct.unpack("i", data_len[14:-15])[0]
                    if len(self.RECV_BUF) >= 33 + data_len + 31:
                        data_info = self.RECV_BUF[33:33 + data_len + 31]  # 获取数据信息，标签+数据
                        data_info_lab_h = data_info[:15]
                        data_info_lab_l = data_info[-16:]
                        data_info_lab_h_id = data_info[10:14]
                        data_info_lab_l_id = data_info[-5:-1]
                        if re.findall(b"<tcp_data_.+>", data_info_lab_h) and re.findall(b"</tcp_data_.+>",
                                                                                        data_info_lab_l) \
                                and data_info_lab_h_id == data_info_lab_l_id and data_len_lab_h_id == data_info_lab_h_id:
                            # 判断数据信息标签是否正确，并且id相等，并且等于数据长度标签id，说明长度标签和数据标签是一对
                            data = data_info[15:-16]
                            data = pickle.loads(data)
                            analysis_list.append(data)
                            self.RECV_BUF = self.RECV_BUF[33 + data_len + 31:]  # 解析完毕后。重新赋值，把解析出来的数据给截取掉，
                        else:  # 标签不正确，或者ID不对，则往后移一位
                            self.RECV_BUF = self.RECV_BUF[1:]
                else:  # 标签不正确，或者ID不对，则往后移一位
                    self.RECV_BUF = self.RECV_BUF[1:]
            after_process_data_len = len(self.RECV_BUF)  # 处理之后的数据长度
            # 处理之前的数据长度 = 处理之后的数据长度。说明没有需要处理的，则退出
            if before_process_data_len == after_process_data_len:
                break
        return analysis_list

    def gen_random_number(self):
        '''生成4位的随机数'''
        datas = random.sample(range(0, 9), 4)
        datas = [str(i) for i in datas]
        datas = "".join(datas)
        return datas

    def tcp_data_change(self,data):
        '''tcp数据转换'''
        data_byte = pickle.dumps(data)  # 把数据转换为字节
        data_len = struct.pack("i", len(data_byte))  # 求出字节数据的长度
        data_id = self.gen_random_number()  # 生成数据id
        send_info = "<tcp_len_{}>".format(data_id).encode() + data_len + "</tcp_len_{}>".format(data_id).encode() \
                    + "<tcp_data_{}>".format(data_id).encode() + data_byte + "</tcp_data_{}>".format(data_id).encode()
        return send_info

    def send_data(self,data_dic):
        '''发送数据'''
        send_data_info = self.tcp_data_change(data_dic)
        self.request.sendall(send_data_info)  # 发送数据
        # print(data_dic["jpg_path"],"发送成功..")

    def data_operation(self,recv_data):
        '''接收数据处理'''
        analysis_list = self.data_analysis(recv_data) #返回解析后的数据，是个列表，列表里面可能会有多条数据
        for datas in analysis_list: #遍历列表里的所有数据
            '''
             {'cam_id': '南园八号办公区H01-JK04', 'name': '20230914093811', 
             'original_path': '/lzh_test/imgs/南园八号办公区H01-JK04/南园八号办公区H01-JK04_20230914093811.jpg', 
             'code': 70335835, 'img': 
             'True'}
            '''
            # print("区域入侵socket接收数据:",datas["cam_id"])
            IMG_QUEUE.put(datas)
            LOGGER_QUEUE.put(f"cam={datas['cam_id']} code={datas['code']} info=http收到数据 time={datetime.datetime.now()}")



    def setup(self):
        '''
        在handle()之前执行，即客户端连接服务器后，会首先执行这个方法
        一般用作设置默认之外的连接配置
        '''
        self.RECV_BUF = b""
        # print("连接成功",self.client_address)

    def finish(self):
        '''
        在handle()之后执行，即退出连接，最后会执行这个方法
        '''
        self.RECV_BUF = b""


class ServerThread(threading.Thread):
    '''
    服务器线程
    启动服务器，等待客户端连接。
    客户端连接成功后，会生成一个线程，专门用来处理这个连接的操作
    '''

    def __init__(self, server_address=None):
        super(ServerThread, self).__init__(None)
        self.server_address = server_address
        self.connect_state = False

    def run(self):
        socketserver.ThreadingTCPServer.allow_reuse_address = True
        self.server = socketserver.ThreadingTCPServer(self.server_address,MyTCPHandler.Creator())  # 多线程
        self.connect_state = True
        self.server.serve_forever() #等待连接

def start_scoket_server(ip,port):
    server_address = (ip,port)
    server_thread = ServerThread(server_address)
    server_thread.start() #开启线程
    while True:
        if server_thread.connect_state:
            break
        time.sleep(0.1)
    print("区域入侵开启socket_server成功~~~")
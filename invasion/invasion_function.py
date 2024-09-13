
import datetime
import os
import sys
import threading
import time
import traceback

import cv2
# import numpy as np
import numpy as np
import torch
from manage.manage_global import CLIENT_PATH
from _utils import is_in_poly, draw_mask
from yolov5 import DetectMultiBackend, non_max_suppression, scale_boxes


class yolov5Thread(threading.Thread):
    """
    invasion检测线程，颗粒度是模型
    """
    def __init__(self, algorithm_id, parent,model):
        super(yolov5Thread, self).__init__()
        print("区域入侵算法function初始化")
        self.algorithm_id = algorithm_id
        self.parent = parent
        self.model = None  # 模型
        self.model_lock = threading.Lock()
        self.letterbox_dict = dict()  # yolov5框架的letterbox函数，空间换时间
        self.model = model
        # try:
        #     load_s_time = datetime.datetime.now()
        #     self.model_load()
        #     print(f"区域入侵，模型加载成功，加载时间:{datetime.datetime.now()-load_s_time}", flush=True)
        # except:
        #     import traceback
        #     print(traceback.format_exc())
        #     print("区域入侵，模型加载失败", flush=True)
            
    def run(self):
        """
        检测主逻辑，先加载模型，开始检测
        先检测人体，并判断人体是否在安全帽佩戴区域内，是，则检测人体是否佩戴安全帽
        检测逻辑：与yolov5框架相同，最后判断是否违规，再发送结果
        """
        # print("开始加载区域入侵算法模型")
        img_queue = self.parent.thread_dict[self.algorithm_id]["queue"]   # [cam_id, name, img]
        device = self.model.device
        print(f"区域入侵算法，开始检测，device:{device}")
        names = self.model.names
        size = img_queue.qsize()  # 判定队列大小
        for i in range(size):  # 遍历大小
            img_queue.get()  # 全部图片get出来
        while True:
            try:
                cam_id, name, img = img_queue.get()
                # all = img_queue.get()
                # print('all type:', type(all))   all type: <class 'list'>
                # print('all,lenth:', len(all))  all,lenth: 3
                # cam_id, name, img = all[0], all[1], all[2]
                invasion_receive_image_time = datetime.datetime.now()  # 区域入侵算法收到图片
                print(f"区域入侵算法，收到{cam_id}设备图片，时间{name}图片大小{img.shape[:2]}",flush=True)
                # img = cv2.imdecode(np.fromfile(img, dtype=np.uint8), -1)  # 读取图片
                img0 = img.copy()
                # im = letterbox(img, (640, 640), 32, auto=True)[0]  # padded resize
                img_shape_2 = img.shape[:2]
                # info = self.letterbox_dict.get(img_shape_2, "")
                # info = (1080, 1920)
                invasion_start_time = datetime.datetime.now()  # 区域入侵开始处理图片的时间
                if True:
                    h, w = img_shape_2
                    new_h, new_w = 640, 640
                    r = min(new_h / h, new_w / w)
                    new_unpad = int(round(w * r)), int(round(h * r))
                    dw, dh = new_w - new_unpad[0], new_h - new_unpad[1]  # wh padding
                    dw, dh = np.mod(dw, 32), np.mod(dh, 32)  # wh padding
                    dw /= 2  # divide padding into 2 sides
                    dh /= 2
                    # print('new_unpad:', new_unpad, flush=True)  # (360, 640, 3)
                    im = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
                    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
                    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
                    im = cv2.copyMakeBorder(im, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(114, 114, 114))
                    # info = [top, bottom, left, right, new_unpad]
                    # self.letterbox_dict[img_shape_2] = info
                # else:
                #     top, bottom, left, right, new_unpad = info
                #     im = cv2.resize(img, new_unpad, interpolation=cv2.INTER_LINEAR)
                #     im = cv2.copyMakeBorder(im, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(114, 114, 114))

                im = im.transpose((2, 0, 1))[::-1]  # HWC to CHW, BGR to RGB
                im = np.ascontiguousarray(im)  # contiguous
                im = torch.from_numpy(im).to(device)
                # im = torch.tensor(im, dtype=torch.float16).to(device)
                im = im.float()  # uint8 to fp16/32
                im /= 255  # 0 - 255 to 0.0 - 1.0
                if len(im.shape) == 3:
                    im = im[None]  # expand for batch dim
                results = dict()
                # 人体检测 ===================================================================================
                with self.model_lock:
                    person_pre = self.model(im)[0]
                    person_pre = non_max_suppression(
                        person_pre,
                        conf_thres=0.7,
                        iou_thres=0.45,
                        classes=None,
                        agnostic=True,
                        max_det=100,
                        nm=0  # 目标检测设置为0
                    )
                # rescale boxes to im0 size
                # person_result = []
                results = {
                            'cam_id': cam_id,
                            'illegal': "未入侵",
                            'name': name,
                        }  # 默认没有入侵
                person_pre[0][:, :4] = scale_boxes(im.shape[2:], person_pre[0][:, :4], img.shape).round()
                # print('person_pre', person_pre, flush=True)
                for *xyxy, conf, cls in person_pre[0]:   # 遍历检测到的人
                    p1, p2 = (int(xyxy[0]), int(xyxy[1])), (int(xyxy[2]), int(xyxy[3]))
                    feet_point = (int((p1[0] + p2[0]) / 2), p2[1])  # 矩形底边的中点
                    poly = [[[0,0], [0,900], [1920,900], [1920,0]]]   # 区域
                    print('feet_point', feet_point, flush=True)  # (1294,416)
                    if is_in_poly(feet_point, poly):  # 检测人在区域内
                        print("入侵", round(float(conf), 4), p1, p2, flush=True)
                        draw_mask(poly, img0, None, (p1, p2))  # 区域外涂黑
                        # results["illegal"].append(["区域入侵", round(float(conf), 4), p1, p2])
                        results = {
                            'cam_id': cam_id,
                            'illegal': "区域入侵",
                            'name': name,
                        }
                    # else:
                        # print("未入侵", round(float(conf), 4), p1, p2)
                        # results["legal"].append(["未入侵", round(float(conf), 4), p1, p2])
                        
                # ============================================================================================
                output = ['区域入侵', results]
                print(f"区域入侵算法处理完毕results:{results}", flush=True)
                self.parent.operation_queue.put(output)
                invasion_handle_time = datetime.datetime.now()  # 区域入侵算法处理时间
                
            except Exception as e:
                print("区域入侵算法处理异常", e, flush=True)
                error_info = sys.exc_info()
                error_tb = traceback.format_tb(error_info[2])
                for line in error_tb:
                    print(line.strip())
                    
            time.sleep(0.1)
            
            
    def model_load(self, queue=None):
        """
        模型加载，queue的作用是等加载完成后才发送给摄像头进程，目前未启用
        模型要求：
        1.yolov5训练得出的模型
        2.模型的names {0:"实际违规类型",1:"实际为违规类型"}，如{0:"佩戴安全帽",1:"佩戴安全帽",2:"未佩戴安全帽",}
        3.模型需要增加一个illegal为key的键值对，value是列表，列表内要求放这个模型的违规项 如["未佩戴安全帽"]
        """
        with self.model_lock:
            weights = self.parent.weights_path
            # weights = os.path.join(CLIENT_PATH, 'models\\weights\\tt.pt')
            device = self.parent.device
            print('weights:', weights, 'device:', device)
            device = torch.device(device)
            weights = "F:\Rtsp\models\weights\person_number_detect_V03.pt"
            self.model = DetectMultiBackend(weights, device)
            print("模型加载完成")





import threading
import traceback

import json
import time

import cv2
import numpy as np
import datetime
from skimage.segmentation import felzenszwalb
from concurrent.futures import ThreadPoolExecutor, as_completed, wait
import os
from shelter_global import LOGGER_QUEUE

from threading import Lock
PARA_CONF_LOCK = Lock()


class ShelterThread(threading.Thread):
    '''
    yolov5线程
    '''

    def __init__(self, algorithm_id=None, parent=None):
        '''
        algorithm_id:第几个算法，也是算法id
        parent:Phone_Thread对象
        '''
        super(ShelterThread, self).__init__()
        self.algorithm_id = algorithm_id  # 算法id
        self.parent = parent
        self.letterbox_dict = dict()

    def read_cam_para_conf(self,cam_id):
        '''读取相机参数配置'''
        ### 读取这个摄像头的参数配置 ###
        ## 1，判定配置文件是否存在
        para_config_file_path = "para_config_file.json"
        # 文件不存在，新建
        if not os.path.exists(para_config_file_path):
            para_config_file_dic = {
                "default_para": {
                    "edge_brightness_threshold": 70,  # 过滤不明显边缘时，边缘的亮度阈值
                    "img_seg_sigma": 2.0,  # 图像分割-sigma参数
                    "img_seg_scale": 500,  # 图像分割-scale参数
                    "img_seg_min_size": 100,  # 图像分割-min_size参数
                    "occlusion_area": 0.9  # 遮挡面积
                }
            }
            with open(para_config_file_path, "w", encoding='utf-8') as f:
                json.dump(para_config_file_dic, f, ensure_ascii=False, indent=4)
        else:  # 文件存在，读取
            with open(para_config_file_path, 'r', encoding='utf-8') as f:
                para_config_file_dic = json.load(f)

        ## 2，读取这个摄像头的参数配置
        if cam_id == None:  # 如果摄像头id为None，读取默认参数
            para_config = para_config_file_dic["default_para"]
        else:  # 说明摄像头id不为None
            if cam_id not in para_config_file_dic.keys():  # 如果这个摄像头id不在参数文件中
                # 给这个摄像头id的参数设置为默认值
                para_config_file_dic.setdefault(
                    cam_id,
                    {
                        "edge_brightness_threshold": 70,  # 过滤不明显边缘时，边缘的亮度阈值
                        "img_seg_sigma": 2.0,  # 图像分割-sigma参数
                        "img_seg_scale": 500,  # 图像分割-scale参数
                        "img_seg_min_size": 100,  # 图像分割-min_size参数
                        "occlusion_area": 0.9  # 遮挡面积
                    }
                )
                # 获取这个cam_id的参数
                para_config = para_config_file_dic[cam_id]
                # 因为写入了值，所以要写入json文件
                with open(para_config_file_path, "w", encoding='utf-8') as f:
                    json.dump(para_config_file_dic, f, ensure_ascii=False, indent=4)
            else:
                para_config = para_config_file_dic[cam_id]
        return para_config

    def run(self):
        print("开始加载摄像头遮挡算法模型")
        load_s_time = datetime.datetime.now()
        # self.model_load()  # 加载算法
        img_queue = self.parent.thread_dict[self.algorithm_id]["queue"]  # 获取图片队列
        # 在算法加载过程中，可能就有图片进来了，所以要把这些图片取出来清除掉，
        size = img_queue.qsize()  # 判定队列大小
        for i in range(size):  # 遍历大小
            img_queue.get()  # 全部图片get出来

        while True:
            try:
                cam_id, original_path = img_queue.get()
                with PARA_CONF_LOCK:
                    para_config = self.read_cam_para_conf(cam_id)

                name = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
                # print(f"the name is {name}")
                results = {"illegal": [], "legal": []}
                s_time = datetime.datetime.now()  # 摄像头遮挡算法收到图片
                ori_size_img = cv2.imdecode(np.fromfile(original_path, dtype=np.uint8), -1)  # 读取图片数据
                (ori_size_h, ori_size_w, _) = ori_size_img.shape
                mapped_h = 720
                mapped_w = 1280
                ori_img = cv2.resize(ori_size_img, (mapped_w, mapped_h), interpolation=cv2.INTER_LINEAR)  # 尺寸转换
                blur_img = cv2.GaussianBlur(ori_img, (0, 0), 5)  # 高斯模糊
                usm_enhance = cv2.addWeighted(ori_img, 1.5, blur_img, -0.5, 0)  # usm增强

                # 2,sobel 边缘检测
                usm_sobel = cv2.cvtColor(usm_enhance, cv2.COLOR_RGB2GRAY)
                sobel_x = cv2.Sobel(usm_sobel, cv2.CV_64F, 1, 0, ksize=3)
                sobel_y = cv2.Sobel(usm_sobel, cv2.CV_64F, 0, 1, ksize=3)
                sobel_edges = np.sqrt(sobel_x ** 2 + sobel_y ** 2).astype(np.uint8)

                # 3,过滤不明显边缘
                new_sobel_edges = np.where(sobel_edges > para_config["edge_brightness_threshold"], 255, 0).astype(
                    np.uint8)  # 调参1

                # 4，形态学变化，开运算与闭运算，目的是去噪声，连接断线
                kernel = np.zeros((3, 3), np.uint8)
                kernel[1][:] = 1
                # 开运算 开运算能够除去孤立的小点，毛刺和小桥，而总的位置和形状不变
                new_sobel_edges_1 = cv2.morphologyEx(new_sobel_edges, cv2.MORPH_OPEN, kernel.T)
                # 闭运算 闭运算能够填平小湖（即小孔），弥合小裂缝，而总的位置和形状不变
                new_sobel_edges_1 = cv2.morphologyEx(new_sobel_edges_1, cv2.MORPH_CLOSE, kernel.T)
                # 开运算 开运算能够除去孤立的小点，毛刺和小桥，而总的位置和形状不变
                new_sobel_edges_2 = cv2.morphologyEx(new_sobel_edges, cv2.MORPH_OPEN, kernel)
                # 闭运算 闭运算能够填平小湖（即小孔），弥合小裂缝，而总的位置和形状不变
                new_sobel_edges_2 = cv2.morphologyEx(new_sobel_edges_2, cv2.MORPH_CLOSE, kernel)
                # 两种算子相加
                new_sobel_edges = cv2.add(new_sobel_edges_1, new_sobel_edges_2)

                # 5, 锐化增强图+边缘增强图
                new_sobel_edges = cv2.cvtColor(new_sobel_edges, cv2.COLOR_GRAY2RGB)  # 边缘增强图
                finsh_img = cv2.add(usm_enhance, new_sobel_edges)  # 合并图片

                # 6，图像分割算法实现
                sigma = para_config["img_seg_sigma"]  # 调参2
                scale = para_config["img_seg_scale"]  # 调参2
                min_size = para_config["img_seg_min_size"]  # 调参
                # print(sigma, scale, min_size)
                h, w, c = finsh_img.shape
                # print(sigma, scale, min_size, h, w, c, cam_id)
                im_mask = felzenszwalb(finsh_img, scale=scale, sigma=sigma, min_size=min_size)  # 进行图像分割算法

                # 7，计算最大遮挡面积
                unique_values, counts = np.unique(im_mask, return_counts=True)
                occlusion_mark_index = np.where(counts == sorted(counts, reverse=True)[0])[0][
                    0]  # 最大面积mask的index，就是遮挡mark的index
                maximum_area_proportion = sorted(counts, reverse=True)[0] / (h * w)
                # print(f"{occlusion_mark_index},{max(counts)} {cam_id}, {h}, {w}, {h * w}")
                # print(f"{sorted(counts, reverse=True)[0]}, {cam_id}, {h}, {w}, {h * w}")
                box = []
                if maximum_area_proportion >= para_config["occlusion_area"]:  # 大于指定的面积，说明时遮挡了，才进行上色保存
                # if maximum_area_proportion >= 0.75:  # 大于指定的面积，说明时遮挡了，才进行上色保存
                    print(f"{cam_id} is {maximum_area_proportion}", flush=True)
                    # if maximum_area_proportion >= 0:  # 大于指定的面积，说明时遮挡了，才进行上色保存
                    # original_path = self.save_result_img(original_path, cam_id)
                    # 随机上色
                    # color_img = np.zeros_like(finsh_img)
                    for i in range(np.max(im_mask)):
                        # color_img[:, :, 0][im_mask == i] = np.random.randint(255)
                        # color_img[:, :, 1][im_mask == i] = np.random.randint(255)
                        # color_img[:, :, 2][im_mask == i] = np.random.randint(255)
                        if i == occlusion_mark_index:  # 找到遮挡mark的index，就是最大面积那个
                            # 创建一个全0矩阵
                            color_img_1 = np.zeros(shape=((finsh_img.shape[:2])), dtype=np.uint8)
                            color_img_1[im_mask == i] = 255  # 给最大面积那个目标，就是i赋值为255。im_mask==i，就是找到im_mask中等于i的像素
                            countours, _ = cv2.findContours(color_img_1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # 找到轮廓
                            x, y, w, h = cv2.boundingRect(countours[0]) # 找到x,y,w,h
                            x1, y1, x2, y2 = x, y, x + w, y + h  # 转为坐标
                            # 坐标映射，（mapped_w,mapped_h），映射回原图尺寸
                            x1 = int(ori_size_w * x1 / mapped_w)
                            y1 = int(ori_size_h * y1 / mapped_h)
                            x2 = int(ori_size_w * x2 / mapped_w)
                            y2 = int(ori_size_h * y2 / mapped_h)
                            if x1 <= 0:
                                x1 = 2
                            if y1 <= 0:
                                y1 = 2
                            if x2 >= ori_size_w:
                                x2 = ori_size_w - 2
                            if y2 >= ori_size_h:
                                y2 = ori_size_h - 2
                            cv2.rectangle(ori_size_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                            pp1, pp2 = (x1, y1), (x2, y2)
                            results["illegal"].append(
                                [self.parent.manage_type, round(float(maximum_area_proportion), 4), pp1, pp2])

                run_time = datetime.datetime.now() - s_time
                output = [self.parent.manage_type, cam_id, name, original_path, results]
                # time.sleep(10)
                self.parent.operation_queue.put(output)
                # print("摄像头遮挡算法处理完毕——————————", img_queue.qsize(), os.getpid(), flush=True)
                LOGGER_QUEUE.put(
                    f'等待处理= {img_queue.qsize()} key={cam_id} 摄像头遮挡花费时间：{run_time}')
            except:
                print(traceback.format_exc(), flush=True)

        # 保存结果图片

    def save_result_img(self, img_path, cam_id):
        # 获取图片url
        def get_url(img_path):
            url_prefix = "http://10.123.232.10:30692/"  # 3d_test图片端口
            url = url_prefix + '/'.join(img_path.split('/')[4:])  # 去掉路径中前面的部分，只留下AGV及其下级目录, 拼接为图片链接
            print(f"the url is {url}")
            return url

        now_time = datetime.datetime.now().strftime("%Y%m%d%H%M%S_")
        img_name = now_time + os.path.basename(img_path)
        result_path = os.path.join(os.path.dirname(img_path), img_name)
        try:
            result_img = cv2.imdecode(np.fromfile(img_path, dtype=np.uint8), -1)
            pts = np.array(
                self.parent.algorithm_kwargs.get(cam_id, dict()).get("roi", [[0, 0], [0, 1080], [1920, 1080],
                                                                             [1920, 0]]))
            cv2.polylines(result_img, [pts], True, (0, 0, 255), 3)
            cv2.imwrite(result_path, result_img)
            # shutil.copy(img_path, result_path)  # 另存图片
        except:
            LOGGER_QUEUE.put(f"xxx {traceback.format_exc()} xxx")
            result_path = img_path

        return get_url(result_path)

    def model_load(self):
        '''
        加载算法，默认
        '''
        self.para_config = {
            "edge_brightness_threshold": 70,  # 过滤不明显边缘时，边缘的亮度阈值
            "img_seg_sigma": 2.0,  # 图像分割-sigma参数
            "img_seg_scale": 500,  # 图像分割-scale参数
            "img_seg_min_size": 100,  # 图像分割-min_size参数
            "occlusion_area": 0.9  # 遮挡面积
        }

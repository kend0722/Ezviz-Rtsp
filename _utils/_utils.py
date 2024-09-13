
import datetime
import os
import platform
import shutil
import time

import cv2
import numpy as np

from _utils._conf import ConfJson
# from _conf import ConfJson


def cmp_abs(img, img_before, threshold=0.9, kernel=np.ones((7, 7), np.uint8), iterations=1):
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


def del_former():
    """
    删除图片线程。删除过期结果图
    """
    # # 旧原图
    # original_path = "\\".join(os.path.abspath(__file__).split("\\")[:-3] + ["original"])
    # if os.path.exists(original_path):
    #     shutil.rmtree(original_path)
    # # 旧debug图
    # debug_path = "\\".join(os.path.abspath(__file__).split("\\")[:-3] + ["debug"])
    # if os.path.exists(debug_path):
    #     shutil.rmtree(debug_path)
    # 删除过期结果图
    results_path = "\\".join(os.path.abspath(__file__).split("\\")[:-3] + ["results"])
    days = ConfJson()["manage"]["clear_results_days"]
    while True:
        time.sleep(60)
        clear_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime("%Y%m%d")
        if not os.path.exists(results_path):
            continue
        for cam_id in os.listdir(results_path):
            clear_file = os.path.join(results_path, cam_id, clear_date)
            if os.path.exists(clear_file):
                shutil.rmtree(clear_file)


def find_port(startPort=6800):
    """
    查找空闲端口，server端没使用到，client端使用
    :param startPort: 从startPort开始查
    :return:返回空闲端口
    """

    def isInuseWindow(port):
        if os.popen('netstat -an | findstr :' + str(port)).readlines():
            portIsUse = True
        else:
            portIsUse = False
        return portIsUse

    def isInuseLinux(port):
        # lsof -i:8080
        # not show pid to avoid complex
        if os.popen('netstat -na | grep :' + str(port)).readlines():
            portIsUse = True
        else:
            portIsUse = False
        return portIsUse

    def choosePlatform():
        machine = platform.platform().lower()
        if 'windows-' in machine:
            return isInuseWindow
        elif 'linux-' in machine:
            return isInuseLinux

    def checkMutiPort(startPortChech):
        isInuseFun = choosePlatform()
        nineIsFree = True
        if isInuseFun(startPortChech):
            nineIsFree = False
        else:
            startPortChech = startPortChech + 1
        return nineIsFree, startPortChech

    while True:
        flag, endPort = checkMutiPort(startPort)
        if flag:
            break
        else:
            startPort = endPort + 1
    return startPort


def is_in_poly(p, polys):
    """
    射线法判断点是否在多边形内，
    :param p: 点坐标[x, y]
    :param poly: 多边形坐标[[x1, y1], [x2, y2], ..., [xn, yn]]
    :return: is_in bool类型，点是否在多边形内/上
    """

    if len(polys) == 0:
        return True
    px, py = p
    is_in = False
    for poly in polys:
        for i, corner in enumerate(poly):
            next_i = i + 1 if i + 1 < len(poly) else 0
            # 多边形一条边上的两个顶点
            # print('corner', corner)
            x1, y1 = corner
            x2, y2 = poly[next_i]
            # 在顶点位置
            if (x1 == px and y1 == py) or (x2 == px and y2 == py):
                is_in = True
                return is_in
            if min(y1, y2) < py <= max(y1, y2):
                x = x1 + (py - y1) * (x2 - x1) / (y2 - y1)
                # 在边上
                if x == px:
                    is_in = True
                    return is_in
                # 射线与边相交
                elif x > px:
                    is_in = not is_in
    return is_in




def draw_mask(polys, img, original_path, person):
    """
    polys: 画的区域
    img: 传过来的图片
    original_path: 图片路径
    person: 人体坐标
    """
    # ------ 取roi及检测到人体的并集，外接矩形
    x = min(person, key=lambda x: x[0])[0]
    y = min(person, key=lambda y: y[1])[1]
    x_ = max(person, key=lambda x: x[0])[0]
    y_ = max(person, key=lambda y: y[1])[1]
    if polys:
        x1 = min([min(poly, key=lambda x: x[0])[0] for poly in polys])
        y1 = min([min(poly, key=lambda y: y[1])[1] for poly in polys])
        x1_ = max([max(poly, key=lambda x: x[0])[0] for poly in polys])
        y1_ = max([max(poly, key=lambda y: y[1])[1] for poly in polys])

        min_x = min(x, x1)
        min_y = min(y, y1)
        max_x = max(x_, x1_)
        max_y = max(y_, y1_)
    else:
        min_x = x
        min_y = y
        max_x = x_
        max_y = y_
    polys = [[min_x, min_y], [min_x, max_y], [max_x, max_y], [max_x, min_y]]
    # ------------------------
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    roi = np.array(polys)
    m = cv2.fillPoly(mask, [roi], (255))
    x1 = cv2.bitwise_and(img, img, mask=m)
    # print("draw", original_path)
    # cv2.imwrite(original_path, x1)


            
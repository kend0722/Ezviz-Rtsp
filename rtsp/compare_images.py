import cv2
import numpy as np
img_before = {}


def cmp_abs(img, img_before, threshold=0.97, kernel=np.ones((7, 7), np.uint8), iterations=1):
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
            dif = cv2.absdiff(img, img_before) # 计算两幅图像的绝对差
            dif_erode_mean = 1 - cv2.erode(dif, kernel, iterations=iterations).mean() # 腐蚀运算
            # print("相似度为: ", dif_erode_mean)
            return False if dif_erode_mean >= threshold else True
    return True
    



    
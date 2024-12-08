import datetime
import time
import cv2
import numpy as np
from PIL import Image
from queue import Queue
import threading
# import ffmpeg
from get_video_url import *


# def write_video_task(frame_queue):
    # '''
    # 写入视频任务
    #     Args:
    #         frame_queue: 存放数据的队列
    #     Returns:
    #         None
    # '''
    # count = 0
    # while True:
    #     get_data = frame_queue.get()
    #     count += 1
    #     if count == 1:
    #         write_process = (
    #             ffmpeg
    #                 .input('pipe:', format='rawvideo', pix_fmt='bgr24',
    #                        s='{}x{}'.format(1600, 900))
    #                 .output("test.mp4", loglevel="quiet", pix_fmt='yuv420p', r=25, crf=31)
    #                 .overwrite_output()
    #                 .run_async(pipe_stdin=True)
    #         )
    #     in_frame = get_data
    #     write_process.stdin.write(
    #         in_frame
    #             .astype(np.uint8)
    #             .tobytes()
    #     )
    #     if count % 25 == 0:
    #         print(count//25,"秒")
    #     if count == 25*60:
    #         write_process.stdin.close()
    #         write_process.wait()
    #         print("写入完毕")
    #         break


# write_video_thread = threading.Thread(target=write_video_task,args=(frame_queue,))
# write_video_thread.start()

# >>>实时播放与回放>>>
# RTMP流的URL
# rtmp_url = ' rtsp://rtmp03open.ys7.com:1935/v3/openpb/K26430757_1_1?begin=20240901143928&end=20240902143928&expire=1725345568&id=750726597517631488&rec=local&t=0d41e682fc7a7501cd764f0fbf21a87508d10b80944790948de37ab33dfc5316&ev=100'


# 视频流存入队列
def write_video_task(frame_queue, rtmp_url):
    counts  = 0
    """写入视频任务
    :param frame_queue: 存放数据的队列
    :param rtmp_url: rtmp流地址
    """
    print('rtmp_url： ', rtmp_url)
    # 创建VideoCapture对象
    cap = cv2.VideoCapture(rtmp_url)
    # 检查是否成功打开流
    if cap.isOpened():
        print("Stream opened successfully")
    else:
        print("Error opening stream")
        exit()
    while True:
        # 读取一帧
        ret, frame = cap.read()
        # 如果读取成功，放到队列，发送到相似度处理容器
        if ret:
            counts += 1
            # time_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            frame = np.array(Image.fromarray(frame).resize((1920, 1080)))
            # send = {'name':time_str, 'frame': frame}
            if counts % 25 == 0:
                # print("put frame")
                frame_queue.put(frame)
        else:
            print("No frame captured")
            time.sleep(0.5)
            continue



if __name__ == '__main__':
    # rtmp_url = get_video_with_url_online()['data']['url']
    # frame_queue = Queue()
    # write_video_thread = threading.Thread(target=write_video_task, args=(frame_queue, rtmp_url))
    # write_video_thread.start()
    time_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")  # 20240902202125
    print(time_str)
from video_logic import Video_Logic

if __name__ == '__main__':
    # 初始化视频逻辑
    deviceSerial = 'K26430757'
    video_logic = Video_Logic(deviceSerial)
    # 启动rtmp
    video_logic.run()

# from multiprocessing import Queue
import time
# INPUT_LOCK = 0
# OUTPUT_LOCK = 0

class Invasion_Events():

    def __init__(self,parent, deviceSerial):  # 一个摄像头开启一个算法检测
        self.parent = parent
        self.deviceSerial = deviceSerial
        self.INPUT_LOCK = 0
        self.OUTPUT_LOCK = 0
        print("摄像头事件服务已启动", self.deviceSerial)
    def run(self):
        
        while True:
            results = self.parent.operation_queue.get()  # 结果队列
            print("摄像头事件服务收到结果", results)   # ['区域入侵', {'cam_id': 'K26430757', 'illegal': '未入侵', 'name': '20240904114117'}]
            if results is None and len(results) != 2:   # 相似或者其他
                continue
            # TODO: 根据结果进行后续处理
            # print("摄像头事件服务处理结果", results[0])
            if '区域入侵' == results[0]:
                '''
                results[1] = {
                        'cam_id': cam_id,
                        'illegal': "未入侵",
                        'name': name,
                    }
                '''
                re = results[1]
                if re['illegal'] == "区域入侵" and self.INPUT_LOCK == 0:
                    name = re['name']
                    print(f"摄像头{self.deviceSerial}检测到人在{name}进入区域")
                    self.INPUT_LOCK = 1
                    self.OUTPUT_LOCK = 0
                    # TODO: 保存报警信息, 数据库
                    print("报警信息已保存", self.deviceSerial, name, re['illegal'])
                
                if re['illegal'] == "未入侵" and self.OUTPUT_LOCK == 0:
                    name = re['name']
                    print(f"摄像头{self.deviceSerial}检测到人在{name}离开区域")
                    self.INPUT_LOCK = 0
                    self.OUTPUT_LOCK = 1
                    # TODO: 保存报警信息
                    print("报警信息已保存", self.deviceSerial, name, re['illegal'])
                    
            time.sleep(0.1)
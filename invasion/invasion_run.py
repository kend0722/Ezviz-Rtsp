import argparse
import sys
import os
# print("1" * 100)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)
try:
    from invasion_logic import InvasionManage
except Exception as e:
    print("invasion_logic启动失败！", e, flush=True)

if __name__ == "__main__":
    print("invasion_run")
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", required=True)  # 类型，目前为安全帽
    parser.add_argument("--yolov5",default="yolov5_seg", required=True)  # 类型，目前为安全帽
    parser.add_argument("--weights",default="../models/weights/person_number_detect_V03.pt", required=True)  # 权重路径
    parser.add_argument("--device",default="cuda", required=True)  # 权重路径
    parser.add_argument("--num",default=1, required=True)  #  开启数量
    args = parser.parse_args()
    # print("args", args, flush=True)
    
    invasion_manage = InvasionManage(args.type, args.yolov5, args.weights, args.device, args.num)
    invasion_manage.run()


import argparse
import os
import sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)
try:
    from shelter_logic import Shelter_manage
except Exception as e:
    import traceback
    print(traceback.format_exc())

if __name__ == "__main__":
    # try:  {'num': 2, 'device': 'cuda:0', 'roi_switch': 1, 'software': 'yolov5_det',
    # 'pt_name': 'rope_ladder_x_v01', 'weights':
    # '/haikui/3d_test_server/server/weights/rope_ladder_x_v01.pt'}
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", required=True)  # 类型，固定摄像头遮挡
    # parser.add_argument("--num", type=int, required=True)  # 加载数量
    # parser.add_argument("--weights", required=True)  # 模型位置，模型要求要有illegal:["违规类型1",] 违规类型 in names.values()
    # parser.add_argument("--device", required=True)  # device


    args = parser.parse_args()
    print("run___", args, flush=True)
    try:
        shelter_manage = Shelter_manage(args.type)
        shelter_manage.run()
    except:
        import traceback
        print(traceback.format_exc())
    # print('摄像头遮挡进程({})'.format(os.getpid()))  # 打印进程号
    sys.stdout.flush()

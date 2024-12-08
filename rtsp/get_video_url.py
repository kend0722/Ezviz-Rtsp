import json
import requests
from get_accessToken import get_deviceList, token

def get_all_device():
    data = []
    for i in range(300):
        # 获取设备信息
        deviceList = get_deviceList(start_page=i, page_size=50)   # deviceList为字典类型
        devicedata = deviceList['data'] # devicedata为列表类型
        if not devicedata:
            break
        data.append(devicedata)
    #     print(f'第{i+1}页获取成功')
    # print("data获取成功", data)
    return data

def device_name():
    data = get_all_device()   # 这里是拿到的所有的设备信息
    # device_name = 'JK468江苏盐城蜂巢'
    deviceSerial = 'K26430757'
    for i in data:   # 遍历每一个分页的设备信息
        for j in i:   # 这里得j, 就是对应每一个摄像头信息
            # num += 1
            # print(num, j)   # j: {'id': '08335cf155194dbabe97310aa507b444K27002336', 'deviceSerial': 'K27002336', 'deviceName': 'JK125', 'deviceType': 'CS-H6c-V101-1G2WF', 'status': 0, 'defence': 0, 'deviceVersion': 'V5.3.0 build 220601', 'addTime': 1660878419016, 'updateTime': 1661531494000, 'parentCategory': 'IPC', 'riskLevel': 0, 'netAddress': '163.179.244.141'}
            if j['deviceSerial'] == deviceSerial:
                device_info = j
                print("device_name获取成功", device_info)
                return device_info
# print(device_name())   # {'id': '08335cf155194dbabe97310aa507b444K26998187', 'deviceSerial': 'K26998187', 'deviceName': 'JK468江苏盐城蜂巢', 'deviceType': 'CS-H6c-V101-1G2WF', 'status': 1, 'defence': 0, 'deviceVersion': 'V5.3.8 build 240110', 'addTime': 1663825688151, 'updateTime': 1705396822000, 'parentCategory': 'IPC', 'riskLevel': 0, 'netAddress': '122.97.173.252'}
device_info = device_name()

# 获取回放播放地址
video_url_deline = 'https://open.ys7.com/api/lapp/v2/live/address/get'
video_url_online = 'https://open.ys7.com/api/lapp/v2/live/address/get'
headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
}



def get_video_with_url_deline(deviceSerial):
    params_deline = {
    'accessToken': token,
    'deviceSerial': deviceSerial,
    'protocol': 3,  # rtmp协议
    'type': 2,
    'startTime': '2024-09-02 11:00:00',
    'stopTime': '2024-09-02 11:01:00'
}
    response = requests.post(video_url_deline, headers=headers, data=params_deline)
    # 解析返回的json数据
    result = json.loads(response.text)
    return result


def get_video_with_url_online(deviceSerial):
    params_online = {
    'accessToken': token,
    'deviceSerial': deviceSerial,
    'protocol': 3,  # rtmp协议
    'type': 2
}
    response = requests.post(video_url_online, headers=headers, data=params_online)
    # 解析返回的json数据
    result = json.loads(response.text)
    return result


if __name__ == '__main__':
    """
    {
        'id': '08335cf155194dbabe97310aa507b444K26998187', 
        'deviceSerial': 'K26998187', 
        'deviceName': 
        'JK468江苏盐城蜂巢', 
        'deviceType': 'CS-H6c-V101-1G2WF', 
        'status': 1, 
        'defence': 0, 
        'deviceVersion': 'V5.3.8 build 240110', 
        'addTime': 1663825688151, 
        'updateTime': 1705396822000, 
        'parentCategory': 'IPC', 
        'riskLevel': 0, 
        'netAddress': '122.97.173.252'}
    """ 
    print(get_video_with_url_online(deviceSerial='K26430757'))
    """
    {'msg': '操作成功', 'code': '200', 
    'data': {'id': '750715169084018688', 
    'url': 'rtsp://rtmp01open.ys7.com:1935/v3/openpb/K26998187_1_1?begin=20240902110000&end=20240902110100&expire=1725342843&id=750715169084018688&rec=local&t=dca8ea13d7134fa395c71a8b68b9057edd4357805957b256b65c009dcbc257d3&ev=100', 
    'expireTime': '2024-09-03 13:54:03'}
    }
    """
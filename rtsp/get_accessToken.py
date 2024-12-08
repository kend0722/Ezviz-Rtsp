import json
import requests

url = 'https://open.ys7.com/api/lapp/token/get'

headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
}

data = {
  'appKey': 'e3454a479d7a47f288dae29d30c0a757',
  'appSecret': '3778bc6afb2b96174b2986f26f80dc0e'
}
# 获取Token
def get_accessToken():
    response = requests.post(url, headers=headers, data=data)
    # print(response.text)
    # 解析返回的json数据
    result = json.loads(response.text)
    accessToken = result['data']['accessToken']
    return accessToken

token = get_accessToken()

# 获取设备序列号
def get_deviceList(start_page:int, page_size:int):
    url2 = 'https://open.ys7.com/api/lapp/device/list'
    headers2 = {
    'Content-Type': 'application/x-www-form-urlencoded',
}
    data2 = {
  'accessToken': token,
  'pageStart': start_page,    # 起始页
  'pageSize':  page_size    # 每页数量
}
    response = requests.post(url2, headers=headers2, data=data2)
    # print(response.text)
    # 解析返回的json数据
    result = json.loads(response.text)
    return result

if __name__ == '__main__':
    # 获取设备序列号
    print(get_deviceList(start_page=1, page_size=10))
    # 调用函数获取accessToken
    # accessToken = get_accessToken()

    # 打印accessToken
    # {"msg":"操作成功!","code":"200",
    #  "data":{
    #     "accessToken":"at.613oaxo1cqes5rcq7bvzqive4yukkric-1ovdrjlwex-0s7b4xt-daejjz9fz",
    #     "expireTime":1725847225945}
    #  }
    # 将accessToken保存到文件中
    # with open('accessToken.py', 'w') as f:
    #     f.write('accessToken = "{}"'.format(accessToken))
    # # # 读取文件中的accessToken
    # with open('accessToken.py', 'r') as f:
    #     accessToken = f.read()
    #     print(accessToken)

import json
import requests
import traceback


class ManageComm(object):
    """
    统一交互接口
    send_http：只发送，不需要返回
    """

    @staticmethod
    def send_http(ip, port, route, send_json):
        url = f'http://{ip}:{port}/{route}'
        try:
            # headers = {'Connection': 'close'}
            requests.post(url=url, json=send_json, timeout=5)
            return True
        except Exception as err:
            print("send_http_{}_{}_{}_{}".format(ip, port, route, err))
            return False

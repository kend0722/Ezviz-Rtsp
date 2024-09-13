
import json
import os


class ConfSingleton(object):
    """
    本地配置文件，单例模式基类
    """
    __instance = None

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    def __init__(self):
        with open("/".join(os.path.abspath(__file__).split('/')[:-2] + ["conf.json"]), "r") as f:
            self.conf_json = json.load(f)


class ConfJson(ConfSingleton):
    """
    配置文件类【一个类似与json的类】，含获取，设置，字符串魔术方法
    """

    def __init__(self):
        super(ConfJson, self).__init__()

    def __getitem__(self, item):
        return self.conf_json[item]

    def __setitem__(self, key, value):
        if isinstance(key, list):
            new_value = self.conf_json
            for k in key[:-1]:
                new_value = self.conf_json[k]
            new_value[key[-1]] = value
        elif isinstance(key, str):
            if key in self.conf_json.keys():
                self.conf_json[key] = value

    def __str__(self):
        return json.dumps(self.conf_json)

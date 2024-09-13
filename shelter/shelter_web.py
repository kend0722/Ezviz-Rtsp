
import os
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import http.server
import socketserver

from shelter_global import INTERACTION_QUEUE, IMG_QUEUE, LOGGER_QUEUE


class MultiThreadedHTTPServer:
    def __init__(self, server_address, handler_class):
        self.server = socketserver.ThreadingTCPServer(server_address, handler_class)
        self.server.allow_reuse_address = True
        self.threads = []

    def serve_forever(self):
        self.server.serve_forever()

    def stop(self):
        self.server.shutdown()
        for thread in self.threads:
            thread.join()


class ShelterHTTPServer(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    """
    http.server的handler类，用于交互
    """

    def do_HEAD(self):
        """
        请求头
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        """
        get请求
        """
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_POST(self):
        """
        post请求
        """
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            self.do_HEAD()
            if self.path[1:] == "image":
                pass
                # get_data = json.loads(post_data)
                # IMG_QUEUE.put(get_data)  # 客户端function的内容
                # LOGGER_QUEUE.put(f"image_recieve")
            elif self.path[1:] == "interaction":
                get_data = json.loads(post_data)
                INTERACTION_QUEUE.put(get_data)
                # print('接受数据1', get_data.keys(), flush=True)
        except Exception as err:
            print("do_Post", err)

    def log_message(self, *args):
        """
        重构日志类，不打印红字
        """
        return


class ShelterApplication(object):
    @staticmethod
    def run(host, port):
        server_address = (host, port)
        # httpd = HTTPServer(server_address, ShelterHTTPServer)
        httpd = MultiThreadedHTTPServer(server_address, ShelterHTTPServer)
        print(f"[shelter] [pid:{os.getpid()}] [server:{host}_{port}]")
        LOGGER_QUEUE.put(f"[shelter] [pid:{os.getpid()}] [server:{host}_{port}]")
        print('shelter web服务启动成功', host, port)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        httpd.server_close()


import os
import json
import datetime
import http.server
import socketserver
from http.server import BaseHTTPRequestHandler, HTTPServer
from invasion_global import IMG_QUEUE


class InvasionHTTPServer:
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


class InvasionHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def do_HEAD(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_GET(self):
        self.send_response(404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            self.do_HEAD()
            # print("区域入侵算法接收到数据")
            if self.path.endswith("images"):
                get_data = json.loads(post_data)
                # print(get_data)   # 收到的是图片字节流字符串
                IMG_QUEUE.put(get_data)
                # print("区域入侵算法接收到图片")
        except Exception as err:
            print("do_Post", err)

    def log_message(self, *args):
        return


class InvasionApplication(object):
    @staticmethod
    def run(host, port):
        server_address = (host, port)
        handler_class = InvasionHTTPRequestHandler
        server = InvasionHTTPServer(server_address, handler_class)
        print(f"[invasion] [pid:{os.getpid()}] [server:{host}_{port}]")
        print("区域入侵web服务启动成功")
        server.serve_forever()

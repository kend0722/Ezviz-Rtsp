import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import http.server
import socketserver

from manage_global import IMG_QUEUE


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


class MultiThreadedHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
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
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        self.do_HEAD()
        print("客户端接收到数据")
        get_data = json.loads(post_data)
        if self.path[1:] == "images":  # 所有客户端接收图片路径的路由
            IMG_QUEUE.put(post_data)
            print("客户端接收到图片")

    def log_message(self, format, *args):
        """
        重构日志类，不打印红字
        """
        return


class ManageApplication(object):
    @staticmethod
    def run(host, port):
        server_address = (host, port)
        handler_class = MultiThreadedHTTPRequestHandler
        server = MultiThreadedHTTPServer(server_address, handler_class)
        print(f"[manage] [pid:{os.getpid()}] [server:{host}_{port}]")
        server.serve_forever()
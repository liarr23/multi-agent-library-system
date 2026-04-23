"""
前端静态文件服务器
"""
import http.server
import socketserver
import os

PORT = 3000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".html": "text/html; charset=utf-8",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"前端服务已启动: http://localhost:{PORT}")
        print(f"服务目录: {DIRECTORY}")
        print("按 Ctrl+C 停止服务")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务已停止")

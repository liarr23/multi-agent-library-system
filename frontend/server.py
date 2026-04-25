"""
前端静态文件服务器
"""
import http.server
import socketserver
import os
import urllib.error
import urllib.request

PORT = 3000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
BACKEND_BASE_URL = os.environ.get("BACKEND_BASE_URL", "http://127.0.0.1:8000").rstrip("/")

class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".html": "text/html; charset=utf-8",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def _should_proxy_to_backend(self):
        return self.path.startswith("/api/")

    def _proxy_to_backend(self):
        target_url = f"{BACKEND_BASE_URL}{self.path}"
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        request_headers = {k: v for k, v in self.headers.items() if k.lower() != "host"}
        request = urllib.request.Request(target_url, data=body, headers=request_headers, method=self.command)

        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                payload = response.read()
                self.send_response(response.status)
                for key, value in response.headers.items():
                    if key.lower() in {"transfer-encoding", "connection"}:
                        continue
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(payload)
        except urllib.error.HTTPError as exc:
            payload = exc.read()
            self.send_response(exc.code)
            for key, value in exc.headers.items():
                if key.lower() in {"transfer-encoding", "connection"}:
                    continue
                self.send_header(key, value)
            self.end_headers()
            if payload:
                self.wfile.write(payload)
        except urllib.error.URLError as exc:
            self.send_response(502)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            error_body = (
                '{"detail":"后端服务不可达，请确认后端已启动并监听 8000 端口",'
                f'"error":"{exc.reason}"}}'
            )
            self.wfile.write(error_body.encode("utf-8"))

    def do_GET(self):
        if self._should_proxy_to_backend():
            self._proxy_to_backend()
            return
        super().do_GET()

    def do_POST(self):
        if self._should_proxy_to_backend():
            self._proxy_to_backend()
            return
        super().do_POST()

    def do_PUT(self):
        if self._should_proxy_to_backend():
            self._proxy_to_backend()
            return
        super().do_PUT()

    def do_DELETE(self):
        if self._should_proxy_to_backend():
            self._proxy_to_backend()
            return
        super().do_DELETE()

    def do_PATCH(self):
        if self._should_proxy_to_backend():
            self._proxy_to_backend()
            return
        super().do_PATCH()

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"前端服务已启动: http://localhost:{PORT}")
        print(f"API代理目标: {BACKEND_BASE_URL}")
        print(f"服务目录: {DIRECTORY}")
        print("按 Ctrl+C 停止服务")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n服务已停止")

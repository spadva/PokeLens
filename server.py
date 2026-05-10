#!/usr/bin/env python3
import http.server
import json
import os
import urllib.request
import urllib.error
import sys

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
PORT = int(os.environ.get("PORT", 8080))
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.BaseHTTPRequestHandler):

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/" or path == "":
            path = "/index.html"
        file_path = os.path.join(SCRIPT_DIR, path.lstrip("/"))
        if not os.path.isfile(file_path):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")
            return
        ext = os.path.splitext(file_path)[1]
        mime = {".html": "text/html", ".js": "text/javascript", ".css": "text/css", ".png": "image/png", ".ico": "image/x-icon"}.get(ext, "application/octet-stream")
        with open(file_path, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", len(data))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path != "/analyze":
            self.send_error_json(404, "Not found")
            return
        if not API_KEY:
            self.send_error_json(500, "ANTHROPIC_API_KEY environment variable is not set.")
            return
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=body,
            headers={
                "Content-Type": "application/json",
                "x-api-key": API_KEY,
                "anthropic-version": "2023-06-01",
                "anthropic-beta": "web-search-2025-03-05",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                result = r.read()
            self.send_json(200, result)
        except urllib.error.HTTPError as e:
            self.send_json(e.code, e.read())
        except Exception as e:
            self.send_error_json(500, str(e))

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def send_json(self, code, raw_bytes):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(raw_bytes))
        self._cors()
        self.end_headers()
        self.wfile.write(raw_bytes)

    def send_error_json(self, code, message):
        body = json.dumps({"error": {"type": "server_error", "message": message}}).encode()
        self.send_json(code, body)

    def log_message(self, fmt, *args):
        print(fmt % args, flush=True)

if __name__ == "__main__":
    print(f"Starting PokéLens on port {PORT}", flush=True)
    if not API_KEY:
        print("WARNING: ANTHROPIC_API_KEY is not set!", flush=True)
    else:
        print(f"API key loaded: {API_KEY[:12]}...", flush=True)
    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Server stopped.")
        sys.exit(0)

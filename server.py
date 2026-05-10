#!/usr/bin/env python3
import http.server, json, os, base64, urllib.request, urllib.error

API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
PORT = int(os.environ.get("PORT", 8080))

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_POST(self):
        if self.path == "/analyze":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)

            if not API_KEY:
                self.send_json(500, {"error": {"type": "no_key", "message": "ANTHROPIC_API_KEY not set. Run: export ANTHROPIC_API_KEY=your_key_here"}})
                return

            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": API_KEY,
                    "anthropic-version": "2023-06-01",
                    "anthropic-beta": "web-search-2025-03-05"
                },
                method="POST"
            )
            try:
                with urllib.request.urlopen(req) as r:
                    result = r.read()
                self.send_json(200, json.loads(result))
            except urllib.error.HTTPError as e:
                self.send_json(e.code, json.loads(e.read()))
            except Exception as e:
                self.send_json(500, {"error": {"type": "server_error", "message": str(e)}})
        else:
            self.send_json(404, {"error": "not found"})

    def send_json(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(fmt % args)

if __name__ == "__main__":
    print(f"\n🎴 PokéLens server running at http://localhost:{PORT}")
    print(f"   Open: http://localhost:{PORT}/pokemon-card-checker.html\n")
    if not API_KEY:
        print("⚠️  No API key found! Run this first:")
        print("   export ANTHROPIC_API_KEY=your_key_here\n")
    http.server.HTTPServer(("", PORT), Handler).serve_forever()

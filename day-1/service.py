import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import urlopen

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

SERVICE = os.environ["SERVICE"]
BACKEND_DELAY = int(os.environ.get("BACKEND_DELAY_MS", "20")) / 1000
REQUESTS = Counter("http_requests_total", "Completed HTTP requests", ["service", "status"])
for status in ("200", "500", "502"):
    REQUESTS.labels(SERVICE, status)
DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request handling time in seconds",
    ["service"],
    buckets=(.01, .025, .05, .1, .25, .5, .75, .85, 1, 1.5, 2, 3, 5),
).labels(SERVICE)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/metrics":
            self.reply(200, generate_latest(), CONTENT_TYPE_LATEST)
            return
        if self.path not in ("/work", "/error"):
            self.reply(404, b"Use /work, /error or /metrics\n")
            return

        start = time.monotonic()
        status = self.handle_work()
        DURATION.observe(time.monotonic() - start)
        REQUESTS.labels(SERVICE, str(status)).inc()
        self.reply(status, f"{SERVICE}: HTTP {status}\n".encode())

    def handle_work(self):
        if SERVICE == "backend":
            time.sleep(BACKEND_DELAY)
            return 500 if self.path == "/error" else 200

        try:
            with urlopen(f"http://backend:8080{self.path}", timeout=3) as response:
                return response.status
        except HTTPError as error:
            error.close()
            return error.code
        except OSError:
            return 502

    def reply(self, status, body, content_type="text/plain; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        if self.path == "/error":
            super().log_message(format, *args)


ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()

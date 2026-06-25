"""Minimal local web interface."""

from __future__ import annotations

from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable
from urllib.parse import parse_qs

from .app import LastLightApp

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def render_page(query: str = "", answer: str = "") -> bytes:
    escaped_query = escape(query)
    escaped_answer = escape(answer)
    output = (
        f"<pre>{escaped_answer}</pre>"
        if answer
        else "<p class=\"muted\">Ask a question from the local knowledge pack.</p>"
    )
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LastLight</title>
<style>
:root {{ color-scheme: dark; }}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  background: #000;
  color: #ddd;
  font: 16px/1.45 system-ui, sans-serif;
}}
main {{
  width: min(760px, 100%);
  margin: 0 auto;
  padding: 1rem;
}}
h1 {{ font-size: 1.25rem; margin: 0 0 1rem; }}
form {{ display: flex; gap: .5rem; margin-bottom: 1rem; }}
input {{
  flex: 1;
  min-width: 0;
  background: #050505;
  color: #eee;
  border: 1px solid #555;
  padding: .7rem;
}}
button {{
  background: #eee;
  color: #000;
  border: 0;
  padding: .7rem .9rem;
  font-weight: 700;
}}
pre {{
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  background: #050505;
  border: 1px solid #333;
  padding: 1rem;
}}
.muted {{ color: #999; }}
</style>
</head>
<body>
<main>
<h1>LastLight</h1>
<form method="post">
<input name="q" value="{escaped_query}" autocomplete="off" autofocus>
<button>Ask</button>
</form>
{output}
</main>
</body>
</html>
"""
    return html.encode("utf-8")


def parse_query(body: bytes) -> str:
    values = parse_qs(body.decode("utf-8"), keep_blank_values=True)
    return values.get("q", [""])[0].strip()


def make_handler(app: LastLightApp) -> type[BaseHTTPRequestHandler]:
    class LastLightHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self._send_page(render_page())

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            query = parse_query(self.rfile.read(length))
            answer = app.answer(query) if query else ""
            self._send_page(render_page(query=query, answer=answer))

        def _send_page(self, body: bytes) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

    return LastLightHandler


def serve(
    app: LastLightApp,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    server_factory: Callable[..., HTTPServer] = HTTPServer,
) -> None:
    server = server_factory((host, port), make_handler(app))
    print(f"Serving LastLight at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        server.server_close()

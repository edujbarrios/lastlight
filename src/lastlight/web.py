"""Minimal local web interface."""

from __future__ import annotations

from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable
from urllib.parse import parse_qs, urlsplit

from .app import LastLightApp
from .session import LastLightSession

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
MAX_TURNS = 4


def render_page(
    query: str = "", answer: str = "", history: list[tuple[str, str]] | None = None
) -> bytes:
    escaped_query = escape(query)
    turns = history if history is not None else ([(query, answer)] if answer else [])
    output = render_history(turns)
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
  color: #b8b8b8;
  font: 16px/1.45 system-ui, sans-serif;
}}
main {{
  width: min(760px, 100%);
  margin: 0 auto;
  padding: 1rem;
}}
h1 {{ color: #c8c8c8; font-size: 1.25rem; margin: 0 0 1rem; }}
form {{ display: flex; gap: .5rem; margin-bottom: 1rem; }}
input {{
  flex: 1;
  min-width: 0;
  background: #000;
  color: #cfcfcf;
  border: 1px solid #2a2a2a;
  padding: .7rem;
}}
button {{
  background: #080808;
  color: #cfcfcf;
  border: 1px solid #2a2a2a;
  padding: .7rem .9rem;
  font-weight: 700;
}}
button:focus,
input:focus {{
  border-color: #555;
  outline: none;
}}
pre {{
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  background: #000;
  color: #b8b8b8;
  border: 1px solid #202020;
  padding: 1rem;
}}
.turn {{
  border: 1px solid #202020;
  margin-bottom: .75rem;
  padding: .8rem;
}}
.q {{
  color: #8f8f8f;
  margin-bottom: .45rem;
}}
.muted {{ color: #777; }}
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


def render_history(history: list[tuple[str, str]]) -> str:
    if not history:
        return "<p class=\"muted\">Ask a question from the local knowledge pack.</p>"
    parts: list[str] = []
    for query, answer in history[-MAX_TURNS:]:
        parts.append(
            "<section class=\"turn\">"
            f"<div class=\"q\">&gt; {escape(query)}</div>"
            f"<pre>{escape(answer)}</pre>"
            "</section>"
        )
    return "\n".join(parts)


def parse_query(body: bytes) -> str:
    values = parse_qs(body.decode("utf-8"), keep_blank_values=True)
    return values.get("q", [""])[0].strip()


def parse_query_string(path: str) -> str:
    values = parse_qs(urlsplit(path).query, keep_blank_values=True)
    return values.get("q", [""])[0].strip()


def solution_answer(session: LastLightSession, query: str) -> str:
    return session.answer_passage(query)


def make_handler(app: LastLightApp) -> type[BaseHTTPRequestHandler]:
    session = LastLightSession(app)
    history: list[tuple[str, str]] = []

    class LastLightHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            query = parse_query_string(self.path)
            answer = self._record_answer(query) if query else ""
            self._send_page(render_page(query=query, answer=answer, history=history))

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            query = parse_query(self.rfile.read(length))
            answer = self._record_answer(query) if query else ""
            self._send_page(render_page(query=query, answer=answer, history=history))

        def _record_answer(self, query: str) -> str:
            answer = solution_answer(session, query)
            history.append((query, answer))
            del history[:-MAX_TURNS]
            return answer

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

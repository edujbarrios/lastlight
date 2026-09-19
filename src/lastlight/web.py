"""Minimal local web interface."""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Callable
from urllib.parse import parse_qs, urlsplit

from .app import LastLightApp
from .safety import LOW_CONFIDENCE_RESPONSE
from .session import LastLightSession
from .triage import first_acceptable_result

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
MAX_TURNS = 4


@dataclass(frozen=True)
class WebPack:
    name: str
    version: str = "unknown"
    source: str = "local"
    path: str = ""


@dataclass(frozen=True)
class WebTurn:
    query: str
    answer: str
    pack_name: str = ""
    pack_version: str = ""
    source_path: str = ""
    confidence: str = ""


def mounted_packs(app: LastLightApp) -> tuple[WebPack, ...]:
    repository = app.repository
    describe_packs = getattr(repository, "describe_packs", None)
    if callable(describe_packs):
        packs = describe_packs()
    else:
        describe_pack = getattr(repository, "describe_pack", None)
        packs = (describe_pack(),) if callable(describe_pack) else ()
    return tuple(
        WebPack(
            name=str(getattr(pack, "name", "knowledge")),
            version=str(getattr(pack, "version", "unknown")),
            source=str(getattr(pack, "source", "local")),
            path=str(getattr(pack, "path", "")),
        )
        for pack in packs
    )


def render_page(
    query: str = "",
    answer: str = "",
    history: list[WebTurn | tuple[str, str]] | None = None,
    packs: tuple[WebPack, ...] = (),
) -> bytes:
    escaped_query = escape(query)
    turns: list[WebTurn | tuple[str, str]]
    turns = history if history is not None else ([(query, answer)] if answer else [])
    output = render_history(turns)
    pack_count = len(packs)
    pack_label = f"{pack_count} pack{'s' if pack_count != 1 else ''} mounted" if pack_count else "Built-in knowledge"
    pack_chips = render_pack_chips(packs)
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
  background: #050505;
  color: #b8b8b8;
  font: 16px/1.45 system-ui, sans-serif;
}}
main {{
  width: min(820px, 100%);
  margin: 0 auto;
  padding: 1rem;
}}
.top {{
  align-items: center;
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: .8rem;
}}
.brand {{ display: flex; align-items: center; gap: .65rem; }}
h1 {{ color: #d5d5d5; font-size: 1.3rem; margin: 0; letter-spacing: .02em; }}
.status {{
  border: 1px solid #29422f;
  color: #89b392;
  font-size: .72rem;
  letter-spacing: .08em;
  padding: .18rem .42rem;
  text-transform: uppercase;
}}
.clear {{
  color: #777;
  font-size: .9rem;
  text-decoration: none;
}}
.clear:focus,
.clear:hover {{ color: #aaa; }}
.pack-panel {{
  border: 1px solid #222;
  background: #090909;
  margin-bottom: 1rem;
  padding: .8rem .9rem;
}}
.pack-head {{
  align-items: center;
  display: flex;
  justify-content: space-between;
  gap: .75rem;
  margin-bottom: .55rem;
}}
.pack-head strong {{ color: #c9c9c9; font-size: .9rem; }}
.pack-head span {{ color: #6e6e6e; font-size: .78rem; }}
.pack-list {{ display: flex; flex-wrap: wrap; gap: .45rem; }}
.pack {{
  border: 1px solid #2a2a2a;
  color: #a8a8a8;
  font-size: .78rem;
  padding: .28rem .48rem;
}}
.pack b {{ color: #d0d0d0; font-weight: 600; }}
.calm {{
  border: 1px solid #202020;
  margin-bottom: 1rem;
  padding: .85rem .95rem;
}}
.calm strong {{
  color: #d0d0d0;
  display: block;
  font-size: .95rem;
  margin-bottom: .45rem;
}}
.calm ol {{
  color: #8f8f8f;
  margin: 0;
  padding-left: 1.2rem;
}}
.calm li {{ margin: .15rem 0; }}
form {{ display: flex; gap: .6rem; margin-bottom: 1rem; }}
input {{
  flex: 1;
  min-width: 0;
  background: #080808;
  color: #d5d5d5;
  border: 1px solid #2a2a2a;
  padding: .75rem;
}}
input::placeholder {{ color: #565656; }}
button {{
  background: #111;
  color: #d5d5d5;
  border: 1px solid #333;
  min-width: 5.5rem;
  padding: .75rem .95rem;
  font-weight: 700;
}}
button:focus,
input:focus {{
  border-color: #666;
  outline: none;
}}
pre {{
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  background: transparent;
  color: #c3c3c3;
  border: 0;
  margin: 0;
  padding: 0;
  font: inherit;
}}
.turn {{
  border: 1px solid #242424;
  background: #080808;
  margin-bottom: .75rem;
  padding: .95rem;
}}
.q {{
  color: #969696;
  margin-bottom: .5rem;
}}
.answer-head {{
  align-items: center;
  display: flex;
  justify-content: space-between;
  gap: .75rem;
  margin-bottom: .42rem;
}}
.a-label {{ color: #737373; font-size: .82rem; }}
.provenance {{ color: #777; font-size: .76rem; text-align: right; }}
.provenance b {{ color: #a8a8a8; font-weight: 600; }}
.muted {{ color: #777; }}
@media (max-width: 620px) {{
  .answer-head, .pack-head {{ align-items: flex-start; flex-direction: column; }}
  .provenance {{ text-align: left; }}
}}
</style>
</head>
<body>
<main>
<div class="top">
<div class="brand"><h1>LastLight</h1><span class="status">offline</span></div>
<a class="clear" href="/?clear=1">Clear</a>
</div>
<section class="pack-panel" aria-label="Mounted knowledge packs">
<div class="pack-head"><strong>{escape(pack_label)}</strong><span>local · auditable · no network required</span></div>
<div class="pack-list">{pack_chips}</div>
</section>
<section class="calm" aria-label="Crisis safety reminder">
<strong>Keep calm. The situation may be unstable, but you can still make safer decisions.</strong>
<ol>
<li>Breathe slowly for 30 seconds.</li>
<li>Check for immediate danger: fire, gas smell, injuries, or flooding.</li>
<li>Preserve power, water, heat, and attention.</li>
<li>Ask one practical question at a time.</li>
</ol>
</section>
<form method="post">
<input name="q" value="{escaped_query}" placeholder="Ask across the mounted knowledge packs..." autocomplete="off" autofocus>
<button>Search</button>
</form>
{output}
</main>
</body>
</html>
"""
    return html.encode("utf-8")


def render_pack_chips(packs: tuple[WebPack, ...]) -> str:
    if not packs:
        return '<span class="pack"><b>LastLight core</b></span>'
    return "".join(
        f'<span class="pack"><b>{escape(pack.name)}</b> · {escape(pack.version)}</span>'
        for pack in packs
    )


def render_history(history: list[WebTurn | tuple[str, str]]) -> str:
    if not history:
        return '<p class="muted">Ask a question from one or more mounted knowledge packs.</p>'
    parts: list[str] = []
    for item in history[-MAX_TURNS:]:
        turn = item if isinstance(item, WebTurn) else WebTurn(item[0], item[1])
        provenance = ""
        if turn.pack_name:
            pack = f"{turn.pack_name} {turn.pack_version}".strip()
            source = f" · {turn.source_path}" if turn.source_path else ""
            confidence = f" · {turn.confidence}" if turn.confidence else ""
            provenance = (
                f'<div class="provenance"><b>{escape(pack)}</b>'
                f"{escape(source)}{escape(confidence)}</div>"
            )
        parts.append(
            '<section class="turn">'
            f'<div class="q">You: {escape(turn.query)}</div>'
            '<div class="answer-head">'
            '<div class="a-label">LastLight answer</div>'
            f"{provenance}"
            "</div>"
            f"<pre>{escape(turn.answer)}</pre>"
            "</section>"
        )
    return "\n".join(parts)


def parse_query(body: bytes) -> str:
    values = parse_qs(body.decode("utf-8"), keep_blank_values=True)
    return values.get("q", [""])[0].strip()


def parse_query_string(path: str) -> str:
    values = parse_qs(urlsplit(path).query, keep_blank_values=True)
    return values.get("q", [""])[0].strip()


def parse_clear(path: str) -> bool:
    values = parse_qs(urlsplit(path).query, keep_blank_values=True)
    return values.get("clear", [""])[0] == "1"


def solution_turn(session: LastLightSession, query: str) -> WebTurn:
    results = session.search(query, top_k=3)
    result = first_acceptable_result(results)
    if result is None:
        return WebTurn(query=query, answer=LOW_CONFIDENCE_RESPONSE)
    document = result.document
    return WebTurn(
        query=query,
        answer=result.passage,
        pack_name=document.pack_name if document.pack_path else "",
        pack_version=document.pack_version if document.pack_path else "",
        source_path=document.path,
        confidence=result.confidence,
    )


def solution_answer(session: LastLightSession, query: str) -> str:
    return solution_turn(session, query).answer


def make_handler(app: LastLightApp) -> type[BaseHTTPRequestHandler]:
    session = LastLightSession(app)
    history: list[WebTurn] = []
    packs = mounted_packs(app)

    class LastLightHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if parse_clear(self.path):
                session.clear()
                history.clear()
                self._send_page(render_page(packs=packs))
                return
            query = parse_query_string(self.path)
            turn = self._record_answer(query) if query else None
            self._send_page(
                render_page(
                    query=query,
                    answer=turn.answer if turn else "",
                    history=history,
                    packs=packs,
                )
            )

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            query = parse_query(self.rfile.read(length))
            turn = self._record_answer(query) if query else None
            self._send_page(
                render_page(
                    query=query,
                    answer=turn.answer if turn else "",
                    history=history,
                    packs=packs,
                )
            )

        def _record_answer(self, query: str) -> WebTurn:
            turn = solution_turn(session, query)
            history.append(turn)
            del history[:-MAX_TURNS]
            return turn

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

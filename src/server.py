"""A small standard-library HTTP server for the URL shortener."""

import argparse
import html
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlsplit

from src.hash_table import HashTable
from src.shortener import Shortener

TABLE = HashTable()
SHORTENER = Shortener(TABLE)


def _page(content: str) -> str:
    return (
        "<!doctype html><html lang=\"en\"><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        "<title>URL shortener</title><body>"
        "<nav><a href=\"/\">Shorten</a> | <a href=\"/table\">Hash table</a></nav>"
        f"{content}</body></html>"
    )


class ShortenerHandler(BaseHTTPRequestHandler):
    table = TABLE
    shortener = SHORTENER

    def _send_html(self, status: int, content: str) -> None:
        body = _page(content).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path == "/":
            self._send_html(
                200,
                "<h1>URL shortener</h1>"
                "<form method=\"post\" action=\"/\">"
                "<label>URL <input name=\"url\" type=\"url\" required></label>"
                "<button type=\"submit\">Shorten</button></form>",
            )
            return
        if path == "/table":
            self._send_html(200, self._render_table())
            return
        if path.startswith("/r/"):
            code = unquote(path[len("/r/") :])
            if not code or "/" in code:
                self._send_html(404, "<h1>Short link not found</h1>")
                return
            try:
                url = self.shortener.expand(code)
            except KeyError:
                self._send_html(404, "<h1>Short link not found</h1>")
                return
            self.send_response(302)
            self.send_header("Location", url)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self._send_html(404, "<h1>Page not found</h1>")

    def do_POST(self) -> None:
        if urlsplit(self.path).path != "/":
            self._send_html(404, "<h1>Page not found</h1>")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0:
                raise ValueError("invalid content length")
            form = parse_qs(
                self.rfile.read(length).decode("utf-8"),
                keep_blank_values=True,
                max_num_fields=20,
            )
            url_values = form.get("url")
            if not url_values:
                raise ValueError("URL is required")
            url = url_values[0]
            code = self.shortener.shorten(url)
        except (UnicodeDecodeError, ValueError, TypeError) as exc:
            self._send_html(
                400,
                "<h1>Invalid URL</h1><p>"
                + html.escape(str(exc))
                + "</p><p><a href=\"/\">Try again</a></p>",
            )
            return

        link = "/r/" + code
        self._send_html(
            200,
            "<h1>Short link created</h1><p><a href=\""
            + html.escape(link, quote=True)
            + "\">"
            + html.escape(link)
            + "</a></p>",
        )

    def _render_table(self) -> str:
        rows = []
        for bucket_index, head in enumerate(self.table.buckets):
            entries = []
            node = head
            while node is not None:
                entries.append(self._render_entry(node.key, node.value))
                node = node.next
            content = "".join(entries) if entries else "<li>empty</li>"
            rows.append(f"<li><strong>Bucket {bucket_index}</strong><ul>{content}</ul></li>")
        return "<h1>Hash table</h1><ol>" + "".join(rows) + "</ol>"

    def _render_entry(self, key: str, value: str) -> str:
        bucket, steps = self.table.hash_details(key)
        self.table.get(key)
        visited = " &rarr; ".join(
            html.escape(visited_key) for visited_key in self.table.last_lookup_trace
        )
        calculations = []
        previous = 0
        for character, step in zip(key, steps):
            calculations.append(
                html.escape(
                    f"(31*{previous}+ord({character!r})) % {self.table.capacity} = {step}"
                )
            )
            previous = step
        calculation = " ; ".join(calculations) or "0 (empty key)"
        return (
            "<li><code>"
            + html.escape(key)
            + "</code> =&gt; <code>"
            + html.escape(value)
            + "</code>; hash steps ("
            + html.escape(key)
            + "): "
            + calculation
            + f"; bucket {bucket}; lookup visited: {visited}</li>"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the URL shortener web server.")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("0.0.0.0", args.port), ShortenerHandler)
    print(f"Serving on http://0.0.0.0:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

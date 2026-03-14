from datetime import datetime
from html import escape
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs
import sqlite3

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "recitations.db"
DISPLAY_TIMESTAMP_FORMAT = "%d-%b-%Y %I:%M %p"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS recitations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                verse TEXT NOT NULL,
                created_at TEXT NOT NULL,
                created_at_iso TEXT NOT NULL
            )
            """
        )
        conn.commit()


def add_recitation(verse: str) -> None:
    verse = verse.strip()
    if not verse:
        return

    now = datetime.now()
    timestamp_display = now.strftime(DISPLAY_TIMESTAMP_FORMAT)
    timestamp_iso = now.isoformat(timespec="seconds")

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO recitations (verse, created_at, created_at_iso)
            VALUES (?, ?, ?)
            """,
            (verse, timestamp_display, timestamp_iso),
        )
        conn.commit()


def list_recitations() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT verse, created_at
            FROM recitations
            ORDER BY created_at_iso DESC, id DESC
            """
        ).fetchall()


def render_index() -> str:
    entries_html = ""
    entries = list_recitations()
    if entries:
        lines = []
        for entry in entries:
            lines.append(
                "<li><span class='verse'>{verse}</span><span class='timestamp'>{ts}</span></li>".format(
                    verse=escape(entry["verse"]),
                    ts=escape(entry["created_at"]),
                )
            )
        entries_html = "<ul>{}</ul>".format("".join(lines))
    else:
        entries_html = "<p class='empty'>No entries yet. Add your first completed verse above.</p>"

    return f"""<!DOCTYPE html>
<html lang='en'>
  <head>
    <meta charset='UTF-8' />
    <meta name='viewport' content='width=device-width, initial-scale=1.0' />
    <title>Quran Recitation Tracker</title>
    <link rel='stylesheet' href='/static/style.css' />
  </head>
  <body>
    <main class='container'>
      <h1>Quran Recitation Tracker</h1>
      <p class='subtitle'>Track the verses you complete with automatic timestamps.</p>
      <form action='/add' method='post' class='entry-form'>
        <label for='verse'>Completed Verse</label>
        <input id='verse' name='verse' type='text' placeholder='e.g., Surah Al-Baqarah 2:255' required />
        <button type='submit'>Add Entry</button>
      </form>
      <section class='entries'>
        <h2>Recent Entries</h2>
        {entries_html}
      </section>
    </main>
  </body>
</html>"""


class RecitationHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/":
            body = render_index().encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path == "/static/style.css":
            css = (APP_DIR / "static" / "style.css").read_text(encoding="utf-8").encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/css; charset=utf-8")
            self.send_header("Content-Length", str(len(css)))
            self.end_headers()
            self.wfile.write(css)
            return

        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/add":
            self.send_error(HTTPStatus.NOT_FOUND)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length).decode("utf-8")
        parsed = parse_qs(body)
        verse = parsed.get("verse", [""])[0]
        add_recitation(verse)

        self.send_response(HTTPStatus.SEE_OTHER)
        self.send_header("Location", "/")
        self.end_headers()


def run(host: str = "0.0.0.0", port: int = 5000) -> None:
    init_db()
    server = HTTPServer((host, port), RecitationHandler)
    print(f"Server running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()

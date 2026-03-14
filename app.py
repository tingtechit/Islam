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
TEMPLATE_PATH = APP_DIR / "templates" / "index.html"

SURAHS = [
    "Al-Fatihah", "Al-Baqarah", "Ali 'Imran", "An-Nisa", "Al-Ma'idah", "Al-An'am", "Al-A'raf",
    "Al-Anfal", "At-Tawbah", "Yunus", "Hud", "Yusuf", "Ar-Ra'd", "Ibrahim", "Al-Hijr", "An-Nahl",
    "Al-Isra", "Al-Kahf", "Maryam", "Ta-Ha", "Al-Anbiya", "Al-Hajj", "Al-Mu'minun", "An-Nur",
    "Al-Furqan", "Ash-Shu'ara", "An-Naml", "Al-Qasas", "Al-'Ankabut", "Ar-Rum", "Luqman", "As-Sajdah",
    "Al-Ahzab", "Saba", "Fatir", "Ya-Sin", "As-Saffat", "Sad", "Az-Zumar", "Ghafir", "Fussilat",
    "Ash-Shuraa", "Az-Zukhruf", "Ad-Dukhan", "Al-Jathiyah", "Al-Ahqaf", "Muhammad", "Al-Fath", "Al-Hujurat",
    "Qaf", "Adh-Dhariyat", "At-Tur", "An-Najm", "Al-Qamar", "Ar-Rahman", "Al-Waqi'ah", "Al-Hadid",
    "Al-Mujadila", "Al-Hashr", "Al-Mumtahanah", "As-Saff", "Al-Jumu'ah", "Al-Munafiqun", "At-Taghabun",
    "At-Talaq", "At-Tahrim", "Al-Mulk", "Al-Qalam", "Al-Haqqah", "Al-Ma'arij", "Nuh", "Al-Jinn",
    "Al-Muzzammil", "Al-Muddaththir", "Al-Qiyamah", "Al-Insan", "Al-Mursalat", "An-Naba", "An-Nazi'at",
    "Abasa", "At-Takwir", "Al-Infitar", "Al-Mutaffifin", "Al-Inshiqaq", "Al-Buruj", "At-Tariq", "Al-A'la",
    "Al-Ghashiyah", "Al-Fajr", "Al-Balad", "Ash-Shams", "Al-Layl", "Ad-Duha", "Ash-Sharh", "At-Tin",
    "Al-'Alaq", "Al-Qadr", "Al-Bayyinah", "Az-Zalzalah", "Al-'Adiyat", "Al-Qari'ah", "At-Takathur", "Al-'Asr",
    "Al-Humazah", "Al-Fil", "Quraysh", "Al-Ma'un", "Al-Kawthar", "Al-Kafirun", "An-Nasr", "Al-Masad",
    "Al-Ikhlas", "Al-Falaq", "An-Nas",
]


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
                surah TEXT NOT NULL,
                verse_start INTEGER NOT NULL,
                verse_end INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                created_at_iso TEXT NOT NULL
            )
            """
        )
        conn.commit()


def add_recitation(surah: str, verse_start: str, verse_end: str) -> None:
    surah = surah.strip()
    if surah not in SURAHS:
        return

    try:
        start = int(verse_start)
        end = int(verse_end)
    except ValueError:
        return

    if start <= 0 or end <= 0 or end < start:
        return

    now = datetime.now()
    timestamp_display = now.strftime(DISPLAY_TIMESTAMP_FORMAT)
    timestamp_iso = now.isoformat(timespec="seconds")

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO recitations (surah, verse_start, verse_end, created_at, created_at_iso)
            VALUES (?, ?, ?, ?, ?)
            """,
            (surah, start, end, timestamp_display, timestamp_iso),
        )
        conn.commit()


def list_recitations() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT surah, verse_start, verse_end, created_at
            FROM recitations
            ORDER BY created_at_iso DESC, id DESC
            """
        ).fetchall()


def build_surah_options() -> str:
    return "".join(
        f"<option value='{escape(surah)}'>{index}. {escape(surah)}</option>"
        for index, surah in enumerate(SURAHS, start=1)
    )


def render_index() -> str:
    entries = list_recitations()
    if entries:
        lines = []
        for entry in entries:
            if entry["verse_start"] == entry["verse_end"]:
                verse_label = f"Verse {entry['verse_start']}"
            else:
                verse_label = f"Verses {entry['verse_start']}-{entry['verse_end']}"

            lines.append(
                (
                    "<li>"
                    f"<span class='verse'>{escape(entry['surah'])} - {escape(verse_label)}</span>"
                    f"<span class='timestamp'>{escape(entry['created_at'])}</span>"
                    "</li>"
                )
            )
        entries_html = f"<ul>{''.join(lines)}</ul>"
    else:
        entries_html = "<p class='empty'>No entries yet. Add your first recitation above.</p>"

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    return (
        template.replace("{{SURAH_OPTIONS}}", build_surah_options())
        .replace("{{ENTRIES_HTML}}", entries_html)
    )


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
        surah = parsed.get("surah", [""])[0]
        verse_start = parsed.get("verse_start", [""])[0]
        verse_end = parsed.get("verse_end", [""])[0]
        add_recitation(surah, verse_start, verse_end)

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

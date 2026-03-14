import importlib.util
import re
import sys
from pathlib import Path

APP_PATH = Path(__file__).resolve().parents[1] / "app.py"
spec = importlib.util.spec_from_file_location("app", APP_PATH)
app = importlib.util.module_from_spec(spec)
sys.modules["app"] = app
assert spec and spec.loader
spec.loader.exec_module(app)


def test_add_entry_stores_formatted_timestamp_and_lists_entries_descending(tmp_path):
    app.DB_PATH = tmp_path / "test_recitations.db"
    app.init_db()

    app.add_recitation("Surah Al-Fatihah 1:1")
    app.add_recitation("Surah Al-Baqarah 2:255")

    entries = app.list_recitations()

    assert entries[0]["verse"] == "Surah Al-Baqarah 2:255"
    assert entries[1]["verse"] == "Surah Al-Fatihah 1:1"

    for entry in entries:
        assert re.fullmatch(r"\d{2}-[A-Za-z]{3}-\d{4} \d{2}:\d{2} (?:AM|PM)", entry["created_at"])

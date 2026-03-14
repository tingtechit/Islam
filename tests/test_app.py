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


def test_add_entry_stores_timestamp_and_lists_entries_descending(tmp_path):
    app.DB_PATH = tmp_path / "test_recitations.db"
    app.init_db()

    app.add_recitation("Al-Fatihah", "1", "3")
    app.add_recitation("Ya-Sin", "10", "10")

    entries = app.list_recitations()

    assert entries[0]["surah"] == "Ya-Sin"
    assert entries[0]["verse_start"] == 10
    assert entries[0]["verse_end"] == 10
    assert entries[1]["surah"] == "Al-Fatihah"
    assert entries[1]["verse_start"] == 1
    assert entries[1]["verse_end"] == 3

    for entry in entries:
        assert re.fullmatch(r"\d{2}-[A-Za-z]{3}-\d{4} \d{2}:\d{2} (?:AM|PM)", entry["created_at"])


def test_invalid_entry_is_not_saved(tmp_path):
    app.DB_PATH = tmp_path / "test_recitations.db"
    app.init_db()

    app.add_recitation("Invalid Surah", "1", "2")
    app.add_recitation("Al-Fatihah", "3", "1")

    entries = app.list_recitations()
    assert entries == []

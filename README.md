# Quran Recitation Tracker

A simple app to record completed Quran recitation with an automatic timestamp.

## Features
- Select a **Surah** from a dropdown list.
- Enter **Verse Start** and **Verse End**.
- Automatically saves the current timestamp in this format: `DD-Mon-YYYY HH:MI AM`.
- Shows entries in descending order (newest first).
- Uses an HTML page at `templates/index.html` for the UI.

## Run locally
```bash
python app.py
```

Open `http://localhost:5000`.

## Run tests
```bash
pytest -p no:cacheprovider
```

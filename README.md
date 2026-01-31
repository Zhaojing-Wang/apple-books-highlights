> This project is forked from [jladicos/apple-books-highlights](https://github.com/jladicos/apple-books-highlights) and upgraded using OpenAI Codex.

# Apple Books Highlights & Notes Export

Export Apple Books highlights and notes to Markdown files.

## What it does

- Optionally refreshes the Books database by opening and closing the app.
- Reads the local sqlite databases and exports one Markdown file per book with YAML frontmatter.
- Preserves a **My notes** section that will not be overwritten on subsequent syncs.

## Notes

- The exporter auto-detects the Books databases from standard container paths and picks the newest sqlite file.
- Output filenames are slugified and capped to avoid macOS filename length limits; the asset id suffix preserves uniqueness.
- When title or author metadata is missing, it falls back to values like `Untitled <asset_id>` and `Unknown`.

## Usage

Simplest way to get your highlights, though you might want to create a `virtualenv` first:

```
$ python3 setup.py install
$ apple-books-highlights.py sync
$ ll books
```

I've personally used a bash alias like this, so I can call `sync-books` from terminal anywhere on my system to update the annotations:

```
alias sync-books="apple-books-highlights.py --bookdir 'absolute/path/to/folder' sync"
```

## Quickstart

```
python3 -m venv .venv
.venv/bin/pip install -e .

.venv/bin/python scripts/apple-books-highlights.py list
.venv/bin/python scripts/apple-books-highlights.py sync
```

## Configuration

- Output directory: `--bookdir/-b` or `APPLE_BOOKS_HIGHLIGHT_DIRECTORY` (default `./books`).
- Skip Books refresh: `-n` for `list` and `sync`.
- Override database locations if Apple changes paths.

```
export APPLE_BOOKS_ANNOTATION_DB_DIR=~/Library/Containers/com.apple.iBooksX/Data/Documents/AEAnnotation
export APPLE_BOOKS_BOOK_DB_DIR=~/Library/Containers/com.apple.iBooksX/Data/Documents/BKLibrary
```

## Troubleshooting

- No books returned: open Apple Books once and rerun with refresh (omit `-n`).
- Database not found: set `APPLE_BOOKS_ANNOTATION_DB_DIR` and `APPLE_BOOKS_BOOK_DB_DIR` to the container paths on your machine.
- `Untitled <asset_id>` entries: metadata is missing in the Books database; export still works.

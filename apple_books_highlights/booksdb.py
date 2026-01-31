import pathlib
import sqlite3
import functools
import os
import subprocess
from time import sleep
from tqdm import tqdm

from typing import List, Dict, Union, Iterable, Optional, Tuple


SqliteQueryType = List[Dict[str, Union[str, int, float, None]]]

DEFAULT_ANNOTATION_DB_DIRS = [
    pathlib.Path.home()
    / "Library/Containers/com.apple.iBooksX/Data/Documents/AEAnnotation",
    pathlib.Path.home()
    / "Library/Containers/com.apple.BKAgentService/Data/Documents/AEAnnotation",
]
DEFAULT_BOOK_DB_DIRS = [
    pathlib.Path.home()
    / "Library/Containers/com.apple.iBooksX/Data/Documents/BKLibrary",
    pathlib.Path.home()
    / "Library/Containers/com.apple.BKAgentService/Data/Documents/BKLibrary",
]

BOOKS_APP_NAME = "Books"


ATTACH_BOOKS_QUERY = """
attach database ? as books
"""


NOTE_LIST_FIELDS = [
    "asset_id",
    "title",
    "author",
    "location",
    "selected_text",
    "note",
    "represent_text",
    "chapter",
    "style",
    "modified_date",
]

ANNOTATION_COLUMN_ALIASES = {
    "asset_id": ["ZANNOTATIONASSETID", "ZASSETID"],
    "location": ["ZANNOTATIONLOCATION", "ZLOCATION", "ZANNOTATIONLOCATIONSTRING"],
    "selected_text": ["ZANNOTATIONSELECTEDTEXT", "ZSELECTEDTEXT"],
    "note": ["ZANNOTATIONNOTE", "ZNOTE"],
    "represent_text": ["ZANNOTATIONREPRESENTATIVETEXT", "ZREPRESENTATIVETEXT"],
    "chapter": ["ZFUTUREPROOFING5", "ZCHAPTER", "ZANNOTATIONCHAPTER"],
    "style": ["ZANNOTATIONSTYLE", "ZSTYLE"],
    "modified_date": ["ZANNOTATIONMODIFICATIONDATE", "ZMODIFICATIONDATE"],
    "deleted": ["ZANNOTATIONDELETED", "ZDELETED"],
    "location_sort": ["ZPLLOCATIONRANGESTART", "ZLOCATIONRANGESTART"],
}

BOOK_COLUMN_ALIASES = {
    "asset_id": ["ZASSETID", "ZASSETID_", "ZASSETID__"],
    "title": ["ZTITLE"],
    "author": ["ZAUTHOR"],
}

BOOK_JOIN_COLUMNS = [
    "ZASSETID",
    "ZEPUBID",
    "ZMAPPEDASSETID",
    "ZTEMPORARYASSETID",
    "ZASSETGUID",
]


def _dir_env_override(env_key: str) -> Optional[pathlib.Path]:
    value = os.environ.get(env_key)
    if not value:
        return None
    return pathlib.Path(value).expanduser()


def _iter_sqlite_files(dirs: Iterable[pathlib.Path]) -> List[pathlib.Path]:
    files: List[pathlib.Path] = []
    for directory in dirs:
        if directory.is_dir():
            files.extend(list(directory.glob("*.sqlite")))
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files


def _table_exists(
    conn: sqlite3.Connection, table: str, schema: Optional[str] = None
) -> bool:
    cur = conn.cursor()
    if schema:
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        )
    else:
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        )
    return cur.fetchone() is not None


def _get_table_columns(
    conn: sqlite3.Connection, table: str, schema: Optional[str] = None
) -> List[str]:
    cur = conn.cursor()
    if schema:
        cur.execute(f"PRAGMA {schema}.table_info({table})")
    else:
        cur.execute(f"PRAGMA table_info({table})")
    return [row[1] for row in cur.fetchall()]


def _pick_column(available: List[str], candidates: List[str]) -> Optional[str]:
    for col in candidates:
        if col in available:
            return col
    return None


def _find_db_file(candidates: List[pathlib.Path], required_table: str) -> pathlib.Path:
    if not candidates:
        raise FileNotFoundError("No sqlite files found in expected directories")
    for path in candidates:
        try:
            conn = sqlite3.connect(str(path))
            if _table_exists(conn, required_table):
                conn.close()
                return path
            conn.close()
        except sqlite3.Error:
            continue
    raise FileNotFoundError(f"No sqlite files contained table {required_table}")


def _build_note_query(
    annotation_columns: List[str],
    book_columns: List[str],
) -> Tuple[str, List[str]]:
    asset_id_col = _pick_column(
        annotation_columns, ANNOTATION_COLUMN_ALIASES["asset_id"]
    )
    if asset_id_col is None:
        raise RuntimeError("Missing asset id column in annotation database")

    selected_text_col = _pick_column(
        annotation_columns, ANNOTATION_COLUMN_ALIASES["selected_text"]
    )
    note_col = _pick_column(annotation_columns, ANNOTATION_COLUMN_ALIASES["note"])
    if selected_text_col is None and note_col is None:
        raise RuntimeError("Missing both selected text and note columns")

    location_col = _pick_column(
        annotation_columns, ANNOTATION_COLUMN_ALIASES["location"]
    )
    represent_col = _pick_column(
        annotation_columns, ANNOTATION_COLUMN_ALIASES["represent_text"]
    )
    chapter_col = _pick_column(annotation_columns, ANNOTATION_COLUMN_ALIASES["chapter"])
    style_col = _pick_column(annotation_columns, ANNOTATION_COLUMN_ALIASES["style"])
    modified_col = _pick_column(
        annotation_columns, ANNOTATION_COLUMN_ALIASES["modified_date"]
    )
    deleted_col = _pick_column(annotation_columns, ANNOTATION_COLUMN_ALIASES["deleted"])
    location_sort_col = _pick_column(
        annotation_columns, ANNOTATION_COLUMN_ALIASES["location_sort"]
    )

    title_col = _pick_column(book_columns, BOOK_COLUMN_ALIASES["title"])
    author_col = _pick_column(book_columns, BOOK_COLUMN_ALIASES["author"])

    join_columns = [col for col in BOOK_JOIN_COLUMNS if col in book_columns]
    join_clause = ""
    if join_columns:
        join_conditions = [
            f"ZAEANNOTATION.{asset_id_col} = books.ZBKLIBRARYASSET.{col}"
            for col in join_columns
        ]
        join_clause = "left join books.ZBKLIBRARYASSET on " + " or ".join(
            join_conditions
        )

    title_expr = "NULL"
    author_expr = "NULL"
    if join_clause:
        if title_col:
            title_expr = f"books.ZBKLIBRARYASSET.{title_col}"
        if author_col:
            author_expr = f"books.ZBKLIBRARYASSET.{author_col}"

    def select_or_null(col: Optional[str]) -> str:
        return f"ZAEANNOTATION.{col}" if col else "NULL"

    select_columns = [
        f"ZAEANNOTATION.{asset_id_col} as asset_id",
        f"{title_expr} as title",
        f"{author_expr} as author",
        f"{select_or_null(location_col)} as location",
        f"{select_or_null(selected_text_col)} as selected_text",
        f"{select_or_null(note_col)} as note",
        f"{select_or_null(represent_col)} as represent_text",
        f"{select_or_null(chapter_col)} as chapter",
        f"{select_or_null(style_col)} as style",
        f"{select_or_null(modified_col)} as modified_date",
    ]

    where_clauses = [
        f"ZAEANNOTATION.{asset_id_col} IS NOT NULL",
        f"ZAEANNOTATION.{asset_id_col} != ''",
    ]
    if deleted_col:
        where_clauses.insert(0, f"ZAEANNOTATION.{deleted_col} = 0")

    text_filters = []
    if selected_text_col:
        text_filters.append(
            f"(ZAEANNOTATION.{selected_text_col} IS NOT NULL AND "
            f"ZAEANNOTATION.{selected_text_col} != '')"
        )
    if note_col:
        text_filters.append(
            f"(ZAEANNOTATION.{note_col} IS NOT NULL AND ZAEANNOTATION.{note_col} != '')"
        )
    if text_filters:
        where_clauses.append("(" + " OR ".join(text_filters) + ")")

    order_expr = location_sort_col or location_col or modified_col or asset_id_col
    order_by = f"order by ZAEANNOTATION.{asset_id_col}"
    if order_expr:
        order_by += f", ZAEANNOTATION.{order_expr}"

    query = "\n".join(
        [
            "select",
            ", ".join(select_columns),
            "from ZAEANNOTATION",
            join_clause,
            "where " + " and ".join(where_clauses),
            order_by + ";",
        ]
    )
    return query, NOTE_LIST_FIELDS


@functools.lru_cache(maxsize=1)
def get_ibooks_database() -> sqlite3.Cursor:
    annotation_override = _dir_env_override("APPLE_BOOKS_ANNOTATION_DB_DIR")
    book_override = _dir_env_override("APPLE_BOOKS_BOOK_DB_DIR")

    annotation_dirs = (
        [annotation_override] if annotation_override else DEFAULT_ANNOTATION_DB_DIRS
    )
    book_dirs = [book_override] if book_override else DEFAULT_BOOK_DB_DIRS

    annotation_files = _iter_sqlite_files(annotation_dirs)
    book_files = _iter_sqlite_files(book_dirs)

    annotation_file = _find_db_file(annotation_files, "ZAEANNOTATION")
    book_file = _find_db_file(book_files, "ZBKLIBRARYASSET")

    db1 = sqlite3.connect(str(annotation_file), check_same_thread=False)
    cursor = db1.cursor()
    cursor.execute(ATTACH_BOOKS_QUERY, (str(book_file),))

    return cursor


def fetch_annotations(refresh: bool, sleep_time: int = 20) -> SqliteQueryType:
    if refresh:
        subprocess.run(["open", "-a", BOOKS_APP_NAME], check=False)
        print("Refreshing database...")
        for _ in tqdm(range(sleep_time)):
            sleep(1)
        subprocess.run(["osascript", "-e", f'quit app "{BOOKS_APP_NAME}"'], check=False)

    cur = get_ibooks_database()
    conn = cur.connection
    annotation_columns = _get_table_columns(conn, "ZAEANNOTATION")
    book_columns = _get_table_columns(conn, "ZBKLIBRARYASSET", schema="books")
    note_query, fields = _build_note_query(annotation_columns, book_columns)
    exe = cur.execute(note_query)
    res = exe.fetchall()
    annos = [dict(zip(fields, r)) for r in res]

    return annos

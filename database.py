import sqlite3
from contextlib import contextmanager
from pathlib import Path

DATABASE_PATH = "data/books.db"


@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    # Ensure data directory exists
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                openlibrary_key TEXT UNIQUE,
                title TEXT NOT NULL,
                author_name TEXT,
                first_publish_year INTEGER,
                cover_id INTEGER,
                isbn TEXT,
                status TEXT,
                rating REAL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def add_book(book_data):
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO books (openlibrary_key, title, author_name, first_publish_year, cover_id, isbn, status, rating)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                book_data.get("key"),
                book_data.get("title"),
                book_data.get("author_name"),
                book_data.get("first_publish_year"),
                book_data.get("cover_i"),
                book_data.get("isbn"),
                book_data.get("status"),
                book_data.get("rating"),
            ),
        )
        conn.commit()
        return cursor.lastrowid


def get_all_books(limit=None, offset=0, search_query=None, status_filter=None):
    with get_db() as conn:
        query = "SELECT * FROM books WHERE 1=1"
        params = []

        # Add search filter
        if search_query:
            query += " AND (LOWER(title) LIKE ? OR LOWER(author_name) LIKE ?)"
            search_pattern = f"%{search_query.lower()}%"
            params.extend([search_pattern, search_pattern])

        # Add status filter
        if status_filter:
            query += " AND status = ?"
            params.append(status_filter)

        query += " ORDER BY added_at DESC"

        # Add pagination
        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])

        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]


def get_books_count(search_query=None, status_filter=None):
    with get_db() as conn:
        query = "SELECT COUNT(*) as count FROM books WHERE 1=1"
        params = []

        # Add search filter
        if search_query:
            query += " AND (LOWER(title) LIKE ? OR LOWER(author_name) LIKE ?)"
            search_pattern = f"%{search_query.lower()}%"
            params.extend([search_pattern, search_pattern])

        # Add status filter
        if status_filter:
            query += " AND status = ?"
            params.append(status_filter)

        cursor = conn.execute(query, params)
        return cursor.fetchone()["count"]


def update_book(book_id, book_data):
    with get_db() as conn:
        conn.execute(
            """
            UPDATE books
            SET status = ?, rating = ?
            WHERE id = ?
        """,
            (
                book_data.get("status"),
                book_data.get("rating"),
                book_id,
            ),
        )
        conn.commit()


def delete_book(book_id):
    with get_db() as conn:
        conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
        conn.commit()

import sqlite3
from pathlib import Path

DATABASE_PATH = Path("data/books.db")


def main():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DATABASE_PATH)
    table_exists = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'books'"
    ).fetchone()
    if not table_exists:
        conn.close()
        print("Migration skipped: books table does not exist yet.")
        return

    try:
        conn.execute("ALTER TABLE books ADD COLUMN status_updated_at TIMESTAMP")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e).lower():
            raise

    conn.execute(
        """
        UPDATE books
        SET status_updated_at = added_at
        """
    )
    conn.commit()
    conn.close()

    print("Migration complete: status_updated_at column ensured and backfilled from added_at.")


if __name__ == "__main__":
    main()

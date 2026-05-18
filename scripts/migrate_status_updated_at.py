import sqlite3
from pathlib import Path

DATABASE_PATH = Path("data/books.db")


def main():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DATABASE_PATH)
    try:
        conn.execute(
            "ALTER TABLE books ADD COLUMN status_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        )
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e).lower():
            raise

    conn.execute(
        """
        UPDATE books
        SET status_updated_at = added_at
        WHERE status_updated_at IS NULL
           OR TRIM(CAST(status_updated_at AS TEXT)) = ''
        """
    )
    conn.commit()
    conn.close()

    print("Migration complete: status_updated_at column ensured and backfilled from added_at.")


if __name__ == "__main__":
    main()

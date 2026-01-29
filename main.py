import os
from sqlite3 import IntegrityError

import requests
from flask import Flask, jsonify, render_template, request

from database import (
    add_book,
    delete_book,
    get_all_books,
    get_books_count,
    init_db,
    update_book,
)

app = Flask(__name__)

init_db()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/search")
def search_books():
    query = request.args.get("q", "")
    if not query:
        return jsonify({"docs": []})

    try:
        response = requests.get(
            "https://openlibrary.org/search.json",
            params={
                "q": query,
                "fields": "key,title,author_name,first_publish_year,cover_i,isbn",
                "limit": 10,
            },
            timeout=5,
        )
        response.raise_for_status()
        return jsonify(response.json())
    except requests.RequestException as e:
        return jsonify({"error": str(e), "docs": []}), 500


@app.route("/api/books", methods=["GET"])
def get_books():
    try:
        # Get pagination parameters
        limit = request.args.get("limit", type=int, default=20)
        offset = request.args.get("offset", type=int, default=0)
        search_query = request.args.get("search", "").strip()
        status_filter = request.args.get("status", "").strip()

        # Get books with filters and pagination
        books = get_all_books(
            limit=limit,
            offset=offset,
            search_query=search_query if search_query else None,
            status_filter=status_filter if status_filter else None,
        )

        # Get total count for pagination info
        total_count = get_books_count(
            search_query=search_query if search_query else None,
            status_filter=status_filter if status_filter else None,
        )

        return jsonify(
            {
                "books": books,
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + len(books) < total_count,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/books", methods=["POST"])
def save_book():
    try:
        book_data = request.json

        if not book_data.get("title"):
            return jsonify({"error": "Book title is required"}), 400

        # Handle manual entry vs. OpenLibrary search result
        is_manual = book_data.get("manual", False)

        if is_manual:
            # Manual entry - generate unique key from title
            import hashlib
            import time

            unique_key = f"manual_{hashlib.md5(f'{book_data.get("title")}_{time.time()}'.encode()).hexdigest()}"

            book_id = add_book(
                {
                    "key": unique_key,
                    "title": book_data.get("title"),
                    "author_name": book_data.get("author_name", ""),
                    "first_publish_year": book_data.get("first_publish_year"),
                    "cover_i": None,
                    "isbn": None,
                    "status": book_data.get("status"),
                    "rating": book_data.get("rating"),
                }
            )
        else:
            # OpenLibrary search result
            if not book_data.get("key"):
                return jsonify({"error": "Book key is required"}), 400

            author_name = (
                ", ".join(book_data.get("author_name", []))
                if isinstance(book_data.get("author_name"), list)
                else book_data.get("author_name", "")
            )
            isbn = (
                book_data.get("isbn", [])[0]
                if isinstance(book_data.get("isbn"), list) and book_data.get("isbn")
                else None
            )

            book_id = add_book(
                {
                    "key": book_data.get("key"),
                    "title": book_data.get("title"),
                    "author_name": author_name,
                    "first_publish_year": book_data.get("first_publish_year"),
                    "cover_i": book_data.get("cover_i"),
                    "isbn": isbn,
                    "status": book_data.get("status"),
                    "rating": book_data.get("rating"),
                }
            )

        return jsonify({"success": True, "id": book_id}), 201
    except IntegrityError:
        return jsonify({"error": "Book already exists in your library"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/books/<int:book_id>", methods=["PUT"])
def edit_book(book_id):
    try:
        book_data = request.json
        update_book(book_id, book_data)
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/books/<int:book_id>", methods=["DELETE"])
def remove_book(book_id):
    try:
        delete_book(book_id)
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    debug_mode = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)

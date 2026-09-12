import os
import uuid
from pathlib import Path
from sqlite3 import IntegrityError
from urllib.parse import urlparse

import requests
from flask import Flask, jsonify, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

from database import (
    add_book,
    delete_book,
    get_all_books,
    get_book,
    get_books_count,
    init_db,
    set_cover_image,
    update_book,
)
from enrichment import enrich

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB cover uploads

UPLOAD_DIR = Path("data/uploads")
ALLOWED_COVER_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
MAX_COVER_BYTES = 5 * 1024 * 1024

# Hosts the cover importer is allowed to fetch from (blocks SSRF via arbitrary URLs).
COVER_HOST_ALLOWLIST = ("covers.openlibrary.org", ".mzstatic.com")
CONTENT_TYPE_EXTENSIONS = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
}

init_db()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def delete_upload(cover_path):
    """Remove a previously uploaded cover file referenced by its /uploads/ URL."""
    if not cover_path or not cover_path.startswith("/uploads/"):
        return
    filename = cover_path[len("/uploads/") :]
    if not filename or "/" in filename or "\\" in filename:
        return
    try:
        (UPLOAD_DIR / filename).unlink()
    except FileNotFoundError:
        pass


def store_cover(book_id, data, extension):
    """Write cover bytes to the uploads dir and point the book at them."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"book_{book_id}_{uuid.uuid4().hex}{extension}"
    (UPLOAD_DIR / filename).write_bytes(data)

    cover_url = f"/uploads/{filename}"
    previous_cover = get_book(book_id).get("cover_image")
    set_cover_image(book_id, cover_url)
    delete_upload(previous_cover)
    return cover_url


def is_allowed_cover_host(url):
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    if parsed.scheme != "https" or not parsed.hostname:
        return False
    host = parsed.hostname.lower()
    return any(
        host == allowed or host.endswith(allowed)
        for allowed in COVER_HOST_ALLOWLIST
    )


def download_cover(url):
    """Fetch an image from an allowlisted host, enforcing the size cap."""
    response = requests.get(
        url,
        timeout=15,
        stream=True,
        headers={"User-Agent": "book-tracker/1.0"},
    )
    response.raise_for_status()

    content_type = (response.headers.get("Content-Type") or "").split(";")[0].strip().lower()
    extension = CONTENT_TYPE_EXTENSIONS.get(content_type)
    if extension is None:
        raise ValueError("URL did not return a supported image type")

    chunks = []
    total = 0
    for chunk in response.iter_content(64 * 1024):
        total += len(chunk)
        if total > MAX_COVER_BYTES:
            raise ValueError("Image is too large (max 5 MB)")
        chunks.append(chunk)

    if total == 0:
        raise ValueError("URL returned an empty image")

    return b"".join(chunks), extension


@app.errorhandler(413)
def upload_too_large(error):
    return jsonify({"error": "Cover image is too large (max 5 MB)"}), 413


@app.route("/uploads/<path:filename>")
def uploaded_cover(filename):
    return send_from_directory(UPLOAD_DIR, filename)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/enrich")
def enrich_book():
    """Best-effort description (OpenLibrary then iTunes) and optional cover candidate."""
    title = (request.args.get("title") or "").strip()
    author = (request.args.get("author") or "").strip()
    openlibrary_key = (request.args.get("key") or "").strip()
    want_cover = request.args.get("want_cover") in ("1", "true", "yes")

    if not title and not openlibrary_key:
        return jsonify({"error": "A title or key is required"}), 400

    return jsonify(
        enrich(
            title=title,
            author=author,
            openlibrary_key=openlibrary_key or None,
            want_cover=want_cover,
        )
    )


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
                    "notes": book_data.get("notes"),
                    "description": book_data.get("description"),
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
                    "notes": book_data.get("notes"),
                    "description": book_data.get("description"),
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
        book_data = request.json or {}

        if not (book_data.get("title") or "").strip():
            return jsonify({"error": "Book title is required"}), 400

        if get_book(book_id) is None:
            return jsonify({"error": "Book not found"}), 404

        update_book(book_id, book_data)
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/books/<int:book_id>/cover", methods=["POST"])
def upload_cover(book_id):
    try:
        if get_book(book_id) is None:
            return jsonify({"error": "Book not found"}), 404

        file = request.files.get("cover")
        if file is None or not file.filename:
            return jsonify({"error": "No image file provided"}), 400

        extension = Path(secure_filename(file.filename)).suffix.lower()
        if extension not in ALLOWED_COVER_EXTENSIONS:
            return jsonify(
                {"error": "Unsupported image type. Use PNG, JPG, GIF, or WEBP."}
            ), 400

        cover_url = store_cover(book_id, file.read(), extension)
        return jsonify({"success": True, "cover_image": cover_url}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/books/<int:book_id>/cover/import", methods=["POST"])
def import_cover(book_id):
    """Store a cover fetched from an allowlisted host (e.g. iTunes artwork)."""
    try:
        if get_book(book_id) is None:
            return jsonify({"error": "Book not found"}), 404

        url = (request.json or {}).get("url")
        if not url:
            return jsonify({"error": "No image URL provided"}), 400
        if not is_allowed_cover_host(url):
            return jsonify({"error": "Image host is not allowed"}), 400

        try:
            data, extension = download_cover(url)
        except (requests.RequestException, ValueError) as e:
            return jsonify({"error": str(e)}), 400

        cover_url = store_cover(book_id, data, extension)
        return jsonify({"success": True, "cover_image": cover_url}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/books/<int:book_id>", methods=["DELETE"])
def remove_book(book_id):
    try:
        book = get_book(book_id)
        delete_book(book_id)
        if book:
            delete_upload(book.get("cover_image"))
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    debug_mode = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)

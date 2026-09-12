# Book Tracker

A simple personal reading tracker for keeping a list of books you've read (or want to read) and your personal ratings.

Responsive for mobile. Built with Python, Flask, and SQLite. Deployable with Docker.

## Screenshots

<img width="1538" height="1262" alt="Screenshot 2026-01-29 at 3 21 24 PM" src="https://github.com/user-attachments/assets/8bbd6f6e-a3e8-40a4-a766-8ca31a1ff7cb" />

## Features

- **Book Search**: Search powered by the Open Library API
  - Search by title, author, or ISBN
  - View book covers, authors, and publication years

- **Personal Library**: Save and manage your book collection
  - Add search results to your library and add a star rating (half stars supported!)
  - View all saved books with cover images
  - Edit every book's metadata after adding it: title, author, publication year, description, and reading status/rating/notes
  - Upload a custom cover image (replacing the Open Library cover) or keep the fetched description as a starting point
  - Descriptions are stored locally and prefilled the first time you edit a book that has none: Open Library first, then the Apple Books (iTunes) API when Open Library has nothing substantial
  - Books with no cover get a suggested cover from Apple Books, imported and stored locally when you save

## Metadata sources

| Source | Used for | Notes |
|---|---|---|
| Open Library | search, covers, descriptions | open data, no key |
| iTunes Search API | description + cover fallback | keyless; results matched on title **and** author, HTML stripped |

Enrichment is best-effort: if a source is unreachable or has no match, the field is simply left empty. Suggested covers are only fetched for books that have no cover, and are only stored when you save.

## Tech stack

- Python 3
- Flask
- SQLite
- Vanilla JS
- Docker Compose
- uv for package management

## Local Development

### Using uv

1. Install dependencies:
```bash
uv sync
```

2. Run the application:
```bash
uv run main.py
```

3. Open your browser to `http://localhost:5000`

### Using Docker Compose

```bash
docker compose up -d
```

To rebuild the image if the code changes:
```bash
docker compose up --build
```

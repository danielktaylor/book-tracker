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

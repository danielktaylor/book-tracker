# Book Tracker

A personal reading tracker web application built with Flask and SQLite.

## Features

- **Book Search**: Real-time autocomplete search powered by the Open Library API
  - Search by title, author, or ISBN
  - View book covers, authors, and publication years
  - Debounced search for optimal performance
  
- **Personal Library**: Save and manage your book collection
  - Click any search result to add it to your library
  - View all saved books with cover images in a responsive grid
  - Remove books from your library
  - Persistent storage using SQLite
  - Duplicate detection (prevents adding the same book twice)

## Tech Stack

- Python 3.14
- Flask
- SQLite
- HTML, CSS, Vanilla JavaScript
- Docker Compose
- uv for package management

## Local Development

### Using uv

1. Install dependencies:
```bash
uv pip install -r pyproject.toml
```

2. Run the application:
```bash
python main.py
```

3. Open your browser to `http://localhost:5000`

### Using Docker Compose

1. Build and run:
```bash
docker-compose up --build
```

2. Open your browser to `http://localhost:5000`

3. Stop the application:
```bash
docker-compose down
```

## Project Structure

```
book-tracker/
├── main.py              # Flask application and API endpoints
├── database.py          # SQLite database operations
├── templates/           # HTML templates
│   └── index.html
├── static/             # Static assets
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── app.js
│   └── images/
│       └── no-cover.svg
├── data/               # SQLite database (created on first run)
│   └── books.db
├── pyproject.toml      # Python dependencies
├── Dockerfile          # Docker configuration
└── docker-compose.yml  # Docker Compose configuration
```

## API Endpoints

- `GET /api/search?q=<query>` - Search for books via Open Library API
- `GET /api/books` - Get all saved books
- `POST /api/books` - Add a book to the library
- `DELETE /api/books/<id>` - Remove a book from the library

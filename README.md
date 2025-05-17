# Notes API Example

This project contains a simple notes and tags API built with FastAPI and a minimal frontend.
See `TODO.md` for the project roadmap.

## Backend

The backend resides in `backend/` and uses FastAPI with an SQLite database.

To run the API server:

```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

## Frontend

The `frontend/` directory contains a basic React app (`src/` directory). Build it with Node and serve the static files from any web server. The older `frontend/index.html` remains for reference.

## Functionality

- CRUD operations for notes and tags via REST endpoints
- Notes can be associated with multiple tags
- Data is stored in a SQLite database (`notes.db`)
- Users must register and log in; pass the returned token in the `Authorization` header.

## Testing

Run tests with `pytest` after installing the requirements:

```bash
pip install -r backend/requirements.txt
pytest
```

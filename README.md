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

The `frontend/` directory holds a very small HTML page that interacts with the API using JavaScript `fetch` calls. Open `frontend/index.html` in your browser after starting the backend server.

## Functionality

- CRUD operations for notes and tags via REST endpoints
- Notes can be associated with multiple tags
- Data is stored in a SQLite database (`notes.db`)

## Testing

Run tests with `pytest` after installing the requirements:

```bash
pip install -r backend/requirements.txt
pytest
```

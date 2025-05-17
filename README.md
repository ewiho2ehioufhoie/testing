# Notes API Example

This project aims to provide a lightweight note taking service with quick capture
and linking of ideas. A small roadmap is maintained in `TODO.md`.

## Goals and Key Features

- **Quick capture** of ideas with minimal friction
- **Linking** notes together using tags
- Future **visualization** of note relationships
- Eventual **synchronization** across devices

## Tech Stack

The project uses **FastAPI** for the backend with a simple SQLite database. A
minimal HTML/JavaScript frontend is provided in `frontend/`. The structure keeps
frontend and backend code in separate directories.

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

## Contributing

1. Fork the repository and create your branch from `work`.
2. Ensure any tests pass with `pytest`.
3. Submit a pull request describing your changes.

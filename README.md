# Notes App

This project provides a simple FastAPI server with CRUD endpoints for notes and tags and a small frontend to interact with the API.

## Requirements

- Python 3
- The packages listed in `requirements.txt`

Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the server

Start the API using uvicorn:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

## Frontend

Open `frontend/index.html` in a browser. It will communicate with the API at the same origin. Ensure the server is running and accessible from your browser.


from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict
import sqlite3
import os
import hashlib
import uuid

DB_FILE = os.environ.get('NOTES_DB_FILE', 'notes.db')


def init_db(db_file: str):
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        user_id INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS note_tags (
        note_id INTEGER NOT NULL,
        tag_id INTEGER NOT NULL,
        PRIMARY KEY(note_id, tag_id),
        FOREIGN KEY(note_id) REFERENCES notes(id) ON DELETE CASCADE,
        FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_note_id INTEGER NOT NULL,
        to_note_id INTEGER NOT NULL,
        FOREIGN KEY(from_note_id) REFERENCES notes(id) ON DELETE CASCADE,
        FOREIGN KEY(to_note_id) REFERENCES notes(id) ON DELETE CASCADE
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS attachments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        note_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        data BLOB,
        FOREIGN KEY(note_id) REFERENCES notes(id) ON DELETE CASCADE
    )''')
    conn.commit()
    conn.close()

app = FastAPI()

# Initialize database
init_db(DB_FILE)

TOKENS: Dict[str, int] = {}

class TagCreate(BaseModel):
    name: str

class Tag(TagCreate):
    id: int

class NoteCreate(BaseModel):
    title: str
    content: str
    tag_ids: Optional[List[int]] = None

class Note(BaseModel):
    id: int
    title: str
    content: str
    tags: List[Tag] = []

class UserCreate(BaseModel):
    username: str
    password: str

class User(BaseModel):
    id: int
    username: str


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def create_token(user_id: int) -> str:
    token = uuid.uuid4().hex
    TOKENS[token] = user_id
    return token


def get_current_user(x_token: str = Header(...)) -> int:
    user_id = TOKENS.get(x_token)
    if not user_id:
        raise HTTPException(status_code=401, detail='Invalid token')
    return user_id


@app.post('/users/register')
def register(user: UserCreate):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    try:
        cur.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                    (user.username, hash_password(user.password)))
        user_id = cur.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail='Username already exists')
    conn.close()
    token = create_token(user_id)
    return {'token': token, 'user': User(id=user_id, username=user.username)}


@app.post('/users/login')
def login(user: UserCreate):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('SELECT id, password_hash FROM users WHERE username=?', (user.username,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=400, detail='Invalid credentials')
    user_id, password_hash_db = row
    if hash_password(user.password) != password_hash_db:
        conn.close()
        raise HTTPException(status_code=400, detail='Invalid credentials')
    conn.close()
    token = create_token(user_id)
    return {'token': token}

@app.post('/tags/', response_model=Tag)
def create_tag(tag: TagCreate):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    try:
        cur.execute('INSERT INTO tags (name) VALUES (?)', (tag.name,))
        tag_id = cur.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail='Tag already exists')
    conn.close()
    return Tag(id=tag_id, name=tag.name)

@app.get('/tags/', response_model=List[Tag])
def get_tags():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('SELECT id, name FROM tags')
    rows = cur.fetchall()
    conn.close()
    return [Tag(id=row[0], name=row[1]) for row in rows]

@app.put('/tags/{tag_id}', response_model=Tag)
def update_tag(tag_id: int, tag: TagCreate):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('UPDATE tags SET name=? WHERE id=?', (tag.name, tag_id))
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail='Tag not found')
    conn.commit()
    conn.close()
    return Tag(id=tag_id, name=tag.name)

@app.delete('/tags/{tag_id}')
def delete_tag(tag_id: int):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('DELETE FROM tags WHERE id=?', (tag_id,))
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail='Tag not found')
    conn.commit()
    conn.close()
    return {'detail': 'Tag deleted'}

@app.post('/notes/', response_model=Note)
def create_note(note: NoteCreate, user_id: int = Depends(get_current_user)):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('INSERT INTO notes (title, content, user_id) VALUES (?, ?, ?)',
                (note.title, note.content, user_id))
    note_id = cur.lastrowid
    if note.tag_ids:
        cur.executemany('INSERT INTO note_tags (note_id, tag_id) VALUES (?, ?)',
                        [(note_id, tag_id) for tag_id in note.tag_ids])
    conn.commit()
    note_obj = fetch_note(conn, note_id, user_id)
    conn.close()
    return note_obj

@app.get('/notes/', response_model=List[Note])
def list_notes(user_id: int = Depends(get_current_user)):
    conn = sqlite3.connect(DB_FILE)
    notes = fetch_notes(conn, user_id)
    conn.close()
    return notes

@app.get('/notes/{note_id}', response_model=Note)
def get_note(note_id: int, user_id: int = Depends(get_current_user)):
    conn = sqlite3.connect(DB_FILE)
    note = fetch_note(conn, note_id, user_id)
    conn.close()
    if note is None:
        raise HTTPException(status_code=404, detail='Note not found')
    return note

@app.put('/notes/{note_id}', response_model=Note)
def update_note(note_id: int, note: NoteCreate, user_id: int = Depends(get_current_user)):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('UPDATE notes SET title=?, content=? WHERE id=? AND user_id=?',
                (note.title, note.content, note_id, user_id))
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail='Note not found')
    cur.execute('DELETE FROM note_tags WHERE note_id=?', (note_id,))
    if note.tag_ids:
        cur.executemany('INSERT INTO note_tags (note_id, tag_id) VALUES (?, ?)',
                        [(note_id, tid) for tid in note.tag_ids])
    conn.commit()
    note_obj = fetch_note(conn, note_id, user_id)
    conn.close()
    return note_obj

@app.delete('/notes/{note_id}')
def delete_note(note_id: int, user_id: int = Depends(get_current_user)):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('DELETE FROM notes WHERE id=? AND user_id=?', (note_id, user_id))
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail='Note not found')
    cur.execute('DELETE FROM note_tags WHERE note_id=?', (note_id,))
    conn.commit()
    conn.close()
    return {'detail': 'Note deleted'}

# Helper functions
def fetch_notes(conn, user_id: int):
    cur = conn.cursor()
    cur.execute('SELECT id, title, content FROM notes WHERE user_id=?', (user_id,))
    notes_rows = cur.fetchall()
    notes = []
    for nid, title, content in notes_rows:
        notes.append(fetch_note(conn, nid, user_id))
    return notes


def fetch_note(conn, note_id: int, user_id: int):
    cur = conn.cursor()
    cur.execute('SELECT id, title, content FROM notes WHERE id=? AND user_id=?', (note_id, user_id))
    row = cur.fetchone()
    if not row:
        return None
    note_id, title, content = row
    cur.execute('''SELECT t.id, t.name FROM tags t
                   JOIN note_tags nt ON t.id = nt.tag_id
                   WHERE nt.note_id=?''', (note_id,))
    tags_rows = cur.fetchall()
    tags = [Tag(id=tid, name=name) for tid, name in tags_rows]
    return Note(id=note_id, title=title, content=content, tags=tags)

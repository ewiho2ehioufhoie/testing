from fastapi import FastAPI, HTTPException, UploadFile, File, Header, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import os
import hashlib
import secrets
import re

DB_FILE = os.environ.get('NOTES_DB_FILE', 'notes.db')
ATTACH_DIR = os.environ.get('ATTACH_DIR', 'attachments')
TOKEN_LENGTH = 32


def init_db(db_file: str):
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS note_tags (
        note_id INTEGER NOT NULL,
        tag_id INTEGER NOT NULL,
        PRIMARY KEY(note_id, tag_id),
        FOREIGN KEY(note_id) REFERENCES notes(id) ON DELETE CASCADE,
        FOREIGN KEY(tag_id) REFERENCES tags(id) ON DELETE CASCADE
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        token TEXT
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS attachments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT UNIQUE NOT NULL,
        note_id INTEGER,
        FOREIGN KEY(note_id) REFERENCES notes(id) ON DELETE CASCADE
    )''')
    conn.commit()
    conn.close()
    os.makedirs(ATTACH_DIR, exist_ok=True)

app = FastAPI()

# Initialize database
init_db(DB_FILE)

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
    links: List[int] = []

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class User(BaseModel):
    id: int
    username: str


@app.post('/users/register', response_model=User)
def register(user: UserCreate):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    password_hash = hash_password(user.password)
    try:
        cur.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                    (user.username, password_hash))
        uid = cur.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail='Username taken')
    conn.close()
    return User(id=uid, username=user.username)


@app.post('/users/login')
def login(creds: UserLogin):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('SELECT id, password_hash FROM users WHERE username=?',
                (creds.username,))
    row = cur.fetchone()
    if not row or not verify_password(creds.password, row[1]):
        conn.close()
        raise HTTPException(status_code=401, detail='Invalid credentials')
    token = create_token()
    cur.execute('UPDATE users SET token=? WHERE id=?', (token, row[0]))
    conn.commit()
    conn.close()
    return {'token': token}


@app.get('/users/me', response_model=User)
def read_me(user: User = Depends(get_current_user)):
    return user

@app.post('/tags/', response_model=Tag)
def create_tag(tag: TagCreate, user: User = Depends(get_current_user)):
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
def get_tags(user: User = Depends(get_current_user)):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('SELECT id, name FROM tags')
    rows = cur.fetchall()
    conn.close()
    return [Tag(id=row[0], name=row[1]) for row in rows]

@app.put('/tags/{tag_id}', response_model=Tag)
def update_tag(tag_id: int, tag: TagCreate, user: User = Depends(get_current_user)):
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
def delete_tag(tag_id: int, user: User = Depends(get_current_user)):
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
def create_note(note: NoteCreate, user: User = Depends(get_current_user)):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('INSERT INTO notes (title, content) VALUES (?, ?)', (note.title, note.content))
    note_id = cur.lastrowid
    if note.tag_ids:
        cur.executemany('INSERT INTO note_tags (note_id, tag_id) VALUES (?, ?)',
                        [(note_id, tag_id) for tag_id in note.tag_ids])
    conn.commit()
    note_obj = fetch_note(conn, note_id)
    conn.close()
    return note_obj

@app.get('/notes/', response_model=List[Note])
def list_notes(user: User = Depends(get_current_user)):
    conn = sqlite3.connect(DB_FILE)
    notes = fetch_notes(conn)
    conn.close()
    return notes

@app.get('/notes/{note_id}', response_model=Note)
def get_note(note_id: int, user: User = Depends(get_current_user)):
    conn = sqlite3.connect(DB_FILE)
    note = fetch_note(conn, note_id)
    conn.close()
    if note is None:
        raise HTTPException(status_code=404, detail='Note not found')
    return note

@app.put('/notes/{note_id}', response_model=Note)
def update_note(note_id: int, note: NoteCreate, user: User = Depends(get_current_user)):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('UPDATE notes SET title=?, content=? WHERE id=?', (note.title, note.content, note_id))
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail='Note not found')
    cur.execute('DELETE FROM note_tags WHERE note_id=?', (note_id,))
    if note.tag_ids:
        cur.executemany('INSERT INTO note_tags (note_id, tag_id) VALUES (?, ?)',
                        [(note_id, tid) for tid in note.tag_ids])
    conn.commit()
    note_obj = fetch_note(conn, note_id)
    conn.close()
    return note_obj

@app.delete('/notes/{note_id}')
def delete_note(note_id: int, user: User = Depends(get_current_user)):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('DELETE FROM notes WHERE id=?', (note_id,))
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail='Note not found')
    cur.execute('DELETE FROM note_tags WHERE note_id=?', (note_id,))
    conn.commit()
    conn.close()
    return {'detail': 'Note deleted'}


@app.get('/search/', response_model=List[Note])
def search_notes(q: str, tag: Optional[str] = None, user: User = Depends(get_current_user)):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    if tag:
        cur.execute('''SELECT n.id FROM notes n
                       JOIN note_tags nt ON n.id = nt.note_id
                       JOIN tags t ON nt.tag_id = t.id
                       WHERE (n.title LIKE ? OR n.content LIKE ?) AND t.name=?''',
                    (f'%{q}%', f'%{q}%', tag))
    else:
        cur.execute('SELECT id FROM notes WHERE title LIKE ? OR content LIKE ?', (f'%{q}%', f'%{q}%'))
    ids = [row[0] for row in cur.fetchall()]
    notes = [fetch_note(conn, nid) for nid in ids]
    conn.close()
    return notes


@app.post('/attachments/upload')
def upload_attachment(file: UploadFile = File(...), note_id: Optional[int] = None, user: User = Depends(get_current_user)):
    filename = secrets.token_hex(8) + '_' + file.filename
    path = os.path.join(ATTACH_DIR, filename)
    with open(path, 'wb') as out:
        out.write(file.file.read())
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('INSERT INTO attachments (filename, note_id) VALUES (?, ?)', (filename, note_id))
    conn.commit()
    conn.close()
    return {'filename': filename}


@app.get('/attachments/{filename}')
def get_attachment(filename: str, user: User = Depends(get_current_user)):
    path = os.path.join(ATTACH_DIR, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail='File not found')
    return FileResponse(path)

# Helper functions
def fetch_notes(conn):
    cur = conn.cursor()
    cur.execute('SELECT id, title, content FROM notes')
    notes_rows = cur.fetchall()
    notes = []
    for nid, title, content in notes_rows:
        notes.append(fetch_note(conn, nid))
    return notes


LINK_RE = re.compile(r"\[\[(\d+)\]\]")


def fetch_note(conn, note_id: int):
    cur = conn.cursor()
    cur.execute('SELECT id, title, content FROM notes WHERE id=?', (note_id,))
    row = cur.fetchone()
    if not row:
        return None
    note_id, title, content = row
    cur.execute('''SELECT t.id, t.name FROM tags t
                   JOIN note_tags nt ON t.id = nt.tag_id
                   WHERE nt.note_id=?''', (note_id,))
    tags_rows = cur.fetchall()
    tags = [Tag(id=tid, name=name) for tid, name in tags_rows]
    links = [int(m.group(1)) for m in LINK_RE.finditer(content)]
    return Note(id=note_id, title=title, content=content, tags=tags, links=links)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return salt.hex() + ':' + hashed.hex()


def verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, hash_hex = stored.split(':')
    except ValueError:
        return False
    salt = bytes.fromhex(salt_hex)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return hashed.hex() == hash_hex


def create_token() -> str:
    return secrets.token_hex(TOKEN_LENGTH)


def get_current_user(authorization: str | None = Header(None)):
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Auth required')
    token = authorization[7:]
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute('SELECT id, username FROM users WHERE token=?', (token,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=401, detail='Invalid token')
    return User(id=row[0], username=row[1])

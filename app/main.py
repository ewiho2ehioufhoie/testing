from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import sqlite3

DB_PATH = 'notes.db'

app = FastAPI(title="Notes API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS note_tags (
            note_id INTEGER,
            tag_id INTEGER,
            PRIMARY KEY (note_id, tag_id),
            FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

init_db()

class TagBase(BaseModel):
    name: str

class Tag(TagBase):
    id: int
    class Config:
        orm_mode = True

class NoteBase(BaseModel):
    title: str
    content: str | None = None
    tag_ids: List[int] = []

class NoteCreate(NoteBase):
    pass

class NoteUpdate(NoteBase):
    pass

class Note(NoteBase):
    id: int
    tags: List[Tag] = []
    class Config:
        orm_mode = True

def fetch_note(conn, note_id: int):
    note_row = conn.execute("SELECT id, title, content FROM notes WHERE id=?", (note_id,)).fetchone()
    if not note_row:
        return None
    tag_rows = conn.execute(
        "SELECT t.id, t.name FROM tags t JOIN note_tags nt ON t.id=nt.tag_id WHERE nt.note_id=?",
        (note_id,)
    ).fetchall()
    tags = [Tag(id=row['id'], name=row['name']) for row in tag_rows]
    return Note(id=note_row['id'], title=note_row['title'], content=note_row['content'], tag_ids=[t.id for t in tags], tags=tags)

@app.get('/notes', response_model=List[Note])
def list_notes():
    conn = get_db()
    note_rows = conn.execute("SELECT id FROM notes").fetchall()
    notes = [fetch_note(conn, row['id']) for row in note_rows]
    conn.close()
    return notes

@app.post('/notes', response_model=Note)
def create_note(note: NoteCreate):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO notes (title, content) VALUES (?, ?)", (note.title, note.content))
    note_id = cur.lastrowid
    for tag_id in note.tag_ids:
        cur.execute("INSERT OR IGNORE INTO note_tags (note_id, tag_id) VALUES (?, ?)", (note_id, tag_id))
    conn.commit()
    result = fetch_note(conn, note_id)
    conn.close()
    return result

@app.get('/notes/{note_id}', response_model=Note)
def read_note(note_id: int):
    conn = get_db()
    note = fetch_note(conn, note_id)
    conn.close()
    if not note:
        raise HTTPException(status_code=404, detail='Note not found')
    return note

@app.put('/notes/{note_id}', response_model=Note)
def update_note(note_id: int, note: NoteUpdate):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE notes SET title=?, content=? WHERE id=?", (note.title, note.content, note_id))
    cur.execute("DELETE FROM note_tags WHERE note_id=?", (note_id,))
    for tag_id in note.tag_ids:
        cur.execute("INSERT OR IGNORE INTO note_tags (note_id, tag_id) VALUES (?, ?)", (note_id, tag_id))
    conn.commit()
    result = fetch_note(conn, note_id)
    conn.close()
    if not result:
        raise HTTPException(status_code=404, detail='Note not found')
    return result

@app.delete('/notes/{note_id}')
def delete_note(note_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM notes WHERE id=?", (note_id,))
    conn.commit()
    deleted = cur.rowcount
    conn.close()
    if not deleted:
        raise HTTPException(status_code=404, detail='Note not found')
    return {'status': 'deleted'}

@app.get('/tags', response_model=List[Tag])
def list_tags():
    conn = get_db()
    rows = conn.execute("SELECT id, name FROM tags").fetchall()
    conn.close()
    return [Tag(id=row['id'], name=row['name']) for row in rows]

@app.post('/tags', response_model=Tag)
def create_tag(tag: TagBase):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO tags (name) VALUES (?)", (tag.name,))
    tag_id = cur.lastrowid
    conn.commit()
    row = conn.execute("SELECT id, name FROM tags WHERE id=?", (tag_id,)).fetchone()
    conn.close()
    return Tag(id=row['id'], name=row['name'])

@app.get('/tags/{tag_id}', response_model=Tag)
def read_tag(tag_id: int):
    conn = get_db()
    row = conn.execute("SELECT id, name FROM tags WHERE id=?", (tag_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail='Tag not found')
    return Tag(id=row['id'], name=row['name'])

@app.put('/tags/{tag_id}', response_model=Tag)
def update_tag(tag_id: int, tag: TagBase):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE tags SET name=? WHERE id=?", (tag.name, tag_id))
    conn.commit()
    if cur.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail='Tag not found')
    row = conn.execute("SELECT id, name FROM tags WHERE id=?", (tag_id,)).fetchone()
    conn.close()
    return Tag(id=row['id'], name=row['name'])

@app.delete('/tags/{tag_id}')
def delete_tag(tag_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM tags WHERE id=?", (tag_id,))
    conn.commit()
    deleted = cur.rowcount
    conn.close()
    if not deleted:
        raise HTTPException(status_code=404, detail='Tag not found')
    return {'status': 'deleted'}


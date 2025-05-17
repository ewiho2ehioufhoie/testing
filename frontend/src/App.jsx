import React, { useState, useEffect } from 'react';
import Login from './Login';
import NoteEditor from './NoteEditor';
import NotesList from './NotesList';
import NoteDetails from './NoteDetails';
import TagFilter from './TagFilter';
import GraphView from './GraphView';
import { fetchNotes, fetchTags, addNote, search, uploadAttachment } from './api';

export default function App() {
  const [token, setToken] = useState(null);
  const [notes, setNotes] = useState([]);
  const [tags, setTags] = useState([]);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    if (token) {
      load();
    }
  }, [token]);

  async function load() {
    const data = await fetchNotes(token);
    setNotes(data);
    const tg = await fetchTags(token);
    setTags(tg);
  }

  async function onAdd(note) {
    const newNote = await addNote(token, note);
    setNotes([...notes, newNote]);
  }

  async function onSearch(q) {
    const results = await search(token, q);
    setNotes(results);
  }

  function onFilter(tagName) {
    if (!tagName) {
      load();
      return;
    }
    const filtered = notes.filter(n => n.tags.some(t => t.name === tagName));
    setNotes(filtered);
  }

  async function onUpload(file) {
    await uploadAttachment(token, file);
  }

  function selectNote(n) {
    setSelected(n);
  }

  if (!token) {
    return <Login onToken={setToken} />;
  }

  return (
    <div>
      <button onClick={() => setToken(null)}>Logout</button>
      <NoteEditor onAdd={onAdd} onSearch={onSearch} onUpload={onUpload} />
      <TagFilter tags={tags} onFilter={onFilter} />
      <NotesList notes={notes} onSelect={selectNote} />
      <NoteDetails note={selected} />
      <GraphView notes={notes} />
    </div>
  );
}

import React, { useState } from 'react';

export default function NoteEditor({ onAdd, onSearch, onUpload }) {
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [query, setQuery] = useState('');

  function submit(e) {
    e.preventDefault();
    onAdd({ title, content });
    setTitle('');
    setContent('');
  }

  function handleSearch(e) {
    e.preventDefault();
    onSearch(query);
  }

  return (
    <div>
      <h2>New Note</h2>
      <form onSubmit={submit}>
        <input value={title} onChange={e => setTitle(e.target.value)} placeholder="Title" />
        <textarea value={content} onChange={e => setContent(e.target.value)} placeholder="Content" />
        <button type="submit">Add</button>
      </form>
      <input type="file" onChange={e => onUpload(e.target.files[0])} />
      <h2>Search</h2>
      <form onSubmit={handleSearch}>
        <input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search" />
        <button type="submit">Go</button>
      </form>
    </div>
  );
}

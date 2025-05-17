import React from 'react';

export default function NotesList({ notes, onSelect }) {
  return (
    <div>
      <h2>Notes</h2>
      {notes.map(n => (
        <div key={n.id} onClick={() => onSelect && onSelect(n)} style={{borderBottom:'1px solid #ccc', marginBottom:'1rem', cursor:'pointer'}}>
          <h3>{n.title}</h3>
          <p>{n.content}</p>
          {n.links.length > 0 && (
            <p>Links to: {n.links.join(', ')}</p>
          )}
          {n.tags.map(t => (
            <span key={t.id} style={{marginRight:'0.5rem'}}>{t.name}</span>
          ))}
        </div>
      ))}
    </div>
  );
}

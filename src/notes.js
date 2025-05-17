let notes = [];

function addNote(text) {
  if (typeof text !== 'string' || !text.trim()) {
    throw new Error('Note text must be a non-empty string');
  }
  const note = { id: notes.length + 1, text };
  notes.push(note);
  return note;
}

function getAllNotes() {
  return notes.slice();
}

function clearNotes() {
  notes = [];
}

module.exports = { addNote, getAllNotes, clearNotes };

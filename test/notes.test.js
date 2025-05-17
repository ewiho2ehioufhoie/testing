const { addNote, getAllNotes, clearNotes } = require('../src/notes');

describe('note management', () => {
  beforeEach(() => {
    clearNotes();
  });

  test('adds a note', () => {
    const note = addNote('First note');
    expect(note.id).toBe(1);
    expect(note.text).toBe('First note');
  });

  test('retrieves all notes', () => {
    addNote('Note 1');
    addNote('Note 2');
    const notes = getAllNotes();
    expect(notes).toHaveLength(2);
  });
});

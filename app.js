function getNotes() {
    return JSON.parse(localStorage.getItem('notes') || '[]');
}

function saveNotes(notes) {
    localStorage.setItem('notes', JSON.stringify(notes));
}

function renderNotes() {
    const notes = getNotes();
    const list = document.getElementById('notesList');
    const search = document.getElementById('searchInput').value.toLowerCase();
    list.innerHTML = '';
    notes
        .filter(n => {
            const haystack = (n.title + ' ' + n.body + ' ' + n.tags.join(' ')).toLowerCase();
            return haystack.includes(search);
        })
        .forEach(note => {
            const div = document.createElement('div');
            div.className = 'note';

            const h3 = document.createElement('h3');
            h3.textContent = note.title;
            div.appendChild(h3);

            const bodyP = document.createElement('p');
            bodyP.textContent = note.body;
            div.appendChild(bodyP);

            const tagP = document.createElement('p');
            const em = document.createElement('em');
            em.textContent = note.tags.join(', ');
            tagP.appendChild(em);
            div.appendChild(tagP);

            const actions = document.createElement('div');
            actions.className = 'note-actions';

            const editBtn = document.createElement('button');
            editBtn.textContent = 'Edit';
            editBtn.addEventListener('click', () => editNote(note.id));
            actions.appendChild(editBtn);

            const deleteBtn = document.createElement('button');
            deleteBtn.textContent = 'Delete';
            deleteBtn.addEventListener('click', () => deleteNote(note.id));
            actions.appendChild(deleteBtn);

            div.appendChild(actions);

            list.appendChild(div);
        });
}

function editNote(id) {
    const notes = getNotes();
    const note = notes.find(n => n.id === id);
    if (!note) return;
    const newTitle = prompt('Edit title', note.title);
    if (newTitle === null) return; // cancelled
    const newBody = prompt('Edit body', note.body);
    if (newBody === null) return;
    note.title = newTitle.trim();
    note.body = newBody.trim();
    saveNotes(notes);
    renderNotes();
}

function deleteNote(id) {
    const notes = getNotes().filter(n => n.id !== id);
    saveNotes(notes);
    renderNotes();
}

document.getElementById('addNoteBtn').addEventListener('click', () => {
    const titleInput = document.getElementById('titleInput');
    const bodyInput = document.getElementById('bodyInput');
    const tagInput = document.getElementById('tagInput');

    const title = titleInput.value.trim();
    const body = bodyInput.value.trim();
    const tags = tagInput.value.split(',').map(t => t.trim()).filter(Boolean);

    if (title || body) {
        const notes = getNotes();
        notes.push({ id: Date.now(), title, body, tags });
        saveNotes(notes);
        titleInput.value = '';
        bodyInput.value = '';
        tagInput.value = '';
        renderNotes();
    }
});

window.addEventListener('DOMContentLoaded', renderNotes);
document.getElementById('searchInput').addEventListener('input', renderNotes);

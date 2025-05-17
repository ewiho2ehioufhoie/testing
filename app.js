const notes = [
  { title: 'First Note', body: 'This is the first note', tags: ['personal', 'todo'] },
  { title: 'Second Note', body: 'Another note example', tags: ['work'] },
  { title: 'Shopping List', body: 'Milk, Bread, Eggs', tags: ['personal', 'shopping'] }
];

function renderNotes(query = '') {
  const container = document.getElementById('notes');
  const q = query.toLowerCase();
  container.innerHTML = '';

  const filtered = notes.filter(n =>
    n.title.toLowerCase().includes(q) ||
    n.body.toLowerCase().includes(q) ||
    n.tags.some(t => t.toLowerCase().includes(q))
  );

  filtered.forEach(n => {
    const div = document.createElement('div');
    div.className = 'note';
    div.innerHTML = `<h2>${n.title}</h2><p>${n.body}</p><p><em>${n.tags.join(', ')}</em></p>`;
    container.appendChild(div);
  });
}

document.getElementById('search').addEventListener('input', (e) => {
  renderNotes(e.target.value);
});

document.addEventListener('DOMContentLoaded', () => renderNotes());


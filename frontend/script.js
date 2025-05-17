async function fetchTagsByNames(names) {
  const tagIds = [];
  for (const name of names) {
    const res = await fetch(`/tags`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name })
    });
    if (res.ok) {
      const tag = await res.json();
      tagIds.push(tag.id);
    }
  }
  return tagIds;
}

async function loadNotes() {
  const res = await fetch('/notes');
  const notes = await res.json();
  const container = document.getElementById('notes');
  container.innerHTML = '';
  notes.forEach(note => {
    const div = document.createElement('div');
    const tags = note.tags.map(t => t.name).join(', ');
    div.innerHTML = `<h3>${note.title}</h3><p>${note.content || ''}</p><small>${tags}</small>`;
    container.appendChild(div);
  });
}

document.getElementById('note-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const title = document.getElementById('title').value;
  const content = document.getElementById('content').value;
  const tagNames = document.getElementById('tags').value.split(',').map(s => s.trim()).filter(Boolean);
  const tagIds = await fetchTagsByNames(tagNames);
  await fetch('/notes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, content, tag_ids: tagIds })
  });
  document.getElementById('title').value = '';
  document.getElementById('content').value = '';
  document.getElementById('tags').value = '';
  loadNotes();
});

loadNotes();

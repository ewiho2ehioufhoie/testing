const API = 'http://localhost:8000';

export async function login(username, password) {
  const res = await fetch(`${API}/users/login`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username, password})
  });
  if (!res.ok) throw new Error('login failed');
  return (await res.json()).token;
}

export async function register(username, password) {
  const res = await fetch(`${API}/users/register`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username, password})
  });
  if (!res.ok) throw new Error('register failed');
  return await res.json();
}

export async function fetchNotes(token) {
  const res = await fetch(`${API}/notes/`, {
    headers: {Authorization: `Bearer ${token}`}
  });
  return await res.json();
}

export async function fetchTags(token) {
  const res = await fetch(`${API}/tags/`, {
    headers: {Authorization: `Bearer ${token}`}
  });
  return await res.json();
}

export async function addNote(token, note) {
  const res = await fetch(`${API}/notes/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(note)
  });
  return await res.json();
}

export async function search(token, q) {
  const url = new URL(`${API}/search/`);
  url.searchParams.set('q', q);
  const res = await fetch(url, {
    headers: {Authorization: `Bearer ${token}`}
  });
  return await res.json();
}

export async function uploadAttachment(token, file) {
  const form = new FormData();
  form.append('file', file);
  const res = await fetch(`${API}/attachments/upload`, {
    method: 'POST',
    headers: {Authorization: `Bearer ${token}`},
    body: form
  });
  return await res.json();
}

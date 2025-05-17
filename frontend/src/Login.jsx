import React, { useState } from 'react';
import { login, register } from './api';

export default function Login({ onToken }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [mode, setMode] = useState('login');

  async function submit(e) {
    e.preventDefault();
    if (mode === 'register') {
      await register(username, password);
    }
    const token = await login(username, password);
    onToken(token);
  }

  return (
    <form onSubmit={submit}>
      <h2>{mode === 'login' ? 'Login' : 'Register'}</h2>
      <input value={username} onChange={e => setUsername(e.target.value)} placeholder="Username" />
      <input value={password} onChange={e => setPassword(e.target.value)} type="password" placeholder="Password" />
      <button type="submit">Submit</button>
      <p>
        {mode === 'login' ? (
          <span>Need an account? <a href="#" onClick={() => setMode('register')}>Register</a></span>
        ) : (
          <span>Already have an account? <a href="#" onClick={() => setMode('login')}>Login</a></span>
        )}
      </p>
    </form>
  );
}

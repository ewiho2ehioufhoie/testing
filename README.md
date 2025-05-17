# Digital Second Brain Demo

This project is a very small prototype of a "digital rhizome" note taking app. It runs entirely in the browser and stores notes in local storage.

## Usage

1. Serve the files with a simple static server. For example:
   ```bash
   npx serve .
   ```
   Then open the printed URL in your browser.
2. Create notes by filling in a title, body, and optional tags.
3. Use the search box to filter notes by any text or tag.
4. Edit or delete notes with the buttons displayed on each note.

Notes are saved locally, so refreshing the page will keep them. There is no backend or account system yet.

## Features
- Add, edit, and delete notes
- Tag notes and filter via the search box
- Notes persist in `localStorage`

This prototype is just a starting point for a more feature rich "second brain" application.

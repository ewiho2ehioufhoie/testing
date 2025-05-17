import os
import importlib
import sqlite3
import pytest
from fastapi.testclient import TestClient

# use temporary database for tests
@pytest.fixture(scope="module")
def client(tmp_path_factory):
    db_path = tmp_path_factory.mktemp('data') / 'test.db'
    os.environ['NOTES_DB_FILE'] = str(db_path)
    # reload the app to ensure DB_FILE is read
    main = importlib.import_module('backend.main')
    importlib.reload(main)
    main.init_db(main.DB_FILE)
    with TestClient(main.app) as c:
        yield c
    # cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


def test_create_tag_and_note(client):
    # create tag
    res = client.post('/tags/', json={'name': 'work'})
    assert res.status_code == 200
    tag = res.json()

    # create note with that tag
    res = client.post('/notes/', json={'title': 'Title', 'content': 'Body', 'tag_ids': [tag['id']]})
    assert res.status_code == 200
    note = res.json()
    assert note['title'] == 'Title'
    assert len(note['tags']) == 1

    # list notes
    res = client.get('/notes/')
    assert res.status_code == 200
    notes = res.json()
    assert len(notes) == 1

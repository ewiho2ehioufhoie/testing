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


def test_auth_and_crud(client):
    # register user
    res = client.post('/users/register', json={'username': 'alice', 'password': 'pw'})
    assert res.status_code == 200

    # login
    res = client.post('/users/login', json={'username': 'alice', 'password': 'pw'})
    assert res.status_code == 200
    token = res.json()['token']
    headers = {'Authorization': f'Bearer {token}'}

    # create tag
    res = client.post('/tags/', headers=headers, json={'name': 'work'})
    assert res.status_code == 200
    tag = res.json()

    # create note with link and tag
    res = client.post('/notes/', headers=headers,
                     json={'title': 'Title', 'content': 'Body [[1]]', 'tag_ids': [tag['id']]})
    assert res.status_code == 200
    note = res.json()
    assert note['title'] == 'Title'
    assert len(note['tags']) == 1
    assert note['links'] == [1]

    # search
    res = client.get('/search/', headers=headers, params={'q': 'Body'})
    assert res.status_code == 200
    assert len(res.json()) == 1

    # upload attachment
    file_content = b'hello world'
    res = client.post('/attachments/upload', headers=headers,
                      files={'file': ('hello.txt', file_content)})
    assert res.status_code == 200
    fname = res.json()['filename']
    res = client.get(f'/attachments/{fname}', headers=headers)
    assert res.status_code == 200
    assert res.content == file_content

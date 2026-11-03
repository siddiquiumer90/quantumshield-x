"""Test setup: isolated SQLite DB + TestClient. Sets DATABASE_URL before
importing the app so tests never touch the dev database."""
import os
import sys
import tempfile

TMP = tempfile.mkdtemp(prefix="qs_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{TMP}/test.db"
os.environ["QS_UPLOAD_DIR"] = os.path.join(TMP, "files")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="module")
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


def _register(client, username):
    r = client.post("/api/auth/register", json={"username": username, "password": "testpass123"})
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def user_token(client):
    return _register(client, "alice")


@pytest.fixture(scope="module")
def admin_token(client):
    r = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def bob_token(client):
    return _register(client, "bob")


def auth(token):
    return {"Authorization": f"Bearer {token}"}

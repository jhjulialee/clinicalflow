import os
import tempfile
import pytest
from server.app import create_app
from server.extensions import db


@pytest.fixture
def app():
    fd, path = tempfile.mkstemp(suffix=".db")
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{path}",
        "SECRET_KEY": "test-secret",
        "CORS_ORIGIN": "http://localhost:5173",
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
    os.close(fd)
    os.unlink(path)


@pytest.fixture
def client(app):
    return app.test_client()


def signup(client, username, email, password="password123"):
    return client.post("/api/signup", json={"username": username, "email": email, "password": password})

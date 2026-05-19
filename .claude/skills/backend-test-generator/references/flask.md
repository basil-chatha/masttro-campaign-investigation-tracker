# Flask + pytest

## Stack signals

- `flask` in requirements
- `app = Flask(__name__)` and `@app.route(...)` decorators
- Often paired with `flask-sqlalchemy`, `flask-restful`, or `flask-smorest`

## Default toolkit

- **Test framework**: `pytest`
- **HTTP client**: `app.test_client()`
- **DB**: SQLAlchemy with a per-test transaction fixture, or an app-factory pattern with a test config

## App factory pattern

If the project uses `create_app()`, build a fixture that returns a fresh app per test (or per session, depending on cost):

```python
import pytest
from myapp import create_app, db

@pytest.fixture
def app():
    app = create_app(config_name="testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()
```

If the project uses a single global `app` (not the factory pattern), import it and use `app.test_client()` directly — but flag this in the summary; factory pattern is generally healthier for testing.

## Smallest useful test

```python
def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"
```

## Authentication / sessions

Flask's test client supports session manipulation:

```python
def test_logged_in_route(client):
    with client.session_transaction() as sess:
        sess["user_id"] = 1
    response = client.get("/me")
    assert response.status_code == 200
```

For token-based auth, just include the header: `client.get("/me", headers={"Authorization": "Bearer ..."})`.

## Running

```bash
pytest
pytest tests/test_views.py::test_health_returns_200
pytest -k "auth"
```

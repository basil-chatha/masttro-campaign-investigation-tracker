# Django / DRF + pytest-django

## Stack signals

- `django` and often `djangorestframework` in `requirements.txt` / `pyproject.toml`
- `manage.py`, `settings.py`, app directories with `models.py` / `views.py` / `urls.py`
- DRF: `serializers.py`, `viewsets.py`, `@api_view` decorators

## Default toolkit

- **Test framework**: `pytest` + `pytest-django` (preferred), or Django's built-in `python manage.py test`
- **HTTP client**: `Client` (Django) or `APIClient` (DRF). For async views, `AsyncClient`.
- **DB**: `pytest-django` provides `db` and `transactional_db` fixtures backed by a real test database.
- **Factories**: `factory_boy` is the de facto standard; `model_bakery` is a lightweight alternative.

## Where tests live

```text
project/
  app1/
    tests/
      __init__.py
      test_models.py
      test_views.py
      test_serializers.py
  conftest.py
  pytest.ini  (or pyproject.toml [tool.pytest.ini_options])
```

`pytest.ini` must point at settings:

```ini
[pytest]
DJANGO_SETTINGS_MODULE = project.settings.test
python_files = test_*.py
```

## Smallest useful test

```python
import pytest
from rest_framework.test import APIClient

@pytest.fixture
def client():
    return APIClient()

@pytest.mark.django_db
def test_list_campaigns_returns_200(client):
    response = client.get("/api/campaigns/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

## DB fixtures

- `@pytest.mark.django_db` — wraps the test in a transaction that rolls back. Use this for ~90% of tests.
- `@pytest.mark.django_db(transaction=True)` — actually commits; use only when testing things that need real transactions (e.g. `select_for_update`, signals fired on commit).
- `factory_boy`:

```python
import factory
from myapp.models import Campaign

class CampaignFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Campaign

    name = factory.Sequence(lambda n: f"Campaign {n}")
    status = "active"
```

Then in tests: `CampaignFactory()` for one, `CampaignFactory.create_batch(5)` for many.

## Authentication

```python
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.fixture
def authed_client(db):
    user = User.objects.create_user(username="t", password="t")
    client = APIClient()
    client.force_authenticate(user=user)
    return client

def test_protected_route(authed_client):
    assert authed_client.get("/api/me/").status_code == 200
```

For permission tests, instantiate a user with the wrong role and assert 403.

## Models, signals, and managers

- Test custom manager methods directly: `Campaign.objects.active().count()`.
- Test signals by acting on the model and asserting the side effect (don't assert "the signal fired" — assert the *outcome* the signal produces).
- Validators on fields: `instance.full_clean()` should raise `ValidationError` for bad data.

## Running

```bash
pytest                                       # full suite
pytest myapp/tests/test_views.py             # one file
pytest -k campaign                           # name filter
python manage.py test myapp.tests.test_views # Django runner
```

## Common gotchas

- Migrations run on every test session by default; `--reuse-db` speeds reruns.
- DRF `APIClient` defaults to JSON; if your API expects form-encoded, pass `format="multipart"`.
- Don't import Django models at module top in conftest unless `django.setup()` has run — `pytest-django` handles this if `DJANGO_SETTINGS_MODULE` is set.

"""
Tests for the lazy database initialization pattern in app/database.py.

Why this matters: per backend/CLAUDE.md the lazy DB pattern is load-bearing —
the API must boot in fresh checkouts without DATABASE_URL so /health, /docs,
and the test harness work out of the box. If someone moves engine/session
creation to module import (or catches RuntimeError where it gets swallowed),
the workshop fails on day one. These tests pin that contract.
"""
import importlib
import os

import pytest
from sqlalchemy.orm import Session


def _reload_database_module(monkeypatch, database_url):
    """
    Reload app.database with a controlled DATABASE_URL value so we can
    exercise both the "missing" and "present" branches of _init_db without
    relying on whatever the developer happens to have in their .env.
    """
    if database_url is None:
        monkeypatch.delenv("DATABASE_URL", raising=False)
    else:
        monkeypatch.setenv("DATABASE_URL", database_url)

    import app.database as database_module
    importlib.reload(database_module)
    return database_module


def test_init_db_raises_runtime_error_when_database_url_missing(monkeypatch):
    """_init_db() must raise RuntimeError when DATABASE_URL is not set.

    The 503 exception handler in main.py depends on this exact exception type.
    """
    database_module = _reload_database_module(monkeypatch, database_url=None)

    with pytest.raises(RuntimeError) as exc_info:
        database_module._init_db()

    # Message should mention DATABASE_URL so the operator knows what to fix.
    assert "DATABASE_URL" in str(exc_info.value)


def test_get_db_raises_runtime_error_when_database_url_missing(monkeypatch):
    """get_db() is the FastAPI dependency — it must surface the same error.

    Iterating the generator triggers _init_db() before yielding anything.
    """
    database_module = _reload_database_module(monkeypatch, database_url=None)

    gen = database_module.get_db()
    with pytest.raises(RuntimeError):
        next(gen)


def test_engine_is_not_created_at_import_time(monkeypatch):
    """Importing app.database must NOT eagerly construct the engine.

    Regression guard: if someone refactors the module to call create_engine()
    at module level, the API will fail to boot without DATABASE_URL — which
    breaks the documented "boots without a database" contract.
    """
    database_module = _reload_database_module(monkeypatch, database_url=None)

    assert database_module._engine is None
    assert database_module._SessionLocal is None


def test_engine_is_created_lazily_on_first_use(monkeypatch):
    """With a valid URL, _init_db() builds the engine + session factory.

    Uses an in-memory SQLite URL so we don't need a real Postgres around.
    """
    database_module = _reload_database_module(
        monkeypatch, database_url="sqlite:///:memory:"
    )

    assert database_module._engine is None  # not yet built
    database_module._init_db()
    assert database_module._engine is not None
    assert database_module._SessionLocal is not None


def test_init_db_is_idempotent(monkeypatch):
    """Calling _init_db() twice must not rebuild the engine.

    The engine is process-wide; rebuilding it on every request would leak
    connections and silently change pool semantics.
    """
    database_module = _reload_database_module(
        monkeypatch, database_url="sqlite:///:memory:"
    )

    database_module._init_db()
    first_engine = database_module._engine
    database_module._init_db()
    assert database_module._engine is first_engine


def test_get_db_yields_a_session_and_closes_it(monkeypatch):
    """get_db() yields a Session, then closes it on generator cleanup."""
    database_module = _reload_database_module(
        monkeypatch, database_url="sqlite:///:memory:"
    )

    gen = database_module.get_db()
    session = next(gen)
    assert isinstance(session, Session)

    # Closing the generator should close the session without error.
    gen.close()

"""
Unit tests for app/database.py — the lazy DB init contract.

This module is the load-bearing piece called out in backend/CLAUDE.md:

  > database.py does NOT create the SQLAlchemy engine at import time —
  > it builds it on first call to get_db(), raising RuntimeError if
  > DATABASE_URL is missing. main.py registers an exception handler
  > that converts that RuntimeError into a 503 response.

These tests pin that contract directly, so a refactor that moves engine
creation to module import (which would break fresh checkouts) fails loudly.

We deliberately do NOT test that get_db() yields a working session — that
requires Postgres and is covered by the existing 200/503 smoke test in
test_health.py.
"""
import importlib

import pytest


def _reload_database_module(monkeypatch, database_url):
    """Reload app.database with a controlled DATABASE_URL env value.

    The module reads DATABASE_URL at import time into a module-level
    constant, so to test different env states we have to reload it.
    """
    if database_url is None:
        monkeypatch.delenv("DATABASE_URL", raising=False)
    else:
        monkeypatch.setenv("DATABASE_URL", database_url)

    import app.database as database_module
    return importlib.reload(database_module)


def test_get_db_raises_runtime_error_when_database_url_missing(monkeypatch):
    database = _reload_database_module(monkeypatch, database_url=None)

    # Reset cached engine/session — reload sets them to None already,
    # but be explicit so this test is robust to module-level changes.
    database._engine = None
    database._SessionLocal = None

    gen = database.get_db()
    with pytest.raises(RuntimeError) as excinfo:
        next(gen)

    assert "DATABASE_URL" in str(excinfo.value)


def test_init_db_is_idempotent(monkeypatch):
    """Calling _init_db multiple times must not rebuild the engine.
    The lazy-init guard relies on the `if _engine is not None: return`
    check; if that's removed, every request creates a new engine and
    pool_pre_ping connections leak."""
    database = _reload_database_module(
        monkeypatch,
        # Use sqlite in-memory so create_engine succeeds without Postgres.
        database_url="sqlite:///:memory:",
    )
    database._engine = None
    database._SessionLocal = None

    database._init_db()
    first_engine = database._engine
    first_session_factory = database._SessionLocal
    assert first_engine is not None

    database._init_db()
    assert database._engine is first_engine
    assert database._SessionLocal is first_session_factory


def test_get_db_yields_a_session_and_closes_it(monkeypatch):
    """get_db must yield a Session and close it on generator teardown.
    Uses sqlite in-memory so the test doesn't need Postgres."""
    database = _reload_database_module(
        monkeypatch, database_url="sqlite:///:memory:"
    )
    database._engine = None
    database._SessionLocal = None

    gen = database.get_db()
    session = next(gen)

    assert session is not None
    # Trigger the finally block (which calls session.close()).
    with pytest.raises(StopIteration):
        next(gen)

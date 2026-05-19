---
name: backend-test-generator
description: Generates a coherent backend test suite (or fills in gaps in an existing one) for whatever backend lives in the current project — FastAPI, Django/DRF, Flask, Node/Express, NestJS, Rails, Spring Boot, Go net/http, etc. Detects the stack from manifest files, surveys routes/handlers/models/services, and produces runnable tests using the project's existing conventions. Use this skill whenever the user asks to "write tests", "add tests", "generate tests", "improve test coverage", "test my API", "test the backend", "test these endpoints/routes/handlers", "set up pytest/Jest/RSpec", scaffold a test suite, or mentions an untested backend file/route/service — even when they don't explicitly say the word "backend" but are pointing at server-side code (route handlers, controllers, services, models, repositories, queue workers, auth middleware). Trigger eagerly: missing tests are the default state of most repos, so when in doubt, prefer to invoke this skill rather than writing tests freehand.
---

# Backend Test Generator

Generate or extend the backend test suite of the current project. Goal: tests that **actually run, actually fail when the code is broken, and match the project's existing conventions** — not boilerplate that looks like tests but doesn't exercise the system.

## When this skill applies vs. doesn't

This skill is for **server-side / backend** code: HTTP APIs, RPC handlers, queue consumers, background jobs, domain services, ORM models, auth middleware. If the user is asking for frontend component tests, browser E2E flows, or mobile UI tests, this is the wrong skill — back out and use a frontend testing approach instead. If the project is a pure CLI or library with no server layer, you can still apply most of the patterns here, but skip the HTTP/route-discovery steps.

## Workflow

Follow these phases in order. Don't skip phases — skipping detection is how you end up generating tests with the wrong framework or fixtures that don't compose with what already exists.

### Phase 1: Detect the stack

Before writing anything, you must know:

1. **Language and backend framework** — Python/FastAPI? Python/Django? Node/Express? Node/NestJS? Ruby/Rails? Go? Spring? Other?
2. **Test framework already in use** (or expected) — pytest, unittest, Jest, Vitest, Mocha, RSpec, minitest, go test, JUnit, etc.
3. **Database / external dependencies** — Postgres? SQLite? Redis? An external API? An in-memory fake?
4. **Test runner command** — how does the project actually run its tests today (`uv run pytest`, `npm test`, `bundle exec rspec`, `go test ./...`, `./gradlew test`)?

Use these signals, in roughly this priority:

- Repo-root `CLAUDE.md`, `backend/CLAUDE.md`, or any `*/CLAUDE.md` near the backend — they often state the stack and the test command directly. Read these first.
- Manifest files: `pyproject.toml`, `requirements.txt`, `package.json`, `Gemfile`, `go.mod`, `pom.xml`, `build.gradle`, `Cargo.toml`.
- Existing test files / test directories: `tests/`, `__tests__/`, `spec/`, `*_test.go`, `*.test.ts`, `test/` — these are gold. They tell you the framework, the fixture style, the assertion style, and the import/path conventions the project already accepts.
- Config files: `pytest.ini`, `pyproject.toml [tool.pytest.ini_options]`, `jest.config.*`, `vitest.config.*`, `.rspec`, `phpunit.xml`.
- Run scripts: `run.sh`, `Makefile`, npm scripts, `tox.ini`, CI workflow files.

When in doubt, **ask the user one targeted question** rather than guessing — getting the stack wrong wastes everyone's time. But don't ask for things you can read: if `pyproject.toml` says FastAPI and `tests/` uses pytest's `TestClient`, just use that.

After detecting, load the matching stack reference for concrete patterns:

- `references/fastapi.md` — FastAPI + pytest + httpx/TestClient + SQLAlchemy
- `references/django.md` — Django/DRF + pytest-django or Django's test runner
- `references/flask.md` — Flask + pytest + test_client
- `references/express.md` — Node/Express + Jest or Vitest + supertest
- `references/nestjs.md` — NestJS + Jest + Testing module
- `references/rails.md` — Rails + RSpec or minitest + factory_bot/fixtures
- `references/go.md` — Go testing + table tests + httptest
- `references/spring.md` — Spring Boot + JUnit 5 + MockMvc/WebTestClient
- `references/general.md` — Stack-agnostic principles (boundaries, doubles, isolation, naming)

Read **the matching reference plus `general.md`** before writing tests. If the project uses a stack not listed, fall back to `general.md` and follow the patterns of any tests that already exist in the repo.

### Phase 2: Survey the surface area

Don't write tests for files in isolation — write tests for the **public boundaries** of the backend. Build a quick map:

1. **HTTP entry points** — list every route. Look for `@app.get/post/...`, `@router.get/...`, `app.MapGet`, `Route::get`, `match /...`, decorators, route registration calls. Group them by resource.
2. **Domain services / use-cases** — pure functions or service classes that contain business logic. These often have the highest leverage tests.
3. **Persistence layer** — models, repositories, queries. Distinguish "owned by us" (worth testing the queries) from "owned by the framework" (don't test the ORM itself).
4. **External integrations** — anything that calls out: HTTP clients, message queues, third-party SDKs. These need to be faked or stubbed at the seam.
5. **Auth / middleware / cross-cutting** — anything that runs on every request and could silently break.

Write the map down briefly (one or two lines per area) before generating tests. This becomes the test plan and prevents producing 30 tests for one trivial endpoint while leaving a complex auth middleware untested.

### Phase 3: Pick what's worth testing

Coverage for its own sake is a trap. Prefer tests in roughly this priority:

1. **Happy path of every public route** — at least one test per HTTP route that asserts the success status and the shape of the response. This is the single biggest payoff.
2. **Error contracts** — wrong method, missing required field, unauthenticated, not-found, conflict. Pick the ones the project's clients actually depend on; don't enumerate every 4xx.
3. **Authorization rules** — if endpoint X requires role Y, write a test with role Z and assert it's rejected. Auth bugs are catastrophic and easy to miss in review.
4. **Domain service logic with branching** — anything with `if`/`else`, validation, calculations, state transitions, idempotency. Table-driven tests work well here.
5. **Bug regressions** — if the user is generating tests in response to a bug or a recent fix, write a test that **fails on the old code and passes on the new code** before adding anything else.

Skip / deprioritize:

- Trivial getters, framework-generated CRUD that has no custom logic.
- Re-testing the framework or ORM (don't test that `select(...)` returns rows).
- Snapshot tests on volatile fixtures — they break on every legitimate change and teach the team to ignore failures.

If the user pointed at a specific area ("test the campaigns router"), respect that scope — don't expand to the whole repo unprompted.

### Phase 4: Generate

For each test you decide to write:

1. **Match the existing style.** If the project's tests use plain `def test_foo():` with `assert`, do that. If they use class-based `unittest.TestCase`, do that. If they import a `TestClient` a specific way, copy the pattern. Inconsistency makes tests harder to read and signals you didn't look at what's already there.
2. **One behavior per test.** If a test name needs `_and_` to describe what it checks, it's probably two tests.
3. **Name tests for the behavior, not the code.** `test_create_campaign_returns_201_with_id` beats `test_post_campaigns`.
4. **Arrange / Act / Assert** with a blank line between sections in tests that are more than a few lines. Optional but helps readers.
5. **Real boundary, fake everything past it.** For an HTTP test, hit the real route and the real handler. Fake the database only if the project's other tests do; otherwise use the same DB strategy they use (real DB with rollback, in-memory SQLite, testcontainers, etc.). Fake outbound HTTP / email / payment calls — never let tests hit the live internet.
6. **Deterministic.** No `datetime.now()`, no `random` unseeded, no time-of-day dependencies, no relying on dict ordering across language versions. If the code uses time, inject a clock or freeze time in the test.
7. **Honor the project's quirks.** Read any per-project CLAUDE.md again — e.g. in this repo's backend, the `/campaigns` endpoint accepts both `200` and `503` because the DB might not be configured; that's a deliberate test contract, not a smell. Don't "fix" it.

Place new test files where existing tests live. If there are no tests yet, follow the conventional location for that stack (see the relevant reference file).

### Phase 5: Run them and iterate

A test you didn't run isn't a test. Always:

1. Run the project's actual test command. If you don't know it, ask or read the CLAUDE.md / README.
2. If a test fails, read the failure carefully before "fixing" it. Three possibilities: (a) the code has a real bug and the test caught it (good — surface this clearly to the user; don't silently weaken the assertion to make it pass); (b) the test has a wrong expectation (fix the test); (c) the test setup / fixtures are wrong (fix the setup).
3. If a test errors during collection / import (vs. assertion failure), that's almost always a setup or import path issue — fix it before generating more tests.
4. Report a short summary at the end: number of tests added, what they cover, which (if any) revealed real bugs, and the exact command to run them again.

## Output expectations

When you're done in a session, the user should have:

- New or updated test files in the project's conventional test location.
- Tests that pass when run against the current code (unless they intentionally surface a bug — call those out explicitly).
- Any new fixtures or test helpers placed where the project would expect them (`conftest.py`, `tests/fixtures/`, `__tests__/helpers/`, `spec/support/`, etc.) — don't sprinkle helpers inline if the project has a helpers convention.
- A short summary message: what was added, what's covered, what's deliberately *not* covered yet, and the command to run the suite.

## Anti-patterns to avoid

- **Generating tests without running them.** "I wrote 14 tests" is not a deliverable; "I wrote 14 tests and they all pass under `uv run pytest`" is.
- **Testing implementation details** that will break on any refactor — internal method calls, private attribute values, log line contents (unless the log line is part of the public contract).
- **Mocking the system under test.** If you mock the function you're trying to test, you're testing the mock.
- **Copy-pasted assertions.** Five tests that all assert `response.status_code == 200` and nothing else add no signal. Each test should justify its existence by checking something different.
- **Adding tests that paper over a real bug.** If a test only passes because you wrote `assert response.status_code in [200, 500]`, that's not a test — that's an alibi. The one exception is documented project contracts (like the 200/503 case noted above), which should be commented to explain *why* both values are acceptable.

## Stack-specific guidance

Read the appropriate file in `references/` once you've identified the stack. They contain concrete templates, fixture patterns, and the specific testing libraries idiomatic for each ecosystem. Do not try to recall this from memory if a reference file exists — the references are the source of truth and reflect current best practice for the stack.

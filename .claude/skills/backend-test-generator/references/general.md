# General testing principles (stack-agnostic)

These apply regardless of language. Read this *and* the stack-specific file before generating tests.

## What a good backend test looks like

A good test, in roughly decreasing order of importance:

1. **Verifies a real behavior at a real boundary.** Hit the HTTP layer and assert the response. Call the service and assert the side effect or return value. Don't assert internal call sequences unless the call sequence *is* the behavior (e.g. "we must call the audit log before responding").
2. **Fails for the right reason when the code is broken.** If you mutate the implementation (off-by-one, wrong branch), at least one test should fail. If nothing fails, the test wasn't testing anything.
3. **Is deterministic.** Same inputs, same outcome, every run.
4. **Is independent.** Order doesn't matter. Test N doesn't depend on test N-1 having run.
5. **Is fast enough to run on every save.** Unit/integration tests in milliseconds–low seconds. End-to-end is allowed to be slower but should be a small fraction of the suite.

## The boundary principle

Pick a layer to call from the outside. Use the real implementation of everything inside that layer. Replace everything outside it with a controlled fake.

For an HTTP API, the natural outer boundary is "send an HTTP request to the app, assert what came back." This catches routing bugs, validation bugs, serialization bugs, auth bugs, and most business logic bugs in a single test — which is why route-level tests have such a high return on investment.

For a domain service, the natural boundary is "call the service method with arguments, assert return value or observable side effect." Stub out the database / HTTP client / clock at injection points.

What lives *outside* the boundary and should be faked:
- The clock (use an injectable clock or freeze time)
- Random number / UUID generation (seed it, or inject a generator)
- Outbound HTTP, email, SMS, push, payments
- Time-based scheduling
- The filesystem when tests would otherwise pollute it

What stays *real*:
- The framework (FastAPI / Express / Rails — don't fake the framework)
- Your own code paths
- The database, in most cases — use a transactional rollback per test, or a fresh in-memory DB, or testcontainers. Mocked databases routinely hide migration / query bugs.

## Naming

- `test_<scenario>_<expected_outcome>` reads well: `test_create_campaign_returns_201_with_id`, `test_get_campaign_returns_404_when_missing`.
- Avoid names that just restate the function under test (`test_post_campaigns` — what about it?).
- One assertion topic per test. "It returns 200 and the body has an id and the audit log fired" is three tests, or one test with three precisely-named assertions in sequence.

## Fixtures and factories

- Reuse setup. If five tests need a logged-in user, a fixture / factory for "logged-in user" beats five inline blocks.
- Make factories produce minimally-realistic data. A user named `"a"` with email `"a"` is a footgun; the next test that adds a uniqueness constraint will mysteriously break old tests.
- Prefer freshly-built data over sharing mutable objects across tests.

## Table-driven tests

For functions with several input/output pairs, a single parametrized test beats five near-duplicate tests. Each row is a case; the test name should include the case name so failures point at the right row.

## Errors and edge cases

For each public route or service method, ask:
- What happens with missing / malformed input?
- What happens when the user isn't authenticated?
- What happens when the user is authenticated but not authorized?
- What happens at empty / one / many?
- What happens at the boundary (max length, min value, off-by-one)?

You don't need to cover all of these for every endpoint — pick the ones the project's clients actually depend on.

## What *not* to test

- The framework's own behavior. Don't test that `@app.get("/x")` registers a route.
- The ORM. Don't test that `session.add(...)` inserts a row.
- Trivial pass-throughs. A handler that just returns `service.do_thing(request.body)` doesn't need both a handler test and a service test that assert the same thing.
- Logging contents, unless the log is part of the contract (audit logs, structured events consumed downstream).
- Private functions directly. Test the public behavior they participate in. The exception: a complex pure helper might earn its own focused unit test — but if you're tempted to test something private, it's often a sign that helper wants to become public or move into its own module.

## Surfacing real bugs

If a generated test fails because the code is genuinely wrong, do not weaken the assertion. Surface the failure to the user with a specific recommendation: "This test caught a bug — `/campaigns/{id}` returns 200 with `null` instead of 404 when the campaign is missing. Fix the handler, or change the contract." Let them decide.
